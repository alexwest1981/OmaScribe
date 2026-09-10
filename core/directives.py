"""
core/directives.py — textmarkeringar som blir riktig formatering.

Man skriver markeringen som en egen rad och får ett riktigt block:

    [kodblock python]
    def hej():
        print("hej")
    [/kodblock]

    [citat]
    Det man inte kan förklara enkelt har man inte förstått.
    [/citat]

Modulen är ren Python utan Qt, så parsningen kan testas fristående
(`python core/directives.py`). Den bestämmer *vad* som ska bli vad och
vilket språk koden är skriven i — själva formateringen gör core/richtext.py.

Kända stängningar är poängen: en oavslutad [kodblock] lämnas orörd och
rapporteras i stället, så att en halvskriven markering inte förstör texten.
"""

import json
import re
from dataclasses import dataclass, field

# Varje direktiv: öppning med valfritt språk, och en stängning.
_SPECS = {
    "code": {
        "open": r"\[(?:kodblock|kod|code|codeblock)(?:\s+(?P<lang>[A-Za-z0-9_+#.\-]+))?\s*\]",
        "close": r"\[/(?:kodblock|kod|code|codeblock)\s*\]",
    },
    "quote": {
        "open": r"\[(?:citat|quote)\s*\]",
        "close": r"\[/(?:citat|quote)\s*\]",
    },
}

_OPENERS = {
    kind: re.compile(rf"^\s*{spec['open']}\s*$", re.IGNORECASE)
    for kind, spec in _SPECS.items()
}
_CLOSERS = {
    kind: re.compile(rf"^\s*{spec['close']}\s*$", re.IGNORECASE)
    for kind, spec in _SPECS.items()
}

# En rad som består av enbart en hakparentes-markering
_MARKER_LINE = re.compile(r"^\s*\[\/?([^\[\]]{1,24})\]\s*$")
# Stammar ur de riktiga nyckelorden — en felstavning innehåller nästan alltid en
_STEMS = ("kod", "code", "citat", "quote")

KEYWORDS = ("kodblock", "kod", "code", "codeblock", "citat", "quote")


@dataclass
class Directive:
    """Ett hittat direktiv i en text."""

    kind: str
    lang: str = ""
    start_line: int = 0
    end_line: int = -1
    body: str = ""
    closed: bool = False
    start_offset: int = 0
    end_offset: int = 0

    @property
    def n_lines(self) -> int:
        return len(self.body.split("\n")) if self.body else 0


# ------------------------------------------------------------------ parsning

def _line_of(text: str, offset: int) -> int:
    """0-baserat radnummer för en teckenposition."""
    return text.count("\n", 0, offset)


def parse(text: str) -> list:
    """Hittar alla kompletta direktiv i texten.

    Markeringarna får stå på egna rader eller mitt i en rad. Både

        [kodblock]
        koden
        [/kodblock]

    och

        [kodblock]koden[/kodblock]

    känns igen. Bara par räknas — en ensam öppning rapporteras av unclosed().
    """
    src = text or ""
    found = []
    for kind, spec in _SPECS.items():
        rx = re.compile(spec["open"] + r"(?P<body>.*?)" + spec["close"],
                        re.IGNORECASE | re.DOTALL)
        for m in rx.finditer(src):
            groups = m.groupdict()
            found.append(Directive(
                kind=kind,
                lang=(groups.get("lang") or "").strip().lower(),
                start_line=_line_of(src, m.start()),
                end_line=_line_of(src, m.end() - 1),
                body=m.group("body").strip("\n"),
                closed=True,
                start_offset=m.start(),
                end_offset=m.end(),
            ))
    found.sort(key=lambda d: d.start_offset)
    return found


def unclosed(text: str) -> list:
    """[(radnummer 1-baserat, typ)] för markeringar som aldrig stängdes."""
    src = text or ""
    spans = [(d.start_offset, d.end_offset) for d in parse(src)]
    out = []
    for kind, spec in _SPECS.items():
        for m in re.finditer(spec["open"], src, re.IGNORECASE):
            if any(s <= m.start() < e for s, e in spans):
                continue
            out.append((_line_of(src, m.start()) + 1, kind))
    out.sort()
    return out


def suspicious_lines(text: str) -> list:
    """Rader som ser ut som en markering men inte känns igen.

    Fångar till exempel [kodblcok]. Utan den kontrollen skulle en felstavning
    bara bli stående som vanlig text, utan att någon begriper varför ingenting
    hände. Medvetet exakt: raden måste bestå av enbart en hakparentes-markering
    OCH innehålla en av stammarna — ingen tröskel som gissar.
    """
    lines = (text or "").split("\n")
    out = []
    for n, line in enumerate(lines, 1):
        m = _MARKER_LINE.match(line)
        if not m:
            continue
        if any(rx.match(line) for rx in list(_OPENERS.values()) + list(_CLOSERS.values())):
            continue
        token = m.group(1).strip().lower().lstrip("/")
        if any(stem in token for stem in _STEMS):
            out.append((n, line.strip()))
    return out


def strip_markers(text: str) -> str:
    """Tar bort själva markeringstexten men behåller allt innehåll."""
    src = text or ""
    out, last = [], 0
    for d in parse(src):
        out.append(src[last:d.start_offset])
        out.append(d.body)
        last = d.end_offset
    out.append(src[last:])
    return "".join(out)


# ------------------------------------------------------------------ språk

_PY = re.compile(r"(^\s*(def|class|import|from)\s+\w|^\s*if __name__|print\(|elif |self\.)", re.M)
_JS = re.compile(r"(=>|\bconst\s+\w+\s*=|\blet\s+\w+\s*=|function\s+\w*\(|console\.log|===)", re.M)
_TS = re.compile(r"(interface\s+\w+|:\s*(string|number|boolean)\b|\bexport\s+(type|interface))", re.M)
_BASH = re.compile(r"(^#!/(usr/)?bin/|^\s*(sudo|export|echo|cd|chmod|systemctl)\s|\$\(|\|\s*grep)", re.M)
_HTML = re.compile(r"(<!DOCTYPE|<html|</(div|p|span|body|head)>|<[a-z]+ [a-z-]+=)", re.I)
_CSS = re.compile(r"([.#][\w-]+\s*\{[^}]*:[^}]*;|^\s*@media\b)", re.M | re.S)
_SQL = re.compile(r"\b(SELECT\s+.+\s+FROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET|CREATE\s+TABLE)\b", re.I | re.M)
_YAML = re.compile(r"^\s*[\w\-.]+\s*:\s*(\S.*)?$", re.M)
_RUST = re.compile(r"(fn\s+\w+\s*\(|let\s+mut\s+|impl\s+\w+|println!|->\s*Result)", re.M)
_C = re.compile(r"(#include\s*<|int\s+main\s*\(|printf\(|std::)", re.M)
_GO = re.compile(r"(^\s*package\s+\w+|func\s+\w+\s*\(|:=\s*|fmt\.Print)", re.M)

LANGUAGES = ["python", "javascript", "typescript", "bash", "html", "css",
             "sql", "json", "yaml", "rust", "c", "go", "text"]


def detect_language(code: str) -> str:
    """Gissar språket ur koden. Tom sträng om inget känns igen."""
    src = (code or "").strip()
    if not src:
        return ""

    # JSON först — det är entydigt och kan avgöras exakt
    if src[0] in "{[" and src[-1] in "}]":
        try:
            json.loads(src)
            return "json"
        except Exception:
            pass

    checks = [
        ("html", _HTML), ("python", _PY), ("typescript", _TS), ("javascript", _JS),
        ("bash", _BASH), ("sql", _SQL), ("rust", _RUST), ("go", _GO), ("c", _C),
        ("css", _CSS), ("yaml", _YAML),
    ]
    best, score = "", 0
    for name, rx in checks:
        hits = len(rx.findall(src))
        if hits > score:
            best, score = name, hits
    return best if score else ""


def label_for(kind: str, lang: str = "") -> str:
    """Rubrik att visa ovanför blocket."""
    base = "Kod" if kind == "code" else "Citat"
    return f"{base} · {lang}" if lang else base


# ------------------------------------------------------------------ självtest

def _self_test() -> int:
    failures = []

    def check(label, got, want):
        if got != want:
            failures.append(f"{label}: fick {got!r}, väntade {want!r}")

    doc = """Inledning.

[kodblock python]
def hej(namn):
    print(f"Hej {namn}")
[/kodblock]

Mellantext.

[citat]
Enkelt är svårt.
[/citat]

[kodblock]
SELECT * FROM users
[/kodblock]

[kodblock]
detta stängs aldrig
"""

    # parse ger bara kompletta par — den oavslutade rapporteras av unclosed()
    found = parse(doc)
    check("antal kompletta direktiv", len(found), 3)
    check("typer", [d.kind for d in found], ["code", "quote", "code"])
    check("språk på första", found[0].lang, "python")
    check("första är stängd", found[0].closed, True)
    check("första kroppen", found[0].body.splitlines()[0], "def hej(namn):")
    check("tredje är sql utan språkangivelse", found[2].body.strip(), "SELECT * FROM users")
    check("radnummer stämmer", [(d.start_line + 1, d.end_line + 1) for d in found],
          [(3, 6), (10, 12), (14, 16)])
    check("oavslutade", unclosed(doc), [(18, "code")])
    check("den oavslutade är inte ett par", any(d.start_line == 17 for d in found), False)
    check("inga felstavningar här", suspicious_lines(doc), [])

    # strip_markers tar bort markeringarna men behåller innehållet
    stripped = strip_markers(doc)
    # Kompletta markeringar försvinner. Den oavslutade är inte ett direktiv och
    # lämnas kvar som text, så att den går att upptäcka och rätta.
    check("komplett öppning borta", "[kodblock python]" in stripped, False)
    check("komplett stängning borta", "[/kodblock]" in stripped, False)
    check("citatmarkeringar borta", "[citat]" in stripped or "[/citat]" in stripped, False)
    check("oavslutad markering lämnad kvar", "[kodblock]" in stripped, True)
    check("koden kvar", "def hej(namn):" in stripped, True)
    check("citatet kvar", "Enkelt är svårt." in stripped, True)
    check("SQL kvar", "SELECT * FROM users" in stripped, True)
    check("oavslutad text lämnas orörd", "detta stängs aldrig" in stripped, True)

    # språkigenkänning
    check("python", detect_language("import os\n\ndef f():\n    return 1"), "python")
    check("json", detect_language('{"a": 1, "b": [2]}'), "json")
    check("sql", detect_language("SELECT id FROM users WHERE x = 1"), "sql")
    check("bash", detect_language("#!/bin/bash\nsudo systemctl restart nginx"), "bash")
    check("html", detect_language("<div class=\"x\">hej</div>"), "html")
    check("tomt", detect_language(""), "")
    check("okänd text", detect_language("bara vanliga ord här"), "")

    # fellstavad markering ska rapporteras, inte tigas ihjäl
    bad = "[kodblcok]\nkod\n[/kodblcok]\n"
    check("ingen träff på felstavning", len(parse(bad)), 0)
    check("felstavning rapporteras", len(suspicious_lines(bad)), 2)
    check("felstavning namnges", suspicious_lines(bad)[0][1], "[kodblcok]")
    check("godkända markeringar flaggas inte", suspicious_lines(doc), [])
    check("vanlig parentes lämnas i fred", suspicious_lines("Se [1] och [SOU 2024:3]"), [])

    # markering mitt i en rad ska inte trigga
    check("mitt i rad", len(parse("text [kodblock] mer text")), 0)

    # skiftläge
    check("versal", parse("[KODBLOCK]\nx\n[/KODBLOCK]")[0].kind, "code")
    check("engelsk", parse("[code]\nx\n[/code]")[0].kind, "code")

    # formen man skriver mitt i en rad
    inline = parse("Text före [kodblock]x = 1[/kodblock] text efter")
    check("inline hittas", len(inline), 1)
    check("inline kropp", inline[0].body, "x = 1")
    check("inline rad", inline[0].start_line, 0)
    check("inline rensas", strip_markers("Före [kodblock]x = 1[/kodblock] efter"), "Före x = 1 efter")
    check("inline flaggas inte som felstavning",
          suspicious_lines("Före [kodblock]x = 1[/kodblock] efter"), [])
    check("två inline på samma rad",
          [d.body for d in parse("[kod]a[/kod] och [kod]b[/kod]")], ["a", "b"])

    if failures:
        print("SJÄLVTEST MISSLYCKADES:")
        for f in failures:
            print("  ✗", f)
        return 1
    print("✓ Alla direktivtester passerade.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
