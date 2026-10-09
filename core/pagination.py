"""
core/pagination.py — delar ett dokument i ark, radbundet.

Sidorna ritas som separata ark (som i Word och LibreOffice), så texten måste
delas *mellan rader*: annars klipper arkets kant en rad mitt itu. Här räknas
var varje ark börjar, i dokumentets egna koordinater.

    starts = page_offsets(doc, content_h)      # [0, 984, 1965, ...]
    sida = bisect_right(starts, doc_y) - 1

Block utan rader (tabeller, bilder, tomma stycken) hålls ihop och flyttas
hela till nästa ark. `ponytail:` ett block som är högre än ett ark får ligga
kvar och skjuta över kanten — att dela en tabell mitt i kräver att man ritar om
dess rader, och det är sällan värt det; säg till om det dyker upp i praktiken.
"""

from bisect import bisect_right

from PyQt6.QtGui import QTextFormat

# "Håll ihop stycket": en egen blockegenskap, aldrig Qts setNonBreakableLines.
# Den flaggan stänger nämligen av **radbrytningen** också (mätt: en rad blev 1120 px
# i ett 646 px ark och gick utanför pappret), och Alex regel är att text alltid
# bryts vid ordet före kanten: "det får inte ens vara under diskussion". Här
# betyder märket i stället: hamnar en sidbrytning inne i stycket flyttas hela
# stycket till nästa ark — det Qt-flaggan var tänkt att göra, utan dess pris.
KEEP_TOGETHER = QTextFormat.Property.UserProperty


def mark_keep_together(block_fmt) -> None:
    """Märker ett blockformat som 'håll ihop'. Ingen radbrytning rörs."""
    block_fmt.setProperty(KEEP_TOGETHER, True)


def keeps_together(block) -> bool:
    """Är blocket märkt att hållas ihop över sidbrytningen?"""
    return bool(block.blockFormat().property(KEEP_TOGETHER))


def page_offsets(document, content_height: float) -> list:
    """Dokumentets y för första raden på varje ark. Ett ark för ett tomt dokument."""
    if content_height <= 0:
        return [0.0]

    layout = document.documentLayout()
    starts = [0.0]
    sida_topp = 0.0

    block = document.begin()
    while block.isValid():
        rect = layout.blockBoundingRect(block)
        textlayout = block.layout()
        rader = textlayout.lineCount() if textlayout is not None else 0
        håll_i = keeps_together(block)

        # En sidbrytning som användaren själv lagt in börjar ett nytt ark
        brytning = block.blockFormat().pageBreakPolicy()
        if brytning & QTextFormat.PageBreakFlag.PageBreak_AlwaysBefore and rect.top() > sida_topp:
            sida_topp = rect.top()
            starts.append(sida_topp)

        if rader == 0:
            # Tabell, bild eller tomt block: flyttas helt om det inte får plats
            if (rect.height() > 0 and rect.top() > sida_topp
                    and rect.top() + rect.height() > sida_topp + content_height):
                sida_topp = rect.top()
                starts.append(sida_topp)
        elif håll_i and rect.top() > sida_topp and rect.top() + rect.height() > sida_topp + content_height:
            # Märkt stycke som inte får plats: hela stycket börjar nästa ark.
            sida_topp = rect.top()
            starts.append(sida_topp)
        else:
            for i in range(rader):
                rad = textlayout.lineAt(i)
                topp = rect.top() + rad.y()
                if topp + rad.height() > sida_topp + content_height and topp > sida_topp:
                    sida_topp = topp
                    starts.append(sida_topp)
        block = block.next()

    return starts


def page_of_offset(starts: list, doc_y: float) -> int:
    """Vilket ark dokumentets y hör till (0-baserat)."""
    return max(0, bisect_right(starts, doc_y) - 1)


def _self_test() -> int:
    """Radbunden paginering mot ett riktigt dokument. 0 = allt grönt."""
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QTextDocument

    app = QApplication.instance() or QApplication([])   # noqa: F841
    fel = 0

    def kolla(ok, text):
        nonlocal fel
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            fel += 1

    doc = QTextDocument()
    doc.setDocumentMargin(38)
    doc.setHtml("".join(f"<p>Stycke {i}. " + "Ord och meningar som fyller en rad. " * 8 + "</p>"
                        for i in range(1, 40)))
    höjd = 400.0
    starts = page_offsets(doc, höjd)
    kolla(len(starts) >= 2, f"flera ark ({len(starts)} stycken)")
    kolla(starts[0] == 0.0, "första arket börjar på 0")

    # Ingen rad får korsa en arkgräns
    layout = doc.documentLayout()
    gränser = list(starts[1:])
    korsar = 0
    block = doc.begin()
    while block.isValid():
        rect = layout.blockBoundingRect(block)
        tl = block.layout()
        for i in range(tl.lineCount() if tl else 0):
            rad = tl.lineAt(i)
            topp = rect.top() + rad.y()
            if any(topp < g < topp + rad.height() for g in gränser):
                korsar += 1
        block = block.next()
    kolla(korsar == 0, f"ingen rad korsar en arkgräns ({korsar} korsande)")

    # Varje ark rymmer så mycket det kan utan att gå över höjden
    för_stort = [s for s in starts
                 if any(s < g < s + höjd for g in starts[1:])]
    kolla(not för_stort, f"arken ligger minst en sidhöjd isär ({len(för_stort)} för täta)")

    kolla(page_of_offset(starts, 0.0) == 0, "y=0 hör till första arket")
    kolla(page_of_offset(starts, starts[-1] + 10) == len(starts) - 1,
          "y efter sista gränsen hör till sista arket")

    # En tabell hålls ihop (block utan rader)
    tabell = QTextDocument()
    tabell.setDocumentMargin(38)
    tabell.setHtml("<p>Före</p>" +
                   "<table border=1 cellspacing=0 cellpadding=6>" +
                   "".join(f"<tr><td>Cell {r}</td><td>Rad {r}</td></tr>" for r in range(12)) +
                   "</table><p>Efter</p>")
    t_starts = page_offsets(tabell, 200.0)
    kolla(len(t_starts) >= 2, f"tabell-dokumentet delas ({len(t_starts)} ark)")
    kolla(all(b - a > 40 for a, b in zip(t_starts, t_starts[1:])),
          "och inga ark ligger orealistiskt tätt")

    # En sidbrytning användaren lagt in börjar ett nytt ark
    bruten = QTextDocument()
    bruten.setDocumentMargin(38)
    bruten.setHtml("<p>Ett</p><p>Tva</p>")
    from PyQt6.QtGui import QTextBlockFormat, QTextCursor
    bf = QTextBlockFormat()
    bf.setPageBreakPolicy(QTextFormat.PageBreakFlag.PageBreak_AlwaysBefore)
    mark = QTextCursor(bruten)
    mark.setPosition(bruten.findBlockByNumber(1).position())
    mark.setBlockFormat(bf)
    b_starts = page_offsets(bruten, 400.0)
    kolla(len(b_starts) == 2 and b_starts[1] > 0,
          f"en inlagd sidbrytning börjar ett nytt ark ({[round(x) for x in b_starts]})")

    tom = QTextDocument()
    kolla(page_offsets(tom, 400.0) == [0.0], "tomt dokument ger ett ark")
    kolla(page_offsets(doc, 0) == [0.0], "nollhöjd ger ett ark")

    return fel


if __name__ == "__main__":
    import sys
    sys.exit(1 if _self_test() else 0)
