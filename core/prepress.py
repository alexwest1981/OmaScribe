"""core/prepress.py — tryckförberedelse (5.16).

Två saker som skiljer ett manus från en tryckfärdig bok:

  * **Änkor och föräldralösa rader.** En änka är sista raden i ett stycke som
    hamnar ensam högst upp på nästa sida; en föräldralös rad är första raden som
    blir ensam kvar sist på sin. Båda mäts här mot samma sidmodell som
    förhandsvisningen ritar med — radens y i dokumentet delat med sidans höjd —
    så siffran i rapporten och sidan på skärmen säger samma sak.
  * **PDF/X-1a:2003 med CMYK.** Qt skriver en PDF, men inte en tryckfärdig:
    ingen OutputIntent, ingen CMYK-konvertering. Ghostscript gör den, och finns
    det på maskinen används det — är det inte installerat sägs det rakt ut i
    stället för att en halvfärdig fil blir liggande.

Ingenting här ändrar texten: rapporten säger vad som finns, och författaren
bestämmer. Att flytta rader automatiskt vore att skriva om någon annans bok.

    python -m core.prepress      kör självprovet
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile

# Marginalerna i QTextDocument räknas i punkter (1/72 tum) när sidan har en
# storlek; förhandsvisningen ritar i samma enheter.
WIDOW = "widow"
ORPHAN = "orphan"

KIND_NAMES = {WIDOW: "änka", ORPHAN: "föräldralös"}

GS_CANDIDATES = ("gs", "ghostscript")

# Ghostscript kräver en definitionsfil för PDF/X: den sätter OutputIntent med
# en ICC-profil, PDF/X-versionen och trimboxen. Utan den blir det en vanlig PDF.
PDFX_DEF_TEMPLATE = """%!
/ICCProfile ({icc}) def
/PDFXOutputIntent {icc} def
[{version} /CompatibilityLevel 1.4 /PDFXTrapped /False
  /Title ({title}) /Creator ({creator}) /DOCINFO pdfmark
"""


def _page_slot(page_settings: dict | None, sidhöjd: float) -> float:
    """Sidans texthöjd i dokumentenheter — samma tal som förhandsvisningen.

    Marginalerna i `page_settings` är i millimeter (de kommer från
    publiceringsfliken) och räknas om till punkter, för det är vad dokumentets
    koordinater står i.
    """
    cfg = page_settings or {}
    topp = float(cfg.get("margin_top_mm", 20) or 0) * 72.0 / 25.4
    botten = float(cfg.get("margin_bottom_mm", 20) or 0) * 72.0 / 25.4
    höjd = float(sidhöjd or cfg.get("page_height_pt", 842) or 842)
    return max(72.0, höjd - topp - botten)


def _line_tops(doc) -> list[tuple[int, list[float], str]]:
    """(blocknummer, varje rads y, blockets text) för varje stycke med rader."""
    layout = doc.documentLayout()
    ut: list[tuple[int, list[float], str]] = []
    block = doc.begin()
    nummer = 0
    while block.isValid():
        bl = block.layout()
        if bl is not None and bl.lineCount() > 0 and block.text().strip():
            topp = layout.blockBoundingRect(block).top()
            ys = [topp + bl.lineAt(i).y() for i in range(bl.lineCount())]
            ut.append((nummer, ys, block.text()))
        block = block.next()
        nummer += 1
    return ut


def widows_and_orphans(doc, page_settings: dict | None = None,
                       slot: float | None = None) -> list[dict]:
    """Rader som blir ensamma på fel sida av ett sidbrott.

    Ett stycke med en enda rad kan varken ha en änka eller en föräldralös rad —
    det är hela stycket som flyttas — och hoppas därför över.
    """
    if doc is None:
        return []
    mått = slot or _page_slot(page_settings, doc.pageSize().height())
    if mått <= 0:
        return []
    ut: list[dict] = []
    for nummer, ys, text in _line_tops(doc):
        if len(ys) < 2:
            continue
        sidor = [int(y // mått) for y in ys]
        if sidor[0] != sidor[1]:
            ut.append({"kind": ORPHAN, "block": nummer, "line": 0,
                       "text": text, "sidor": (sidor[0], sidor[1])})
        if sidor[-1] != sidor[-2]:
            ut.append({"kind": WIDOW, "block": nummer, "line": len(ys) - 1,
                       "text": text, "sidor": (sidor[-2], sidor[-1])})
    return ut


def policy_fixes(doc, page_settings: dict | None = None,
                 slot: float | None = None) -> int:
    """Håller ihop de stycken rapporten pekar ut, så ingen rad blir ensam.

    Verktyget Qt har för det är `setNonBreakableLines(True)`: styckets rader
    följs åt till nästa sida i stället för att en rad lämnas kvar. Det är samma
    sak som Words "Keep lines together". Formatering, inte text — en ångring tar
    tillbaka den.

    Priset är känt: ett stycke som inte får plats på en sida flyttas helt, och
    då kan föregående sida sluta med tomrum. Det är författarens val, därför är
    det en knapp och inte något som sker av sig självt.
    """
    from PyQt6.QtGui import QTextCursor

    fynd = widows_and_orphans(doc, page_settings, slot)
    if not fynd:
        return 0
    ändrade = 0
    for block in _blocks_by_number(doc, {f["block"] for f in fynd}):
        fmt = block.blockFormat()
        fmt.setNonBreakableLines(True)
        markor = QTextCursor(doc)
        markor.setPosition(block.position())
        markor.mergeBlockFormat(fmt)
        ändrade += 1
    return ändrade


def _blocks_by_number(doc, nummer: set[int]):
    block = doc.begin()
    i = 0
    while block.isValid():
        if i in nummer:
            yield block
        block = block.next()
        i += 1


# ------------------------------------------------------------------ PDF/X-1a

def gs_path() -> str | None:
    """Ghostscript, om det finns. Sökvägen cachas inte: ett paket kan installeras."""
    for namn in GS_CANDIDATES:
        funnen = shutil.which(namn)
        if funnen:
            return funnen
    return None


def available() -> bool:
    return gs_path() is not None


def _icc_profile() -> str | None:
    """En ICC-profil att deklarera som OutputIntent.

    Ghostscripts egen standardprofil räcker för PDF/X-1a (den är den som
    används när inget annat anges) och finns alltid där gs finns.
    """
    gs = gs_path()
    if not gs:
        return None
    rot = os.path.join(os.path.dirname(os.path.realpath(gs)), "..", "share", "ghostscript")
    for kandidat in ("iccprofiles/default_cmyk.icc", "iccprofiles/default_gray.icc"):
        sökväg = os.path.normpath(os.path.join(rot, kandidat))
        if os.path.exists(sökväg):
            return sökväg
    return None


def to_pdfx(source_pdf: str, out_pdf: str, *, title: str = "", creator: str = "OmaScribe",
            version: str = "/GTS_PDFXVersion (PDF/X-1a:2003)") -> str:
    """Konverterar en PDF till PDF/X-1a:2003 med CMYK och inbäddade teckensnitt.

    Kastar `RuntimeError` med skälet om Ghostscript saknas eller om körningen
    misslyckas — en halvfärdig fil skall inte ligga kvar som om den vore klar.
    """
    gs = gs_path()
    if not gs:
        raise RuntimeError("no_ghostscript")
    if not os.path.exists(source_pdf):
        raise RuntimeError("no_source")
    icc = _icc_profile()
    if not icc:
        raise RuntimeError("no_icc_profile")

    def _escape(text: str) -> str:
        return (str(text).replace("\\", "").replace("(", "").replace(")", "")
                .replace("\n", " "))[:200]

    arbetskatalog = tempfile.mkdtemp(prefix="pdfx-")
    try:
        def_fil = os.path.join(arbetskatalog, "PDFX_def.ps")
        with open(def_fil, "w", encoding="utf-8") as f:
            f.write(PDFX_DEF_TEMPLATE.format(icc=icc, version=version,
                                             title=_escape(title), creator=_escape(creator)))
        if os.path.exists(out_pdf):
            os.remove(out_pdf)
        resultat = subprocess.run(
            [gs, "-dBATCH", "-dNOPAUSE", "-dQUIET", "-dSAFER",
             f"-sOutputFile={out_pdf}", "-sDEVICE=pdfwrite",
             "-dPDFX", "-dProcessColorModel=/DeviceCMYK",
             "-dEmbedAllFonts=true", "-dSubsetFonts=true", "-dCompatibilityLevel=1.4",
             "-dAutoRotatePages=/None",
             f"-sColorConversionStrategy=CMYK",
             def_fil, source_pdf],
            capture_output=True, text=True, timeout=300)
        if resultat.returncode != 0 or not os.path.exists(out_pdf):
            raise RuntimeError("ghostscript_failed: " + (resultat.stderr or "").strip()[:300])
        return out_pdf
    finally:
        shutil.rmtree(arbetskatalog, ignore_errors=True)


def has_pdfx_marker(pdf_path: str) -> bool:
    """PDF/X-versionen står i filen. Det är beviset, inte gs:s utdata."""
    if not os.path.exists(pdf_path):
        return False
    with open(pdf_path, "rb") as f:
        data = f.read()
    return b"GTS_PDFXVersion" in data


def embedded_fonts(pdf_path: str) -> list[tuple[str, bool]]:
    """(teckensnitt, inbäddat) för varje teckensnitt i filen, via poppler.

    Ett tryckeri kräver att varje teckensnitt finns *i* filen; en PDF som bara
    hänvisar till ett systemteckensnitt är inte tryckfärdig. Utan `pdffonts`
    returneras en tom lista — kontrollen kan inte ljuga om den inte kan mäta.
    """
    pdffonts = shutil.which("pdffonts")
    if not pdffonts or not os.path.exists(pdf_path):
        return []
    resultat = subprocess.run([pdffonts, pdf_path], capture_output=True, text=True, timeout=120)
    ut: list[tuple[str, bool]] = []
    for rad in (resultat.stdout or "").splitlines()[2:]:
        delar = rad.split()
        if len(delar) < 4:
            continue
        namn = delar[0]
        # Kolumnerna är inte fasta: typen kan vara två ord ("CID TrueType"), så
        # inbäddningen är den *första* ja/nej-kolumnen efter namnet, inte den
        # fjärde token. En fast index sa "nej" om en inbäddad delmängd.
        inbäddat = False
        for bit in delar[2:]:
            if bit in ("yes", "no", "ja", "nej"):
                inbäddat = bit in ("yes", "ja")
                break
        ut.append((namn, inbäddat))
    return ut


def _self_check() -> int:
    """Mäter mot riktiga radpositioner, inte mot en gissning om dem."""
    import os as _os

    _os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtCore import QSizeF
    from PyQt6.QtGui import QTextCursor, QTextDocument, QTextOption
    from PyQt6.QtWidgets import QApplication

    # Dokumentets layout frågar teckensnittsdatabasen: utan en applikation
    # avbryter Qt processen i stället för att kasta ett fel.
    _app = QApplication.instance() or QApplication([])

    checks = 0
    failures = 0

    def kolla(ok, text):
        nonlocal checks, failures
        checks += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            failures += 1

    def prov(text: str, bredd: int = 260) -> QTextDocument:
        doc = QTextDocument()
        doc.setPageSize(QSizeF(bredd, 900))
        val = QTextOption()
        val.setWrapMode(QTextOption.WrapMode.WordWrap)
        doc.setDefaultTextOption(val)
        QTextCursor(doc).insertText(text)
        return doc

    stycke = ("Hon hade burit den i fickan hela dagen utan att veta om det och "
              "kvällsljuset låg kvar över taken när hon äntligen satte sig ner "
              "och vände nyckeln i handen och såg att den glänste.")
    doc = prov(stycke)
    rader = _line_tops(doc)
    kolla(len(rader) == 1 and len(rader[0][1]) >= 3,
          f"ett stycke blir flera rader på en smal sida ({len(rader[0][1])} rader)")
    ys = rader[0][1]

    kolla(widows_and_orphans(doc, slot=10_000) == [],
          "ett sidbrott efter texten ger inga ensamma rader")
    höjd = ys[-1] + 100
    kolla(widows_and_orphans(doc, slot=höjd) == [],
          "och en sida som rymmer hela stycket ger inga heller")

    # Ett brott precis mellan första och andra raden: rad 1 blir föräldralös.
    brott = (ys[0] + ys[1]) / 2.0
    fynd = widows_and_orphans(doc, slot=brott)
    arter = sorted(f["kind"] for f in fynd)
    kolla(ORPHAN in arter, f"ett brott efter första raden ger en föräldralös rad ({arter})")

    # Och ett brott mellan näst sista och sista raden: sista raden blir änka.
    brott2 = (ys[-2] + ys[-1]) / 2.0
    fynd2 = widows_and_orphans(doc, slot=brott2)
    arter2 = sorted(f["kind"] for f in fynd2)
    kolla(WIDOW in arter2, f"och ett brott före sista raden ger en änka ({arter2})")
    kolla(all(f["text"].startswith("Hon hade") for f in fynd2),
          "med styckets egen text i fyndet")

    korta = prov("En enda rad.")
    kolla(widows_and_orphans(korta, slot=40) == [],
          "en enradare kan inte bli ensam")
    kolla(_page_slot({"margin_top_mm": 25.4, "margin_bottom_mm": 25.4}, 842) == 842 - 144,
          "marginalerna räknas om från millimeter till dokumentets punkter")

    # Formateringen: de utpekade styckena hålls ihop.
    ändrade = policy_fixes(doc, slot=brott)
    kolla(ändrade >= 1, f"och de utpekade styckena hålls ihop ({ändrade})")
    kolla(doc.begin().blockFormat().nonBreakableLines() is True,
          "mätt i blockformatet, inte bara i returvärdet")

    # PDF/X: finns gs används det, annars sägs det.
    if available():
        kolla(gs_path() is not None, f"Ghostscript hittas ({gs_path()})")
        kolla(_icc_profile() is not None, f"och en ICC-profil att deklarera ({_icc_profile()})")
        from core import doc_manager

        arbete = tempfile.mkdtemp(prefix="pdfx-check-")
        try:
            källa = os.path.join(arbete, "bok.pdf")
            doc_manager.DocumentManager.save_file(källa, doc, {}, {"clean_print": True})
            kolla(os.path.exists(källa) and os.path.getsize(källa) > 0,
                  f"en vanlig PDF skrivs först ({os.path.getsize(källa)} byte)")
            kolla(not has_pdfx_marker(källa),
                  "och den är inte PDF/X — Qt skriver ingen OutputIntent")
            mål = os.path.join(arbete, "bok-pdfx.pdf")
            to_pdfx(källa, mål, title="Provboken")
            kolla(os.path.exists(mål) and os.path.getsize(mål) > 0,
                  f"efter Ghostscript finns en PDF/X-fil ({os.path.getsize(mål)} byte)")
            kolla(has_pdfx_marker(mål),
                  "och filen bär PDF/X-versionen, mätt i filen själv")
            teckensnitt = embedded_fonts(mål)
            kolla(teckensnitt != [] and all(inbäddat for _, inbäddat in teckensnitt),
                  f"med alla teckensnitt inbäddade ({teckensnitt})")
            try:
                to_pdfx(os.path.join(arbete, "finns-inte.pdf"), mål)
                kolla(False, "en källa som inte finns skall ge ett fel")
            except RuntimeError as fel:
                kolla("no_source" in str(fel), f"och en saknad källa ger ett tydligt fel ({fel})")
        finally:
            shutil.rmtree(arbete, ignore_errors=True)
    else:
        print("  ..  Ghostscript saknas — PDF/X-delen prövas inte här")

    print(f"prepress: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
