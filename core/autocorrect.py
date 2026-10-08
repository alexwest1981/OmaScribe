"""Small, dependency-free autocorrect and autotext helpers for OmaScribe."""

from __future__ import annotations

from dataclasses import dataclass
import json
import difflib
import re
import sys
import tempfile
from pathlib import Path


@dataclass
class Rule:
    pattern: str
    replacement: str
    kind: str
    enabled: bool = True


_BUILTIN_RULES = (
    Rule("teskt", "test", "word"),
    Rule("teh", "the", "word"),
    Rule("recieve", "receive", "word"),
    Rule("seperat", "separat", "word"),
    Rule("definately", "definitely", "word"),
    Rule("adress", "address", "word"),
)


class Autocorrect:
    """Apply safe whole-word corrections and expand user-defined text snippets."""

    def __init__(self, rules_path: str | None = None):
        self.rules_path = Path(rules_path) if rules_path is not None else None
        self.last_error: str | None = None
        self.rules: list[Rule] = list(_BUILTIN_RULES)
        if self.rules_path is not None:
            self.load()

    @staticmethod
    def _valid_rule(pattern: str, replacement: str, kind: str) -> bool:
        # Empty and one-character patterns are rejected to avoid broad, unsafe rules.
        if not isinstance(pattern, str) or len(pattern) < 2 or not pattern.strip():
            return False
        if not isinstance(replacement, str) or kind not in ("word", "text"):
            return False
        # A rule may never replace its own result; apply is also deliberately single-pass.
        if pattern.casefold() == replacement.casefold():
            return False
        return True

    def load(self) -> None:
        """Load user rules; a broken file leaves only the built-ins available."""
        self.last_error = None
        self.rules = list(_BUILTIN_RULES)
        if self.rules_path is None or not self.rules_path.exists():
            return
        try:
            data = json.loads(self.rules_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Rules file must contain a JSON list")
            user_rules: list[Rule] = []
            for item in data:
                if not isinstance(item, dict):
                    raise ValueError("Each rule must be a JSON object")
                pattern = item.get("pattern")
                replacement = item.get("replacement")
                kind = item.get("kind")
                enabled = item.get("enabled", True)
                if not isinstance(enabled, bool) or not self._valid_rule(pattern, replacement, kind):
                    raise ValueError("Invalid rule in rules file")
                user_rules.append(Rule(pattern, replacement, kind, enabled))
            # User rules replace built-ins with a matching pattern (case-insensitive).
            by_pattern = {rule.pattern.casefold(): rule for rule in _BUILTIN_RULES}
            by_pattern.update({rule.pattern.casefold(): rule for rule in user_rules})
            self.rules = list(by_pattern.values())
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            self.last_error = str(exc)
            self.rules = list(_BUILTIN_RULES)

    @staticmethod
    def _case_match(word: str, replacement: str) -> str:
        if word.isupper():
            return replacement.upper()
        if word[:1].isupper() and word[1:].islower():
            return replacement[:1].upper() + replacement[1:].lower()
        return replacement

    def apply(self, word: str) -> str:
        """Correct one complete plain word, preserving common capitalization."""
        if not isinstance(word, str) or not word:
            return word
        # Never edit a substring: code, paths, URLs, snake_case, and camelCase stay intact.
        if not re.fullmatch(r"[^\W_]+", word, flags=re.UNICODE):
            return word
        if any(char.isupper() for char in word[1:]) and not word.isupper():
            return word
        for rule in self.rules:
            if rule.enabled and rule.kind == "word" and word.casefold() == rule.pattern.casefold():
                if rule.pattern.casefold() == rule.replacement.casefold():
                    return word
                return self._case_match(word, rule.replacement)
        return word

    def apply_typography(self, text: str) -> str:
        """Apply paragraph typography without changing fractions such as 1/2."""
        text = text.replace("...", "…").replace(" -- ", " – ")
        # Paired straight quotes use Swedish quotation marks; unmatched quotes remain untouched.
        return re.sub(r'"([^"\n]*)"', lambda match: f"”{match.group(1)}”", text)

    def expand(self, prefix: str) -> str | None:
        for rule in self.rules:
            if rule.enabled and rule.kind == "text" and rule.pattern == prefix:
                return rule.replacement
        return None

    def candidates(self, prefix: str, limit: int = 8) -> list[Rule]:
        if limit <= 0:
            return []
        return [rule for rule in self.rules if rule.enabled and rule.kind == "text" and rule.pattern.startswith(prefix)][:limit]

    def add_rule(self, pattern: str, replacement: str, kind: str = "word") -> None:
        if not self._valid_rule(pattern, replacement, kind):
            raise ValueError("Rule must have a pattern of at least two characters and a different replacement")
        self.rules = [rule for rule in self.rules if rule.pattern.casefold() != pattern.casefold()]
        self.rules.append(Rule(pattern, replacement, kind))

    def remove_rule(self, pattern: str) -> None:
        self.rules = [rule for rule in self.rules if rule.pattern.casefold() != pattern.casefold()]

    def save(self) -> None:
        if self.rules_path is None:
            raise ValueError("No rules path configured")
        self.rules_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [rule.__dict__ for rule in self.rules]
        self.rules_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def changed_spans(before: str, after: str) -> list[tuple[int, int, str]]:
    """Varje sammanhängande ändring som (start, slut, ny text) — tom om lika.

    Gränssnittet skriver bara om de här områdena i stället för hela stycket: ett
    helt stycke i taget hade plattat ut fet och kursiv stil i resten av det.
    Ändringarna ligger i stigande ordning, så de ska läggas på plats bakifrån.
    """
    if before == after:
        return []
    return [(i1, i2, after[j1:j2])
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
                a=before, b=after, autojunk=False).get_opcodes()
            if tag != "equal"]


def _self_test() -> int:
    checks = 0

    assert changed_spans("Hej", "Hej") == []
    assert changed_spans('Sa "hej"', "Sa \u201dhej\u201d") == [(3, 4, "\u201d"), (7, 8, "\u201d")]
    assert changed_spans("Hej", "Hej!") == [(3, 3, "!")]
    # Två rättelser runt ett ord: ordet emellan ska inte röras, för där sitter
    # formateringen. Det här är hela poängen med områdena i stället för ett svep.
    assert changed_spans('Sa "hej" och ...', 'Sa \u201dhej\u201d och \u2026') == [
        (3, 4, "\u201d"), (7, 8, "\u201d"), (13, 16, "\u2026")]

    def check(condition: bool) -> None:
        nonlocal checks
        assert condition
        checks += 1

    autocorrect = Autocorrect()
    check(autocorrect.apply("teskt") == "test")
    check(autocorrect.apply("Teskt") == "Test")
    check(autocorrect.apply("TESKT") == "TEST")
    check(autocorrect.apply("tesktext") == "tesktext")
    check(autocorrect.apply("http://teskt.se") == "http://teskt.se")
    check(autocorrect.apply("/usr/teskt/bin") == "/usr/teskt/bin")
    check(autocorrect.apply("camelTeskt") == "camelTeskt")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "rules.json"
        path.write_text(json.dumps([{"pattern": "teskt", "replacement": "proof", "kind": "word"}]), encoding="utf-8")
        custom = Autocorrect(str(path))
        check(custom.apply("teskt") == "proof")
        path.write_text("{broken", encoding="utf-8")
        broken = Autocorrect(str(path))
        check(broken.apply("teskt") == "test" and bool(broken.last_error))
        broken.add_rule(";adr", "Example Street 1", "text")
        check(broken.expand(";unknown") is None)
        check(broken.expand(";adr") == "Example Street 1")
    typo = autocorrect.apply_typography('Wait... "citat" 1/2')
    check("…" in typo and "1/2" in typo and '”citat”' in typo)
    autocorrect.add_rule("teskt", "proof", "word")
    once = autocorrect.apply("teskt")
    check(autocorrect.apply(once) == once)
    check(not Autocorrect._valid_rule("a", "aa", "word"))
    print(f"autocorrect: {checks} kontroller gröna")
    return checks


if __name__ == "__main__":
    _self_test()
