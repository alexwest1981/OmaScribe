"""Släpp boken: filerna i en mapp, med checksummor och en rapport (R05.10).

En utgivning är inte en fil, den är ett *paket*: EPUB:en, tryck-PDF:en och en
rapport som säger vad som ligger där, när det byggdes, och vad kanalen kommer att
klaga på. Utan checksummorna går det inte att svara på frågan "är det här samma
fil som jag skickade i går?" — och den frågan kommer alltid, först när något gått
fel.

Rapporten är medvetet tråkig: ren text, en rad per fil, inget man behöver ett
program för att läsa. Den ska gå att skicka till ett tryckeri.

Ren Python utan Qt — `python core/release.py` provar hela vägen.
"""

import hashlib
import json
import os
import shutil
from datetime import datetime


def sha256(path: str) -> str | None:
    """Filens SHA-256, eller None om den inte går att läsa."""
    try:
        sammanfattning = hashlib.sha256()
        with open(path, "rb") as fil:
            for bit in iter(lambda: fil.read(1 << 20), b""):
                sammanfattning.update(bit)
        return sammanfattning.hexdigest()
    except OSError:
        return None


def _storlek(path: str) -> str:
    try:
        byte = os.path.getsize(path)
    except OSError:
        return "?"
    if byte >= 1 << 20:
        return f"{byte / (1 << 20):.2f} MB"
    if byte >= 1 << 10:
        return f"{byte / (1 << 10):.1f} kB"
    return f"{byte} B"


def build_release(folder: str, files, metadata: dict | None = None,
                  warnings=None, when: datetime | None = None) -> dict:
    """Samlar filerna i `folder` och skriver en rapport. Returnerar rapporten.

    Filerna kopieras med sina egna namn; en fil som inte finns hoppas över och
    namnges i rapporten i stället för att tyst försvinna — en saknad fil är
    exakt vad rapporten är till för.
    """
    metadata = metadata or {}
    tid = when or datetime.now()
    os.makedirs(folder, exist_ok=True)

    poster = []
    saknade = []
    for källa in files:
        if not källa or not os.path.isfile(källa):
            saknade.append(os.path.basename(källa) if källa else "?")
            continue
        mål = os.path.join(folder, os.path.basename(källa))
        if os.path.abspath(källa) != os.path.abspath(mål):
            shutil.copy2(källa, mål)
        poster.append({
            "file": os.path.basename(mål),
            "bytes": os.path.getsize(mål),
            "sha256": sha256(mål),
        })

    rapport = {
        "book": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        "publisher": metadata.get("publisher", ""),
        "isbn": metadata.get("identifier", ""),
        "built": tid.strftime("%Y-%m-%d %H:%M"),
        "files": poster,
        "missing": saknade,
        "warnings": list(warnings or []),
    }
    with open(os.path.join(folder, "release.json"), "w", encoding="utf-8") as fil:
        json.dump(rapport, fil, ensure_ascii=False, indent=2)
    with open(os.path.join(folder, "RAPPORT.md"), "w", encoding="utf-8") as fil:
        fil.write(rapport_text(rapport))
    return rapport


def rapport_text(rapport: dict) -> str:
    """Rapporten som text — det tryckeriet kan läsas av vem som helst."""
    rader = [f"# {rapport.get('book') or 'Utan titel'}", ""]
    for etikett, nyckel in (("Författare", "author"), ("Förlag", "publisher"),
                            ("ISBN", "isbn"), ("Byggd", "built")):
        if rapport.get(nyckel):
            rader.append(f"{etikett}: {rapport[nyckel]}")
    rader += ["", "## Filer", ""]
    if rapport.get("files"):
        rader.append("| Fil | Storlek | SHA-256 |")
        rader.append("|---|---|---|")
        for post in rapport["files"]:
            rader.append(f"| {post['file']} | {_storlek_text(post['bytes'])} | `{post['sha256']}` |")
    else:
        rader.append("Inga filer.")
    if rapport.get("missing"):
        rader += ["", "## Saknas", ""]
        rader += [f"- {namn}" for namn in rapport["missing"]]
    if rapport.get("warnings"):
        rader += ["", "## Att kontrollera innan filen skickas", ""]
        rader += [f"- {text}" for text in rapport["warnings"]]
    return "\n".join(rader) + "\n"


def _storlek_text(byte: int) -> str:
    if byte >= 1 << 20:
        return f"{byte / (1 << 20):.2f} MB"
    if byte >= 1 << 10:
        return f"{byte / (1 << 10):.1f} kB"
    return f"{byte} B"


def _self_test() -> int:
    import tempfile
    grönt = 0

    def check(namn: str, fick, väntat) -> None:
        nonlocal grönt
        assert fick == väntat, f"{namn}: {fick!r} != {väntat!r}"
        grönt += 1

    källa = tempfile.mkdtemp(prefix="slapp-")
    epub = os.path.join(källa, "boken.epub")
    with open(epub, "wb") as fil:
        fil.write(b"PK\x03\x04 inte en riktig epub men en fil")
    mapp = os.path.join(tempfile.mkdtemp(prefix="slapp-ut-"), "slapp")

    rapport = build_release(
        mapp, [epub, os.path.join(källa, "saknas.pdf")],
        {"title": "Källaren", "author": "Alex", "identifier": "978-91-0"},
        ["Innermarginalen är 12,7 mm"], when=datetime(2026, 10, 8, 8, 30))

    check("filen kopierades", os.path.isfile(os.path.join(mapp, "boken.epub")), True)
    check("och fick sin checksumma", len(rapport["files"][0]["sha256"]), 64)
    check("checksumman är av innehållet",
          rapport["files"][0]["sha256"],
          hashlib.sha256(b"PK\x03\x04 inte en riktig epub men en fil").hexdigest())
    check("den saknade filen namnges", rapport["missing"], ["saknas.pdf"])
    check("och varningen följer med", rapport["warnings"], ["Innermarginalen är 12,7 mm"])
    check("rapporten skrivs som json",
          json.load(open(os.path.join(mapp, "release.json"), encoding="utf-8"))["book"], "Källaren")
    text = open(os.path.join(mapp, "RAPPORT.md"), encoding="utf-8").read()
    check("och som läsbar text", "# Källaren" in text and "Författare: Alex" in text, True)
    check("med filen och dess checksumma i",
          "boken.epub" in text and rapport["files"][0]["sha256"] in text, True)
    check("utan att ljuga om storleken", "B" in text, True)
    check("och en andra körning ger samma summa",
          build_release(mapp, [epub])["files"][0]["sha256"], rapport["files"][0]["sha256"])
    check("en fil som inte finns ger ingen post",
          len(build_release(mapp, ["/finns/inte.pdf"])["files"]), 0)
    check("och en tom körning ger en tom rapport",
          build_release(mapp, [])["files"], [])
    return grönt


if __name__ == "__main__":
    print(f"release: {_self_test()} kontroller gröna")
