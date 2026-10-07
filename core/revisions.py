"""Spårade ändringar som operationer (R02.1).

En revision är en operation, inte en färg: den vet vad som stod där förut, vad
som står där nu, och vilket stycke den hör till. Det är formen forskningen pekar
ut — ankare, gammal och ny text, typ, tid — och den enda som går att acceptera
eller avvisa stycke för stycke.

Jämförelsen sker på **blocknivå**: ett stycke ställs mot ett stycke, och två
stycken som ser olika ut i HTML men läser likadant räknas som oförändrade. Det
undviker den falska ändringen som en naiv HTML-diff ger: Qt skriver om
attributen när dokumentet sparas, och en radvis jämförelse skulle kalla det en
ändring. Textdiff *inom* ett ändrat stycke är nästa steg och står i planen.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

# Block som en författare tänker i: de blir varsin enhet i granskningen.
BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "div",
              "blockquote", "pre", "table", "ul", "ol", "tr"}
VOID_TAGS = {"br", "hr", "img", "meta", "link", "input", "col", "source"}
HEAD_TAGS = {"head", "style", "title", "script"}


class _TopLevel(HTMLParser):
    """Hittar de översta blocken och deras läge i källtexten.

    Djupet räknas så att ett `<ul>` med sina `<li>` blir **en** enhet: annars
    kunde en granskning behålla listan men avvisa ett av dess punkter, och kvar
    blev halv HTML. Ett block är en enhet bara om det är komplett.
    """

    def __init__(self, source: str):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.spans: list[tuple[int, int]] = []
        self._rad_start = [0]
        for rad in source.splitlines(keepends=True):
            self._rad_start.append(self._rad_start[-1] + len(rad))
        self._djup = 0
        self._start: int | None = None
        self._i_head = 0

    def _pos(self) -> int:
        rad, kolumn = self.getpos()
        return self._rad_start[min(rad - 1, len(self._rad_start) - 1)] + kolumn

    def handle_starttag(self, tag, attrs):
        if tag in HEAD_TAGS:
            self._i_head += 1
            return
        if self._i_head:
            return
        if tag in VOID_TAGS:
            return
        if tag in BLOCK_TAGS and self._djup == 0 and self._start is None:
            self._start = self._pos()
        self._djup += 1

    def handle_startendtag(self, tag, attrs):
        return              # <br/> och liknande ändrar inget djup

    def handle_endtag(self, tag):
        if tag in HEAD_TAGS:
            self._i_head = max(0, self._i_head - 1)
            return
        if self._i_head or tag in VOID_TAGS:
            return
        self._djup = max(0, self._djup - 1)
        if self._djup == 0 and self._start is not None:
            slut = self.source.find(">", self._pos())
            self.spans.append((self._start, slut + 1 if slut != -1 else self._pos()))
            self._start = None


def blocks(html: str) -> list[str]:
    """HTML:en delad i kompletta block — en delning som alltid går att sätta ihop.

    Bitarna är tillsammans texten oförändrad, och varje bit är ett *komplett*
    element. Därför ger vilket urval av beslut som helst giltig HTML: halva `<ul>`
    kan aldrig bli kvar. Provat i självprovet.
    """
    text = html or ""
    if not text.strip():
        return [text] if text else []
    parser = _TopLevel(text)
    parser.feed(text)
    parser.close()
    if not parser.spans:
        return [text]
    delar, förra = [], 0
    for start, slut in parser.spans:
        if start > förra:
            # mellanrummet före ett block hör till biten innan, så delningen
            # förblir en fullständig partition
            if delar:
                delar[-1] += text[förra:start]
            else:
                delar.append(text[förra:start])
        delar.append(text[start:slut])
        förra = slut
    if förra < len(text):
        if delar:
            delar[-1] += text[förra:]
        else:
            delar.append(text[förra:])
    return delar


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bitar: list[str] = []

    def handle_data(self, data):
        self.bitar.append(data)


def plain(block: str) -> str:
    """Blockets läsbara text — nyckeln jämförelsen görs på."""
    parser = _Text()
    try:
        parser.feed(block)
    except Exception:                                # noqa: BLE001 — trasig HTML
        return re.sub(r"<[^>]+>", "", block)
    return " ".join("".join(parser.bitar).split())


@dataclass
class Change:
    """En revision: vad som stod där, vad som står där, och var."""

    kind: str                      # "added" | "removed" | "changed"
    before: str = ""
    after: str = ""
    anchor: str = ""               # slutet av stycket före ändringen
    index: int = 0                 # plats i granskningens ordning
    block_from: int = 0
    block_to: int = 0

    @property
    def before_text(self) -> str:
        return plain(self.before)

    @property
    def after_text(self) -> str:
        return plain(self.after)


def _slots(before_html: str, after_html: str):
    """Blocken på båda sidor, parade i de enheter en granskning beslutar om.

    Ett omskrivet stycke är ett beslut för sig — inte en klump med grannstycket.
    Bara när antalet stycken skiljer sig (ett stycke som blir tre) slås de ihop
    till ett beslut, och det står i så fall i granskningen.
    """
    före, efter = blocks(before_html), blocks(after_html)
    matcher = difflib.SequenceMatcher(a=[plain(b) for b in före],
                                      b=[plain(b) for b in efter], autojunk=False)
    platser = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                platser.append(("equal", före[i], efter[j]))
        elif tag == "insert":
            for j in range(j1, j2):
                platser.append(("added", "", efter[j]))
        elif tag == "delete":
            for i in range(i1, i2):
                platser.append(("removed", före[i], ""))
        elif (i2 - i1) == (j2 - j1):
            for i, j in zip(range(i1, i2), range(j1, j2)):
                platser.append(("changed", före[i], efter[j]))
        else:
            platser.append(("changed", "".join(före[i1:i2]), "".join(efter[j1:j2])))
    return platser


def _anchor(platser, index: int) -> str:
    """Slutet av stycket före ändringen, så den går att hitta i texten."""
    for i in range(index - 1, -1, -1):
        text = plain(platser[i][1] or platser[i][2])
        if text:
            return text[-60:]
    return ""


def changes(before_html: str, after_html: str) -> list[Change]:
    """Ändringarna från en text till en annan, som operationer."""
    platser = _slots(before_html, after_html)
    ut: list[Change] = []
    for index, (slag, gammal, ny) in enumerate(platser):
        if slag == "equal":
            continue
        ut.append(Change(kind=slag, before=gammal, after=ny,
                         anchor=_anchor(platser, index), index=len(ut)))
    return ut


def apply_changes(before_html: str, after_html: str, decisions) -> str:
    """Texten efter granskningen: behåll eller avvisa varje ändring.

    `decisions` är en följd av "keep" eller "revert", en per ändring i samma
    ordning som `changes` gav dem. Platserna räknas om från samma uppställning
    som ändringarna byggdes ur, så styckena hamnar rätt även när flera ändringar
    ligger efter varandra.

    Ett stycke som är oförändrat behåller filens bytes: jämförelsen läser text,
    men filen är källan. Det som garanteras är att läsningen blir densamma.
    """
    platser = _slots(before_html, after_html)
    beslut = list(decisions)
    bitar, n = [], 0
    for slag, gammal, ny in platser:
        if slag == "equal":
            bitar.append(ny)
            continue
        behåll = True
        if n < len(beslut):
            behåll = str(beslut[n]).lower() in ("keep", "behåll", "1", "true")
        n += 1
        bitar.append(ny if behåll else gammal)
    return "".join(bitar)


# ------------------------------------------------------------------ självprov

def _self_test() -> int:
    checks = 0

    def check(label, got, want):
        nonlocal checks
        assert got == want, f"{label}: fick {got!r}, väntade {want!r}"
        checks += 1

    # delningen är en fullständig partition — annars kan beslut ge halv HTML
    for html in ("<p>a</p><p>b</p>", "text utan block", "",
                 "<head><style>p{}</style></head><body><p>a</p></body>",
                 "<ul><li>a</li><li>b</li></ul><p>c</p>"):
        check(f"delningen av {html[:14]!r} är hel", "".join(blocks(html)), html)
    check("ett ul med två li är en enhet", len(blocks("<ul><li>a</li><li>b</li></ul>")), 1)
    check("och två p blir två enheter", len(blocks("<p>a</p><p>b</p>")), 2)

    gammal = "<p>Hon gick in i källaren.</p><p>Nyckeln låg på bordet.</p>"
    ny = "<p>Hon gick in i källaren.</p><p>Hon stannade.</p><p>Nyckeln låg på bordet.</p>"
    ändringar = changes(gammal, ny)
    check("ett tillägg ger en ändring", len(ändringar), 1)
    check("och den är just ett tillägg", ändringar[0].kind, "added")
    check("med den nya texten", ändringar[0].after_text, "Hon stannade.")
    check("och ett ankare från stycket före", ändringar[0].anchor.endswith("källaren."), True)

    check("behåll allt ger den nya texten", apply_changes(gammal, ny, ["keep"]), ny)
    check("avvisa allt ger den gamla", apply_changes(gammal, ny, ["revert"]), gammal)

    borta = changes(ny, gammal)
    check("borttagningen blir en egen sorts ändring", borta[0].kind, "removed")
    check("och avvisad borttagning ger texten tillbaka",
          apply_changes(ny, gammal, ["revert"]), ny)

    skriven = gammal.replace("låg på bordet", "låg kvar på bordet")
    ändringar = changes(gammal, skriven)
    check("en omskrivning ger en ändrad", [c.kind for c in ändringar], ["changed"])
    check("med båda texterna",
          (ändringar[0].before_text, ändringar[0].after_text),
          ("Nyckeln låg på bordet.", "Nyckeln låg kvar på bordet."))
    check("behållen blir den nya", apply_changes(gammal, skriven, ["keep"]), skriven)
    check("avvisad blir den gamla", apply_changes(gammal, skriven, ["revert"]), gammal)

    # kärnan: en omskrivning av attributen är ingen ändring för en läsare
    om_skriven = '<p style="margin-top:0px;">Hon gick in i källaren.</p><p>Nyckeln låg på bordet.</p>'
    check("nya attribut är ingen ändring", changes(gammal, om_skriven), [])
    # ett oförändrat stycke behåller filens bytes — jämförelsen är text, filen är
    # källan — så det som ska hålla är att läsningen är densamma
    check("och texten läses likadant efter granskningen",
          plain(apply_changes(gammal, om_skriven, [])), plain(gammal))

    # flera ändringar, blandade beslut, i rätt ordning
    tre = gammal.replace("Hon gick in i källaren.", "Hon smög in i källaren.")
    tre = tre.replace("Nyckeln låg på bordet.", "Nyckeln låg på hyllan.")
    ändringar = changes(gammal, tre)
    check("två ändringar", [c.kind for c in ändringar], ["changed", "changed"])
    check("behåll första, avvisa andra",
          apply_changes(gammal, tre, ["keep", "revert"]),
          gammal.replace("Hon gick in i källaren.", "Hon smög in i källaren."))
    check("avvisa första, behåll andra",
          apply_changes(gammal, tre, ["revert", "keep"]),
          gammal.replace("Nyckeln låg på bordet.", "Nyckeln låg på hyllan."))
    check("utan beslut behålls allt", apply_changes(gammal, tre, []), tre)
    check("ingen ändring ger ingen ändring", changes(gammal, gammal), [])

    lista_fore = "<ul><li>a</li><li>b</li></ul>"
    lista_efter = "<ul><li>a</li><li>b</li><li>c</li></ul>"
    check("en ändrad lista är en ändring", len(changes(lista_fore, lista_efter)), 1)
    check("och beslutet ger hel lista",
          apply_changes(lista_fore, lista_efter, ["revert"]), lista_fore)

    print(f"revisions: {checks} kontroller gröna")
    return checks


if __name__ == "__main__":
    _self_test()
