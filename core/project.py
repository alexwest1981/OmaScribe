"""core/project.py — projektmodellen: manuset som en mapp med noder.

Ett projekt är en katalog:

    <projekt>/
      project.json          manifest: titel, inställningar, noder, statusvärden
      manuscript/
        0001-forsta-scenen.html   en fil per scen (Qt:s rika HTML)
      research/             fritt material, aldrig med i exporten
      .snapshots/           ögonblicksbilder (core/snapshots.py)

Modulen håller sig fri från Qt med flit: provet skall kunna köras utan skärm,
och modellen skall kunna läsas och skrivas av ett kommandoradsverktyg.

    python -m core.project        kör självprovet
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import uuid
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

MANIFEST = "project.json"
MANUSCRIPT_DIR = "manuscript"
RESEARCH_DIR = "research"
SNAPSHOT_DIR = ".snapshots"
SCHEMA_VERSION = 1

PART, CHAPTER, SCENE, NOTE = "part", "chapter", "scene", "note"
WRITABLE = (SCENE, NOTE)          # nodtyper som har en egen textfil
CONTAINERS = (PART, CHAPTER)      # nodtyper som bara håller ordning


# ------------------------------------------------------------------ textmätning

class _TextExtract(HTMLParser):
    """Plockar ut den text en läsare ser ur Qt:s HTML."""

    _SKIP = {"style", "script", "head"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._depth_skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._depth_skip += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._depth_skip:
            self._depth_skip -= 1

    def handle_data(self, data):
        if not self._depth_skip:
            self.parts.append(data)

    def text(self) -> str:
        return " ".join(self.parts)


def html_to_text(html: str) -> str:
    parser = _TextExtract()
    parser.feed(html or "")
    return parser.text()


def count_words(html: str) -> int:
    # ponytail: räknar ord som \w+, samma mått modulen överallt. Bindestreck och
    # siffror mitt i ord räknas som ett ord — byt till en delad räknare i
    # core/document_stats.py om siffrorna skall stämma med statusfältet.
    return len(re.findall(r"\w+", html_to_text(html), flags=re.UNICODE))


# --------------------------------------------------------------------- noder

@dataclass
class ProjectNode:
    """En nod i manuset: del, kapitel, scen eller anteckning."""

    id: str
    type: str
    title: str
    parent: str | None = None
    order: int = 0
    synopsis: str = ""
    status: str = ""
    labels: list[str] = field(default_factory=list)
    target_words: int = 0
    pov: str = ""
    file: str | None = None            # relativ sökväg, bara för SCENE/NOTE
    revision: int = 1                  # utkast 1, 2, 3 (R03.13)

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "parent": self.parent,
            "order": self.order,
            "synopsis": self.synopsis,
            "status": self.status,
            "labels": list(self.labels),
            "target_words": self.target_words,
            "pov": self.pov,
            "revision": self.revision,
        }
        if self.file:
            d["file"] = self.file
        return d

    @staticmethod
    def from_dict(d: dict) -> "ProjectNode":
        return ProjectNode(
            id=d["id"],
            type=d.get("type", SCENE),
            title=d.get("title", ""),
            parent=d.get("parent"),
            order=int(d.get("order", 0)),
            synopsis=d.get("synopsis", ""),
            status=d.get("status", ""),
            labels=list(d.get("labels") or []),
            target_words=int(d.get("target_words", 0)),
            pov=d.get("pov", ""),
            file=d.get("file"),
            revision=int(d.get("revision", 1)),
        )

    @property
    def is_writable(self) -> bool:
        return self.type in WRITABLE


# ------------------------------------------------------------------- projektet

DEFAULT_SETTINGS = {
    "language": "sv",
    "target_words": 0,
    "deadline": "",
    "writing_days": [1, 2, 3, 4, 5, 6, 7],
    "statuses": ["Idé", "Utkast", "Revidering", "Klart"],
    "labels": [],
    "series": "",
    "genre": "",
    "audience": "",
}


class Project:
    """Ett projekt på disk. Alla ändringar skrivs med `save()`."""

    def __init__(self, root: str | os.PathLike) -> None:
        self.root = Path(root).expanduser().resolve()
        self.title = ""
        self.settings: dict = dict(DEFAULT_SETTINGS)
        self.nodes: list[ProjectNode] = []
        self._words: dict[str, int] = {}          # cache per nod-id

    # ------------------------------------------------------------- skapa/ladda

    @staticmethod
    def create(root: str | os.PathLike, title: str, template: str | None = None) -> "Project":
        project = Project(root)
        if project.root.exists() and any(project.root.iterdir()):
            raise FileExistsError(f"projektmappen är inte tom: {project.root}")
        project.root.mkdir(parents=True, exist_ok=True)
        project.title = title
        (project.root / MANUSCRIPT_DIR).mkdir(exist_ok=True)
        (project.root / RESEARCH_DIR).mkdir(exist_ok=True)
        if template == "roman":
            part = project.add_node(PART, "Del ett")
            chapter = project.add_node(CHAPTER, "Kapitel 1", parent=part.id)
            project.add_node(SCENE, "Scen 1", parent=chapter.id)
            project.settings["target_words"] = 80_000
        else:
            chapter = project.add_node(CHAPTER, "Kapitel 1")
            project.add_node(SCENE, "Scen 1", parent=chapter.id)
        project.save()
        return project

    @staticmethod
    def load(root: str | os.PathLike) -> "Project":
        project = Project(root)
        manifest = project.root / MANIFEST
        if not manifest.exists():
            raise FileNotFoundError(f"ingen projektfil: {manifest}")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        project.title = data.get("title", "")
        project.settings = {**DEFAULT_SETTINGS, **(data.get("settings") or {})}
        project.nodes = [ProjectNode.from_dict(d) for d in data.get("nodes", [])]
        return project

    def save(self) -> None:
        data = {
            "schema": SCHEMA_VERSION,
            "title": self.title,
            "settings": self.settings,
            "nodes": [n.to_dict() for n in self.nodes],
        }
        self.root.mkdir(parents=True, exist_ok=True)
        atomic_write_text(
            self.root / MANIFEST,
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        )

    # -------------------------------------------------------------- uppslagning

    def by_id(self, node_id: str) -> ProjectNode:
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise KeyError(f"okänd nod: {node_id}")

    def children(self, parent: str | None) -> list[ProjectNode]:
        kids = [n for n in self.nodes if n.parent == parent]
        return sorted(kids, key=lambda n: (n.order, n.title))

    def walk(self, parent: str | None = None) -> list[ProjectNode]:
        """Hela trädet i läsordning — samma ordning manuset läses i."""
        out: list[ProjectNode] = []
        for node in self.children(parent):
            out.append(node)
            out.extend(self.walk(node.id))
        return out

    def manuscript(self) -> list[ProjectNode]:
        """Bara det som blir bok: scener, i läsordning, utan research."""
        return [n for n in self.walk() if n.is_writable and n.type == SCENE]

    def path_of(self, node: ProjectNode) -> Path | None:
        return (self.root / node.file) if node.file else None

    # ------------------------------------------------------------------ ändring

    def _new_id(self) -> str:
        while True:
            node_id = "n_" + uuid.uuid4().hex[:8]
            if all(n.id != node_id for n in self.nodes):
                return node_id

    def add_node(self, type: str, title: str, parent: str | None = None,
                 position: int | None = None) -> ProjectNode:
        siblings = self.children(parent)
        if position is None or position > len(siblings):
            position = len(siblings)
        node = ProjectNode(id=self._new_id(), type=type, title=title, parent=parent)
        if type in WRITABLE:
            node.file = self._scene_path(title)
            atomic_write_text(self.root / node.file, empty_scene_html(title))
        self.nodes.append(node)
        siblings.insert(position, node)
        self._renumber(parent)
        return node

    def _scene_path(self, title: str) -> str:
        taken = {n.file for n in self.nodes if n.file}
        index = 1
        while True:
            candidate = f"{MANUSCRIPT_DIR}/{index:04d}-{slugify(title)}.html"
            if candidate not in taken:
                return candidate
            index += 1

    def _renumber(self, parent: str | None) -> None:
        # ponytail: O(n) per flytt, n = syskonen. En bok har kapitel i tiotal,
        # inte tusental — byt till glesa ordningstal först om det känns.
        for index, node in enumerate(self.children(parent)):
            node.order = index

    def move_node(self, node_id: str, parent: str | None, position: int = 0) -> None:
        node = self.by_id(node_id)
        if parent is not None:
            target = self.by_id(parent)
            if target.type not in CONTAINERS:
                raise ValueError(f"{target.type} kan inte innehålla noder")
            if self._is_descendant(parent, node_id):
                raise ValueError("en nod kan inte flyttas in i sig själv")
        old_parent = node.parent
        node.parent = parent
        # children() läser self.nodes och hade redan räknat in noden med sin
        # gamla ordning — den måste bort ur listan innan den sätts in på ny plats,
        # annars hamnar samma nod två gånger och ordningstalen skräpar.
        siblings = [n for n in self.children(parent) if n.id != node.id]
        position = max(0, min(position, len(siblings)))
        siblings.insert(position, node)
        for index, sibling in enumerate(siblings):
            sibling.order = index
        if old_parent != parent:
            self._renumber(old_parent)

    def _is_descendant(self, candidate: str, ancestor: str) -> bool:
        node: ProjectNode | None = self.by_id(candidate)
        while node is not None:
            if node.id == ancestor:
                return True
            node = self.by_id(node.parent) if node.parent else None
        return False

    def rename(self, node_id: str, title: str) -> None:
        self.by_id(node_id).title = title

    def set_meta(self, node_id: str, **fields) -> None:
        node = self.by_id(node_id)
        for key, value in fields.items():
            if not hasattr(node, key):
                raise AttributeError(f"okänt fält: {key}")
            setattr(node, key, value)
        if "status" in fields and fields["status"] not in self.settings["statuses"]:
            self.settings["statuses"].append(fields["status"])

    def delete_node(self, node_id: str, delete_files: bool = True) -> list[str]:
        """Tar bort noden och allt under den. Returnerar borttagna nod-id:n."""
        node = self.by_id(node_id)
        doomed = [node] + [n for n in self.walk(node_id)]
        ids = [n.id for n in doomed]
        for victim in doomed:
            if delete_files and victim.file:
                path = self.root / victim.file
                if path.exists():
                    path.unlink()
            self._words.pop(victim.id, None)
        self.nodes = [n for n in self.nodes if n.id not in ids]
        self._renumber(node.parent)
        return ids

    # ------------------------------------------------------------------- texten

    def read(self, node_id: str) -> str:
        node = self.by_id(node_id)
        path = self.path_of(node)
        if path is None or not path.exists():
            return empty_scene_html(node.title)
        return path.read_text(encoding="utf-8")

    def write(self, node_id: str, html: str) -> None:
        node = self.by_id(node_id)
        if not node.is_writable:
            raise ValueError(f"{node.type} har ingen egen textfil")
        if not node.file:
            node.file = self._scene_path(node.title)
        atomic_write_text(self.root / node.file, html)
        self._words[node.id] = count_words(html)

    def words(self, node_id: str) -> int:
        if node_id not in self._words:
            self._words[node_id] = count_words(self.read(node_id))
        return self._words[node_id]

    def total_words(self) -> int:
        return sum(self.words(n.id) for n in self.manuscript())

    def progress(self) -> dict:
        """Framsteg för statusfältet och projektpanelen."""
        total = self.total_words()
        goal = int(self.settings.get("target_words") or 0)
        return {
            "words": total,
            "target": goal,
            "percent": round(total * 100 / goal) if goal else 0,
            "daily_quota": self.daily_quota(),
        }

    def daily_quota(self) -> int:
        """Hur många ord per skrivdag som återstår till deadline (R03.2)."""
        goal = int(self.settings.get("target_words") or 0)
        deadline = self.settings.get("deadline") or ""
        if not goal or not deadline:
            return 0
        from datetime import date
        try:
            end = date.fromisoformat(deadline)
        except ValueError:
            return 0
        days = [d for d in self.settings.get("writing_days") or []]
        today = date.today()
        if end < today:
            return 0
        remaining_days = 0
        cursor = today
        while cursor <= end:
            if not days or cursor.isoweekday() in days:
                remaining_days += 1
            cursor = date.fromordinal(cursor.toordinal() + 1)
        if remaining_days <= 0:
            return 0
        left = max(0, goal - self.total_words())
        return -(-left // remaining_days)          # ceil

    # ------------------------------------------------------------------ kontroll

    def validate(self) -> list[str]:
        """Säger till om något är trasigt i stället för att gissa."""
        problems: list[str] = []
        ids = {n.id for n in self.nodes}
        if len(ids) != len(self.nodes):
            problems.append("duplicerade nod-id:n")
        for node in self.nodes:
            if node.parent is not None and node.parent not in ids:
                problems.append(f"{node.title}: förälder {node.parent} finns inte")
            if node.type in CONTAINERS and node.file:
                problems.append(f"{node.title}: {node.type} skall inte ha en textfil")
            if node.is_writable:
                path = self.path_of(node)
                if path is None or not path.exists():
                    problems.append(f"{node.title}: textfilen saknas ({node.file})")
        seen: set[str] = set()
        for node in self.nodes:
            if node.file:
                if node.file in seen:
                    problems.append(f"{node.title}: två noder delar filen {node.file}")
                seen.add(node.file)
        # cykler: en nod som är sin egen förfader. Okänd förälder avbryter
        # vandringen i stället för att kasta — den är redan rapporterad ovan.
        for node in self.nodes:
            walker, hops = node, 0
            while walker.parent is not None and hops <= len(self.nodes):
                nxt = next((n for n in self.nodes if n.id == walker.parent), None)
                if nxt is None:
                    break
                walker = nxt
                hops += 1
            if hops > len(self.nodes):
                problems.append(f"{node.title}: cirkel i trädet")
        return problems


# ------------------------------------------------------------------ hjälpmedel

def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[åä]", "a", text)
    text = re.sub(r"ö", "o", text)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:40] or "utan-titel"


def empty_scene_html(title: str) -> str:
    return (
        "<!DOCTYPE HTML><html><head><meta charset=\"utf-8\"></head><body>"
        f"<h1>{title}</h1><p></p></body></html>"
    )


def atomic_write_text(path: Path, text: str) -> None:
    """Skriv helt eller inte alls — en avbruten skrivning får inte äta manuset."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def project_at_or_above(path: str | os.PathLike) -> Path | None:
    """Hittar projektmappen för en fil, så appen kan öppna rätt projekt."""
    candidate = Path(path).expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for folder in [candidate, *candidate.parents]:
        if (folder / MANIFEST).exists():
            return folder
    return None


# ------------------------------------------------------------------- självprov

def _self_check() -> int:
    checks = 0
    failures: list[str] = []

    def check(ok: bool, label: str) -> bool:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)
        return bool(ok)

    tmp = tempfile.mkdtemp(prefix="omascribe-project-")
    try:
        root = Path(tmp) / "Min bok"
        book = Project.create(root, "Min bok", template="roman")
        check(book.title == "Min bok", "titeln sparas")
        check(len(book.walk()) == 3, "romanmallen ger del, kapitel och scen")
        check(book.validate() == [], f"färskt projekt är giltigt: {book.validate()}")

        part = book.children(None)[0]
        chapter = book.children(part.id)[0]
        scene = book.children(chapter.id)[0]

        # text och ordräkning ("Rubrik" + fyra ord = 5)
        book.write(scene.id, "<html><body><h1>Rubrik</h1><p>ord ett två tre</p></body></html>")
        check(book.words(scene.id) == 5, f"ordräkningen stämmer ({book.words(scene.id)} != 5)")
        check(book.total_words() == 5, "totalen räknar scenerna")

        # spara och ladda om
        book.save()
        again = Project.load(root)
        check(len(again.walk()) == 3, "trädet överlever en omladdning")
        check(again.words(scene.id) == 5, "texten överlever en omladdning")

        # ordning och flytt
        second = book.add_node(SCENE, "Scen 2", parent=chapter.id)
        check([n.title for n in book.children(chapter.id)] == ["Scen 1", "Scen 2"],
              "nya noder hamnar sist")
        book.move_node(second.id, chapter.id, 0)
        check([n.title for n in book.children(chapter.id)] == ["Scen 2", "Scen 1"],
              "flytt ändrar ordningen")
        check([n.order for n in book.children(chapter.id)] == [0, 1],
              "ordningstalen numreras om utan hål")

        # flytt till en annan nivå och tillbaka
        new_chapter = book.add_node(CHAPTER, "Kapitel 2", parent=part.id)
        book.move_node(second.id, new_chapter.id)
        check(second.parent == new_chapter.id, "flytt byter förälder")
        check(len(book.children(chapter.id)) == 1, "gamla föräldern tappar noden")

        # en nod får inte flyttas in i sig själv
        try:
            book.move_node(chapter.id, scene.id)
            check(False, "cirkelflytt skall avvisas")
        except ValueError:
            check(True, "cirkelflytt avvisas")

        # metadata
        book.set_meta(scene.id, synopsis="Hon kommer hem.", status="Utkast",
                      labels=["POV: Anna"], target_words=1200, pov="Anna")
        check(book.by_id(scene.id).synopsis == "Hon kommer hem.", "synopsis sparas")
        check("Utkast" in book.settings["statuses"], "nya statusvärden lärs in")

        # borttagning tar barnen med sig och filen försvinner
        scene_file = book.path_of(book.by_id(scene.id))
        book.delete_node(chapter.id)
        check(all(n.id != chapter.id for n in book.nodes), "kapitlet är borta")
        check(scene_file is not None and not scene_file.exists(),
              "scenens fil städas bort")
        check(book.validate() == [], "projektet är giltigt efter borttagning")

        # mål och dagsbehov
        book.settings["target_words"] = 0
        check(book.progress()["percent"] == 0, "utan mål ingen procent")
        book.settings["target_words"] = 100
        book.settings["deadline"] = ""
        check(book.daily_quota() == 0, "utan deadline ingen kvot")
        book.settings["deadline"] = "2020-01-01"
        check(book.daily_quota() == 0, "förfluten deadline ger ingen kvot")
        from datetime import date, timedelta
        book.settings["deadline"] = (date.today() + timedelta(days=3)).isoformat()
        quota = book.daily_quota()
        check(quota > 0 and quota * 4 >= 100, f"dagsbehovet räknas ({quota})")

        # ett trasigt manifest skall säga till, inte gissa
        manifest = root / MANIFEST
        broken = json.loads(manifest.read_text(encoding="utf-8"))
        broken["nodes"][0]["parent"] = "n_finnsinte"
        manifest.write_text(json.dumps(broken), encoding="utf-8")
        problems = Project.load(root).validate()
        check(any("finns inte" in p for p in problems),
              f"trasig förälder rapporteras ({problems})")

        # en saknad textfil rapporteras också
        healthy = Project.create(Path(tmp) / "Andra boken", "Andra boken")
        scene2 = healthy.children(healthy.children(None)[0].id)[0]
        scene2_path = healthy.path_of(scene2)
        assert scene2_path is not None
        scene2_path.unlink()
        check(any("saknas" in p for p in healthy.validate()),
              "saknad textfil rapporteras")

        # atomär skrivning lämnar ingen temp-fil efter sig
        healthy.save()
        leftovers = [p.name for p in healthy.root.iterdir() if p.name.startswith(".tmp-")]
        check(not leftovers, f"inga temp-filer kvar ({leftovers})")

        # projektuppslag från en fil
        found = project_at_or_above(scene2_path)
        check(found == healthy.root, "projektmappen hittas inifrån en scenfil")
        check(project_at_or_above("/tmp") is None, "utanför projekt hittas inget")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"project: {checks - len(failures)} av {checks} kontroller gröna")
    for failure in failures:
        print(f"  ✗ {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
