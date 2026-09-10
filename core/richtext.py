"""
core/richtext.py — blockroller: gör kod och citat till riktiga blocktyper.

Problemet med att markera kod enbart med ett teckensnitt är att ingenting
senare kan avgöra vad blocket var. Här får blocket en roll som egenskap på
själva blockformatet, vilket gör att:

  * Markdown-exporten kan skriva ut ```-staket med rätt språk
  * inläsning kan sätta tillbaka rollen, så en rundtur bevarar koden
  * AI-analysen kan plocka ut exakt de block som är kod

Rollerna ligger på QTextFormat.UserProperty, det villkoret Qt avsätter för
applikationer, så de krockar inte med Qts egna egenskaper.
"""

from PyQt6.QtGui import (
    QTextBlockFormat, QTextCharFormat, QTextFormat, QTextCursor, QTextDocument,
    QFont, QFontDatabase, QColor, QBrush,
)

ROLE_PROPERTY = QTextFormat.Property.UserProperty + 1
LANG_PROPERTY = QTextFormat.Property.UserProperty + 2

ROLE_CODE = "code"
ROLE_QUOTE = "quote"

# Teckensnitt i tur och ordning — första som finns på systemet vinner
MONO_PREFERENCES = ["JetBrains Mono", "Fira Code", "Cascadia Code", "Source Code Pro",
                    "IBM Plex Mono", "DejaVu Sans Mono", "Liberation Mono", "monospace"]

_mono_cache = None


def mono_family() -> str:
    """Första monospace-typsnittet som faktiskt finns installerat."""
    global _mono_cache
    if _mono_cache:
        return _mono_cache
    try:
        available = set(QFontDatabase.families())
    except Exception:
        available = set()
    for name in MONO_PREFERENCES:
        if name in available:
            _mono_cache = name
            return name
    _mono_cache = MONO_PREFERENCES[-1]
    return _mono_cache


# ------------------------------------------------------------------ roller

def set_role(block_format: QTextBlockFormat, role: str, lang: str = "") -> QTextBlockFormat:
    block_format.setProperty(ROLE_PROPERTY, role)
    if lang:
        block_format.setProperty(LANG_PROPERTY, lang)
    return block_format


def role_of(block_format: QTextBlockFormat) -> str:
    if block_format is None:
        return ""
    val = block_format.property(ROLE_PROPERTY)
    return str(val) if val else ""


def lang_of(block_format: QTextBlockFormat) -> str:
    if block_format is None:
        return ""
    val = block_format.property(LANG_PROPERTY)
    return str(val) if val else ""


def block_role(block) -> str:
    return role_of(block.blockFormat()) if block is not None and block.isValid() else ""


# ------------------------------------------------------------------ format

def code_block_format(colors: dict, lang: str = "") -> QTextBlockFormat:
    """Yttre formatering för ett kodblock."""
    fmt = QTextBlockFormat()
    fmt.setHeadingLevel(0)
    fmt.setLeftMargin(14)
    fmt.setRightMargin(8)
    fmt.setTopMargin(8)
    fmt.setBottomMargin(8)
    # Kod ska inte radbrytas — den ska kunna scrollas i sidled
    try:
        fmt.setNonBreakableLines(True)
    except Exception:
        pass
    bg = colors.get("code_bg") or colors.get("sidebar_card")
    if bg:
        fmt.setBackground(QBrush(QColor(bg)))
    set_role(fmt, ROLE_CODE, lang)
    return fmt


def code_char_format(colors: dict) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setFontFamily(mono_family())
    fmt.setFontFixedPitch(True)
    fmt.setFontPointSize(10.5)
    fmt.setFontItalic(False)
    fmt.setFontWeight(QFont.Weight.Normal.value)
    fg = colors.get("code_text") or colors.get("text_color")
    if fg:
        fmt.setForeground(QColor(fg))
    return fmt


def quote_block_format(colors: dict) -> QTextBlockFormat:
    fmt = QTextBlockFormat()
    fmt.setHeadingLevel(0)
    fmt.setLeftMargin(26)
    fmt.setTopMargin(4)
    fmt.setBottomMargin(4)
    set_role(fmt, ROLE_QUOTE)
    return fmt


def quote_char_format(colors: dict) -> QTextCharFormat:
    fmt = QTextCharFormat()
    fmt.setFontItalic(True)
    muted = colors.get("text_muted")
    if muted:
        fmt.setForeground(QColor(muted))
    return fmt


# ------------------------------------------------------------------ tillämpning

def _block_range(cursor: QTextCursor):
    """(första blocknummer, sista blocknummer) för markören eller markeringen."""
    doc = cursor.document()
    start, end = cursor.selectionStart(), cursor.selectionEnd()
    c = QTextCursor(doc)
    c.setPosition(start)
    first = c.blockNumber()
    c.setPosition(end)
    last = c.blockNumber()
    return first, last


def _expanded_range(cursor: QTextCursor):
    """Som _block_range, men håller ihop ett sammanhängande block.

    Står markören utan markering mitt i ett kodblock och man väljer "Normal"
    är avsikten att göra sig av med hela blocket — inte att klyva det på
    mitten och lämna resten som kod. Ett kodblock över flera rader är flera
    QTextBlock, så raden måste vidgas till hela följden.
    """
    doc = cursor.document()
    first, last = _block_range(cursor)
    if cursor.hasSelection() or doc is None:
        return first, last

    role = block_role(doc.findBlockByNumber(first))
    if not role:
        return first, last

    while first > 0 and block_role(doc.findBlockByNumber(first - 1)) == role:
        first -= 1
    count = doc.blockCount()
    while last < count - 1 and block_role(doc.findBlockByNumber(last + 1)) == role:
        last += 1
    return first, last


def _formats_for(role: str, colors: dict, lang: str = ""):
    """(blockformat, teckenformat) för en roll."""
    if role == ROLE_CODE:
        bfmt = code_block_format(colors, lang)
        cfmt = code_char_format(colors)
    elif role == ROLE_QUOTE:
        bfmt = quote_block_format(colors)
        cfmt = quote_char_format(colors)
    else:  # rensa rollen och återställ vanligt stycke
        bfmt = QTextBlockFormat()
        bfmt.setHeadingLevel(0)
        bfmt.setLeftMargin(0)
        bfmt.setTopMargin(0)
        bfmt.setBottomMargin(0)
        try:
            bfmt.setNonBreakableLines(False)
        except Exception:
            pass
        set_role(bfmt, "")
        cfmt = QTextCharFormat()
        cfmt.setFontItalic(False)
        cfmt.setFontFixedPitch(False)
        cfmt.setFontWeight(QFont.Weight.Normal.value)
    return bfmt, cfmt


def _apply_formats(document, first: int, last: int, bfmt, cfmt):
    """Lägger formaten på blocken first..last i en enda redigeringspost."""
    cursor = QTextCursor(document)
    cursor.beginEditBlock()
    try:
        block = document.findBlockByNumber(first)
        while block.isValid() and block.blockNumber() <= last:
            bc = QTextCursor(block)
            bc.mergeBlockFormat(bfmt)
            # Tomma block har ingen text att sätta teckenformat på, men
            # blockets standardteckenformat styr vad som skrivs härnäst.
            bc.setBlockCharFormat(cfmt)
            if block.length() > 1:
                bc.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                bc.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                                QTextCursor.MoveMode.KeepAnchor)
                bc.mergeCharFormat(cfmt)
            block = block.next()
    finally:
        cursor.endEditBlock()


def apply_role(cursor: QTextCursor, role: str, colors: dict, lang: str = ""):
    """Ger varje block i markeringen (eller aktuellt block) en roll.

    Ett block utan markering vidgas till hela det sammanhängande blocket, så
    att "Normal" mitt i ett kodblock tar bort hela. Sker i en enda
    redigeringspost, så att ett enda Ctrl+Z ångrar omformateringen.
    """
    doc = cursor.document()
    if doc is None:
        return
    first, last = _expanded_range(cursor)
    bfmt, cfmt = _formats_for(role, colors, lang)
    _apply_formats(doc, first, last, bfmt, cfmt)


def apply_role_to_blocks(document, first: int, last: int, role: str,
                         colors: dict, lang: str = ""):
    """Sätter rollen på ett exakt blockintervall.

    Till skillnad från apply_role vidgas intervallet inte, och tomma block
    hanteras rätt: deras markering blir noll tecken bred, och Qt ser då ingen
    markering alls — vilket får apply_role att vidga och råka tömma grannblocket.
    """
    if document is None or last < first:
        return
    bfmt, cfmt = _formats_for(role, colors, lang)
    _apply_formats(document, first, last, bfmt, cfmt)


def apply_role_and_restore(cursor: QTextCursor, role: str, colors: dict, lang: str = ""):
    """Som apply_role, men sätter tillbaka markören där den var."""
    pos = cursor.position()
    sel_anchor = cursor.anchor()
    apply_role(cursor, role, colors, lang)
    c = QTextCursor(cursor.document())
    c.setPosition(sel_anchor)
    c.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
    return c


# ------------------------------------------------------------------ utläsning

def code_blocks(document: QTextDocument) -> list:
    """Alla kodblock, med intilliggande rader sammanslagna till ett block.

    Ett kodblock över flera rader är flera QTextBlock i Qt, så de måste
    fogas samman för att AI:n ska få koden som en sammanhängande enhet.
    """
    out = []
    current = None
    block = document.begin()
    while block.isValid():
        if block_role(block) == ROLE_CODE:
            if current is None:
                current = {
                    "first_block": block.blockNumber(),
                    "last_block": block.blockNumber(),
                    "lang": lang_of(block.blockFormat()),
                    "lines": [],
                }
            current["last_block"] = block.blockNumber()
            if not current["lang"]:
                current["lang"] = lang_of(block.blockFormat())
            current["lines"].append(block.text())
        elif current is not None:
            out.append(current)
            current = None
        block = block.next()
    if current is not None:
        out.append(current)

    for c in out:
        c["code"] = "\n".join(c["lines"])
    return out


def blocks_with_role(document: QTextDocument, role: str) -> list:
    out, block = [], document.begin()
    while block.isValid():
        if block_role(block) == role:
            out.append(block.blockNumber())
        block = block.next()
    return out


def cursor_for_blocks(document: QTextDocument, first: int, last: int) -> QTextCursor:
    """Markör som omfattar blocken first..last."""
    c = QTextCursor(document)
    b1 = document.findBlockByNumber(first)
    b2 = document.findBlockByNumber(last)
    if not b1.isValid() or not b2.isValid():
        return c
    c.setPosition(b1.position())
    c.setPosition(b2.position() + b2.length() - 1, QTextCursor.MoveMode.KeepAnchor)
    return c


def replace_blocks(document: QTextDocument, first: int, last: int,
                   new_text: str, colors: dict, lang: str = "") -> QTextCursor:
    """Byter ut blocken mot ny text och ger den kodrollen igen."""
    c = cursor_for_blocks(document, first, last)
    start = c.selectionStart()
    c.beginEditBlock()
    try:
        c.removeSelectedText()
        c.insertText(new_text)
    finally:
        c.endEditBlock()
    # Markören står nu utan markering vid slutet av den infogade texten —
    # intervallet måste anges explicit för att hela koden ska få rollen
    sel = QTextCursor(document)
    sel.setPosition(start)
    sel.setPosition(start + len(new_text), QTextCursor.MoveMode.KeepAnchor)
    apply_role(sel, ROLE_CODE, colors, lang)
    return sel
