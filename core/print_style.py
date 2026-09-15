"""core/print_style.py — papperets färger, och rening av dokument inför export.

Principen: programmets tema får färga *applikationen*, aldrig *dokumentet*.
Papper är vitt, brödtext är svart, linjer och tabeller är grå. Allt som
lämnar programmet — PDF, DOCX, HTML, utskrift — går genom
`normalize_document()` på en klon, så att färg som ändå hamnat i dokumentet
(temafärgade kodblock, inklistrad färgad text, importerad DOCX, markerad
text) blir akromatiskt utan att originalet rörs.

Reningen är luminansbaserad, inte en tvätt: mörk text blir svart, ljus text
(designad för mörk bakgrund) blir svart i stället för osynlig, mörka
bakgrunder blir ljusgrå i stället för att sluka texten, och kulörta toner
tappar sin kroma men behåller sin ljushet så att hierarkin syns kvar.
"""

import os
import re
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QTextDocument, QTextCursor, QTextCharFormat, QTextBlockFormat, QColor,
    QBrush, QTextTable, QTextImageFormat, QTextFormat, QTextFrameFormat,
)

# ------------------------------------------------------------------ pappret
PAPER_WHITE = "#ffffff"
PAPER_TEXT = "#000000"
PAPER_MUTED = "#333333"        # dämpad text (citat, bildtext, metauppgifter)
PAPER_RULE = "#999999"         # tabellramar, avdelare, sidhuvudslinje
PAPER_TINT = "#f2f2f2"         # kodblock, tabellrubrik, informationsruta
PAPER_TINT_STRONG = "#e6e6e6"

# Nycklar som matchar temats färgordbok, så att anropande kod kan byta ut
# temafärger mot pappersfärger utan att känna till skillnaden.
PAPER_COLORS = {
    "text_color": PAPER_TEXT,
    "text_muted": PAPER_MUTED,
    "code_bg": PAPER_TINT,
    "code_text": PAPER_TEXT,
    "sidebar_card": PAPER_TINT,
    "canvas_bg": PAPER_WHITE,
    "canvas_border": PAPER_RULE,
    "table_border": PAPER_RULE,
    "table_header_bg": PAPER_TINT,
    "rule": PAPER_RULE,
}


def paper_colors(overrides: dict | None = None) -> dict:
    """Pappersfärgerna, med valfria explicita undantag."""
    colors = dict(PAPER_COLORS)
    if overrides:
        colors.update(overrides)
    return colors


def paper_palette():
    """Paletten som hör till papperet.

    Text som saknar egen färg ritas av Qt med den palett som följer med i
    ``QAbstractTextDocumentLayout.PaintContext``. Lämnar man den tom blir
    sådan text vit — osynlig på vitt papper — så utskriften måste skicka med
    papperets palett, inte skärmens.
    """
    from PyQt6.QtGui import QPalette

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Base, QColor(PAPER_WHITE))
    pal.setColor(QPalette.ColorRole.Window, QColor(PAPER_WHITE))
    pal.setColor(QPalette.ColorRole.Text, QColor(PAPER_TEXT))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(PAPER_TEXT))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(PAPER_TINT_STRONG))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(PAPER_TEXT))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(PAPER_WHITE))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(PAPER_TEXT))
    return pal


# ------------------------------------------------------------------ färgverktyg

def _rgb(value) -> tuple[int, int, int]:
    if isinstance(value, (tuple, list)) and len(value) >= 3:
        return int(value[0]), int(value[1]), int(value[2])
    if isinstance(value, QColor):
        return value.red(), value.green(), value.blue()
    c = QColor(value)
    if not c.isValid():
        return (0, 0, 0)
    return c.red(), c.green(), c.blue()


def luminance(rgb) -> float:
    """Upplevd ljushet 0..1 (Rec. 709), oberoende av kulör."""
    r, g, b = _rgb(rgb)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def chroma(rgb) -> int:
    r, g, b = _rgb(rgb)
    return max(r, g, b) - min(r, g, b)


def is_achromatic(rgb, tolerance: int = 2) -> bool:
    return chroma(rgb) <= tolerance


def gray_hex(rgb, level: float | None = None) -> str:
    """Akromatisk motsvarighet. `level` sätter ljusheten (0..1) i stället."""
    value = int(round(255 * level)) if level is not None else int(round(255 * luminance(rgb)))
    value = max(0, min(255, value))
    return f"#{value:02x}{value:02x}{value:02x}"


def clean_foreground(rgb) -> str:
    """Textfärg på papper: svart, med dämpad grå för text som ska vara dämpad.

    Ljus text (skriven för en mörk bakgrund) blir svart — annars skulle den
    försvinna på vitt papper.
    """
    if not QColor(rgb).isValid():
        return PAPER_TEXT
    level = luminance(rgb)
    if level > 0.55:
        return PAPER_TEXT
    if is_achromatic(rgb) and 0.18 <= level <= 0.55:
        return gray_hex(rgb)      # behåll "dämpad" utan kulör
    return PAPER_TEXT


def clean_background(rgb) -> str:
    """Bakgrund på papper: vit om den var ljus, ljusgrå om den var mörk."""
    if not QColor(rgb).isValid():
        return PAPER_WHITE
    level = luminance(rgb)
    if level >= 0.985:
        return PAPER_WHITE
    if level < 0.5:
        return PAPER_TINT        # mörk bakgrund designad för skärm
    # Ljus, kulört ton (markering, tabellhuvud) → neutral ljusgrå, men
    # behåll skillnaden mellan svag och tydlig ton.
    return gray_hex(rgb, 0.90 if level > 0.9 else 0.85)


def clean_border(rgb) -> str:
    """Ram/linje: behåll ljusheten, ta bort kulören, håll den synlig."""
    if not QColor(rgb).isValid():
        return PAPER_RULE
    level = luminance(rgb)
    if level > 0.95:
        return "#d9d9d9"
    if level < 0.25:
        return PAPER_TEXT
    return gray_hex(rgb)


# ------------------------------------------------------------------ rening

def _clean_brush(brush: QBrush, fixer) -> QBrush | None:
    if brush.style() == Qt.BrushStyle.NoBrush:
        return None
    col = brush.color()
    if not col.isValid() or col.alpha() == 0:
        return None
    fixed = fixer(col)
    if fixed == col.name():
        return None
    return QBrush(QColor(fixed))


def _clean_char_format(fmt: QTextCharFormat, force_black: bool = True) -> QTextCharFormat | None:
    """Kopia av formatet med enbart färgerna rena. None om inget ändras.

    ``force_black`` ger text som saknar egen färg en explicit svart färg. Utan
    den ritas texten med den palett som råkar gälla vid utskriften, och en
    mörk skärmpalett ger då vit text på vitt papper.
    """
    changed = False
    out = QTextCharFormat(fmt)

    fg_brush = fmt.foreground()
    if fg_brush.style() == Qt.BrushStyle.NoBrush or not fg_brush.color().isValid():
        if force_black and not fmt.isImageFormat():
            out.setForeground(QBrush(QColor(PAPER_TEXT)))
            changed = True
    else:
        fg = fg_brush.color()
        fixed = clean_foreground(fg)
        if fixed != fg.name():
            out.setForeground(QBrush(QColor(fixed)))
            changed = True

    bg_brush = fmt.background()
    if bg_brush.style() != Qt.BrushStyle.NoBrush and bg_brush.color().isValid():
        bg = bg_brush.color()
        if bg.alpha() > 0:
            fixed = clean_background(bg)
            if fixed != bg.name():
                out.setBackground(QBrush(QColor(fixed)))
                changed = True

    return out if changed else None


def _clean_block_format(fmt: QTextBlockFormat) -> QTextBlockFormat | None:
    """Blockformat: bara bakgrunden kan bära färg.

    Blockramar (CSS ``border-left`` i inklistrad HTML) lagras som interna
    egenskaper som PyQt-bindningen inte exponerar — de fångas i stället vid
    källan, där mallar och informationsrutor sätter neutrala gråa ramar.
    """
    bg = _clean_brush(fmt.background(), clean_background)
    if bg is None:
        return None
    out = QTextBlockFormat(fmt)
    out.setBackground(bg)
    return out


def _copy_as_same_kind(fmt: QTextFormat) -> QTextFormat:
    """Kopia som behåller sin sort.

    ``QTextFormat(fmt)`` ger ett *allmänt* QTextFormat, och då finns inte
    ``borderBrush``/``setBorderBrush`` kvar — de ligger på undervarianterna
    (QTextTableFormat, QTextFrameFormat, QTextTableCellFormat). Kopierar man
    i stället via ``to*Format()`` behåller kopian både egenskaperna och
    åtkomsten till dem.
    """
    if fmt.isTableFormat():
        return fmt.toTableFormat()
    if fmt.isTableCellFormat():
        return fmt.toTableCellFormat()
    if fmt.isFrameFormat():
        return fmt.toFrameFormat()
    if fmt.isBlockFormat():
        return fmt.toBlockFormat()
    return QTextFormat(fmt)


def _clean_frame_or_cell(fmt: QTextFormat) -> QTextFormat | None:
    """Ram- eller cellformat: bakgrund och alla rampenslar som finns."""
    changed = False
    out = _copy_as_same_kind(fmt)

    bg = _clean_brush(fmt.background(), clean_background)
    if bg is not None:
        out.setBackground(bg)
        changed = True

    border_getter = getattr(fmt, "borderBrush", None)
    border_setter = getattr(out, "setBorderBrush", None)
    if border_getter is not None and border_setter is not None:
        border = _clean_brush(border_getter(), clean_border)
        if border is not None:
            border_setter(border)
            changed = True

    # Celler har dessutom en pensel per sida
    for prefix in ("top", "bottom", "left", "right"):
        getter = getattr(fmt, f"{prefix}BorderBrush", None)
        setter = getattr(out, f"set{prefix.capitalize()}BorderBrush", None)
        if getter is None or setter is None:
            continue
        fixed = _clean_brush(getter(), clean_border)
        if fixed is not None:
            setter(fixed)
            changed = True

    return out if changed else None


def grayscale_image(img) -> object:
    """Gråskaleversion av en QImage (används när bilder ska tryckas neutralt)."""
    try:
        from PyQt6.QtGui import QImage
        if not isinstance(img, QImage):
            return img
        gray = img.convertToFormat(QImage.Format.Format_Grayscale8)
        return gray.convertToFormat(QImage.Format.Format_RGB32)
    except Exception:
        return img


# Diagram som programmet självt ritat märks med den här egenskapen. De är
# vår egen utdata, inte användarens innehåll, och neutraliseras därför alltid
# vid ren export — även om man valde en färgpalett på skärmen.
CHART_PROPERTY = QTextFormat.Property.UserProperty + 11


def mark_as_generated_chart(char_format: QTextCharFormat,
                            mono_name: str = "") -> QTextCharFormat:
    """Märker ett bildformat som ett diagram OmaScribe ritat.

    ``mono_name`` är resursnamnet för samma diagram ritat i gråskala. Finns
    den byter exporten bild i stället för att tona ned den färgade — två
    kulörer med samma ljushet blir annars samma grå, och diagrammets delar
    går inte längre att skilja åt.
    """
    char_format.setProperty(CHART_PROPERTY, mono_name or True)
    return char_format


def is_generated_chart(char_format: QTextCharFormat) -> bool:
    if char_format is None or not char_format.isImageFormat():
        return False
    value = char_format.property(CHART_PROPERTY)
    return bool(value) if value is not None else False


def chart_mono_name(char_format: QTextCharFormat) -> str:
    """Resursnamnet för diagrammets gråskaleversion, om det finns någon."""
    value = char_format.property(CHART_PROPERTY)
    return value if isinstance(value, str) else ""


def _image_names(doc: QTextDocument, only_charts: bool) -> set[str]:
    """Resursnamn för inbäddade bilder.

    ``only_charts=True`` ger de diagram som *saknar* gråskaleversion och
    därför måste tonas ned; ``False`` ger samtliga bilder i dokumentet.
    """
    names: set[str] = set()
    block = doc.begin()
    while block.isValid():
        it = block.begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid():
                cfmt = frag.charFormat()
                if cfmt.isImageFormat() and (not only_charts or (
                        is_generated_chart(cfmt) and not chart_mono_name(cfmt))):
                    fmt = cfmt.toImageFormat()
                    if fmt.isValid() and fmt.name():
                        names.add(fmt.name())
            it += 1
        block = block.next()
    return names


def _desaturate_resources(doc: QTextDocument, names: set[str]) -> int:
    from PyQt6.QtCore import QUrl
    from PyQt6.QtGui import QImage, QPixmap

    replaced = 0
    for name in names:
        res = doc.resource(QTextDocument.ResourceType.ImageResource, QUrl(name))
        # Qt kan lämna tillbaka antingen en QImage eller en QPixmap beroende på
        # hur bilden kom in i dokumentet (HTML-bild blir en QPixmap).
        img = None
        if isinstance(res, QImage):
            img = res
        elif isinstance(res, QPixmap):
            img = res.toImage()
        if img is None or img.isNull() or img.isGrayscale():
            continue
        doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(name),
                        grayscale_image(img))
        replaced += 1
    return replaced


def normalize_document(doc: QTextDocument, grayscale_images: bool = False,
                       neutralize_charts: bool = True) -> int:
    """Gör en klon av dokumentet tryckrent. Returnerar antalet ändrade format.

    Originalet rörs inte: anroparen skickar in en klon och skriver ut den.
    """
    if doc is None:
        return 0

    changes = 0
    cursor = QTextCursor(doc)
    cursor.beginEditBlock()
    try:
        block = doc.begin()
        while block.isValid():
            bfmt = _clean_block_format(block.blockFormat())
            if bfmt is not None:
                QTextCursor(block).mergeBlockFormat(bfmt)
                changes += 1

            # Blockets standardteckenformat styr vad som skrivs härnäst
            block_char = block.charFormat()
            cleaned = _clean_char_format(block_char)
            if cleaned is not None:
                QTextCursor(block).setBlockCharFormat(cleaned)
                changes += 1

            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid():
                    cfmt = frag.charFormat()
                    replacement = None
                    # Våra egna diagram: byt till gråskaleversionen om den finns
                    if cfmt.isImageFormat() and is_generated_chart(cfmt):
                        mono = chart_mono_name(cfmt)
                        if mono:
                            img_fmt = cfmt.toImageFormat()
                            img_fmt.setName(mono)
                            replacement = img_fmt
                    if replacement is None:
                        replacement = _clean_char_format(cfmt)
                    if replacement is not None:
                        fc = QTextCursor(doc)
                        fc.setPosition(frag.position())
                        fc.setPosition(frag.position() + frag.length(),
                                       QTextCursor.MoveMode.KeepAnchor)
                        fc.setCharFormat(replacement)
                        changes += 1
                it += 1
            block = block.next()

        # Tabeller: cellbakgrunder och ramar
        seen = set()
        block = doc.begin()
        while block.isValid():
            table = QTextCursor(block).currentTable()
            if table is not None and id(table) not in seen:
                seen.add(id(table))
                tfmt = _clean_frame_or_cell(table.format())
                if tfmt is not None:
                    table.setFormat(tfmt.toTableFormat())
                    changes += 1
                for row in range(table.rows()):
                    for col in range(table.columns()):
                        cell = table.cellAt(row, col)
                        cfmt = _clean_frame_or_cell(cell.format())
                        if cfmt is not None:
                            cell.setFormat(cfmt.toTableCellFormat())
                            changes += 1
            block = block.next()

        # Sidans rotram
        root = doc.rootFrame()
        if root is not None:
            rfmt = _clean_frame_or_cell(root.frameFormat())
            if rfmt is not None:
                root.setFrameFormat(rfmt.toFrameFormat())
                changes += 1
    finally:
        cursor.endEditBlock()

    # Bilder: våra egna diagram neutraliseras alltid, foton bara på begäran
    if neutralize_charts:
        changes += _desaturate_resources(doc, _image_names(doc, only_charts=True))
    if grayscale_images:
        changes += _desaturate_resources(doc, _image_names(doc, only_charts=False))
    return changes


_COLOR_ELEMENT_RE = re.compile(r"<w:color\b[^>]*>")
_COLOR_ATTR_RE = re.compile(r'w:(?:color|fill)="([0-9A-Fa-f]{6})"')
_THEME_ATTR_RE = re.compile(r'\sw:theme(?:Color|Tint|Shade|Fill|Pattern)="[^"]*"')


def _neutralize_xml(xml: str) -> tuple[str, int]:
    """Byter ut varje kulört färg i ett OOXML-dokument mot en neutral.

    Word-mallen vi skriver från bär på ett antal färdiga stilar (rubriker,
    länkar, citat) som pekar på temats blåa accenter. De används inte av
    innehållet, men de ligger i filen och kan plockas fram av den som öppnar
    dokumentet. Här blir de svarta, grå eller vita i stället.
    """
    changes = 0

    def fix_color_element(match: "re.Match[str]") -> str:
        nonlocal changes
        tag = match.group(0)
        out = _THEME_ATTR_RE.sub("", tag)          # temareferensen bort
        val = re.search(r'w:val="([0-9A-Fa-f]{6})"', out)
        if val:
            hexval = val.group(1)
            rgb = tuple(int(hexval[i:i + 2], 16) for i in (0, 2, 4))
            if chroma(rgb) > 2:
                out = out.replace(f'w:val="{hexval}"', f'w:val="{PAPER_TEXT.lstrip("#").upper()}"')
                changes += 1
        if out != tag:
            changes += 1
        return out

    xml = _COLOR_ELEMENT_RE.sub(fix_color_element, xml)

    def fix_attr(match: "re.Match[str]") -> str:
        nonlocal changes
        name = "w:fill" if match.group(0).startswith("w:fill") else "w:color"
        hexval = match.group(1)
        rgb = tuple(int(hexval[i:i + 2], 16) for i in (0, 2, 4))
        if chroma(rgb) <= 2:
            return match.group(0)
        changes += 1
        # Skuggning blir vit, ramar blir grå, text blir svart
        new = PAPER_WHITE if name == "w:fill" else PAPER_RULE
        return f'{name}="{new.lstrip("#").upper()}"'

    xml = _COLOR_ATTR_RE.sub(fix_attr, xml)
    xml = _THEME_ATTR_RE.sub("", xml)
    return xml, changes


def neutralize_docx(path) -> int:
    """Gör en .docx-fil fri från kulörer. Returnerar antalet ändringar.

    Körs efter att python-docx sparat filen: biblioteket når inte alla stilar
    (kopplade teckenstilar och tabellstilar ligger utanför ``doc.styles``),
    men filen är ett zip och XML:en går att städa direkt.
    """
    import zipfile

    src = Path(path)
    if not src.exists():
        return 0

    targets = ("word/document.xml", "word/styles.xml", "word/numbering.xml",
               "word/footer1.xml", "word/header1.xml", "word/footer2.xml", "word/header2.xml")
    changes = 0
    tmp = src.with_suffix(src.suffix + ".tmp")

    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename in targets:
                xml, n = _neutralize_xml(data.decode("utf-8"))
                changes += n
                data = xml.encode("utf-8")
            zout.writestr(item, data)

    os.replace(tmp, src)
    return changes


def clean_html(doc: QTextDocument) -> str:
    """HTML-export med garanterat vit bakgrund och svart text."""
    html = doc.toHtml()
    body_style = f"background-color: {PAPER_WHITE}; color: {PAPER_TEXT};"
    if "<body" in html:
        head, _, tail = html.partition("<body")
        if "style=" in tail.split(">", 1)[0]:
            before, _, after = tail.partition('style="')
            attr, quote, rest = after.partition('"')
            tail = f'{before}style="{body_style} {attr}"{quote}{rest}'
        else:
            tag_end = tail.find(">")
            tail = f' style="{body_style}"' + tail[tag_end:] if tag_end >= 0 else f' style="{body_style}">' + tail
        html = head + "<body" + tail
    else:
        html = (f'<body style="{body_style}">' + html + "</body>")
    return html
