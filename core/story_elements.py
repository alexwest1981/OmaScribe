"""Story-element per scen (2.19) — Fictionarys frågor, som data.

Källan (R06) belägger tre familjer — Character, Plot, Setting — och de element som
namnges i dem: POV-karaktär och mål, scenfunktion, öppning/avslut, hooks,
tension/conflict, revelation, backstory/flashback, action/sequel, reader
knowledge, plats/tid, sinnen, emotion och weather. Deras fulla lista på 38 element
är **inte** belagd i vår research, och att fylla ut de återstående arton vore att
hitta på en konkurrents taxonomi. De tjugo nedan är de belagda, grupperade i sina
tre familjer — en namnlagd lucka är ärligare än en påhittad rad.

Elementen är data: nyckel, familj och etikett (i18n). Värdet är författarens eget
svar i några ord, för Fictionary ställer frågor och du svarar; "ifyllt" betyder
helt enkelt att svaret inte är tomt. Story Map är samma data summerad per scen,
och den som saknar svar syns som en lucka i stället för att tigas bort.

    python -m core.story_elements      kör självprovet
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile

FAMILIES = ("character", "plot", "setting")

# (nyckel, familj). Ordningen är familjernas, och inom familjen den ordning
# Fictionary frågar i: karaktären först, sedan handlingen, sedan rummet.
ELEMENTS = (
    ("pov_character", "character"),
    ("pov_goal", "character"),
    ("pov_obstacle", "character"),
    ("others_present", "character"),
    ("character_change", "character"),
    ("scene_purpose", "plot"),
    ("opening", "plot"),
    ("hook", "plot"),
    ("tension", "plot"),
    ("revelation", "plot"),
    ("backstory", "plot"),
    ("action_sequel", "plot"),
    ("reader_knowledge", "plot"),
    ("outcome", "plot"),
    ("closing", "plot"),
    ("place", "setting"),
    ("time", "setting"),
    ("senses", "setting"),
    ("weather", "setting"),
    ("emotion", "setting"),
)

KEYS = tuple(key for key, _familj in ELEMENTS)
TOTAL = len(ELEMENTS)


def of_family(family: str) -> tuple[str, ...]:
    """Elementen i en familj, i frågeordning."""
    return tuple(key for key, fam in ELEMENTS if fam == family)


def is_filled(value) -> bool:
    return bool(str(value or "").strip())


def scene_row(node) -> dict:
    """En scens ifyllnad: antal svar per familj och totalt.

    `node.elements` är en dict nyckel -> svar. En äldre nod (eller en nod som
    aldrig fyllts i) saknar den helt, och då är svaret noll — inte ett fel.
    """
    svar = getattr(node, "elements", None) or {}
    by_family = {fam: sum(is_filled(svar.get(key)) for key in of_family(fam))
                 for fam in FAMILIES}
    fyllda = sum(by_family.values())
    return {"node_id": node.id, "title": node.title, "filled": fyllda,
            "total": TOTAL, "by_family": by_family}


def story_map(project, draft: int = 0) -> list[dict]:
    """Varje scen med sin ifyllnad, och vilka element som saknas.

    `draft` följer revisionsläget i plot-tavlan: välj utkast 2 och kartan visar
    bara de scener som nått dit.
    """
    rows = []
    for node in project.manuscript():
        if draft and int(getattr(node, "revision", 1) or 1) != draft:
            continue
        rad = scene_row(node)
        svar = getattr(node, "elements", None) or {}
        rad["missing"] = [key for key in KEYS if not is_filled(svar.get(key))]
        rows.append(rad)
    return rows


def report(project, draft: int = 0) -> dict:
    """Story Map med summan över manuset — underlaget för "var är luckorna".

    `worst_gap` är scenen med flest obesvarade element, för det är den fråga
    siffran skall svara på: var börjar arbetet?
    """
    rows = story_map(project, draft=draft)
    fyllda = sum(rad["filled"] for rad in rows)
    return {"scenes": rows, "filled": fyllda, "total": TOTAL * len(rows),
            "worst_gap": min(rows, key=lambda rad: rad["filled"]) if rows else None}


def _self_check() -> int:
    from core.project import Project

    checks = 0
    failures = 0

    def kolla(ok, text):
        nonlocal checks, failures
        checks += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            failures += 1

    kolla(len(KEYS) == len(set(KEYS)), f"elementnycklarna är unika ({len(KEYS)})")
    kolla(all(fam in FAMILIES for _k, fam in ELEMENTS), "varje element har en känd familj")
    kolla(sum(len(of_family(fam)) for fam in FAMILIES) == TOTAL,
          f"familjerna täcker alla {TOTAL} element")

    # Etiketterna bor i språkfilerna: en ny nyckel utan etikett visar en rå nyckel
    # i gränssnittet, och det är precis vad det här provet skall fånga.
    locales = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locales")
    for lang in ("sv", "en"):
        with open(os.path.join(locales, f"{lang}.json"), encoding="utf-8") as f:
            data = json.load(f)
        saknas = [f"element_{key}" for key in KEYS if f"element_{key}" not in data]
        saknas += [f"element_family_{fam}" for fam in FAMILIES if f"element_family_{fam}" not in data]
        kolla(not saknas, f"{lang}.json har etiketter för alla element ({saknas[:3]})")

    root = tempfile.mkdtemp(prefix="elements-check-")
    try:
        project = Project.create(root, "Elementprov", template="enkel")
        forst = project.manuscript()[0]
        kolla(scene_row(forst)["filled"] == 0, "en scen utan svar är noll ifylld")
        project.set_meta(forst.id, elements={"pov_character": "Anna", "tension": "  ",
                                             "place": "Köket"})
        rad = scene_row(project.by_id(forst.id))
        kolla(rad["filled"] == 2, f"bara svar med innehåll räknas ({rad['filled']})")
        kolla(rad["by_family"]["character"] == 1 and rad["by_family"]["setting"] == 1
              and rad["by_family"]["plot"] == 0, f"och räknas per familj ({rad['by_family']})")
        kolla(len(story_map(project)[0]["missing"]) == TOTAL - 2,
              "Story Map listar de element som saknas")

        andra = project.add_node("scene", "Andra")
        karta = story_map(project)
        kolla(len(karta) == 2 and karta[1]["filled"] == 0, "kartan har en rad per scen")
        summan = report(project)
        kolla(summan["filled"] == 2 and summan["total"] == TOTAL * 2,
              f"och rapporten summerar manuset ({summan['filled']}/{summan['total']})")
        kolla(summan["worst_gap"]["title"] == "Andra",
              f"scenen med flest luckor pekas ut ({summan['worst_gap']['title']})")

        project.set_meta(andra.id, revision=3)
        kolla(len(story_map(project, draft=3)) == 1, "utkastfiltret följer revisionen")

        # Modellen skall bära elementen genom en sparning och en omläsning.
        project.save()
        igen = Project.load(project.root)
        kolla((omläst := igen.by_id(forst.id)).elements.get("place") == "Köket",
              f"elementen överlever en sparning ({omläst.elements})")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"story_elements: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
