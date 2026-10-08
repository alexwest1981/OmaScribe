"""Omslagsarket: hela arket i kanalens mått, med ryggen utmärkt (R05.6).

Det som behövs för ett omslag är inte en bild utan ett *ark* i rätt storlek med
rätt ryggbredd — den enda siffran som ändras varje gång sidantalet eller pappret
gör det. Formgivningen gör författaren (eller en formgivare) i sitt program; det
här är arket den läggs på: rätt mått, vikstrecken på rätt ställe, och bokens egna
uppgifter på plats så att inget behöver mätas för hand.

Geometrin är ren millimeter utan Qt (`cover_layout`) så att den går att prova;
bara ritandet behöver Qt.
"""

import os

from core.publishing import BLOED_MM, cover_mm, spine_mm, trim_mm

# Marginal från skärmens kant in till texten, och från vikstrecket till ryggtexten.
SAFE_MARGIN_MM = 6.35          # 0,25 tum, kanalernas vanliga säkerhetsmarginal
SPINE_TEXT_MIN_MM = 6.0        # under detta får ingen text plats på ryggen


def cover_layout(trim: str, pages: int, paper: str = "white", bleed: bool = True,
                 channel: str = "kdp") -> dict | None:
    """Arket i millimeter: baksida, rygg och framsida, plus säkerhetszoner.

    Returnerar None när kanalen eller formatet inte går att räkna på — samma
    besked som `cover_mm` ger, så att anroparen slipper två sorters fel.
    """
    mått = cover_mm(trim, pages, paper, bleed, channel)
    trim_mått = trim_mm(trim)
    rygg = spine_mm(pages, paper, channel)
    if mått is None or trim_mått is None or rygg is None:
        return None
    blöd = BLOED_MM if bleed else 0.0
    fram_bredd = trim_mått[0]
    höjd = mått[1]
    baksida = (blöd, blöd, fram_bredd, trim_mått[1])
    rygg_rect = (blöd + fram_bredd, blöd, rygg, trim_mått[1])
    framsida = (blöd + fram_bredd + rygg, blöd, fram_bredd, trim_mått[1])
    # Säkerhetszonerna: blöd + marginal in, och ryggtexten hålls innanför vikarna.
    säker = {
        "back": (baksida[0] + blöd + SAFE_MARGIN_MM, baksida[1] + blöd + SAFE_MARGIN_MM,
                 max(1.0, baksida[2] - 2 * (blöd + SAFE_MARGIN_MM)),
                 max(1.0, baksida[3] - 2 * (blöd + SAFE_MARGIN_MM))),
        "front": (framsida[0] + blöd + SAFE_MARGIN_MM, framsida[1] + blöd + SAFE_MARGIN_MM,
                  max(1.0, framsida[2] - 2 * (blöd + SAFE_MARGIN_MM)),
                  max(1.0, framsida[3] - 2 * (blöd + SAFE_MARGIN_MM))),
        "spine": (rygg_rect[0], rygg_rect[1], max(0.0, rygg - 2 * SAFE_MARGIN_MM), rygg_rect[3]),
    }
    return {
        "sheet": mått,                 # (bredd, höjd) för hela arket
        "bleed": blöd,
        "spine_mm": rygg,
        "trim": trim_mått,
        "channel": channel,
        "panels": {"back": baksida, "spine": rygg_rect, "front": framsida},
        "safe": säker,
        "spine_text": rygg >= SPINE_TEXT_MIN_MM,
    }


def draw_cover(path: str, layout: dict, title: str = "", author: str = "",
               blurb: str = "", language: str = "sv") -> dict:
    """Ritar arket som PDF. Tunt skal runt layouten — Qt gör jobbet."""
    from PyQt6.QtCore import QMarginsF, QRectF, QSizeF, Qt
    from PyQt6.QtGui import QColor, QFont, QPageSize, QPainter, QPdfWriter, QPen

    from core.i18n import _

    bredd, höjd = layout["sheet"]
    skrivare = QPdfWriter(path)
    skrivare.setResolution(300)
    skrivare.setPageSize(QPageSize(QSizeF(bredd, höjd), QPageSize.Unit.Millimeter))
    skrivare.setPageMargins(QMarginsF(0, 0, 0, 0))   # arket är hela arket
    dpi = skrivare.resolution()
    mm = dpi / 25.4

    def ruta(rect):
        return QRectF(rect[0] * mm, rect[1] * mm, rect[2] * mm, rect[3] * mm)

    målare = QPainter(skrivare)
    try:
        målare.fillRect(QRectF(0, 0, bredd * mm, höjd * mm), QColor("#ffffff"))

        # Vikstrecken: tunna, streckade linjer — de ska synas på arket men inte i tryck
        penna = QPen(QColor("#b9b9b9"), max(1, dpi // 300))
        penna.setStyle(Qt.PenStyle.DashLine)
        målare.setPen(penna)
        for x_mm in (layout["panels"]["spine"][0], layout["panels"]["front"][0]):
            målare.drawLine(int(x_mm * mm), 0, int(x_mm * mm), int(höjd * mm))

        # Baksidan: baksidestexten
        if blurb:
            målare.setPen(QColor("#333333"))
            typ = QFont("Serif")
            typ.setPointSizeF(10.5)
            målare.setFont(typ)
            målare.drawText(ruta(layout["safe"]["back"]),
                            int(Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap), blurb)

        # Ryggen: titel och författare, vridna — bara när ryggen är bred nog
        if layout["spine_text"] and (title or author):
            målare.save()
            mitt = ruta(layout["panels"]["spine"])
            målare.translate(mitt.center())
            målare.rotate(-90)
            typ = QFont("Serif")
            typ.setPointSizeF(8.5)
            målare.setFont(typ)
            målare.setPen(QColor("#333333"))
            text = f"{title}   ·   {author}" if author else title
            målare.drawText(QRectF(-mitt.height() / 2, -mitt.width() / 2,
                                   mitt.height(), mitt.width()),
                            int(Qt.AlignmentFlag.AlignCenter), text)
            målare.restore()

        # Framsidan: titeln och författaren, centrerade
        fram = ruta(layout["safe"]["front"])
        typ = QFont("Serif")
        typ.setPointSizeF(28)
        typ.setBold(True)
        målare.setFont(typ)
        målare.setPen(QColor("#111111"))
        målare.drawText(fram.adjusted(0, fram.height() * 0.18, 0, 0),
                        int(Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap), title)
        if author:
            typ2 = QFont("Serif")
            typ2.setPointSizeF(14)
            målare.setFont(typ2)
            målare.drawText(fram.adjusted(0, fram.height() * 0.55, 0, 0),
                            int(Qt.AlignmentFlag.AlignHCenter | Qt.TextFlag.TextWordWrap), author)

        # Nedre raden: vad arket är och vilka mått det har — det tryckeriet frågar efter
        typ3 = QFont("Sans Serif")
        typ3.setPointSizeF(6)
        målare.setFont(typ3)
        målare.setPen(QColor("#8a8a8a"))
        fot = _("cover_footer", width=f"{bredd:g}", height=f"{höjd:g}",
                spine=f"{layout['spine_mm']:g}", channel=layout["channel"])
        målare.drawText(QRectF(0, (höjd - 5) * mm, bredd * mm, 4 * mm),
                        int(Qt.AlignmentFlag.AlignHCenter), fot)
    finally:
        målare.end()
    return {"path": path, "sheet": layout["sheet"], "spine_mm": layout["spine_mm"],
            "bytes": os.path.getsize(path) if os.path.exists(path) else 0}


def _self_test() -> int:
    """Geometrin, utan Qt: den enda delen som går att räkna fel på."""
    grönt = 0

    def check(namn: str, fick, väntat) -> None:
        nonlocal grönt
        assert fick == väntat, f"{namn}: {fick!r} != {väntat!r}"
        grönt += 1

    # 6x9 tum, 300 sidor, vitt papper, med blöd: 3,2 + 152,4 + rygg + 152,4 + 3,2
    ritning = cover_layout("6x9", 300, "white", bleed=True)
    check("arket är baksida + rygg + framsida + blöd", ritning["sheet"],
          (round(2 * (3.2 + 152.4) + ritning["spine_mm"], 2), round(228.6 + 6.4, 2)))
    check("ryggen ligger mellan panelerna",
          round(ritning["panels"]["spine"][0], 2), round(3.2 + 152.4, 2))
    check("och framsidan börjar efter ryggen",
          round(ritning["panels"]["front"][0], 2),
          round(3.2 + 152.4 + ritning["spine_mm"], 2))
    check("panelernas höjd är tryckhöjden", ritning["panels"]["front"][3], 228.6)
    check("och säkerhetszonen håller sig innanför framsidan",
          ritning["safe"]["front"][0] > ritning["panels"]["front"][0], True)
    check("utan blöd krymper arket med 6,4 mm på varje led",
          round(cover_layout("6x9", 300, "white", bleed=False)["sheet"][0], 2),
          round(2 * 152.4 + cover_layout("6x9", 300, "white", bleed=False)["spine_mm"], 2))
    check("en tunn rygg får ingen text", cover_layout("6x9", 60)["spine_text"], False)
    check("och en tjock får det", cover_layout("6x9", 400)["spine_text"], True)
    check("okänt format ger None i stället för ett påhittat ark",
          cover_layout("finns-inte", 300), None)
    return grönt


if __name__ == "__main__":
    print(f"cover: {_self_test()} kontroller gröna")
