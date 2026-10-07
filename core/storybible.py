"""Local, editable story facts and scene links for OmaScribe.

Run ``python -m core.storybible`` for a small dependency-free self-check.
"""

from __future__ import annotations

import json
import re
import sqlite3
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ENTITY_TYPES = ("character", "place", "object", "faction", "other")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Entity:
    id: str
    type: str
    name: str
    aliases: list[str]
    summary: str
    fields: dict
    notes: str
    created: str
    updated: str


@dataclass
class Relation:
    from_id: str
    to_id: str
    kind: str
    note: str


class StoryBible:
    """SQLite backed story bible. Node IDs are opaque strings."""

    def __init__(self, path: str) -> None:
        self.path = str(path)
        self._db = sqlite3.connect(self.path)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY, type TEXT NOT NULL, name TEXT NOT NULL,
                aliases TEXT NOT NULL, summary TEXT NOT NULL, fields TEXT NOT NULL,
                notes TEXT NOT NULL, created TEXT NOT NULL, updated TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS node_entities (
                entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                node_id TEXT NOT NULL, PRIMARY KEY(entity_id, node_id)
            );
            CREATE TABLE IF NOT EXISTS relations (
                from_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                to_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                kind TEXT NOT NULL, note TEXT NOT NULL DEFAULT '',
                PRIMARY KEY(from_id, to_id, kind)
            );
            CREATE INDEX IF NOT EXISTS idx_node_entities_node ON node_entities(node_id);
        """)
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "StoryBible":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    @staticmethod
    def _decode(row: sqlite3.Row | None) -> Entity | None:
        if row is None:
            return None
        return Entity(row["id"], row["type"], row["name"], json.loads(row["aliases"]),
                      row["summary"], json.loads(row["fields"]), row["notes"],
                      row["created"], row["updated"])

    def add_entity(self, name: str, type: str = "character", aliases=None,
                   summary: str = "", fields=None) -> Entity:
        if type not in ENTITY_TYPES:
            raise ValueError(f"unsupported entity type: {type}")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("entity name must not be empty")
        now = _now()
        aliases = list(aliases or [])
        fields = dict(fields or {})
        entity_id = str(uuid.uuid4())
        self._db.execute(
            "INSERT INTO entities(id,type,name,aliases,summary,fields,notes,created,updated) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (entity_id, type, name.strip(), json.dumps(aliases, ensure_ascii=False), summary,
             json.dumps(fields, ensure_ascii=False), "", now, now))
        self._db.commit()
        return self.entity(entity_id)

    def entity(self, entity_id: str) -> Entity | None:
        return self._decode(self._db.execute("SELECT * FROM entities WHERE id=?", (entity_id,)).fetchone())

    def entities(self, type: str | None = None) -> list[Entity]:
        if type is None:
            rows = self._db.execute("SELECT * FROM entities ORDER BY name COLLATE NOCASE, id")
        else:
            rows = self._db.execute("SELECT * FROM entities WHERE type=? ORDER BY name COLLATE NOCASE, id", (type,))
        return [self._decode(row) for row in rows]

    def update_entity(self, entity_id: str, **fields) -> Entity:
        current = self.entity(entity_id)
        if current is None:
            raise KeyError(f"unknown entity: {entity_id}")
        allowed = {"type", "name", "aliases", "summary", "fields", "notes"}
        unknown = fields.keys() - allowed
        if unknown:
            raise TypeError(f"unknown entity fields: {', '.join(sorted(unknown))}")
        if "type" in fields and fields["type"] not in ENTITY_TYPES:
            raise ValueError(f"unsupported entity type: {fields['type']}")
        if "name" in fields and (not isinstance(fields["name"], str) or not fields["name"].strip()):
            raise ValueError("entity name must not be empty")
        values = {key: getattr(current, key) for key in allowed}
        values.update(fields)
        values["name"] = values["name"].strip()
        values["aliases"] = json.dumps(list(values["aliases"] or []), ensure_ascii=False)
        values["fields"] = json.dumps(dict(values["fields"] or {}), ensure_ascii=False)
        values["updated"] = _now()
        self._db.execute("UPDATE entities SET type=:type,name=:name,aliases=:aliases,summary=:summary,"
                         "fields=:fields,notes=:notes,updated=:updated WHERE id=:id",
                         {**values, "id": entity_id})
        self._db.commit()
        return self.entity(entity_id)

    def delete_entity(self, entity_id: str) -> None:
        self._db.execute("DELETE FROM entities WHERE id=?", (entity_id,))
        self._db.commit()

    def by_name(self, name: str, type: str | None = None) -> Entity | None:
        key = name.casefold()
        for entity in self.entities(type):
            if entity.name.casefold() == key or any(alias.casefold() == key for alias in entity.aliases):
                return entity
        return None

    def link(self, entity_id: str, node_id: str) -> None:
        self._db.execute("INSERT OR IGNORE INTO node_entities(entity_id,node_id) VALUES(?,?)",
                         (entity_id, str(node_id)))
        self._db.commit()

    def unlink(self, entity_id: str, node_id: str) -> None:
        self._db.execute("DELETE FROM node_entities WHERE entity_id=? AND node_id=?", (entity_id, str(node_id)))
        self._db.commit()

    def for_node(self, node_id: str) -> list[Entity]:
        rows = self._db.execute("SELECT e.* FROM entities e JOIN node_entities n ON n.entity_id=e.id "
                                "WHERE n.node_id=? ORDER BY e.name COLLATE NOCASE,e.id", (str(node_id),))
        return [self._decode(row) for row in rows]

    def add_relation(self, from_id: str, to_id: str, kind: str, note: str = "") -> Relation:
        self._db.execute("INSERT INTO relations(from_id,to_id,kind,note) VALUES(?,?,?,?) "
                         "ON CONFLICT(from_id,to_id,kind) DO UPDATE SET note=excluded.note",
                         (from_id, to_id, kind, note))
        self._db.commit()
        return Relation(from_id, to_id, kind, note)

    def relations(self, entity_id: str) -> list[Relation]:
        rows = self._db.execute("SELECT from_id,to_id,kind,note FROM relations "
                                "WHERE from_id=? OR to_id=? ORDER BY from_id,to_id,kind",
                                (entity_id, entity_id))
        return [Relation(*row) for row in rows]

    def search(self, text: str) -> list[Entity]:
        needle = text.casefold()
        if not needle:
            return []
        found = []
        for item in self.entities():
            haystack = " ".join([item.name, *item.aliases, item.summary,
                                 json.dumps(item.fields, ensure_ascii=False, sort_keys=True)])
            if needle in haystack.casefold():
                found.append(item)
        return found

    def mentions(self, text: str, type: str | None = None) -> list[Entity]:
        found = []
        for item in self.entities(type):
            names = [item.name, *item.aliases]
            if any(name and re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text, re.IGNORECASE | re.UNICODE)
                   for name in names):
                found.append(item)
        return found

    def export_json(self, path) -> None:
        data = {"version": 1, "entities": [e.__dict__ for e in self.entities()],
                "relations": [r.__dict__ for e in self.entities() for r in self.relations(e.id)
                              if e.id == r.from_id]}
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def import_json(self, path) -> None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        entities = data.get("entities", [])
        relations = data.get("relations", [])
        with self._db:
            self._db.execute("DELETE FROM entities")
            for e in entities:
                if e.get("type") not in ENTITY_TYPES:
                    raise ValueError(f"unsupported entity type: {e.get('type')}")
                self._db.execute("INSERT INTO entities(id,type,name,aliases,summary,fields,notes,created,updated) "
                                 "VALUES(?,?,?,?,?,?,?,?,?)",
                                 (str(e["id"]), e["type"], e["name"],
                                  json.dumps(e.get("aliases", []), ensure_ascii=False), e.get("summary", ""),
                                  json.dumps(e.get("fields", {}), ensure_ascii=False), e.get("notes", ""),
                                  e.get("created", _now()), e.get("updated", _now())))
            for r in relations:
                self._db.execute("INSERT INTO relations(from_id,to_id,kind,note) VALUES(?,?,?,?)",
                                 (str(r["from_id"]), str(r["to_id"]), r["kind"], r.get("note", "")))


def _self_test() -> None:
    checks = 0
    with tempfile.TemporaryDirectory() as temp:
        db_path = str(Path(temp) / "bible.sqlite")
        with StoryBible(db_path) as bible:
            anna = bible.add_entity("Anna", aliases=["Anka"], summary="A brave pilot", fields={"home": "Northport"})
            other = bible.add_entity("Annabelle", aliases=["Belle"], type="character")
            place = bible.add_entity("Northport", type="place", summary="A harbor town")
            assert {e.id for e in bible.mentions("ANNA met Anka. Anna waved.")} == {anna.id}; checks += 1
            assert all(e.id != anna.id for e in bible.mentions("Annabelle arrived.")); checks += 1
            assert [e.id for e in bible.mentions("Anna, Anna, Anna")] == [anna.id]; checks += 1
            assert bible.by_name("ANKA").id == anna.id and bible.by_name("missing") is None; checks += 1
            bible.link(anna.id, "scene:1")
            bible.link(place.id, "scene:1")
            bible.link(other.id, "scene:2")
            assert {e.id for e in bible.for_node("scene:1")} == {anna.id, place.id}; checks += 1
            bible.delete_entity(place.id)
            assert all(e.id != place.id for e in bible.for_node("scene:1")); checks += 1
            bible.add_relation(anna.id, other.id, "sibling", "They grew up together")
            assert len(bible.relations(anna.id)) == 1 and len(bible.relations(other.id)) == 1; checks += 1
            assert anna.id in {e.id for e in bible.search("brave")} and anna.id in {e.id for e in bible.search("Northport")}; checks += 1
            exported = Path(temp) / "export.json"
            bible.export_json(exported)
            clone_path = str(Path(temp) / "clone.sqlite")
            with StoryBible(clone_path) as clone:
                clone.import_json(exported)
                assert [e.__dict__ for e in clone.entities()] == [e.__dict__ for e in bible.entities()]; checks += 1
                assert clone.relations(anna.id) == bible.relations(anna.id); checks += 1

            # Prove the core assertion catches a deliberately broken matcher.
            correct_mentions = bible.mentions
            bible.mentions = lambda *_args, **_kwargs: []
            try:
                assert bible.mentions("Anna")
            except AssertionError:
                checks += 1
            else:
                raise AssertionError("self-test failed to catch the deliberately broken matcher")
            finally:
                bible.mentions = correct_mentions
    print(f"storybible: {checks} kontroller gröna")


if __name__ == "__main__":
    _self_test()
