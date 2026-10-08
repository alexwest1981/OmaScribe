"""Numeric reports derived from an Scribentia project and its story bible."""

from __future__ import annotations

import tempfile
from collections import defaultdict
from pathlib import Path

from core.project import CHAPTER, PART, SCENE, Project
from core.storybible import StoryBible


def _scene_text(project: Project, node_id: str) -> str:
    return project.read(node_id)


def scene_rows(project, bible=None) -> list[dict]:
    """Return manuscript scene facts in the order readers encounter them."""
    rows = []
    for node in project.manuscript():
        linked_names = []
        if bible is not None:
            linked_names = [entity.name for entity in bible.for_node(node.id)]
        parent = project.by_id(node.parent) if node.parent else None
        part = ""
        chapter = ""
        cursor = parent
        while cursor is not None:
            if cursor.type == CHAPTER and not chapter:
                chapter = cursor.title
            elif cursor.type == PART and not part:
                part = cursor.title
            cursor = project.by_id(cursor.parent) if cursor.parent else None
        rows.append({
            "node_id": str(node.id), "title": node.title, "part": part,
            "chapter": chapter, "pov": node.pov or "", "status": node.status or "",
            "labels": list(node.labels or []), "when": node.when or "",
            "draft": int(node.revision or 0), "words": int(project.words(node.id)),
            "target": int(node.target_words or 0), "characters": linked_names,
        })
    return rows


def chapter_rows(project) -> list[dict]:
    """Summarize each part and chapter using only its descendant manuscript scenes."""
    scenes = project.manuscript()
    rows = []
    for container in project.walk():
        if container.type not in (PART, CHAPTER):
            continue
        descendants = {node.id for node in project.walk(container.id)}
        own_scenes = [scene for scene in scenes if scene.id in descendants]
        words = sum(project.words(scene.id) for scene in own_scenes)
        target = int(project.target(container.id))
        rows.append({
            "node_id": str(container.id), "title": container.title,
            "level": "part" if container.type == PART else "chapter",
            "scenes": len(own_scenes), "words": words, "target": target,
            "progress": words / target if target else 0.0,
            # Scenerna bakom siffran: rapporten per kapitel (4.21) grupperar
            # fynd per scen, och en siffra utan sina scener går inte att gruppera.
            "scene_ids": [scene.id for scene in own_scenes],
        })
    return rows


def pov_distribution(project) -> dict:
    counts = {}
    for node in project.manuscript():
        pov = node.pov or "Utan POV"
        counts[pov] = counts.get(pov, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold())))


def character_presence(project, bible) -> list[dict]:
    """Report links and textual mentions separately; scenes is their union."""
    scenes = project.manuscript()
    scene_data = [(scene, _scene_text(project, scene.id), int(project.words(scene.id)))
                  for scene in scenes]
    # One pass builds the link map. Asking `for_node` once per entity per scene
    # was 60 x 40 SQLite queries and measured 2.1 s on a small fixture; a book
    # with 200 scenes and 100 codex posts would be minutes.
    linked_by_entity: dict[str, set[str]] = defaultdict(set)
    for scene in scenes:
        for link in bible.for_node(scene.id):
            linked_by_entity[link.id].add(scene.id)
    result = []
    for entity in bible.entities():
        linked_ids = set(linked_by_entity.get(entity.id, ()))
        mentioned_ids = set()
        mention_count = 0
        for scene, text, _words in scene_data:
            mentions = bible.mentions(text)
            if any(item.id == entity.id for item in mentions):
                mentioned_ids.add(scene.id)
                # mentions() identifies entities, not occurrences. Count each
                # name and alias occurrence here while preserving its boundary rules.
                import re
                for name in [entity.name, *entity.aliases]:
                    if name:
                        mention_count += len(re.findall(
                            r"(?<!\w)" + re.escape(name) + r"(?!\w)", text,
                            re.IGNORECASE | re.UNICODE))
        present_ids = linked_ids | mentioned_ids
        present = [(scene, word_count) for scene, _text, word_count in scene_data
                   if scene.id in present_ids]
        result.append({
            "name": entity.name, "type": entity.type, "scenes": len(present),
            "words": sum(word_count for _scene, word_count in present),
            "first_scene": present[0][0].title if present else "",
            "first_node_id": str(present[0][0].id) if present else "",
            "last_scene": present[-1][0].title if present else "",
            "last_node_id": str(present[-1][0].id) if present else "",
            "mentions": mention_count, "linked": bool(linked_ids),
        })
    return result


def report(project, bible=None) -> dict:
    scenes = scene_rows(project, bible)
    return {
        "scenes": scenes, "chapters": chapter_rows(project),
        "pov": pov_distribution(project),
        "characters": character_presence(project, bible) if bible is not None else [],
        "total_words": sum(row["words"] for row in scenes),
        "scene_count": len(scenes),
    }


def _self_check() -> int:
    checks = 0
    failures = 0

    def check(condition):
        nonlocal checks, failures
        checks += 1
        if not condition:
            failures += 1

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        project = Project.create(root / "book", "Stats")
        for node in [item for item in project.nodes if item.parent is None]:
            project.delete_node(node.id)
        part = project.add_node(PART, "Del ett")
        chapter = project.add_node(CHAPTER, "Kapitel", part.id)
        first = project.add_node(SCENE, "Start", chapter.id)
        second = project.add_node(SCENE, "Möte", chapter.id)
        third = project.add_node(SCENE, "Slut", chapter.id)
        project.write(first.id, "Anna går.")
        project.write(second.id, "Örnen 🦅 flyger med Anna.")
        project.write(third.id, "Slutet.")
        project.set_meta(first.id, pov="Anna", status="Utkast", labels=["resa"], target_words=0, revision=2)
        project.set_meta(second.id, pov="", status="", labels=[], target_words=0, revision=1)
        project.set_meta(third.id, pov="Anna", status="Klart", labels=[], target_words=0, revision=3)
        with StoryBible(str(root / "book" / "codex.sqlite")) as bible:
            anna = bible.add_entity("Anna")
            silent = bible.add_entity("NoMention")
            bible.link(anna.id, second.id)
            rows = scene_rows(project, bible)
            check([row["title"] for row in rows] == ["Start", "Möte", "Slut"])
            check([row["words"] for row in rows] == [2, 4, 1])
            check(rows[0]["draft"] == 2 and rows[0]["labels"] == ["resa"])
            containers = chapter_rows(project)
            check(len(containers) == 2 and all(row["scenes"] == 3 for row in containers))
            check(all(row["words"] == 7 for row in containers))
            check(all(row["progress"] == 0.0 for row in containers))
            check(pov_distribution(project).get("Utan POV") == 1)
            presence = {row["name"]: row for row in character_presence(project, bible)}
            check(presence["Anna"]["first_scene"] == "Start" and presence["Anna"]["last_scene"] == "Möte")
            check(presence["Anna"]["mentions"] == 2 and presence["Anna"]["linked"])
            check(presence["NoMention"]["mentions"] == 0 and not presence["NoMention"]["linked"])
        empty = Project.create(root / "empty", "Empty")
        for node in [item for item in empty.nodes if item.parent is None]:
            empty.delete_node(node.id)
        check(scene_rows(empty) == [] and chapter_rows(empty) == [])
        check(report(empty)["characters"] == [] and report(empty)["scene_count"] == 0)
        single = Project.create(root / "single", "Single")
        check(len(scene_rows(single)) == 1 and len(chapter_rows(single)) == 1)
    print(f"story_stats: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
