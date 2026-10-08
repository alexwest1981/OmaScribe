"""tools/i18n_keys_check.py — varje `_("nyckel")` i koden skall finnas i båda språkfilerna.

En nyckel som saknas visar en rå nyckel i gränssnittet ("element_hook") i stället
för en etikett, och felet syns bara i den ena språkversionen om man råkar fylla i
den andra först. Vakten läser bokstavliga nycklar i core/ och ui/ och jämför med
sv.json och en.json; dynamiska nycklar (f"grid_sort_{key}") kan den inte se, och
deras familjer täcks av modulernas egna prov i stället.

Vakten jämför också **varje annan språkfil mot engelskan**: samma nycklar, samma
platshållare och minst lika många flertalsformer. En halvöversatt fil är en fil
som visar engelska mitt i en tysk meny — den skall inte gå att committa tyst.

    python tools/i18n_keys_check.py
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CALLS = {"_", "tr"}          # i18n-funktionen, under båda sina namn
P = re.compile(r"\{(\w+)\}")


def former(text: str) -> int:
    """Antal flertalsformer i en sträng (1 = ingen)."""
    return str(text).count("|") + 1


def compare_locale(fil: str, mall: dict) -> list[str]:
    """Vad som skiljer en språkfil från engelskan. Tom lista = komplett."""
    with open(fil, encoding="utf-8") as f:
        egna = json.load(f)
    namn = os.path.basename(fil)
    fel = []
    saknas = [k for k in mall if k not in egna]
    if saknas:
        fel.append(f"{namn}: {len(saknas)} nycklar saknas (t.ex. {saknas[:3]})")
    for k, värde in egna.items():
        if k not in mall:
            continue
        if set(P.findall(str(värde))) != set(P.findall(str(mall[k]))):
            fel.append(f"{namn}: {k} har platshållarna {sorted(set(P.findall(str(värde))))} "
                       f"mot {sorted(set(P.findall(str(mall[k]))))}")
        if former(värde) < former(mall[k]):
            fel.append(f"{namn}: {k} har {former(värde)} former mot {former(mall[k])}")
        if not str(värde).strip():
            fel.append(f"{namn}: {k} är tom")
    return fel


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

    # De övriga språken: varje fil mot engelskan.
    with open(os.path.join(ROOT, "locales", "en.json"), encoding="utf-8") as f:
        mall = json.load(f)
    språkfiler = sorted(namn for namn in os.listdir(os.path.join(ROOT, "locales"))
                        if namn.endswith(".json") and namn not in ("en.json", "sv.json"))
    språkfel: list[str] = []
    for namn in språkfiler:
        språkfel.extend(compare_locale(os.path.join(ROOT, "locales", namn), mall))
    if språkfiler:
        klara = sum(1 for namn in språkfiler
                    if not compare_locale(os.path.join(ROOT, "locales", namn), mall))
        print(f"i18n: {klara} av {len(språkfiler)} övriga språk kompletta "
              f"({', '.join(n[:-5] for n in språkfiler)})")
    for fel in språkfel[:12]:
        print(f"  ✗ {fel}")

    return 1 if any(saknas.values()) or språkfel else 0


if __name__ == "__main__":
    raise SystemExit(main())
