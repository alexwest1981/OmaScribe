"""Document snapshots and lightweight version history."""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import shutil
import tempfile
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Snapshot:
    id: str
    source: str
    label: str
    created: str
    sha256: str
    size: int


class SnapshotStore:
    """Store immutable text snapshots and a rebuildable JSON index."""

    def __init__(self, root: str):
        self.root = Path(root)
        self.content_dir = self.root / "content"
        self.index_path = self.root / "index.json"
        self.content_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _digest(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _atomic_write(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except BaseException:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            raise

    def _write_index(self, snapshots: list[Snapshot]) -> None:
        payload = json.dumps([asdict(item) for item in snapshots], ensure_ascii=False,
                             indent=2).encode("utf-8")
        self._atomic_write(self.index_path, payload)

    def _recover(self) -> list[Snapshot]:
        recovered: list[Snapshot] = []
        for path in self.content_dir.glob("*.txt"):
            try:
                data = path.read_bytes()
                metadata = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
                item = Snapshot(**metadata)
                if item.id != path.stem or item.sha256 != self._digest(data):
                    continue
                item.size = len(data)
                recovered.append(item)
            except (OSError, ValueError, TypeError, KeyError):
                continue
        recovered.sort(key=lambda item: (item.created, item.id), reverse=True)
        self._write_index(recovered)
        return recovered

    def _load(self) -> list[Snapshot]:
        try:
            raw = json.loads(self.index_path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise ValueError("Snapshot index must be a list")
            result = [Snapshot(**entry) for entry in raw]
            # Läsbarhet och integritet kontrolleras mot innehållsfilerna.
            for item in result:
                if not (self.content_dir / f"{item.id}.txt").is_file():
                    raise ValueError("Snapshot content is missing")
            return result
        except (OSError, ValueError, TypeError, KeyError):
            return self._recover()

    def create(self, source: str, label: str = "", content: str | None = None) -> Snapshot:
        source_path = os.path.abspath(os.fspath(source))
        text = Path(source_path).read_text(encoding="utf-8") if content is None else content
        data = text.encode("utf-8")
        snapshot_id = uuid.uuid4().hex
        item = Snapshot(
            id=snapshot_id,
            source=source_path,
            label=label,
            created=datetime.now(timezone.utc).isoformat(),
            sha256=self._digest(data),
            size=len(data),
        )
        self._atomic_write(self.content_dir / f"{snapshot_id}.txt", data)
        # Separat sidofil gör indexet helt återskapningsbart efter korruption.
        self._atomic_write(self.content_dir / f"{snapshot_id}.json",
                           json.dumps(asdict(item), ensure_ascii=False).encode("utf-8"))
        items = self._load()
        items.append(item)
        items.sort(key=lambda entry: (entry.created, entry.id), reverse=True)
        self._write_index(items)
        return item

    def list(self, source: str | None = None) -> list[Snapshot]:
        items = self._load()
        if source is not None:
            source_path = os.path.abspath(os.fspath(source))
            items = [item for item in items if item.source == source_path]
        return sorted(items, key=lambda item: (item.created, item.id), reverse=True)

    def _find(self, snapshot_id: str) -> Snapshot:
        for item in self._load():
            if item.id == snapshot_id:
                return item
        raise KeyError(f"Unknown snapshot: {snapshot_id}")

    def read(self, snapshot_id: str) -> str:
        self._find(snapshot_id)
        return (self.content_dir / f"{snapshot_id}.txt").read_text(encoding="utf-8")

    def restore(self, snapshot_id: str, target: str | None = None) -> str:
        item = self._find(snapshot_id)
        destination = os.path.abspath(os.fspath(target if target is not None else item.source))
        text = self.read(snapshot_id)
        self._atomic_write(Path(destination), text.encode("utf-8"))
        return destination

    def diff(self, snapshot_id: str) -> str:
        item = self._find(snapshot_id)
        try:
            current = Path(item.source).read_text(encoding="utf-8")
        except FileNotFoundError:
            current = ""
        # difflib ger en läsbar unified diff direkt i stdlib, med färre rader än DMP-konvertering.
        return "".join(difflib.unified_diff(
            self.read(snapshot_id).splitlines(keepends=True),
            current.splitlines(keepends=True),
            fromfile=f"snapshot/{snapshot_id}", tofile=item.source,
        ))

    def prune(self, source: str, keep: int = 50) -> int:
        if keep < 0:
            raise ValueError("keep must be non-negative")
        source_path = os.path.abspath(os.fspath(source))
        matching = [item for item in self._load() if item.source == source_path]
        matching.sort(key=lambda item: (item.created, item.id), reverse=True)
        removed = matching[keep:]
        if not removed:
            return 0
        doomed = {item.id for item in removed}
        remaining = [item for item in self._load() if item.id not in doomed]
        self._write_index(remaining)
        for item in removed:
            for suffix in (".txt", ".json"):
                try:
                    (self.content_dir / f"{item.id}{suffix}").unlink()
                except FileNotFoundError:
                    pass
        return len(removed)


def _self_test() -> int:
    import time

    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        assert condition, message
        checks += 1

    temporary = tempfile.mkdtemp(prefix="omascribe-snapshots-")
    try:
        base = Path(temporary)
        source = base / "draft.md"
        other = base / "other.md"
        store = SnapshotStore(str(base / ".snapshots"))
        original = "Första raden\nEn rad till.\n"
        source.write_text(original, encoding="utf-8")
        first = store.create(str(source), "Ursprung")
        first_hash = hashlib.sha256(store.read(first.id).encode()).hexdigest()
        source.write_text("Första raden\nÄndrad rad.\n", encoding="utf-8")
        check("-En rad till." in store.diff(first.id) and "+Ändrad rad." in store.diff(first.id),
              "diff must show changed lines")
        restored = store.restore(first.id)
        check(restored == str(source) and hashlib.sha256(source.read_bytes()).hexdigest() == first_hash,
              "restore must reproduce exact snapshot bytes")
        source.unlink()
        store.restore(first.id)
        check(source.read_text(encoding="utf-8") == original, "deleted source must be restored")
        time.sleep(0.002)
        second = store.create(str(source), "Second", "second\n")
        time.sleep(0.002)
        third = store.create(str(source), "Third", "third\n")
        store.create(str(other), "Other", "other\n")
        listed = store.list()
        check(listed[0].id != listed[-1].id and listed[0].created >= listed[1].created,
              "list must be newest first")
        check(all(item.source == str(source) for item in store.list(str(source))),
              "list must filter by source")
        store.index_path.write_text("{broken", encoding="utf-8")
        check({item.id for item in store.list()} >= {first.id, second.id, third.id},
              "corrupt index must recover from content files")
        old = store.create(str(source), "Old", "old\n")
        time.sleep(0.002)
        newest = store.create(str(source), "Newest", "new\n")
        removed = store.prune(str(source), keep=2)
        retained = store.list(str(source))
        check(removed == 3, "prune must remove all but keep count")
        check([item.id for item in retained] == [newest.id, old.id],
              "prune must retain newest snapshots")
    finally:
        shutil.rmtree(temporary, ignore_errors=True)
    print(f"snapshots: {checks} kontroller gröna")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
