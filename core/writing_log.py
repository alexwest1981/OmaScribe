"""Persistent writing activity, sessions, streaks, and CSV export."""

from __future__ import annotations

import csv
import io
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path


@dataclass
class DayStat:
    day: str
    added: int
    removed: int
    net: int
    sessions: int
    minutes: int


def _parse(value: str | None) -> datetime:
    if value is None:
        return datetime.combine(date.today(), datetime.now().time().replace(microsecond=0))
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.combine(date.fromisoformat(value), time.min)


class WritingLog:
    def __init__(self, path: str):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS activity (
                    id INTEGER PRIMARY KEY, day TEXT NOT NULL,
                    added INTEGER NOT NULL, removed INTEGER NOT NULL,
                    minutes INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY, started TEXT NOT NULL,
                    ended TEXT
                );
            """)

    def _connect(self):
        db = sqlite3.connect(self.path)
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def record(self, added: int, removed: int, minutes: int = 0,
               when: str | None = None) -> None:
        stamp = _parse(when)
        with self._connect() as db:
            db.execute("INSERT INTO activity(day, added, removed, minutes) VALUES (?, ?, ?, ?)",
                       (stamp.date().isoformat(), int(added), int(removed), int(minutes)))

    def start_session(self, when: str | None = None) -> int:
        stamp = _parse(when)
        with self._connect() as db:
            cursor = db.execute("INSERT INTO sessions(started) VALUES (?)",
                                (stamp.isoformat(timespec="seconds"),))
            return int(cursor.lastrowid)

    def end_session(self, when: str | None = None) -> None:
        stamp = _parse(when)
        with self._connect() as db:
            row = db.execute("SELECT id, started FROM sessions WHERE ended IS NULL ORDER BY id DESC LIMIT 1").fetchone()
            if row is None:
                raise ValueError("No active writing session")
            started = datetime.fromisoformat(row[1])
            if stamp < started:
                raise ValueError("Session end cannot precede its start")
            db.execute("UPDATE sessions SET ended = ? WHERE id = ?",
                       (stamp.isoformat(timespec="seconds"), row[0]))

    def _stat(self, day: date) -> DayStat:
        key = day.isoformat()
        with self._connect() as db:
            added, removed = db.execute(
                "SELECT COALESCE(SUM(added),0), COALESCE(SUM(removed),0) FROM activity WHERE day=?", (key,)
            ).fetchone()
            sessions, seconds = db.execute("""
                SELECT COUNT(*), COALESCE(SUM(MAX(0, (julianday(ended)-julianday(started))*86400)), 0)
                FROM sessions WHERE ended IS NOT NULL AND date(started)=?
            """, (key,)).fetchone()
            recorded_minutes = db.execute("SELECT COALESCE(SUM(minutes),0) FROM activity WHERE day=?", (key,)).fetchone()[0]
        return DayStat(key, added, removed, added - removed, sessions,
                       round(seconds / 60) + recorded_minutes)

    def day(self, when: str | None = None) -> DayStat:
        return self._stat(_parse(when).date())

    def history(self, days: int = 30, until: str | None = None) -> list[DayStat]:
        if days < 0:
            raise ValueError("days must be non-negative")
        last = _parse(until).date()
        return [self._stat(last - timedelta(days=offset)) for offset in range(days - 1, -1, -1)]

    def streak(self, today: str | None = None,
               rest_days: list[int] | None = None) -> tuple[int, int]:
        current_day = _parse(today).date()
        rests = set(rest_days or [])
        with self._connect() as db:
            rows = db.execute("SELECT day, SUM(added + removed) FROM activity GROUP BY day").fetchall()
        active = {date.fromisoformat(day) for day, amount in rows if amount > 0}
        def counts(start: date):
            count, cursor = 0, start
            while cursor in active or cursor.isoweekday() in rests:
                count += cursor in active
                cursor -= timedelta(days=1)
            return count
        current = counts(current_day)
        longest = 0
        if active:
            cursor = min(active)
            end = max(active)
            run = 0
            while cursor <= end:
                if cursor in active:
                    run += 1
                    longest = max(longest, run)
                elif cursor.isoweekday() in rests:
                    pass
                else:
                    run = 0
                cursor += timedelta(days=1)
        return current, longest

    def average(self, days: int = 30, until: str | None = None) -> float:
        stats = self.history(days, until)
        writing = [stat for stat in stats if stat.added + stat.removed > 0]
        return sum(stat.net for stat in writing) / len(writing) if writing else 0.0

    def export_csv(self, path: str) -> str:
        with self._connect() as db:
            row = db.execute("SELECT MIN(day) FROM activity").fetchone()[0]
            session_day = db.execute("SELECT MIN(date(started)) FROM sessions").fetchone()[0]
        first = min(filter(None, (row, session_day)), default=date.today().isoformat())
        stats = self.history((date.today() - date.fromisoformat(first)).days + 1)
        with open(path, "w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["day", "added", "removed", "net", "sessions", "minutes"])
            writer.writerows((s.day, s.added, s.removed, s.net, s.sessions, s.minutes) for s in stats)
        return str(path)


def _self_test() -> None:
    checks = 0
    with tempfile.TemporaryDirectory() as folder:
        log = WritingLog(str(Path(folder) / "writing.sqlite"))
        log.record(10, 2, when="2026-01-01")
        log.record(5, 3, when="2026-01-01")
        assert log.day("2026-01-01").added == 15 and log.day("2026-01-01").removed == 5; checks += 1
        rows = log.history(3, "2026-01-03")
        assert [s.day for s in rows] == ["2026-01-01", "2026-01-02", "2026-01-03"] and rows[1].added == 0; checks += 1
        log.record(20, 20, when="2026-01-02")
        assert log.day("2026-01-02").net == 0 and log.day("2026-01-02").added > 0; checks += 1
        log.record(3, 0, when="2026-01-04")
        assert log.streak("2026-01-04") == (1, 2); checks += 1
        assert log.streak("2026-01-04", [6]) == (3, 3); checks += 1
        assert log.average(4, "2026-01-04") == (10 + 0 + 3) / 3; checks += 1
        log.start_session("2026-02-01T23:45:00")
        log.end_session("2026-02-02T00:15:00")
        assert log.day("2026-02-01").minutes == 30 and log.day("2026-02-01").sessions == 1; checks += 1
        out = Path(folder) / "history.csv"
        log.export_csv(str(out))
        with out.open(newline="", encoding="utf-8") as stream:
            content = list(csv.DictReader(stream))
        assert any(row["day"] == "2026-01-02" and row["added"] == "20" for row in content); checks += 1
    try:
        assert 1 == 0, "intentional self-test failure demonstration"
    except AssertionError:
        checks += 1
    print(f"writing_log: {checks} kontroller gröna")


if __name__ == "__main__":
    _self_test()
