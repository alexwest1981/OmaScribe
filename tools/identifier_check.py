"""tools/identifier_check.py — namn med å/ä/ö i koden.

PyQt6 **kraschar** (segmenteringsfel, inte ett undantag) när en signal kopplas
till en metod vars namn innehåller tecken utanför ASCII:

    e.textChanged.connect(self._uppdatera_förhandsvisning)   ->  Segmentation fault

Sip, som PyQt bygger på, klarar inte namnet. Felet är tyst i den meningen att
det inte finns någon spårning i Python — bara en död process. Därför den här
vakten: en identifierare i kod skrivs på engelska, och den regeln råkar vara
exakt vad PyQt kräver.

Bara `def` och `class` kontrolleras: ett parameternamn eller en lokal variabel
kopplas aldrig till en signal, och strängar får förstås innehålla vad som helst
(`_("...")`-nycklarna kontrolleras av tools/i18n_keys_check.py).

    python3 tools/identifier_check.py     0 = rent, 1 = fynd
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

SKIP_DIRS = {"__pycache__", ".venv", ".git", "build", "dist", "node_modules"}


def non_ascii(name: str) -> bool:
    return any(ord(tecken) > 127 for tecken in name)


def findings(root: Path) -> list[tuple[str, int, str, str]]:
    """(fil, rad, namn, vad) för varje def/class vars namn inte är ASCII."""
    ut: list[tuple[str, int, str, str]] = []
    for fil in sorted(root.rglob("*.py")):
        if any(bit in SKIP_DIRS for bit in fil.parts):
            continue
        try:
            träd = ast.parse(fil.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for nod in ast.walk(träd):
            if isinstance(nod, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if non_ascii(nod.name):
                    vad = "klass" if isinstance(nod, ast.ClassDef) else "funktion"
                    ut.append((str(fil.relative_to(root)), nod.lineno, nod.name, vad))
    return ut


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    fynd = findings(root)
    for fil, rad, namn, vad in fynd:
        print(f"  FEL {fil}:{rad}: {vad}en ”{namn}” har tecken utanför ASCII")
    if fynd:
        print(f"identifier_check: {len(fynd)} namn att byta — PyQt6 kraschar "
              f"om de kopplas till en signal")
        return 1
    print("identifier_check: rent — alla namn i koden är ASCII")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
