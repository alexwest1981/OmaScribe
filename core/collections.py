"""core/collections.py — samlingar: manuella grupper och sparade sökningar.

En samling är en vy över manuset, inte en kopia: den sparar node-id:n eller en
fråga. Binderordningen rörs aldrig — samlingen pekar på scenerna där de ligger.

Frågan är en rad med villkor, åtskilda av mellanslag, och alla måste stämma:

    status:Utkast            scenens status
    etikett:Anna             någon av scenens etiketter innehåller ordet
    pov:Anna                 scenens synvinkel
    text:havet               ord i scenens text
    havet                    ensamt ord = textsökning

Den här modulen importerar inget från projektet — den får scenens text
skickad till sig — så den går att prova utan projekt och utan Qt.
"""

from dataclasses import dataclass, field
from typing import Iterable
from uuid import uuid4

MANUAL, SEARCH = "manual", "search"
KNOWN_KEYS = ("status", "etikett", "pov", "text")


@dataclass
class Collection:
    """En sparad vy: antingen en handplockad lista eller en fråga."""

    id: str
    name: str
    kind: str = MANUAL
    node_ids: list[str] = field(default_factory=list)
    query: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "kind": self.kind,
                "node_ids": list(self.node_ids), "query": self.query}

    @staticmethod
    def from_dict(data: dict) -> "Collection":
        kind = data.get("kind")
        return Collection(
            id=str(data.get("id") or new_id()),
            name=str(data.get("name") or ""),
            kind=kind if kind in (MANUAL, SEARCH) else MANUAL,
            node_ids=[str(n) for n in (data.get("node_ids") or [])],
            query=str(data.get("query") or ""),
        )

    def contains(self, node_id: str) -> bool:
        return node_id in self.node_ids


def new_id() -> str:
    return f"c_{uuid4().hex[:8]}"


def parse_query(query: str) -> list[tuple[str, str]]:
    """'status:Utkast havet' -> [('status', 'Utkast'), ('text', 'havet')]."""
    terms: list[tuple[str, str]] = []
    for word in (query or "").split():
        key, sep, value = word.partition(":")
        if sep and key.lower() in KNOWN_KEYS and value:
            terms.append((key.lower(), value))
        else:
            # En okänd nyckel ("mål:1000") blir en textsökning efter hela ordet.
            # Bättre att hitta inget än att tyst matcha allt.
            terms.append(("text", word))
    return terms


def matches(node, terms: Iterable[tuple[str, str]], text: str = "") -> bool:
    """Stämmer scenen med alla villkor? (node är valfritt objekt med fälten.)"""
    haystack = (text or "").casefold()
    for key, value in terms:
        target = value.casefold()
        if key == "status":
            if (getattr(node, "status", "") or "").casefold() != target:
                return False
        elif key == "pov":
            if (getattr(node, "pov", "") or "").casefold() != target:
                return False
        elif key == "etikett":
            labels = getattr(node, "labels", None) or []
            if not any(target in label.casefold() for label in labels):
                return False
        else:
            if target not in haystack:
                return False
    return True


def describe(collection: Collection) -> str:
    """Frågan som den skrivs, för verktygstipset."""
    return collection.query.strip() or ("handplockad" if collection.kind == MANUAL else "")


# ------------------------------------------------------------------ självprov

def _self_check() -> int:
    from dataclasses import dataclass as _dc

    @_dc
    class Nod:
        id: str
        status: str = ""
        labels: list = field(default_factory=list)
        pov: str = ""

    checks = 0
    failures: list[str] = []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    terms = parse_query("status:Utkast text:havet")
    check(terms == [("status", "Utkast"), ("text", "havet")], f"frågan delas ({terms})")
    check(parse_query("havet") == [("text", "havet")], "ensamt ord blir textsökning")
    check(parse_query("") == [], "tom fråga ger inga villkor")
    check(parse_query("mål:1000") == [("text", "mål:1000")],
          f"okänd nyckel blir textsökning ({parse_query('mål:1000')})")
    check(parse_query("status:") == [("text", "status:")], "nyckel utan värde blir textsökning")
    check(parse_query("TEXT:havet") == [("text", "havet")], "nyckeln är skiftlägesokänslig")

    utkast = Nod("n_1", status="Utkast", labels=["POV: Anna"], pov="Anna")
    klar = Nod("n_2", status="Klar", labels=["kväll"])
    check(matches(utkast, terms, "Hon seglade ut på havet."), "rätt scen matchar")
    check(not matches(klar, terms, "Hon seglade ut på havet."), "fel status stoppar")
    check(not matches(utkast, terms, "Hon gick hem."), "texten måste finnas")
    check(matches(utkast, parse_query("status:utkast"), ""), "status jämförs utan versaler")
    check(matches(utkast, parse_query("etikett:anna"), ""),
          f"etiketten matchas inuti texten ({utkast.labels})")
    check(not matches(utkast, parse_query("etikett:kalle"), ""), "fel etikett stoppar")
    check(matches(utkast, parse_query("pov:ANNA"), ""), "synvinkeln jämförs utan versaler")
    check(not matches(utkast, parse_query("pov:Bo"), ""), "fel synvinkel stoppar")
    check(matches(utkast, parse_query("status:Utkast etikett:Anna pov:Anna"), ""),
          "flera villkor måste alla stämma")
    check(not matches(utkast, parse_query("status:Klar etikett:Anna"), ""),
          "ett villkor som inte stämmer fäller hela")
    check(matches(Nod("n_3"), parse_query(""), "vad som helst"),
          "en tom fråga matchar allt")

    samling = Collection(id="c_1", name="Bearbetning", kind=SEARCH, query="status:Utkast")
    igen = Collection.from_dict(samling.to_dict())
    check(igen.name == samling.name and igen.query == samling.query, "rundtur genom dict")
    check(Collection.from_dict({"name": "x", "kind": "konstig"}).kind == MANUAL,
          "okänd sort blir handplockad")
    check(Collection.from_dict({"name": "x"}).id, "en samling utan id får ett")
    check(describe(samling) == "status:Utkast", "frågan beskrivs")
    check(describe(Collection(id="c", name="Hand")) == "handplockad", "handplockad beskrivs")

    print(f"collections: {checks - len(failures)} av {checks} kontroller gröna")
    for failure in failures:
        print(f"  ✗ {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
