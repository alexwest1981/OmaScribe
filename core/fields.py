"""Fält i texten: fotnoter, bildtexter och korsreferenser (R02.5–R02.8).

En markering i texten *räknas fram* i stället för att skrivas. Man skriver

    Det var mörkt i källaren.[not: Hon hade varit där förut, samma vinter.]
    [figur: Källartrappan sedd från hallen.]
    Se [ref: Första kapitlet] för sammanhanget.

och får en numrerad fotnot, en numrerad bildtext och en hänvisning till rätt
kapitel. Numren bestäms av **ordningen i texten**, så att flytta ett stycke är
att numrera om — det är hela skillnaden mellan ett fält och en skriven siffra,
och därför markeringen står kvar i filen i stället för att bli en siffra.

Formen är appens egen: ``[kodblock]`` och ``[citat]`` har sett likadana ut sedan
0b, och den som lärt sig en markering kan de andra. En oavslutad markering utan
stängning lämnas orörd, som direktiven gör.

Ren Python utan Qt — orden sätts av gränssnittet, så modulen är språkoberoende,
och parsningen kan provas fristående (``python core/fields.py``).
"""

import re
from dataclasses import dataclass

# Skrivsätten som gäller, med svenska och engelska ord för samma sak.
KINDS = {
    "not": "note", "fotnot": "note", "note": "note", "footnote": "note",
    "figur": "figure", "bild": "figure", "figure": "figure",
    "tabell": "table", "table": "table",
    "ref": "ref", "referens": "ref", "reference": "ref",
}

# De slag som får ett löpnummer.
NUMBERED = ("note", "figure", "table")

_FIELD = re.compile(
    r"\[(not|fotnot|note|footnote|figur|bild|figure|tabell|table|ref|referens|reference)"
    r"\s*:\s*([^\[\]\n]*)\]", re.IGNORECASE)


@dataclass
class Field:
    """En hittad markering, med sitt nummer i ordningen."""

    kind: str          # note, figure, table eller ref
    value: str         # texten innanför markeringen
    start: int         # teckenposition i texten
    end: int
    number: int = 0    # löpnummer inom sitt slag (ref har inget)

    @property
    def marker(self) -> str:
        return f"[{self.value}]" if self.kind == "ref" else self.value


def fields(text: str) -> list[Field]:
    """Alla markeringar i texten, numrerade i den ordning de står."""
    found: list[Field] = []
    räknare: dict[str, int] = {}
    for träff in _FIELD.finditer(text or ""):
        kind = KINDS.get(träff.group(1).casefold())
        if kind is None:
            continue
        if kind in NUMBERED:
            räknare[kind] = räknare.get(kind, 0) + 1
        found.append(Field(kind, träff.group(2).strip(), träff.start(),
                           träff.end(), räknare.get(kind, 0)))
    return found


def counters(text: str) -> dict[str, int]:
    """Antal av varje slag — det panelen och registren visar."""
    ut = {kind: 0 for kind in NUMBERED}
    for field in fields(text):
        if field.kind in ut:
            ut[field.kind] += 1
    return ut


def of_kind(text: str, kind: str) -> list[Field]:
    """Markeringarna av ett slag, i ordning, med sina nummer."""
    return [field for field in fields(text) if field.kind == kind]


def number_headings(levels: list[int]) -> list[str]:
    """Kapitelnumren ur rubriknivåerna: 1, 1.1, 1.2, 2 (R02.7).

    Nivåerna kommer från dokumentets rubriker i ordning (1 = kapitel, 2 =
    avsnitt). En nivå som hoppar över ett steg (1 → 3) räknas ändå, för en
    rubrik som saknas får inte flytta numren på allt efter sig — den blir 1.1,
    inte 1.0.1. Dokumentets **första** rubrik sätter den yttersta nivån, så en
    bok som börjar på nivå 2 får sitt första kapitel som 1 och inte som 0.1.
    """
    if not levels:
        return []
    bas = max(1, int(levels[0]))
    nummer: list[int] = []
    ut: list[str] = []
    for nivå in levels:
        nivå = max(1, int(nivå) - bas + 1)
        if len(nummer) < nivå:
            nummer.extend([0] * (nivå - len(nummer)))
        elif len(nummer) > nivå:
            nummer = nummer[:nivå]
        nummer[nivå - 1] += 1
        ut.append(".".join(str(n) for n in nummer if n))
    return ut


def ref_number(value: str, headings: list[str], numbers: list[str]) -> str | None:
    """Vilket kapitelnumret en hänvisning pekar på, om rubriken finns.

    Jämförelsen ser förbi skiftläge och inledande nummer, så både
    ``[ref: Första kapitlet]`` och ``[ref: 1. Första kapitlet]`` träffar samma
    rubrik. Saknas rubriken blir svaret None, och då står markeringen kvar som
    den är — hellre en synlig hänvisning som inte stämmer än en tyst felaktig.
    """
    def nyckel(text: str) -> str:
        rent = re.sub(r"^\s*\d+(\.\d+)*\.?\s*", "", text or "")
        return " ".join(rent.split()).casefold()

    sökt = nyckel(value)
    if not sökt:
        return None
    for index, rubrik in enumerate(headings):
        if nyckel(rubrik) == sökt:
            return numbers[index] if index < len(numbers) else None
    return None


def _self_test() -> int:
    grönt = 0

    def check(namn: str, fick, väntat) -> None:
        nonlocal grönt
        assert fick == väntat, f"{namn}: {fick!r} != {väntat!r}"
        grönt += 1

    text = ("Källaren var mörk.[not: Hon hade varit där förut.] "
            "[figur: Trappan från hallen.] Se [ref: Andra kapitlet]. "
            "[not: Och ljuset.] "
            "[tabell: Ord per kapitel.]")
    hittade = fields(text)
    check("alla markeringar hittas", len(hittade), 5)
    check("slagen blir rätt", [f.kind for f in hittade],
          ["note", "figure", "ref", "note", "table"])
    check("noterna numreras i ordning", [f.number for f in hittade if f.kind == "note"], [1, 2])
    check("figurer och tabeller har egna serier",
          [(f.kind, f.number) for f in hittade if f.kind in ("figure", "table")],
          [("figure", 1), ("table", 1)])
    check("räknaren ger antal per slag", counters(text), {"note": 2, "figure": 1, "table": 1})
    check("slaget kan filtreras", [f.value for f in of_kind(text, "note")],
          ["Hon hade varit där förut.", "Och ljuset."])

    # Kapitelnumren ur nivåerna — och att en överhoppad nivå inte flyttar resten
    check("kapitelnumren följer nivåerna", number_headings([1, 2, 2, 1, 2]),
          ["1", "1.1", "1.2", "2", "2.1"])
    check("en överhoppad nivå hoppar över nollan", number_headings([1, 3, 3]),
          ["1", "1.1", "1.2"])
    check("ett dokument som börjar på nivå 2 räknas från sin egen nivå",
          number_headings([2, 2, 3]), ["1", "2", "2.1"])
    check("och nivåer som går uppåt igen fortsätter", number_headings([2, 1]),
          ["1", "2"])
    check("inga rubriker ger inga nummer", number_headings([]), [])

    rubriker = ["Första kapitlet", "Andra kapitlet"]
    nummer = ["1", "2"]
    check("en hänvisning hittar sitt kapitel",
          ref_number("Andra kapitlet", rubriker, nummer), "2")
    check("skiftläge spelar ingen roll",
          ref_number("andra KAPITLET", rubriker, nummer), "2")
    check("och ett inledande nummer i rubriken stör inte",
          ref_number("Andra kapitlet", ["1. Första kapitlet", "2. Andra kapitlet"], nummer), "2")
    check("en rubrik som inte finns ger inget svar",
          ref_number("Tredje kapitlet", rubriker, nummer), None)
    check("och tom hänvisning ger inget svar", ref_number("  ", rubriker, nummer), None)

    # Former: svenska och engelska ska betyda samma sak
    check("engelska ord fungerar", [f.kind for f in fields("[note: x] [figure: y]")],
          ["note", "figure"])
    check("och svenska med versaler", [f.kind for f in fields("[NOT: x]")], ["note"])
    # En halvskriven markering ska lämnas orörd, som direktiven
    check("oavslutad markering rörs inte", fields("Här [not: utan slut"), [])
    check("och vanliga hakparenteser är inget fält", fields("se [bilaga 3]"), [])
    return grönt


if __name__ == "__main__":
    print(f"fields: {_self_test()} kontroller gröna")
