"""tools/i18n_keys_check.py — varje `_(\"nyckel\")` i koden skall finnas i båda språkfilerna.

En nyckel som saknas visar en rå nyckel i gränssnittet ("element_hook") i stället
för en etikett, och felet syns bara i den ena språkversionen om man råkar fylla i
den andra först. Vakten läser bokstavliga nycklar i core/ och ui/ och jämför med
sv.json och en.json; dynamiska nycklar (f"grid_sort_{key}") kan den inte se, och
deras familjer täcks av modulernas egna prov i stället.

    python tools/i18n_keys_check.py
"""

from __future__ import annotations

import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALLS = {"_", "tr"}          # i18n-funktionen, under båda sina namn


def literal_keys(path: str) -> set[str]:
    """Bokstavliga nycklar i _("...")-anrop i en fil."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    keys = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        namn = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if namn not in CALLS:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            keys.add(arg.value)
    return keys


def main() -> int:
    locales = {}
    for lang in ("sv", "en"):
        with open(os.path.join(ROOT, "locales", f"{lang}.json"), encoding="utf-8") as f:
            locales[lang] = set(json.load(f))

    funna: set[str] = set()
    for mapp in ("core", "ui"):
        for fil in sorted(os.listdir(os.path.join(ROOT, mapp))):
            if fil.endswith(".py"):
                funna |= literal_keys(os.path.join(ROOT, mapp, fil))
    for fil in ("tools/ui_smoke.py", "tools/screenshots.py"):
        funna |= literal_keys(os.path.join(ROOT, fil))

    saknas = {lang: sorted(funna - keys) for lang, keys in locales.items()}
    osakta = sorted(set(locales["sv"]) - funna)
    print(f"i18n: {len(funna)} bokstavliga nycklar i koden, "
          f"{len(locales['sv'])} i sv.json, {len(locales['en'])} i en.json")
    for lang, borta in saknas.items():
        if borta:
            print(f"SAKNAS i {lang}.json: {borta[:12]}")
    # En nyckel som står i språkfilerna men inte i koden är oftast rester efter
    # en borttagen funktion — inte ett fel, men värt att se.
    print(f"oanvända i koden (kan vara dynamiska): {len(osakta)}")
    return 1 if any(saknas.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
