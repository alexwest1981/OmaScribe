"""Tracebacken till en fil, och appen lever vidare.

Ett ohanterat undantag i en slot dödar PyQt6-processen med SIGABRT, och tracebacken
skrivs till stderr — som en app startad från skrivbordet inte har någonstans.
Alex 9/10: "Applikationen kraschade när jag försökte ändra och ta bort formatering
på en text som var på tok för stor" — och det fanns ingen traceback att läsa, bara
en core dump med `QMessageLogger::fatal` i. Ett manus får inte gå förlorat på en
krasch i en knapptryckning, och nästa gång skall felet gå att läsa.

`sys.excepthook` är den väg som bär: mätt med en slot som kastar från
händelseloopen (som en knapp gör) skrevs tracebacken till crash.log och appen
överlevde. En `QApplication.notify`-override prövades först och anropades aldrig —
PyQt6 stödjer den inte, så den är borttagen i stället för kvar som en tröst.
"""

from __future__ import annotations

import os
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path


def crash_log_path() -> Path:
    """Var tracebacken hamnar. Samma katalog som configen."""
    mapp = os.environ.get("SCRIBENTIA_CONFIG_PATH")
    bas = Path(mapp).parent if mapp else Path.home() / ".config" / "scribentia"
    bas.mkdir(parents=True, exist_ok=True)
    return bas / "crash.log"


def write_traceback(exc_type, exc, tb, note: str = "") -> str:
    """Skriver tracebacken till crash.log och till stderr. Returnerar filvägen."""
    rad = "".join(traceback.format_exception(exc_type, exc, tb))
    text = (f"\n{'=' * 70}\n{datetime.now().isoformat(timespec='seconds')}"
            f"{'  ' + note if note else ''}\n{'-' * 70}\n{rad}")
    fil = None
    try:
        fil = crash_log_path()
        with open(fil, "a", encoding="utf-8") as f:
            f.write(text)
    except OSError as fel:                     # går inte att skriva: stderr duger
        print(f"[crash] kunde inte skriva crash.log: {fel}", file=sys.stderr)
    # Stderr ändå: körs appen från terminalen ser man felet direkt.
    print(text, file=sys.stderr)
    sys.stderr.flush()
    return str(fil) if fil else ""


def install_handlers() -> None:
    """Fångar undantag i händelseloopen, i huvudtråden och i andra trådar."""

    def _hook(exc_type, exc, tb):
        write_traceback(exc_type, exc, tb, note="(i händelseloopen)")

    sys.excepthook = _hook

    def _thread_hook(args):
        if args.exc_type is SystemExit:
            return
        write_traceback(args.exc_type, args.exc_value, args.exc_traceback,
                        note=f"(tråd {args.thread.name if args.thread else '?'})")

    threading.excepthook = _thread_hook
