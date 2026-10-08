"""core/events.py — händelser kopplade till scener (2.23).

Datahalvan av tidslinjen: en händelse har en tid i berättelsen, en beskrivning
och de scener den spelas i. En händelse kan **återanvändas** — samma avslöjande
nämns i flera scener — så kopplingen är en lista av scen-id:n, inte ett fält på
scenen. Scenen har sin egen tid (`when`) för *var* den ligger; händelsen har sin
för *vad* som händer, och de två behöver inte vara samma.

Ingen ritad vy: en grafisk tidslinje är ett eget beslut (planen avstod från den i
2.9). Det här är tabellen den vyn skulle rita, och den går att läsa och ändra i
`ui/events_dialog.py`.

    python -m core.events      kör självprovet
"""

from __future__ import annotations

import shutil
import tempfile
import uuid


def _new_id() -> str:
    return "e" + uuid.uuid4().hex[:8]


def by_id(project, event_id: str) -> dict | None:
    return next((e for e in project.events if e["id"] == event_id), None)


def add_event(project, text: str = "", when: str = "", scene_ids=()) -> dict:
    """Ny händelse. Tom beskrivning är tillåten — man skriver ofta tiden först."""
    event = {"id": _new_id(), "when": str(when), "text": str(text),
             "scenes": [str(s) for s in scene_ids]}
    project.events.append(event)
    return event


def update_event(project, event_id: str, **fields) -> dict:
    event = by_id(project, event_id)
    if event is None:
        raise KeyError(f"okänd händelse: {event_id}")
    for key in ("when", "text"):
        if key in fields:
            event[key] = str(fields[key])
    if "scenes" in fields:
        event["scenes"] = [str(s) for s in fields["scenes"]]
    return event


def remove_event(project, event_id: str) -> bool:
    event = by_id(project, event_id)
    if event is None:
        return False
    project.events.remove(event)
    return True


def attach(project, event_id: str, node_id: str) -> bool:
    """Koppla en scen till händelsen. Samma scen två gånger blir en koppling."""
    event = by_id(project, event_id)
    if event is None or not node_id:
        return False
    if node_id in event["scenes"]:
        return False
    event["scenes"].append(node_id)
    return True


def detach(project, event_id: str, node_id: str) -> bool:
    event = by_id(project, event_id)
    if event is None or node_id not in event["scenes"]:
        return False
    event["scenes"].remove(node_id)
    return True


def events_of(project, node_id: str) -> list[dict]:
    """Händelserna i en scen, i tidsordning — tom tid sist."""
    egna = [e for e in project.events if node_id in e["scenes"]]
    return sorted(egna, key=lambda e: (not e["when"], e["when"]))


def ordered(project) -> list[dict]:
    """Alla händelser sorterade som plot-tavlans tidslinje: tom tid sist."""
    return sorted(project.events, key=lambda e: (not e["when"], e["when"]))


def scene_titles(project, event: dict) -> list[str]:
    """Scenernas rubriker för en händelse — id:n är till för koden, inte läsaren."""
    ut = []
    for node_id in event["scenes"]:
        try:
            ut.append(project.by_id(node_id).title)
        except KeyError:
            continue          # en scen som tagits bort lämnar ingen tom rad
    return ut


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

    root = tempfile.mkdtemp(prefix="events-check-")
    try:
        project = Project.create(root, "Händelseprov", template="enkel")
        forst = project.manuscript()[0]
        andra = project.add_node("scene", "Andra")

        def händelse(eid, projekt=None):
            """Händelsen, eller ett tydligt fel — provet skall inte gissa."""
            e = by_id(projekt or project, eid)
            if e is None:
                raise AssertionError(f"händelsen {eid} finns inte")
            return e

        kolla(project.events == [], "ett nytt projekt har inga händelser")
        e1 = add_event(project, text="Anna hittar nyckeln", when="dag 3",
                       scene_ids=[forst.id])
        e2 = add_event(project, text="Bo försvinner", when="dag 1")
        kolla(len(project.events) == 2, f"två händelser ({len(project.events)})")
        kolla(e1["id"] != e2["id"], "med var sitt id")

        kolla(attach(project, e1["id"], andra.id) is True, "en scen kan kopplas till")
        kolla(attach(project, e1["id"], andra.id) is False,
              "och samma scen två gånger blir en koppling")
        kolla(len(händelse(e1["id"])["scenes"]) == 2, "två scener på samma händelse")
        kolla(detach(project, e1["id"], andra.id) is True, "och en koppling kan lossas")
        kolla(detach(project, e1["id"], andra.id) is False, "en gång räcker")

        kolla([e["id"] for e in ordered(project)] == [e2["id"], e1["id"]],
              "ordningen är tidsordning med tom tid sist")
        kolla([e["id"] for e in events_of(project, forst.id)] == [e1["id"]],
              "och scenen ser sina egna händelser")
        kolla(events_of(project, andra.id) == [], "en scen utan händelser ger en tom lista")

        update_event(project, e1["id"], when="dag 5", text="Anna hittar nyckeln i lådan")
        igen = händelse(e1["id"])
        kolla(igen["when"] == "dag 5" and "lådan" in igen["text"],
              "en händelse går att ändra")
        kolla(scene_titles(project, igen) == [forst.title],
              f"och scenernas rubriker går att läsa ({scene_titles(project, igen)})")

        project.save()
        omlast = Project.load(project.root)
        kolla(len(omlast.events) == 2 and händelse(e1["id"], omlast)["when"] == "dag 5",
              "händelserna överlever en sparning")
        kolla(händelse(e1["id"], omlast)["scenes"] == [forst.id],
              "med sina scenkopplingar")

        project.delete_node(andra.id)
        kolla(scene_titles(project, händelse(e1["id"])) == [forst.title],
              "en borttagen scen lämnar ingen tom rad i listan")

        kolla(remove_event(project, e2["id"]) is True, "en händelse kan tas bort")
        kolla(remove_event(project, e2["id"]) is False, "och en gång räcker")
        kolla(len(project.events) == 1, f"kvar är en ({len(project.events)})")
        try:
            update_event(project, "finns-inte", text="x")
            kolla(False, "ett okänt id skall ge ett fel")
        except KeyError:
            kolla(True, "och ett okänt id ger ett fel i stället för en tyst no-op")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"events: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
