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

from core.collections import Collection
from core import collections as collections_mod

MANIFEST = "project.json"
MANUSCRIPT_DIR = "manuscript"
RESEARCH_DIR = "research"
SNAPSHOT_DIR = ".snapshots"
CODEX_FILE = "codex.sqlite"        # projektets entiteter och scenkopplingar
SCHEMA_VERSION = 1

PART, CHAPTER, SCENE, NOTE, RESEARCH = "part", "chapter", "scene", "note", "research"
WRITABLE = (SCENE, NOTE)          # nodtyper som har en egen textfil
CONTAINERS = (PART, CHAPTER, RESEARCH)   # nodtyper som bara håller ordning


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
    note: str = ""                     # författarens egen anteckning om scenen (R01.12)
    comments: list[dict] = field(default_factory=list)   # marginalkommentarer (R01.12)
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
            "note": self.note,
            "comments": [dict(c) for c in self.comments],
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
            note=d.get("note", ""),
            comments=[
                {
                    "id": str(c.get("id") or uuid.uuid4().hex[:8]),
                    "quote": str(c.get("quote", "")),
                    "text": str(c.get("text", "")),
                    "resolved": bool(c.get("resolved", False)),
                }
                for c in (d.get("comments") or [])
                if isinstance(c, dict) and (c.get("quote") or "").strip()
            ],
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

# Statusfärger är presentation: de följer ordningen i projektets statuslista, så
# samma status har samma färg varje gång och ingen behöver ställa in något. Vill
# du välja färg själv är det ett eget steg — värdet ligger redan som en nyckel.
# Färgen bär aldrig ensam betydelse: statusen står som text också (R01.5).
STATUS_PALETTE = (
    "#7f8c8d", "#2980b9", "#27ae60", "#d35400",
    "#8e44ad", "#16a085", "#c0392b", "#b7950b",
)


# Projektmallar (R01.13, R03.8): vilken struktur och vilket ordmål ett nytt
# projekt börjar med. Skilda från dokumentmallarna i core/templates.py — de är
# färdiga texter, det här är ett tomt projekt att fylla. `structure` läses som
# (nodtyp, rubrik, förälderns nodtyp): raderna byggs uppifrån och ned.
PROJECT_TEMPLATES = {
    "roman": {
        "target_words": 80_000,
        "structure": [
            (PART, "Del ett", None),
            (CHAPTER, "Kapitel 1", PART),
            (SCENE, "Scen 1", CHAPTER),
        ],
    },
    "fackbok": {
        "target_words": 40_000,
        "structure": [
            (CHAPTER, "Kapitel 1", None),
            (SCENE, "Avsnitt 1", CHAPTER),
        ],
    },
    "novell": {
        "target_words": 8_000,
        "structure": [
            (SCENE, "Novellen", None),
        ],
    },
    "enkel": {
        "target_words": 0,
        "structure": [
            (CHAPTER, "Kapitel 1", None),
            (SCENE, "Scen 1", CHAPTER),
        ],
    },
}
DEFAULT_TEMPLATE = "roman"      # vad väljaren föreslår för ett nytt projekt
MINIMAL_TEMPLATE = "enkel"      # vad create() utan mall ger — minsta möjliga


class Project:
    """Ett projekt på disk. Alla ändringar skrivs med `save()`."""

    def __init__(self, root: str | os.PathLike) -> None:
        self.root = Path(root).expanduser().resolve()
        self.title = ""
        self.settings: dict = dict(DEFAULT_SETTINGS)
        self.nodes: list[ProjectNode] = []
        self.collections: list[Collection] = []
        self.variants: list[dict] = []      # namngivna ordningar av scener (R01.14)
        self.links: list[dict] = []               # [{"scene": id, "material": id}]
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
        if template not in PROJECT_TEMPLATES:
            template = MINIMAL_TEMPLATE
        spec = PROJECT_TEMPLATES[template]
        made: dict = {}
        for node_type, node_title, parent_type in spec["structure"]:
            parent = made.get(parent_type)
            made[node_type] = project.add_node(
                node_type, node_title, parent=parent.id if parent else None)
        # Ordmålet är mallens förslag — går att ändra i inställningarna.
        project.settings["target_words"] = spec["target_words"]
        # Researchmappen ligger i projektet men utanför manuset: bara scener
        # räknas in i manuset, ordtalen och exporten (R01.7).
        project.add_node(RESEARCH, "Research")
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
        project.collections = [Collection.from_dict(d) for d in data.get("collections", [])]
        project.variants = [
            {"id": str(v.get("id")), "name": str(v.get("name", "")),
             "nodes": [str(n) for n in (v.get("nodes") or [])]}
            for v in (data.get("variants") or [])
            if v.get("id")
        ]
        project.links = [
            {"scene": str(l.get("scene")), "material": str(l.get("material"))}
            for l in (data.get("links") or [])
            if l.get("scene") and l.get("material")
        ]
        return project

    def save(self) -> None:
        data = {
            "schema": SCHEMA_VERSION,
            "title": self.title,
            "settings": self.settings,
            "nodes": [n.to_dict() for n in self.nodes],
            "collections": [c.to_dict() for c in self.collections],
            "variants": [dict(v) for v in self.variants],
            "links": [dict(l) for l in self.links],
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

    def research(self) -> list[ProjectNode]:
        """Materialet vid sidan av manuset: anteckningar och researchmappar."""
        return [n for n in self.walk() if n.type in (RESEARCH, NOTE)]

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
        # Ordningstalen sätts ur den avsiktliga listan, inte ur en sortering:
        # en ny nod har inget order-värde än, och sorteringen föll då tillbaka på
        # titeln — "Scen 3" hamnade före "Scen 2".
        ordered = siblings[:position] + [node] + siblings[position:]
        self.nodes.append(node)
        for index, sibling in enumerate(ordered):
            sibling.order = index
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
        # Kopplingar till det som försvann städas, annars samlas döda id:n.
        self.links = [l for l in self.links
                      if l["scene"] not in ids and l["material"] not in ids]
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

    def words_in(self, node_id: str) -> int:
        """Ord i noden: scenens egna, eller summan av scenerna under en behållare."""
        node = self.by_id(node_id)
        if node.is_writable:
            return self.words(node_id)
        return sum(self.words(n.id) for n in self.walk(node_id)
                   if n.is_writable and n.type == SCENE)

    def target(self, node_id: str) -> int:
        """Mål i ord: scenens eget mål, eller summan av barnens mål.

        Ett kapitel har sällan ett eget mål — det är scenerna som har dem — så
        summan är standard och ett eget värde på behållaren vinner om det finns.
        """
        node = self.by_id(node_id)
        if node.is_writable or int(node.target_words or 0):
            return int(node.target_words or 0)
        return sum(self.target(n.id) for n in self.children(node_id))

    def node_progress(self, node_id: str) -> dict:
        """Ord, mål och andel för en nod — samma mått som projektets."""
        words, target = self.words_in(node_id), self.target(node_id)
        return {
            "words": words,
            "target": target,
            "percent": round(words * 100 / target) if target else 0,
        }

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

    # -------------------------------------------------------------- samlingar

    def add_collection(self, name: str, kind: str = collections_mod.MANUAL,
                       query: str = "", node_ids=None) -> Collection:
        collection = Collection(
            id=collections_mod.new_id(),
            name=name.strip() or collections_mod.describe(
                Collection(id="", name="", kind=kind, query=query)),
            kind=kind if kind in (collections_mod.MANUAL, collections_mod.SEARCH)
            else collections_mod.MANUAL,
            query=(query or "").strip(),
            node_ids=[str(n) for n in (node_ids or [])],
        )
        self.collections.append(collection)
        return collection

    def collection(self, collection_id: str) -> Collection:
        for collection in self.collections:
            if collection.id == collection_id:
                return collection
        raise KeyError(f"ingen samling med id {collection_id}")

    def remove_collection(self, collection_id: str) -> bool:
        before = len(self.collections)
        self.collections = [c for c in self.collections if c.id != collection_id]
        return len(self.collections) != before

    def toggle_in_collection(self, collection_id: str, node_id: str) -> bool:
        """Lägger till eller tar bort scenen. True om den ligger i samlingen efteråt."""
        collection = self.collection(collection_id)
        if collection.kind != collections_mod.MANUAL:
            return False               # en sökning äger sina träffar själv
        self.by_id(node_id)            # kastar om scenen inte finns
        if collection.contains(node_id):
            collection.node_ids.remove(node_id)
            return False
        collection.node_ids.append(node_id)
        return True

    def select_collection(self, collection_id: str) -> list[ProjectNode]:
        """Scenerna i samlingen, i manusets ordning. Binderordningen rörs inte.

        En handplockad samling tappar scener som tagits bort ur projektet, och
        en sökning räknas om varje gång — den är en fråga, inte en lista.
        """
        collection = self.collection(collection_id)
        if collection.kind == collections_mod.MANUAL:
            wanted = set(collection.node_ids)
            return [n for n in self.manuscript() if n.id in wanted]
        terms = collections_mod.parse_query(collection.query)
        return [n for n in self.manuscript()
                if collections_mod.matches(n, terms, html_to_text(self.read(n.id)))]

    # ----------------------------------------------------- scen och material

    def link_material(self, scene_id: str, material_id: str) -> bool:
        """Kopplar researchmaterial till en scen. True om kopplingen är ny."""
        self.by_id(scene_id)
        self.by_id(material_id)
        if any(l["scene"] == scene_id and l["material"] == material_id for l in self.links):
            return False
        self.links.append({"scene": scene_id, "material": material_id})
        return True

    def unlink_material(self, scene_id: str, material_id: str) -> bool:
        before = len(self.links)
        self.links = [l for l in self.links
                      if not (l["scene"] == scene_id and l["material"] == material_id)]
        return len(self.links) != before

    def material_for(self, scene_id: str) -> list[ProjectNode]:
        """Materialet som hör till scenen, i läsordning.

        Kopplingen är ett id, inte en kopia — en anteckning kan höra till flera
        scener, och en nod som tagits bort faller ur listan av sig själv.
        """
        ids = {l["material"] for l in self.links if l["scene"] == scene_id}
        return [n for n in self.walk() if n.id in ids]

    def material_candidates(self, scene_id: str) -> list[ProjectNode]:
        """Researchmaterial som ännu inte hör till scenen."""
        linked = {n.id for n in self.material_for(scene_id)}
        return [n for n in self.research() if n.is_writable and n.id not in linked]

    # ---------------------------------------------------------- kommentarerna

    def add_comment(self, node_id: str, quote: str, text: str) -> dict:
        """Fäster en kommentar vid ett textställe (R01.12).

        Ankaret är citatet, inte en position: texten flyttar sig när man skriver,
        och ett citat går att hitta igen. Se _refresh_comment_marks i fönstret.
        """
        node = self.by_id(node_id)
        quote = (quote or "").strip()
        if not quote:
            raise ValueError("en kommentar måste hänga på ett textställe")
        comment = {
            "id": uuid.uuid4().hex[:8],
            "quote": quote,
            "text": (text or "").strip(),
            "resolved": False,
        }
        node.comments.append(comment)
        return comment

    def comment(self, node_id: str, comment_id: str):
        for comment in self.by_id(node_id).comments:
            if comment["id"] == comment_id:
                return comment
        return None

    def comments_for(self, node_id: str, include_resolved: bool = True) -> list:
        """Kommentarerna på en scen, ogiltiga först."""
        try:
            comments = list(self.by_id(node_id).comments)
        except KeyError:
            return []
        if not include_resolved:
            comments = [c for c in comments if not c.get("resolved")]
        # ogiltiga först: de är de man letar efter
        return sorted(comments, key=lambda c: bool(c.get("resolved")))

    def resolve_comment(self, node_id: str, comment_id: str, resolved: bool = True) -> bool:
        comment = self.comment(node_id, comment_id)
        if comment is None:
            return False
        comment["resolved"] = bool(resolved)
        return True

    def delete_comment(self, node_id: str, comment_id: str) -> bool:
        node = self.by_id(node_id)
        for index, comment in enumerate(node.comments):
            if comment["id"] == comment_id:
                node.comments.pop(index)
                return True
        return False

    def unresolved_comments(self) -> list:
        """(nod, kommentar) för alla ogiltiga kommentarer i projektet."""
        return [(node, comment) for node in self.walk()
                for comment in node.comments if not comment.get("resolved")]

    # ---------------------------------------------------------- varianterna

    def add_variant(self, name: str, nodes=None) -> dict:
        """En variant: en namngiven ordning av scener (R01.14, steg 1).

        Bara ordningen förgernas — innehållet ligger kvar i scenens egen fil, så
        en variant kan inte tappa text eller råka skriva över något annat. Ett
        innehållsligt grenat manus kräver snapshots per scen (fas 3.1).
        """
        kalla = list(self.manuscript() if nodes is None else nodes)
        variant = {
            "id": uuid.uuid4().hex[:8],
            "name": (name or "").strip() or f"Variant {len(self.variants) + 1}",
            "nodes": [n.id for n in kalla if n.is_writable],
        }
        self.variants.append(variant)
        return variant

    def variant(self, variant_id: str):
        for variant in self.variants:
            if variant["id"] == variant_id:
                return variant
        return None

    def delete_variant(self, variant_id: str) -> bool:
        variant = self.variant(variant_id)
        if variant is None:
            return False
        self.variants.remove(variant)
        return True

    def set_variant_order(self, variant_id: str, node_ids) -> bool:
        """Sätter variantens ordning. Okända eller icke skrivbara noder avvisas."""
        variant = self.variant(variant_id)
        if variant is None:
            return False
        rena = []
        for node_id in node_ids:
            try:
                node = self.by_id(node_id)
            except KeyError:
                return False
            if not node.is_writable or node_id in rena:
                return False
            rena.append(node_id)
        variant["nodes"] = rena
        return True

    def move_in_variant(self, variant_id: str, node_id: str, delta: int) -> bool:
        """Flyttar en scen ett steg framåt eller bakåt i varianten (steg 2)."""
        variant = self.variant(variant_id)
        if variant is None or node_id not in variant["nodes"]:
            return False
        index = variant["nodes"].index(node_id)
        ny = max(0, min(index + delta, len(variant["nodes"]) - 1))
        if ny == index:
            return False
        variant["nodes"].pop(index)
        variant["nodes"].insert(ny, node_id)
        return True

    def replace_in_variant(self, variant_id: str, index: int, node_id: str) -> bool:
        """Byter ut scenen på en plats i varianten (steg 2)."""
        variant = self.variant(variant_id)
        if variant is None or not (0 <= index < len(variant["nodes"])):
            return False
        try:
            node = self.by_id(node_id)
        except KeyError:
            return False
        if not node.is_writable:
            return False
        if node_id in variant["nodes"]:
            variant["nodes"].remove(node_id)
        variant["nodes"][min(index, len(variant["nodes"]) - 1)] = node_id
        return True

    def variant_nodes(self, variant_id: str) -> list:
        """Variantens scener i dess ordning. Borttagna scener hoppas över."""
        variant = self.variant(variant_id)
        if variant is None:
            return []
        ut = []
        for node_id in variant["nodes"]:
            try:
                ut.append(self.by_id(node_id))
            except KeyError:
                continue
        return ut

    def variant_diff(self, variant_id: str) -> dict:
        """Jämför varianten med manusets ordning (steg 3).

        flyttade: scener som ligger på en annan plats än i manuset.
        utanför:  scener i varianten som inte längre är med i manuset.
        saknas:   scener i manuset som inte finns i varianten.
        """
        variant = self.variant(variant_id)
        if variant is None:
            return {"moved": [], "outside": [], "missing": []}
        manus = [n.id for n in self.manuscript()]
        i_variant = list(variant["nodes"])
        moved = [nid for nid in i_variant if nid in manus
                 and manus.index(nid) != i_variant.index(nid)]
        return {
            "moved": moved,
            "outside": [nid for nid in i_variant if nid not in manus],
            "missing": [nid for nid in manus if nid not in i_variant],
        }

    def apply_variant(self, variant_id: str) -> int:
        """Lägger variantens ordning på manuset (steg 4). Antal flyttade scener.

        Hierarkin rörs inte: bara ordningen inom varje förälder ändras, så en
        scen kan inte hamna i fel kapitel av en variant. Det går att ångra genom
        att lägga tillbaka den gamla ordningen — eller lägga en variant till.
        """
        variant = self.variant(variant_id)
        if variant is None:
            return 0
        ordning = {nid: index for index, nid in enumerate(variant["nodes"])}
        moved = 0
        for parent_id in {n.parent for n in self.manuscript()}:
            syskon = self.children(parent_id)
            # Scener utanför varianten behåller sin inbördes ordning sist.
            sorterade = sorted(
                syskon,
                key=lambda n: (ordning.get(n.id, len(ordning) + n.order), n.order))
            for index, node in enumerate(sorterade):
                if node.order != index:
                    node.order = index
                    moved += 1
        return moved

    @property
    def codex_path(self) -> Path:
        """Projektets codex ligger i projektmappen, så projektet är självständigt.

        Skapas först när någon öppnar den — ett projekt utan entiteter har ingen fil.
        """
        return self.root / CODEX_FILE

    def status_color(self, status: str):
        """Färgen för en status, eller None. Härledd ur statuslistans ordning."""
        statuses = list(self.settings.get("statuses") or [])
        if status not in statuses:
            return None
        return STATUS_PALETTE[statuses.index(status) % len(STATUS_PALETTE)]

    def status_color_for(self, node_id: str):
        """Färgen för nodens status, eller None om den inte har någon."""
        try:
            status = self.by_id(node_id).status
        except KeyError:
            return None
        return self.status_color(status) if status else None

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
        for link in self.links:
            if link.get("scene") not in ids or link.get("material") not in ids:
                problems.append(
                    f"koppling till en nod som inte finns "
                    f"({link.get('scene')} → {link.get('material')})")
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
        check(book.title == "Min bok", "titeln sätts")
        check([n.type for n in book.children(None)] == [PART, RESEARCH],
              f"romanmallen har del och research ({[n.type for n in book.children(None)]})")
        check(book.settings["target_words"] == 80_000, "och romanens ordmål")

        # projektmallarna: struktur och ordmål per mall (R01.13)
        mallar = {}
        for namn in PROJECT_TEMPLATES:
            mapp = tempfile.mkdtemp(prefix=f"mall-{namn}-")
            try:
                p = Project.create(mapp, f"Test {namn}", template=namn)
                mallar[namn] = ([n.type for n in p.children(None)], p.settings["target_words"])
            finally:
                shutil.rmtree(mapp, ignore_errors=True)
        check(mallar["roman"][0] == [PART, RESEARCH], f"roman: {mallar['roman'][0]}")
        check(mallar["fackbok"][0] == [CHAPTER, RESEARCH], f"fackbok: {mallar['fackbok'][0]}")
        check(mallar["novell"][0] == [SCENE, RESEARCH],
              f"novell: {mallar['novell'][0]} — en scen, inga kapitel")
        check(mallar["enkel"][0] == [CHAPTER, RESEARCH], f"enkel: {mallar['enkel'][0]}")
        check(len(set(PROJECT_TEMPLATES)) == len(mallar), "alla mallar går att skapa")
        check(mallar["roman"][1] > mallar["novell"][1] > mallar["enkel"][1],
              f"ordmålen skiljer sig åt ({[m[1] for m in mallar.values()]})")
        mapp = tempfile.mkdtemp(prefix="mall-okand-")
        try:
            p = Project.create(mapp, "Okänd mall", template="finns-inte")
            check([n.type for n in p.children(None)] == [CHAPTER, RESEARCH],
                  f"en okänd mall ger den minsta strukturen "
                  f"({[n.type for n in p.children(None)]})")
            tom = Project.create(tempfile.mkdtemp(prefix="mall-tom-"), "Ingen mall alls")
            check([n.type for n in tom.children(None)] == [CHAPTER, RESEARCH],
                  "och samma sak utan mall alls")
        finally:
            shutil.rmtree(mapp, ignore_errors=True)
        check(book.title == "Min bok", "titeln sparas")
        check(len(book.walk()) == len(book.nodes),
              f"allt ligger i trädet ({len(book.walk())} av {len(book.nodes)})")
        check(book.validate() == [], f"färskt projekt är giltigt: {book.validate()}")

        part = book.children(None)[0]
        chapter = book.children(part.id)[0]
        scene = book.children(chapter.id)[0]

        # researchmappen ligger i projektet men utanför manuset (R01.7)
        research = next((n for n in book.children(None) if n.type == RESEARCH), None)
        check(research is not None, "projektet har en researchmapp")
        check(not research.file, f"researchmappen är en behållare utan textfil ({research.file!r})")
        anteckning = book.add_node(NOTE, "Källor", parent=research.id)
        book.write(anteckning.id, "<p>Källa ett två tre fyra</p>")
        check(book.words(anteckning.id) == 5,
              f"anteckningen har sin egen text ({book.words(anteckning.id)})")
        check(all(n.id != anteckning.id for n in book.manuscript()),
              "anteckningen är inte med i manuset")
        check(book.words_in(research.id) == 0 and book.node_progress(research.id)["target"] == 0,
              f"researchmappen har noll manusord och inget mål "
              f"({book.node_progress(research.id)})")
        check(anteckning.id in [n.id for n in book.research()], "men den finns i research")
        check(book.validate() == [], "en anteckning i research är giltig")

        # koppling scen ↔ researchmaterial (R01.7)
        check(book.link_material(scene.id, anteckning.id) is True,
              "materialet kopplas till scenen")
        check([n.id for n in book.material_for(scene.id)] == [anteckning.id],
              f"scenen visar sitt material ({[n.title for n in book.material_for(scene.id)]})")
        check(book.link_material(scene.id, anteckning.id) is False,
              "samma koppling läggs inte två gånger")
        check(book.material_candidates(scene.id) == [],
              "det kopplade materialet är inte kvar som förslag")
        karta = book.add_node(NOTE, "Karta", parent=research.id)
        check([n.title for n in book.material_candidates(scene.id)] == ["Karta"],
              f"ett okopplat material föreslås "
              f"({[n.title for n in book.material_candidates(scene.id)]})")
        check(book.unlink_material(scene.id, anteckning.id) is True, "kopplingen kan tas bort")
        check(book.material_for(scene.id) == [], "och scenen visar inget material")
        book.link_material(scene.id, anteckning.id)
        check(book.validate() == [], "en koppling mellan två noder som finns är giltig")

        # text och ordräkning ("Rubrik" + fyra ord = 5)
        book.write(scene.id, "<html><body><h1>Rubrik</h1><p>ord ett två tre</p></body></html>")
        check(book.words(scene.id) == 5, f"ordräkningen stämmer ({book.words(scene.id)} != 5)")
        check(book.total_words() == 5, "totalen räknar scenerna")

        # spara och ladda om
        book.save()
        again = Project.load(root)
        check(len(again.walk()) == len(book.nodes),
              f"trädet överlever en omladdning ({len(again.walk())} av {len(book.nodes)})")
        check([n.id for n in again.material_for(scene.id)] == [anteckning.id],
              "och kopplingen scen ↔ material följer med")
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

        # ordning: en ny nod hamnar där den beställdes, inte i titelordning
        tredje = book.add_node(SCENE, "Aaa först i alfabetet", parent=chapter.id)
        check([n.title for n in book.children(chapter.id)][-1] == tredje.title,
              f"en ny nod hamnar sist även när titeln sorterar först "
              f"({[n.title for n in book.children(chapter.id)]})")
        book.delete_node(tredje.id)

        # metadata
        book.set_meta(scene.id, synopsis="Hon kommer hem.", status="Utkast",
                      labels=["POV: Anna"], target_words=1200, pov="Anna")
        check(book.by_id(scene.id).synopsis == "Hon kommer hem.", "synopsis sparas")
        check("Utkast" in book.settings["statuses"], "nya statusvärden lärs in")

        # statusfärg: härledd ur statuslistans ordning, samma varje gång (R01.5)
        check(book.status_color("Idé") == STATUS_PALETTE[0],
              f"första statusen får första färgen ({book.status_color('Idé')})")
        check(book.status_color("Utkast") == STATUS_PALETTE[1], "nästa status nästa färg")
        check(book.status_color("Finns inte") is None, "en status utanför listan har ingen färg")
        book.set_meta(second.id, status="Bearbetning")
        check(book.status_color("Bearbetning") == STATUS_PALETTE[4],
              f"en ny status får nästa lediga färg ({book.status_color('Bearbetning')})")
        check(book.status_color_for(scene.id) == book.status_color("Utkast"),
              "noden får sin status färg")
        check(book.status_color_for(part.id) is None, "en nod utan status har ingen färg")
        book.save()
        check(Project.load(root).status_color("Bearbetning") == STATUS_PALETTE[4],
              "och färgen är densamma efter en omladdning")
        # fler statusar än färger: paletten börjar om, inte kraschar
        for i in range(len(STATUS_PALETTE)):
            book.settings["statuses"].append(f"Status {i}")
        sista = len(book.settings["statuses"]) - 1
        check(book.status_color(f"Status {len(STATUS_PALETTE) - 1}")
              == STATUS_PALETTE[sista % len(STATUS_PALETTE)],
              f"paletten börjar om när statusarna är fler än färgerna "
              f"({book.status_color(f'Status {len(STATUS_PALETTE) - 1}')})")

        # ord och mål summerade i hierarkin (R01.10)
        book.write(scene.id, "<p>ett två tre fyra fem sex sju</p>")
        # En ny scen har sin rubrik som text i filen: "Scen 2" är två ord.
        check(book.words(second.id) == 2, f"en ny scen bär sin rubrik ({book.words(second.id)})")
        # Kapitel ett har bara scen ett (scen två flyttades till kapitel två ovan).
        check(book.node_progress(chapter.id)["words"] == 7,
              f"kapitlet summerar sina sceners ord ({book.node_progress(chapter.id)})")
        check(book.node_progress(part.id)["words"] == 9,
              f"delen summerar vidare nedåt i trädet ({book.node_progress(part.id)})")
        check(book.node_progress(chapter.id)["target"] == 1200,
              f"kapitlets mål är summan av scenernas ({book.node_progress(chapter.id)['target']})")
        book.set_meta(second.id, target_words=300)
        check(book.target(part.id) == 1500,
              f"delens mål är summan av båda kapitlens ({book.target(part.id)})")
        check(book.node_progress(chapter.id)["percent"] == 1,
              f"procenten räknas mot målet ({book.node_progress(chapter.id)})")
        book.set_meta(chapter.id, target_words=100)
        check(book.target(chapter.id) == 100,
              f"ett eget mål på behållaren vinner över summan ({book.target(chapter.id)})")
        book.set_meta(chapter.id, target_words=0)
        book.settings["target_words"] = book.total_words()
        check(book.progress()["percent"] == 100,
              f"projektet når 100 procent på sitt eget mål ({book.progress()})")
        book.settings["target_words"] = 0

        # samlingar: en handplockad och en sparad sökning (R01.8)
        manuell = book.add_collection("Tråd A", node_ids=[scene.id, second.id])
        check([n.id for n in book.select_collection(manuell.id)] == [scene.id, second.id],
              f"den handplockade samlingen ger sina scener i manusordning "
              f"({[n.title for n in book.select_collection(manuell.id)]})")
        check(book.toggle_in_collection(manuell.id, second.id) is False,
              "en scen kan tas ur samlingen")
        check([n.id for n in book.select_collection(manuell.id)] == [scene.id],
              "och är då borta ur urvalet")
        check(book.toggle_in_collection(manuell.id, second.id) is True, "och in igen")

        sokning = book.add_collection("Utkast", kind="search", query="status:Utkast")
        check([n.id for n in book.select_collection(sokning.id)] == [scene.id],
              f"sökningen hittar scenen med rätt status "
              f"({[n.title for n in book.select_collection(sokning.id)]})")
        bok = book.add_collection("Timglas", kind="search", query="Timglas")
        check(book.select_collection(bok.id) == [], "en sökning utan träff ger inget")
        book.write(second.id, "<p>Ett timglas stod på bordet.</p>")
        check([n.id for n in book.select_collection(bok.id)] == [second.id],
              "och hittar ordet när det finns i texten")
        book.write(second.id, "<p>Inget glas alls.</p>")
        check(book.select_collection(bok.id) == [],
              "en sökning är en fråga och räknas om varje gång")

        book.save()
        omladdad = Project.load(root)
        check([c.name for c in omladdad.collections] == [c.name for c in book.collections],
              f"samlingarna följer med till disk ({[c.name for c in omladdad.collections]})")
        check(omladdad.collection(sokning.id).query == "status:Utkast",
              "och frågan står kvar")
        kast = book.add_collection("Kastas")
        check(book.remove_collection(kast.id) is True
              and all(c.id != kast.id for c in book.collections), "en samling kan tas bort")
        try:
            book.collection("finns_inte")
            check(False, "okänt samlings-id skall ge KeyError")
        except KeyError:
            check(True, "okänt samlings-id ger KeyError")

        # scenanteckningen hör till scenen, inte till manuset (R01.12)
        fore_ord = book.words(scene.id)
        book.set_meta(scene.id, note="Kolla kapitel 3: hon har nyckeln redan här.")
        check(book.by_id(scene.id).note.startswith("Kolla kapitel 3"), "scenanteckningen sparas")
        check(book.words(scene.id) == fore_ord,
              f"och räknas inte in i prosan ({book.words(scene.id)} mot {fore_ord})")
        book.save()
        med_anteckning = Project.load(root)
        check(med_anteckning.by_id(scene.id).note.startswith("Kolla kapitel 3"),
              "scenanteckningen följer med till disk")

        # kommentarerna hänger på ett citat, inte på en position (R01.12)
        kom = book.add_comment(scene.id, "Hon kommer hem.", "Bygg ut den här scenen.")
        check(kom["id"] and not kom["resolved"], "en kommentar skapas ogiltig")
        check(book.comments_for(scene.id) == [kom], "och ligger på scenen")
        check(len(book.unresolved_comments()) == 1, "projektet räknar ogiltiga")
        check(book.resolve_comment(scene.id, kom["id"]) is True, "den kan markeras löst")
        check(book.unresolved_comments() == [], "och räknas då inte längre")
        check(book.comments_for(scene.id) == [kom], "men ligger kvar på scenen")
        check(book.resolve_comment(scene.id, kom["id"], False) is True,
              "och gå tillbaka till ogiltig")
        andra_kom = book.add_comment(scene.id, "Ja.", "Kort replik.")
        check([c["id"] for c in book.comments_for(scene.id)] == [kom["id"], andra_kom["id"]],
              f"ogiltiga kommentarer först ({book.comments_for(scene.id)})")
        check(book.resolve_comment(scene.id, "finns-inte") is False, "okänt id ger False")
        try:
            book.add_comment(scene.id, "   ", "utan textställe")
            check(False, "en kommentar utan citat skall vägras")
        except ValueError:
            check(True, "en kommentar utan citat vägras")
        book.save()
        igen = Project.load(root)
        check(len(igen.comments_for(scene.id)) == 2, "kommentarerna följer med till disk")
        check(igen.comment(scene.id, kom["id"])["text"] == "Bygg ut den här scenen.",
              "med sin text i behåll")
        check(igen.delete_comment(scene.id, kom["id"]) is True, "en kommentar kan tas bort")
        check(len(igen.comments_for(scene.id)) == 1, "och då är den borta")
        # ett trasigt manifest: kommentar utan citat faller bort i stället för att krascha
        trasig = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
        for node in trasig["nodes"]:
            if node["id"] == scene.id:
                node["comments"] = [{"id": "x1", "quote": "", "text": "utan citat"},
                                    {"id": "x2", "quote": "Ja.", "text": "med citat"}]
        (root / MANIFEST).write_text(json.dumps(trasig), encoding="utf-8")
        lagad = Project.load(root)
        check([c["id"] for c in lagad.comments_for(scene.id)] == ["x2"],
              f"en kommentar utan citat faller bort ({lagad.comments_for(scene.id)})")
        check(lagad.validate() == [], "och projektet är fortfarande giltigt")

        # manusvarianter: en namngiven ordning av scener (R01.14)
        book.move_node(second.id, chapter.id, 1)        # två scener i samma kapitel
        manus_fore = [n.id for n in book.manuscript()]
        check(len(manus_fore) == 2, f"två scener att ordna ({manus_fore})")
        variant = book.add_variant("Omvänd")
        check(variant["nodes"] == manus_fore,
              f"varianten börjar som manuset ({variant['nodes']})")
        check(book.variant(variant["id"]) is variant, "och går att slå upp")
        check(book.variant_diff(variant["id"]) == {"moved": [], "outside": [], "missing": []},
              "en färsk variant skiljer sig inte från manuset")

        sist, forst = manus_fore[1], manus_fore[0]
        check(book.move_in_variant(variant["id"], sist, -1) is True,
              "en scen kan flyttas i varianten")
        check(book.variant(variant["id"])["nodes"] == [sist, forst],
              f"och ordningen ändras ({book.variant(variant['id'])['nodes']})")
        check(book.move_in_variant(variant["id"], sist, -1) is False,
              "den som ligger först går inte att flytta framåt")
        check(book.move_in_variant(variant["id"], "finns-inte", 1) is False,
              "och en scen utanför varianten rörs inte")
        check(book.move_in_variant(variant["id"], sist, 5) is True,
              "en flytt förbi slutet stannar sist")
        check(book.variant(variant["id"])["nodes"] == [forst, sist],
              f"och ordningen är den begärda ({book.variant(variant['id'])['nodes']})")
        book.set_variant_order(variant["id"], [sist, forst])   # tillbaka till omvänd
        check([n.id for n in book.manuscript()] == manus_fore,
              "manuset är orört så länge varianten bara är en variant")

        diff = book.variant_diff(variant["id"])
        check(sorted(diff["moved"]) == sorted([sist, forst]),
              f"jämförelsen pekar ut de flyttade ({diff})")
        check(diff["missing"] == [] and diff["outside"] == [], "och inget saknas")

        # en scen som tagits bort ligger kvar i varianten, som 'utanför'
        tillfallig = book.add_node(SCENE, "Tillfällig", parent=chapter.id)
        book.set_variant_order(variant["id"], [tillfallig.id, sist, forst])
        book.delete_node(tillfallig.id)
        diff = book.variant_diff(variant["id"])
        check(diff["outside"] == [tillfallig.id],
              f"en borttagen scen märks som utanför ({diff})")
        check(book.variant_nodes(variant["id"]) == [book.by_id(sist), book.by_id(forst)],
              "och hoppas över när varianten läses")
        book.set_variant_order(variant["id"], [sist, forst])

        # variantens ordning kan läggas tillbaka på manuset (steg 4)
        check(book.apply_variant(variant["id"]) >= 1, "varianten läggs på manuset")
        check([n.id for n in book.manuscript()] == [sist, forst],
              f"och manuset får variantens ordning ({[n.title for n in book.manuscript()]})")
        check(book.variant_diff(variant["id"])["moved"] == [],
              "efteråt skiljer sig varianten inte från manuset")

        # och tillbaka igen, med en variant av den gamla ordningen
        tillbaka = book.add_variant("Tillbaka", [book.by_id(n) for n in manus_fore])
        book.apply_variant(tillbaka["id"])
        check([n.id for n in book.manuscript()] == manus_fore, "ordningen går att lägga tillbaka")

        # en variant tar bara emot scener — inte behållare, dubbletter eller okända
        check(book.set_variant_order(variant["id"], [chapter.id]) is False,
              "en behållare kan inte stå i en variant")
        check(book.set_variant_order(variant["id"], [forst, forst]) is False,
              "och inte samma scen två gånger")
        check(book.set_variant_order(variant["id"], ["finns-inte"]) is False, "okänt id avvisas")
        check(book.set_variant_order(variant["id"], [forst]) is True,
              "en riktig ordning tas emot")
        check(book.replace_in_variant(variant["id"], 0, sist) is True,
              "en scen kan bytas ut på en plats")
        check(book.variant(variant["id"])["nodes"] == [sist],
              f"och då står den där ({book.variant(variant['id'])['nodes']})")

        # rundtur till disk
        book.save()
        med_variant = Project.load(root)
        check([v["name"] for v in med_variant.variants] == ["Omvänd", "Tillbaka"],
              f"varianterna följer med till disk ({[v['name'] for v in med_variant.variants]})")
        check(med_variant.variant(variant["id"])["nodes"] == [sist],
              "med sin ordning i behåll")
        check(med_variant.delete_variant(variant["id"]) is True, "en variant kan tas bort")
        check(len(med_variant.variants) == 1, "och försvinner")
        check(med_variant.delete_variant("finns-inte") is False, "okänt id ger False")

        # ställ tillbaka fixturen: second hörde till Kapitel 2
        book.move_node(second.id, new_chapter.id)
        check(second.parent == new_chapter.id, "fixturen är tillbaka där den var")

        # borttagning tar barnen med sig och filen försvinner
        scene_file = book.path_of(book.by_id(scene.id))
        book.delete_node(chapter.id)
        check(all(n.id != chapter.id for n in book.nodes), "kapitlet är borta")
        check(scene_file is not None and not scene_file.exists(),
              "scenens fil städas bort")
        check([n.id for n in book.select_collection(manuell.id)] == [second.id],
              f"en borttagen scen faller ur den handplockade samlingen "
              f"({[n.title for n in book.select_collection(manuell.id)]})")
        check(book.links == [] or all(l["scene"] in {n.id for n in book.nodes}
                                      for l in book.links),
              f"kopplingen städas när scenen tas bort ({book.links})")
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
