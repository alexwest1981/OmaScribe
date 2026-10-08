"""Övningar mot skrivblock — "vad händer nu?" (R03.16).

Forskningen är tydlig med arbetsflödet: markera text eller välj scen, välj en
fråga, granska förslagen, välj eller ignorera, och återgå till skrivandet. Det
här är den lokala, provbara delen: kategorierna, frågan som byggs, och
tolkningen av svaret. Själva anropet gör AI-klienten, som redan finns.
"""
from __future__ import annotations

import re

# (nyckel, etikett, instruktion, antal) — vägar in när det låser sig, och två
# generatorer för namn och ord. Antalet står per kategori: tre vägar vidare är
# lagom att välja mellan, tolv namn är lagom att välja ur.
CATEGORIES = (
    ("next", "Vad händer nu?", "Föreslå tre helt olika vägar vidare härifrån.", 3),
    ("dialogue", "Dialog", "Föreslå tre rader dialog som kan komma härnäst.", 3),
    ("action", "Handling", "Föreslå tre konkreta saker som kan hända just nu.", 3),
    ("senses", "Sinnesintryck", "Föreslå tre sinnesintryck att lägga in här.", 3),
    ("namn", "Namn", "Föreslå namn som passar i den här boken och på den här platsen. "
                     "Skriv ett namn per rad, följt av ett tankstreck och en kort not om vem "
                     "personen kunde vara.", 12),
    ("ord", "Ord och uttryck", "Föreslå ord och uttryck ur den här tidens och platsens språk. "
                               "Ett per rad, följt av ett tankstreck och en kort förklaring.", 12),
)

SYSTEM = (
    "Du är en svensk skrivcoach åt en författare som har fastnat. Föreslå {n} "
    "korta, konkreta alternativ — ett per rad, numrerade 1–{n}, högst en mening "
    "var. Ingen inledning, ingen sammanfattning, ingen färdig prosa: författaren "
    "skriver själv. Svara på {lang}."
)

_NUMMER = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s*")


def category(key: str):
    """Kategorin med den nyckeln, eller None."""
    for rad in CATEGORIES:
        if rad[0] == key:
            return rad
    return None


def build_prompt(category_key: str, selection: str = "", scene_note: str = "",
                 chapter: str = "", lang: str = "svenska"):
    """System- och användarprompt för en övningsfråga.

    Fältet medvetet samma form som forskningens arbetsflöde: vald text om det
    finns en, annars scenens sammanhang (rubrik och anteckning).
    """
    rad = category(category_key) or CATEGORIES[0]
    antal = rad[3] if len(rad) > 3 else 3
    bitar = [f"Uppgift: {rad[2]}"]
    if chapter.strip():
        bitar.append(f"Scen: {chapter.strip()}")
    if scene_note.strip():
        bitar.append(f"Författarens egen anteckning om scenen: {scene_note.strip()}")
    if selection.strip():
        bitar.append("Vald text:\n" + selection.strip())
    else:
        bitar.append("Ingen text är markerad — föreslå något som kan hända i scenen.")
    return SYSTEM.format(lang=lang, n=antal), "\n\n".join(bitar)


def max_suggestions(key: str) -> int:
    """Hur många alternativ en kategori ber om."""
    rad = category(key)
    return (rad[3] if rad and len(rad) > 3 else 3)


def parse_suggestions(text: str, max_n: int = 3):
    """Tolkningen av svaret: numrerade eller punktade rader blir förslag.

    Modellen får instruktionen att ge en per rad, men den lägger ibland till en
    inledning; tomma rader och en eventuell inledningsrad faller bort här.
    """
    förslag = []
    for rad in (text or "").splitlines():
        rent = _NUMMER.sub("", rad).strip()
        if rent:
            förslag.append(rent)
    return förslag[:max_n]


def _self_test() -> int:
    checks = 0
    assert len(CATEGORIES) == 6 and category("next")[1] == "Vad händer nu?"; checks += 1
    assert category("finns-inte") is None; checks += 1

    system, user = build_prompt("dialogue", "Hon öppnade dörren.", "nyckeln ligger i lådan", "Kapitel 3")
    assert "skrivcoach" in system and "svenska" in system; checks += 1
    assert "Dialog" in user or "dialog" in user; checks += 1
    assert "Hon öppnade dörren." in user and "nyckeln ligger i lådan" in user; checks += 1
    assert "Kapitel 3" in user; checks += 1
    _, utan = build_prompt("next")
    assert "Ingen text är markerad" in utan; checks += 1
    assert "öppnade" not in utan; checks += 1

    svar = "1. Hon går in i rummet.\n2) Hon stannar på tröskeln.\n- Hon ropar.\n\n4. Fjärde förslaget\n"
    förslag = parse_suggestions(svar)
    assert förslag == ["Hon går in i rummet.", "Hon stannar på tröskeln.", "Hon ropar."], förslag; checks += 1
    assert len(parse_suggestions(svar, max_n=1)) == 1; checks += 1
    assert parse_suggestions("") == [] and parse_suggestions(None) == []; checks += 1
    assert max_suggestions("next") == 3 and max_suggestions("namn") == 12; checks += 1
    assert category("ord")[1] == "Ord och uttryck"; checks += 1
    tolv = "\n".join(f"{i}. Namn {i} — kort not" for i in range(1, 15))
    assert len(parse_suggestions(tolv, max_n=max_suggestions("namn"))) == 12; checks += 1
    assert "Namn 1 — kort not" in parse_suggestions(tolv)[0]; checks += 1
    print(f"exercises: {checks} kontroller gröna")
    return checks


if __name__ == "__main__":
    _self_test()
