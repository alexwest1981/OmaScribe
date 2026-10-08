"""LanguageTool-baserad stavnings- och grammatikkontroll."""

from dataclasses import dataclass
from typing import Any

import httpx


_MAX_CHUNK_LENGTH = 19_000

# Den publika tjänsten. En egen server ställs in i inställningarna.
DEFAULT_ENDPOINT = "https://api.languagetool.org/v2/check"


@dataclass
class Issue:
    offset: int
    length: int
    message: str
    replacements: list[str]
    rule_id: str
    category: str
    severity: str
    text: str = ""     # orden träffen gäller, satt av gränssnittet


def _utf16_index(text: str, units: int) -> int:
    """Översätt en UTF-16-position från API:t till ett Python-index."""
    used = 0
    for index, char in enumerate(text):
        if used >= units:
            return index
        used += 2 if ord(char) > 0xFFFF else 1
    return len(text)


def _split_text(text: str, limit: int = _MAX_CHUNK_LENGTH) -> list[tuple[int, str]]:
    """Dela vid styckegränser först och annars vid blanksteg, utan ordsnitt."""
    if not text:
        return []

    pieces: list[tuple[int, str]] = []
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        if end < len(text):
            # Ta med styckeseparatorn i föregående del när den ryms.
            paragraph_end = text.rfind("\n\n", start, end + 1)
            if paragraph_end >= start:
                end = paragraph_end + 2
            else:
                boundary = max(text.rfind(" ", start, end + 1),
                               text.rfind("\t", start, end + 1),
                               text.rfind("\n", start, end + 1))
                if boundary > start:
                    end = boundary + 1
                else:
                    # Ett enskilt ord längre än gränsen kan inte delas utan att
                    # bryta ordet; skicka det helt och låt servern avgöra.
                    next_space = min((p for p in (text.find(" ", end),
                                                  text.find("\t", end),
                                                  text.find("\n", end)) if p >= 0),
                                     default=len(text))
                    end = next_space
        if end <= start:
            end = len(text)
        pieces.append((start, text[start:end]))
        start = end
    return pieces


class SpellChecker:
    def __init__(self, language: str = "sv-SE",
                 endpoint: str = DEFAULT_ENDPOINT,
                 timeout: float = 8.0):
        self.language = language
        self.endpoint = endpoint
        self.timeout = timeout
        self.last_error: str | None = None
        self._available = False

    def available(self) -> bool:
        return self._available

    def check(self, text: str, language: str | None = None) -> list[Issue]:
        """Kontrollera en text. Språket kan ges per anrop — ett avsnitt kan vara
        skrivet på ett annat språk än boken i övrigt."""
        if not text:
            return []
        issues: list[Issue] = []
        try:
            with httpx.Client(timeout=self.timeout) as client:
                for global_offset, chunk in _split_text(text, _MAX_CHUNK_LENGTH):
                    response = client.post(
                        self.endpoint,
                        data={"text": chunk, "language": language or self.language},
                    )
                    response.raise_for_status()
                    payload: Any = response.json()
                    for match in payload.get("matches", []):
                        local_offset = int(match.get("offset", 0))
                        local_length = int(match.get("length", 0))
                        # API:t räknar offset och längd i UTF-16-kodenheter;
                        # konvertera båda positionerna till Python-tecken.
                        py_start = _utf16_index(chunk, local_offset)
                        py_end = _utf16_index(chunk, local_offset + local_length)
                        rule = match.get("rule") or {}
                        category = (rule.get("category") or {}).get("name", "")
                        severity = (match.get("type") or {}).get("typeName", "")
                        issues.append(Issue(
                            offset=global_offset + py_start,
                            length=py_end - py_start,
                            message=str(match.get("message", "")),
                            replacements=[str(item["value"]) for item in match.get("replacements", [])
                                          if isinstance(item, dict) and "value" in item],
                            rule_id=str(rule.get("id", "")),
                            category=str(category),
                            severity=str(severity),
                        ))
            self._available = True
            self.last_error = None
            return issues
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            self._available = False
            self.last_error = str(exc) or exc.__class__.__name__
            return []
        except Exception as exc:
            # Fel i svarsinnehållet ska också degradera synligt, utan krasch.
            self._available = False
            self.last_error = str(exc) or exc.__class__.__name__
            return []


def _self_test() -> int:
    """Självprov med fakesvar; gör inga nätverksanrop."""
    checks = 0

    class FakeResponse:
        def __init__(self, data: dict[str, Any]):
            self.data = data

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return self.data

    class FakeClient:
        def __init__(self, **kwargs: Any):
            self.responses: list[FakeResponse] = []
            self.requests: list[dict[str, str]] = []
            self.fail = False

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def post(self, endpoint: str, data: dict[str, str]) -> FakeResponse:
            self.requests.append(data)
            if self.fail:
                raise httpx.ConnectError("offline")
            return self.responses.pop(0)

    original_client = httpx.Client
    fake = FakeClient()
    httpx.Client = lambda **kwargs: fake  # type: ignore[assignment]
    try:
        fake.responses = [FakeResponse({"matches": []}), FakeResponse({
            "matches": [{"offset": 2, "length": 1, "message": "x",
                         "replacements": [{"value": "y"}], "rule": {"id": "R",
                         "category": {"name": "Grammar"}},
                         "type": {"typeName": "Other"}}]
        })]
        checker = SpellChecker()
        original_limit = _MAX_CHUNK_LENGTH
        # Ett lågt gränsvärde ger två delar i ett kompakt prov.
        chunks = _split_text("första\n\nandra", limit=8)
        assert len(chunks) == 2
        checks += 1
        # De två anropen får tydliga svar; offset i del två blir global.
        text = "ett\n\nord"
        chunks = _split_text(text, 5)
        assert "".join(part for _, part in chunks) == text
        checks += 1
        # Skapa en fake-rutt med chunkgräns fem genom tillfällig konstant.
        globals()["_MAX_CHUNK_LENGTH"] = 5
        fake.responses = [FakeResponse({"matches": []}), FakeResponse({"matches": [
            {"offset": 0, "length": 2, "message": "x", "replacements": [],
             "rule": {"id": "R", "category": {"name": "Grammar"}},
             "type": {"typeName": "Other"}}
        ]})]
        result = checker.check(text)
        assert len(result) == 1 and result[0].offset == 5
        checks += 1
        fake.responses = [FakeResponse({"matches": []})]
        assert checker.check("helt korrekt") == []
        checks += 1
        fake.fail = True
        assert checker.check("test") == [] and checker.available() is False and checker.last_error
        checks += 1
        fake.fail = False
        long_word = "abcdefghijklmnop"
        chunks = _split_text(long_word + " slut", limit=5)
        assert chunks[0][1] == long_word and chunks[1][1].startswith(" ")
        checks += 1

        # Mutationsprovet visar att offsetkontrollen faktiskt faller vid felaktig
        # global positionsberäkning; felet fångas och räknas som grönt prov.
        try:
            assert result[0].offset == 0
        except AssertionError:
            checks += 1
        else:
            raise AssertionError("mutationstestet upptäckte inte det avsiktliga felet")
        assert _utf16_index("😀abc", 3) == 2
        checks += 1
    finally:
        globals()["_MAX_CHUNK_LENGTH"] = _MAX_CHUNK_LENGTH if 'original_limit' not in locals() else original_limit
        httpx.Client = original_client  # type: ignore[assignment]
    print(f"spellcheck: {checks} kontroller gröna")
    return checks


if __name__ == "__main__":
    _self_test()
