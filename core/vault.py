"""
core/vault.py — Obsidian-liknande anteckningsvalv för OmaScribe.

Hanterar en mapp med Markdown-anteckningar: indexering, [[wikilinks]],
backlinks, taggar, sökning och skapande av nya anteckningar.

Medvetet fritt från Qt och HTTP — ren Python — så att valvlogiken kan
testas fristående (se _self_test längst ned: `python core/vault.py`).
"""

import os
import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

VAULT_DEFAULT_DIR = os.path.expanduser("~/Documents/OmaScribe Vault")
NOTE_EXTS = (".md", ".markdown", ".txt")   # textfiler som indexeras
NOTE_EXT = ".md"                            # ändelsen nya anteckningar får
MAX_SCAN_BYTES = 2_000_000  # skydda mot att läsa in enorma filer i indexet

# [[Mål]] | [[Mål|alias]] | [[Mål#rubrik]] | [[Mål#rubrik|alias]]
WIKILINK_RE = re.compile(r"\[\[([^\[\]]+?)\]\]")
# #tagg — men inte "# Rubrik" (kräver ett ordtecken direkt efter #).
# [^\W_] = bokstav eller siffra i valfritt skriftsystem, alltså även å ä ö é ü.
TAG_RE = re.compile(r"(?:^|[\s(])#([^\W_][\w\-/]*)")
FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_ILLEGAL_FILENAME = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def slugify(name: str) -> str:
    """Normaliserar ett länk-/filnamn för uppslagning.

    Gör 'Min Anteckning', 'min-anteckning' och 'Min_Anteckning' till samma
    nyckel, precis som Obsidian matchar länkar oberoende av skiftläge och
    avstavning.
    """
    s = (name or "").strip().lower()
    # NFKD delar upp 'é' i 'e' + accenttecken, som sedan plockas bort. Det
    # täcker å ä ö é ü och resten, inte bara de tre svenska bokstäverna.
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("ø", "o").replace("æ", "ae").replace("ß", "ss")
    s = re.sub(r"[\s_\-]+", "", s)
    return s


def split_link_target(raw: str) -> tuple:
    """Delar upp ett rå länktext i (mål, rubrik, alias)."""
    alias = ""
    if "|" in raw:
        raw, alias = raw.split("|", 1)
    heading = ""
    if "#" in raw:
        raw, heading = raw.split("#", 1)
    return raw.strip(), heading.strip(), alias.strip()


@dataclass
class Note:
    """En anteckning i valvet."""

    path: str
    title: str
    rel_path: str
    mtime: float = 0.0
    size: int = 0
    links: list = field(default_factory=list)      # utgående [[länkar]] (mål)
    tags: list = field(default_factory=list)
    h1: str = ""                                    # första H1-rubriken, om den skiljer sig
    content: str = ""
    is_open: bool = False

    @property
    def modified_label(self) -> str:
        try:
            return time.strftime("%Y-%m-%d %H:%M", time.localtime(self.mtime))
        except Exception:
            return ""

    def preview(self, length: int = 140) -> str:
        """Kort textutsnitt för listvisning."""
        body = self.content
        # Hoppa över frontmatter och rubriker
        body = FRONTMATTER_RE.sub("", body)
        lines = []
        for line in body.splitlines():
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("---"):
                continue
            s = WIKILINK_RE.sub(lambda m: split_link_target(m.group(1))[2] or split_link_target(m.group(1))[0], s)
            lines.append(s)
            if sum(len(x) for x in lines) > length:
                break
        text = " ".join(lines)
        return (text[:length] + "…") if len(text) > length else text

    def word_count(self) -> int:
        return len(self.content.split())


class Vault:
    """Ett anteckningsvalv på disk."""

    def __init__(self, root: Optional[str] = None):
        self.root = os.path.abspath(os.path.expanduser(root or VAULT_DEFAULT_DIR))
        self.notes: list = []
        self._by_path: dict = {}
        self._by_slug: dict = {}
        self._last_scan = 0.0

    # ---------------------------------------------------------------- filsystem

    def ensure_exists(self) -> bool:
        try:
            os.makedirs(self.root, exist_ok=True)
            return True
        except Exception as e:
            print(f"[Vault] Kan inte skapa valvet {self.root}: {e}")
            return False

    def exists(self) -> bool:
        return os.path.isdir(self.root)

    # ------------------------------------------------------------------ skanning

    def scan(self) -> int:
        """Bygger om indexet från disk. Returnerar antalet anteckningar."""
        self.notes = []
        self._by_path = {}
        self._by_slug = {}

        if not self.exists():
            self._last_scan = time.time()
            return 0

        for dirpath, dirnames, filenames in os.walk(self.root):
            # Dolda mappar (.obsidian, .git, .trash) hoppas över
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fname in filenames:
                if not fname.lower().endswith(NOTE_EXTS) or fname.startswith("."):
                    continue
                full = os.path.join(dirpath, fname)
                note = self._read_note(full)
                if note is not None:
                    self.notes.append(note)

        self.notes.sort(key=lambda n: n.title.lower())
        self._last_scan = time.time()
        return len(self.notes)

    def scan_if_stale(self, max_age_sec: float = 5.0) -> bool:
        """Skannar bara om indexet är äldre än max_age_sec. True om den skannade."""
        if (time.time() - self._last_scan) > max_age_sec or not self.notes:
            self.scan()
            return True
        return False

    def _read_note(self, path: str) -> Optional[Note]:
        try:
            size = os.path.getsize(path)
            mtime = os.path.getmtime(path)
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(MAX_SCAN_BYTES)
        except Exception as e:
            print(f"[Vault] Kan inte läsa {path}: {e}")
            return None

        title = os.path.splitext(os.path.basename(path))[0]
        body = FRONTMATTER_RE.sub("", content)

        links = []
        for m in WIKILINK_RE.finditer(body):
            target, _h, _a = split_link_target(m.group(1))
            if target:
                links.append(target)

        tags = []
        for m in TAG_RE.finditer(body):
            tag = m.group(1)
            if tag and tag not in tags:
                tags.append(tag)

        h1 = ""
        hm = H1_RE.search(body)
        if hm:
            h1 = hm.group(1).strip()
            if slugify(h1) == slugify(title):
                h1 = ""

        note = Note(
            path=path,
            title=title,
            rel_path=os.path.relpath(path, self.root),
            mtime=mtime,
            size=size,
            links=links,
            tags=tags,
            h1=h1,
            content=content,
        )
        self._by_path[os.path.abspath(path)] = note
        self._by_slug.setdefault(slugify(title), note)
        return note

    # ------------------------------------------------------------------ uppslagning

    def get(self, name: str) -> Optional[Note]:
        """Slår upp en anteckning på titel/filnamn (skiftläges- och avstavningsokänsligt)."""
        if not name:
            return None
        s = slugify(name)
        if s in self._by_slug:
            return self._by_slug[s]
        # Sista utväg: matcha mot rel_path utan ändelse
        for n in self.notes:
            if slugify(os.path.splitext(n.rel_path)[0]) == s:
                return n
        return None

    def get_by_path(self, path: str) -> Optional[Note]:
        return self._by_path.get(os.path.abspath(path))

    def resolve(self, target: str) -> Optional[Note]:
        """Löser ett [[wikilink]]-mål till en anteckning (None = oskapad länk)."""
        t, _h, _a = split_link_target(target)
        return self.get(t)

    def unresolved_targets(self) -> list:
        """Alla länkade mål som ännu inte har någon anteckning."""
        seen, out = set(), []
        for n in self.notes:
            for link in n.links:
                s = slugify(link)
                if s and s not in seen and self.resolve(link) is None:
                    seen.add(s)
                    out.append(link)
        return sorted(out, key=str.lower)

    # ------------------------------------------------------------------ relationer

    def outlinks(self, note: Note) -> list:
        """Utgående länkar som (titel, Note|None, rå)."""
        result, seen = [], set()
        for link in note.links:
            s = slugify(link)
            if s in seen:
                continue
            seen.add(s)
            result.append((link, self.resolve(link), link))
        return result

    def backlinks(self, note: Note) -> list:
        """Anteckningar som länkar hit. Returnerar [(Note, kontextmening)]."""
        out, seen = [], set()
        keys = {slugify(note.title), slugify(os.path.splitext(note.rel_path)[0])}
        for other in self.notes:
            if other.path == note.path:
                continue
            for link in other.links:
                t, _h, _a = split_link_target(link)
                if slugify(t) in keys:
                    if other.path in seen:
                        break
                    seen.add(other.path)
                    out.append((other, self._context_for(other.content, link)))
                    break
        return out

    @staticmethod
    def _context_for(content: str, link: str, width: int = 70) -> str:
        """Plockar fram meningen där länken förekommer."""
        idx = content.find(f"[[{link}]]")
        if idx < 0:
            idx = content.find(link)
            if idx < 0:
                return ""
        start = max(0, idx - width)
        end = min(len(content), idx + len(link) + width)
        snippet = content[start:end].replace("\n", " ").strip()
        return ("…" if start > 0 else "") + snippet + ("…" if end < len(content) else "")

    def graph(self) -> tuple:
        """Returnerar (noder, kanter) för en grafvy. Kanter är (källa, mål)-titlar."""
        nodes = [n.title for n in self.notes]
        edges, valid = [], {slugify(n.title) for n in self.notes}
        for n in self.notes:
            for link in n.links:
                t, _h, _a = split_link_target(link)
                if slugify(t) in valid:
                    target = self.get(t)
                    if target is not None:
                        edges.append((n.title, target.title))
        return nodes, edges

    def all_tags(self) -> list:
        """[(tagg, antal)] sorterat på antal."""
        counts = {}
        for n in self.notes:
            for t in n.tags:
                counts[t] = counts.get(t, 0) + 1
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0].lower()))

    # ------------------------------------------------------------------ sökning

    def search(self, query: str, limit: int = 50) -> list:
        """Rankad sökning. Returnerar [(Note, snutt, poäng)]. Titel > tagg > innehåll."""
        q = (query or "").strip()
        if not q:
            return [(n, n.preview(), 0) for n in self.notes[:limit]]

        ql = q.lower()
        qs = slugify(q)
        results = []

        for n in self.notes:
            score, snippet = 0, ""

            if ql == n.title.lower():
                score += 100
            elif qs and qs == slugify(n.title):
                score += 90
            elif ql in n.title.lower():
                score += 60

            if any(ql == t.lower() for t in n.tags):
                score += 40
            elif any(ql in t.lower() for t in n.tags):
                score += 25

            if n.h1 and ql in n.h1.lower():
                score += 15

            low = n.content.lower()
            hits = low.count(ql)
            if hits:
                score += min(hits, 8) * 5
                idx = low.find(ql)
                start = max(0, idx - 60)
                end = min(len(n.content), idx + len(q) + 60)
                snippet = n.content[start:end].replace("\n", " ").strip()
                snippet = ("…" if start > 0 else "") + snippet + ("…" if end < len(n.content) else "")

            if score > 0:
                results.append((n, snippet or n.preview(), score))

        results.sort(key=lambda r: (-r[2], r[0].title.lower()))
        return results[:limit]

    # ------------------------------------------------------------------ skrivande

    @staticmethod
    def safe_filename(title: str) -> str:
        """Gör om en titel till ett säkert filnamn."""
        name = _ILLEGAL_FILENAME.sub("", (title or "").strip())
        name = re.sub(r"\s+", " ", name).strip(" .")
        return name or "Anteckning"

    def unique_path(self, title: str, folder: str = "") -> str:
        """Hittar en ledig sökväg för en ny anteckning (lägger till 2, 3, ...)."""
        base = self.safe_filename(title)
        target_dir = os.path.join(self.root, folder) if folder else self.root
        candidate = os.path.join(target_dir, base + NOTE_EXT)
        i = 2
        while os.path.exists(candidate):
            candidate = os.path.join(target_dir, f"{base} {i}{NOTE_EXT}")
            i += 1
        return candidate

    def create_note(self, title: str, content: str = "", folder: str = "") -> Optional[Note]:
        """Skapar en ny anteckning och lägger in den i indexet."""
        if not self.ensure_exists():
            return None
        path = self.unique_path(title, folder)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if content and not content.endswith("\n"):
                content += "\n"
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"[Vault] Kan inte skapa {path}: {e}")
            return None

        note = self._read_note(path)
        if note is not None:
            self.notes.append(note)
            self.notes.sort(key=lambda n: n.title.lower())
        return note

    def read_note_content(self, note: Note) -> str:
        """Läser hela filen från disk (indexet kan vara äldre)."""
        try:
            with open(note.path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return note.content

    def write_note_content(self, note: Note, content: str) -> bool:
        """Skriver tillbaka en anteckning till disk och uppdaterar indexet."""
        try:
            with open(note.path, "w", encoding="utf-8") as f:
                f.write(content)
            refreshed = self._read_note(note.path)
            if refreshed is not None:
                for i, n in enumerate(self.notes):
                    if n.path == note.path:
                        self.notes[i] = refreshed
                        break
            return True
        except Exception as e:
            print(f"[Vault] Kan inte skriva {note.path}: {e}")
            return False

    def append_to_note(self, note: Note, text: str) -> bool:
        """Lägger till text i slutet av en anteckning (skapar filen om den saknas)."""
        current = self.read_note_content(note) if os.path.exists(note.path) else ""
        if current and not current.endswith("\n"):
            current += "\n"
        if current and not current.endswith("\n\n"):
            current += "\n"
        return self.write_note_content(note, current + text.rstrip() + "\n")

    def stats(self) -> dict:
        links_total = sum(len(n.links) for n in self.notes)
        return {
            "notes": len(self.notes),
            "words": sum(n.word_count() for n in self.notes),
            "links": links_total,
            "tags": len(self.all_tags()),
            "unresolved": len(self.unresolved_targets()),
            "root": self.root,
        }


# ---------------------------------------------------------------------- självtest

def _self_test() -> int:
    """Bygger ett tillfälligt valv och kontrollerar kärnlogiken. 0 = OK."""
    import tempfile
    import shutil

    failures = []

    def check(label, got, want):
        if got != want:
            failures.append(f"{label}: fick {got!r}, väntade {want!r}")

    tmp = tempfile.mkdtemp(prefix="omascribe-vault-")
    try:
        v = Vault(tmp)
        v.ensure_exists()

        a = v.create_note("Projektidé", "# Projektidé\n\nDetta bygger på [[Forskning]] och [[Saknas|en tom länk]].\n\n#arbete #anteckning")
        b = v.create_note("Forskning", "## Källor\nSe [[Projektidé]].\n\n#arbete")
        c = v.create_note("Dagbok", "Inga länkar här.\n\n#privat")

        check("skanning", v.scan(), 3)
        check("create_note returnerar Note", a is not None, True)

        # Länkuppslagning, skiftläge och avstavning
        def title_of(name):
            n = v.get(name)
            return n.title if n else None

        def content_of(name):
            n = v.get(name)
            return n.content if n else ""

        check("get exakt", title_of("Projektidé"), "Projektidé")
        check("get skiftläge", title_of("projektidé"), "Projektidé")
        check("get avstavat", v.get("Projekt-Idé") is not None, True)
        check("get okänd", v.get("Finns Inte"), None)

        # Utgående länkar + oskapade mål
        a_fresh = v.get("Projektidé")
        assert a_fresh is not None
        outs = [t for t, _n, _r in v.outlinks(a_fresh)]
        check("utgående länkar", sorted(outs), sorted(["Forskning", "Saknas"]))
        check("olösta mål", v.unresolved_targets(), ["Saknas"])

        # Backlinks
        bl = v.backlinks(a_fresh)
        check("backlinks från Forskning", [n.title for n, _ctx in bl], ["Forskning"])
        check("backlinks kontext", "Projektidé" in bl[0][1], True)

        # Taggar — "# Rubrik" ska inte bli en tagg
        tags = dict(v.all_tags())
        check("tagg arbete", tags.get("arbete"), 2)
        check("tagg privat", tags.get("privat"), 1)
        check("rubrik ej tagg", "Projektidé" in tags, False)

        # Sökning och rangordning
        res = v.search("projekt")
        check("sök träffar", res[0][0].title, "Projektidé")
        check("sök tagg", [n.title for n, _s, _p in v.search("arbete")], ["Forskning", "Projektidé"])
        check("sök innehåll", [n.title for n, _s, _p in v.search("Källor")], ["Forskning"])
        check("sök tomt = alla", len(v.search("")), 3)

        # Graf
        nodes, edges = v.graph()
        check("grafnoder", len(nodes), 3)
        check("grafkanter", ("Projektidé", "Forskning") in edges, True)

        # Skrivande
        v.append_to_note(a_fresh, "\nTillägg i slutet.")
        v.scan()
        check("append", "Tillägg i slutet." in content_of("Projektidé"), True)

        # Filnamnssanering och unika namn
        check("sanering", Vault.safe_filename('Fråga: "ja/nej"?'), "Fråga janej")
        dup = v.create_note("Projektidé")  # kollision ska ge ett nytt namn
        assert dup is not None
        check("unik titel", os.path.basename(dup.path), "Projektidé 2.md")

        check("statistik", v.stats()["notes"], 4)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("SJÄLVTEST MISSLYCKADES:")
        for f in failures:
            print("  ✗", f)
        return 1
    print("✓ Alla valvtester passerade.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
