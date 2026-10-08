"""Vakten mot att `_` skuggas — tredje gången felet dök upp i fas 4 och 5.

i18n-funktionen heter `_`, och den som skriver `for _, x in ...` eller
`namn, _, not = ...` i samma metod får ett heltal i stället för en funktion.
Felet är tyst tills raden körs, och då kraschar en menyväg ingen kontroll rör.

Kontrollen är medvetet enkel och förlåtande: den larmar bara när en **metod**
både anropar `_("...")` och binder `_`. Att binda `_` i en metod som aldrig
använder i18n är helt ofarligt och ska inte hindra någon.
"""
from __future__ import annotations

import ast
import pathlib
import sys


def _binds_underscore(target: ast.AST) -> bool:
    if isinstance(target, ast.Name):
        return target.id == "_"
    if isinstance(target, (ast.Tuple, ast.List)):
        return any(_binds_underscore(element) for element in target.elts)
    return False


def shadowing_scopes(path: pathlib.Path) -> list:
    """(rad, namn) för varje funktion som både anropar och binder `_`."""
    try:
        träd = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as fel:
        return [(getattr(fel, "lineno", 0), f"syntaxfel: {fel.msg}")]

    ut = []
    for nod in ast.walk(träd):
        if not isinstance(nod, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        anropar = False
        binder = None
        for barn in ast.walk(nod):
            if isinstance(barn, ast.Call) and isinstance(barn.func, ast.Name) and barn.func.id == "_":
                anropar = True
            elif isinstance(barn, ast.Assign) and _binds_underscore(barn.targets[0]):
                binder = binder or barn.lineno
            elif isinstance(barn, (ast.For, ast.comprehension)):
                mål = getattr(barn, "target", None)
                if mål is not None and _binds_underscore(mål):
                    binder = binder or getattr(barn, "lineno", 0)
        if anropar and binder:
            ut.append((binder, nod.name))
    return ut


def main() -> int:
    rot = pathlib.Path(__file__).resolve().parent.parent
    fynd = []
    filer = sorted(list((rot / "core").glob("*.py")) + list((rot / "ui").glob("*.py")))
    for fil in filer:
        for rad, namn in shadowing_scopes(fil):
            fynd.append(f"{fil.relative_to(rot)}:{rad} i {namn}()")
    if fynd:
        print("SKUGGAD: `_` binds i en metod som använder i18n-funktionen:")
        for rad in fynd:
            print("  ✗", rad)
        return 1
    print(f"rent: ingen av {len(filer)} moduler binder `_` och anropar den samtidigt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
