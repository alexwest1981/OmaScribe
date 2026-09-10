import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QScrollArea, QFrame, QMenu, QApplication,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import (
    QTextDocument, QTextCursor, QTextCharFormat, QTextBlockFormat,
    QFont, QColor, QPainter, QAction, QKeySequence, QPalette,
    QSyntaxHighlighter
)
from core.i18n import _
from core.vault import WIKILINK_RE, split_link_target, slugify
from core import directives, richtext

class WikiLinkHighlighter(QSyntaxHighlighter):
    """Färgar [[wikilänkar]] så att de syns som länkar och inte som vanlig text.

    Länkar vars mål finns i valvet får temats accentfärg. Länkar till något
    som ännu inte finns får varningston och streckad understrykning — samma
    signal som Obsidian ger. Highlightern ritar bara ovanpå dokumentet och
    rör inte texten, så sparning och export påverkas inte.
    """

    def __init__(self, document):
        super().__init__(document)
        self.known = set()
        self.color_resolved = QColor("#2d7ff9")
        self.color_missing = QColor("#d97706")
        self._build_formats()

    def set_known_targets(self, titles):
        """Vilka länkmål som faktiskt har en anteckning."""
        self.known = {slugify(t) for t in (titles or []) if t}
        self.rehighlight()

    def set_colors(self, resolved, missing):
        self.color_resolved = QColor(resolved)
        self.color_missing = QColor(missing)
        self._build_formats()
        self.rehighlight()

    def _build_formats(self):
        self.fmt_ok = QTextCharFormat()
        self.fmt_ok.setForeground(self.color_resolved)
        self.fmt_ok.setFontUnderline(True)
        self.fmt_ok.setUnderlineColor(self.color_resolved)

        self.fmt_missing = QTextCharFormat()
        self.fmt_missing.setForeground(self.color_missing)
        self.fmt_missing.setFontUnderline(True)
        self.fmt_missing.setUnderlineStyle(QTextCharFormat.UnderlineStyle.DashUnderline)
        self.fmt_missing.setUnderlineColor(self.color_missing)

    def highlightBlock(self, text):
        for m in WIKILINK_RE.finditer(text):
            target, _heading, _alias = split_link_target(m.group(1))
            fmt = self.fmt_ok if slugify(target) in self.known else self.fmt_missing
            self.setFormat(m.start(), m.end() - m.start(), fmt)


class DocumentCanvas(QTextEdit):
    cursor_format_changed = pyqtSignal()
    magic_ai_requested = pyqtSignal(str, QPoint) # (selected_text, global_pos)
    wikilink_activated = pyqtSignal(str)         # [[mål]] följt med Ctrl+klick
    directives_converted = pyqtSignal(int)       # antal [kodblock]/[citat] som blev block

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Document page settings
        doc = self.document()
        doc.setDocumentMargin(36) # ~25mm page padding

        # Wikilänkar: färgning av länkar + förslag när man skriver [[
        self.highlighter = WikiLinkHighlighter(self.document())
        self._link_titles = []
        self._colors = {}          # temafärger för kod- och citatblock
        self._completer_start = 0
        self.completer = QListWidget(self)
        self.completer.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.completer.setVisible(False)
        self.completer.itemClicked.connect(lambda item: self._insert_link(item.text()))
        self.verticalScrollBar().valueChanged.connect(self._hide_completer)

        # Cursor change listener to update toolbar
        self.cursorPositionChanged.connect(self._on_cursor_changed)

    def _on_cursor_changed(self):
        self.cursor_format_changed.emit()

    def keyPressEvent(self, event):
        # Trigger inline Magic AI with Ctrl+K
        if event.key() == Qt.Key.Key_K and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            cursor = self.textCursor()
            selected = cursor.selectedText()
            # Calculate global popup point near cursor
            rect = self.cursorRect()
            global_pos = self.mapToGlobal(rect.bottomLeft())
            self.magic_ai_requested.emit(selected, global_pos)
            event.accept()
            return

        # Wikilänk-förslag: navigering med piltangenter, val med Enter/Tab
        if self.completer.isVisible():
            if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                row = self.completer.currentRow()
                row += 1 if event.key() == Qt.Key.Key_Down else -1
                self.completer.setCurrentRow(max(0, min(row, self.completer.count() - 1)))
                event.accept()
                return
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                item = self.completer.currentItem()
                if item is not None:
                    self._insert_link(item.text())
                    event.accept()
                    return
            if event.key() == Qt.Key.Key_Escape:
                self._hide_completer()
                event.accept()
                return

        super().keyPressEvent(event)
        self._maybe_show_completer()
        # Stängs en markering med ] ska den bli ett riktigt block direkt
        if event.text() == "]":
            self._maybe_convert_directive()

    # ---------------------------------------------------------------- markeringar

    def set_block_colors(self, colors: dict):
        """Temafärger för kod- och citatblock."""
        self._colors = dict(colors or {})

    def format_directives(self) -> int:
        """Gör om [kodblock] och [citat] till riktiga block. Returnerar antalet.

        Baklänges, så att tidigare teckenpositioner förblir giltiga när
        texter byts ut.
        """
        found = directives.parse(self.toPlainText())
        if not found:
            return 0
        converted = 0
        for d in sorted(found, key=lambda x: -x.start_offset):
            if self._convert_directive(d):
                converted += 1
        if converted:
            self.directives_converted.emit(converted)
        return converted

    def _convert_directive(self, d) -> bool:
        """Byter ut en markering mot sitt innehåll och ger det rätt roll."""
        doc = self.document()
        last = doc.characterCount() - 1

        sel = QTextCursor(doc)
        sel.setPosition(min(d.start_offset, last))
        sel.setPosition(min(d.end_offset, last), QTextCursor.MoveMode.KeepAnchor)
        sel.beginEditBlock()
        try:
            sel.removeSelectedText()
            sel.insertText(d.body)
        finally:
            sel.endEditBlock()

        role = richtext.ROLE_CODE if d.kind == "code" else richtext.ROLE_QUOTE
        lang = d.lang
        if role == richtext.ROLE_CODE and not lang:
            lang = directives.detect_language(d.body)

        end = min(d.start_offset + len(d.body), doc.characterCount() - 1)
        sel2 = QTextCursor(doc)
        sel2.setPosition(min(d.start_offset, end))
        sel2.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        richtext.apply_role(sel2, role, self._colors, lang)
        return True

    def _maybe_convert_directive(self):
        """Konverterar den markering som just avslutades vid markören."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            return
        pos = cursor.position()
        for d in directives.parse(self.toPlainText()):
            if d.end_offset != pos:
                continue
            if self._convert_directive(d):
                end = min(d.start_offset + len(d.body),
                          self.document().characterCount() - 1)
                c = QTextCursor(self.document())
                c.setPosition(end)
                self.setTextCursor(c)
            return

    # ---------------------------------------------------------------- wikilänkar

    def set_link_titles(self, titles):
        """Anteckningstitlar som förslås när man skriver [[."""
        self._link_titles = sorted(set(t or "" for t in (titles or []) if t), key=str.lower)
        self.highlighter.set_known_targets(self._link_titles)

    def style_links(self, resolved, missing):
        """Sätter länkfärgerna utifrån aktivt tema."""
        self.highlighter.set_colors(resolved, missing)

    def _hide_completer(self):
        if self.completer.isVisible():
            self.completer.hide()

    def _link_query(self):
        """(söktext, start i blocket) om markören står inuti ett oavslutat [[."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            return None
        block_text = cursor.block().text()
        before = block_text[:cursor.positionInBlock()]
        start = before.rfind("[[")
        if start < 0:
            return None
        between = before[start + 2:]
        if "]]" in between:
            return None
        return between, start

    def _maybe_show_completer(self):
        info = self._link_query()
        if info is None or not self._link_titles:
            self._hide_completer()
            return

        query, start = info
        self._completer_start = start
        q = query.strip().lower()
        matches = [t for t in self._link_titles if q in t.lower()] if q else list(self._link_titles)
        matches = matches[:40]
        if not matches:
            self._hide_completer()
            return

        self.completer.clear()
        for t in matches:
            self.completer.addItem(QListWidgetItem(t))

        row = 0
        for i, t in enumerate(matches):
            if t.lower().startswith(q):
                row = i
                break
        self.completer.setCurrentRow(row)

        rect = self.cursorRect()
        width = max(200, min(340, max(200, self.width() - rect.left() - 24)))
        self.completer.setFixedWidth(width)
        self.completer.setFixedHeight(min(180, 22 * len(matches) + 6))
        self.completer.move(rect.left(), rect.bottom() + 2)
        self.completer.show()
        self.completer.raise_()

    def _insert_link(self, title):
        """Ersätter den påbörjade [[söktexten med en färdig länk."""
        cursor = self.textCursor()
        # Läs av vad som följer INNAN ankaret flyttas — position() pekar annars
        # på selektionsstarten och vi tappar bort ett befintligt ]].
        original_pos = cursor.position()
        n = max(0, cursor.positionInBlock() - (self._completer_start + 2))
        if n > 0:
            cursor.setPosition(original_pos - n, QTextCursor.MoveMode.KeepAnchor)

        after = self.toPlainText()[original_pos:original_pos + 2]
        closing = "" if after.startswith("]]") else "]]"
        cursor.insertText(f"{title}{closing}")
        self.setTextCursor(cursor)
        self._hide_completer()

    def _link_at(self, pos):
        """Länkmålet om positionen ligger inuti en [[länk]], annars None."""
        cursor = self.cursorForPosition(pos)
        in_block = cursor.positionInBlock()
        for m in WIKILINK_RE.finditer(cursor.block().text()):
            if m.start() <= in_block <= m.end():
                target, _heading, _alias = split_link_target(m.group(1))
                return target or None
        return None

    def mousePressEvent(self, event):
        # Ctrl+klick följer en wikilänk, som i Obsidian
        if (event.button() == Qt.MouseButton.LeftButton
                and (event.modifiers() & Qt.KeyboardModifier.ControlModifier)):
            target = self._link_at(event.position().toPoint())
            if target:
                self.wikilink_activated.emit(target)
                event.accept()
                return
        self._hide_completer()
        super().mousePressEvent(event)

    def style_completer(self, c):
        """Temastyling för förslagslistan."""
        self.completer.setStyleSheet(f"""
            QListWidget {{
                background-color: {c['bg']};
                color: {c['fg']};
                border: 1px solid {c['border']};
                border-radius: 4px;
                font-size: 12px;
                outline: none;
            }}
            QListWidget::item {{ padding: 3px 8px; }}
            QListWidget::item:selected {{
                background-color: {c['accent']};
                color: #ffffff;
            }}
        """)

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        
        cursor = self.textCursor()
        selected = cursor.selectedText()
        table = cursor.currentTable()

        if table:
            tbl_menu = menu.addMenu("📊 " + _("tb_table"))
            cell = table.cellAt(cursor)
            
            def add_row_above():
                c = self.textCursor()
                t = c.currentTable()
                if t: t.insertRows(t.cellAt(c).row(), 1)

            def add_row_below():
                c = self.textCursor()
                t = c.currentTable()
                if t: t.insertRows(t.cellAt(c).row() + 1, 1)

            def add_col_left():
                c = self.textCursor()
                t = c.currentTable()
                if t: t.insertColumns(t.cellAt(c).column(), 1)

            def add_col_right():
                c = self.textCursor()
                t = c.currentTable()
                if t: t.insertColumns(t.cellAt(c).column() + 1, 1)

            def del_row():
                c = self.textCursor()
                t = c.currentTable()
                if t: t.removeRows(t.cellAt(c).row(), 1)

            def del_col():
                c = self.textCursor()
                t = c.currentTable()
                if t: t.removeColumns(t.cellAt(c).column(), 1)

            def del_table():
                c = self.textCursor()
                t = c.currentTable()
                if t:
                    c.setPosition(t.firstPosition())
                    c.setPosition(t.lastPosition(), QTextCursor.MoveMode.KeepAnchor)
                    c.removeSelectedText()

            tbl_menu.addAction("⬆️ " + _("tb_table_insert_rows_above"), add_row_above)
            tbl_menu.addAction("⬇️ " + _("tb_table_insert_rows_below"), add_row_below)
            tbl_menu.addAction("⬅️ " + _("tb_table_insert_cols_left"), add_col_left)
            tbl_menu.addAction("➡️ " + _("tb_table_insert_cols_right"), add_col_right)
            tbl_menu.addSeparator()
            tbl_menu.addAction("🗑️ " + _("tb_table_delete_row"), del_row)
            tbl_menu.addAction("🗑️ " + _("tb_table_delete_col"), del_col)
            tbl_menu.addAction("⚠️ " + _("tb_table_delete_table"), del_table)
            menu.addSeparator()

        ai_act = menu.addAction("✨ " + _("inline_ai_title") + " (Ctrl+K)")
        ai_act.triggered.connect(lambda: self.magic_ai_requested.emit(selected, event.globalPos()))

        menu.exec(event.globalPos())


class EditorView(QWidget):
    def __init__(self, theme_mgr, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Centered Paper Page Container
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Page Container (Simulating A4 paper)
        self.page_frame = QFrame()
        self.page_frame.setObjectName("PageFrame")
        # A4-bredd som önskemål, inte som tvång. Med fixed width klipptes
        # högerkanten av dokumentet på smala fönster — exemplet som avslöjade
        # det var ett kodblock vars rader blev oläsbara.
        self.page_frame.setMinimumWidth(360)
        self.page_frame.setMaximumWidth(820)
        self.page_frame.setMinimumHeight(1160)

        page_layout = QVBoxLayout(self.page_frame)
        page_layout.setContentsMargins(12, 16, 12, 16)

        self.canvas = DocumentCanvas(self.page_frame)
        page_layout.addWidget(self.canvas)

        self.scroll_area.setWidget(self.page_frame)
        layout.addWidget(self.scroll_area)

        self.apply_theme()
        self.theme_mgr.theme_changed.connect(self.apply_theme)

    @property
    def document(self):
        return self.canvas.document()

    def textCursor(self):
        return self.canvas.textCursor()

    def setTextCursor(self, cursor):
        self.canvas.setTextCursor(cursor)

    def apply_theme(self):
        c = self.theme_mgr.current
        self.scroll_area.setStyleSheet(f"background-color: {c['window_bg']};")
        self.page_frame.setStyleSheet(f"""
            #PageFrame {{
                background-color: {c['canvas_bg']};
                border: 1px solid {c['canvas_border']};
                border-radius: 4px;
                margin-top: 20px;
                margin-bottom: 40px;
            }}
        """)
        self.canvas.setStyleSheet(f"""
            background-color: {c['canvas_bg']};
            color: {c['text_color']};
            selection-background-color: {c['accent']};
            selection-color: #ffffff;
            font-size: 13pt;
            line-height: 1.5;
        """)
        self.canvas.style_completer({
            "bg": c["sidebar_card"],
            "fg": c["text_color"],
            "border": c["canvas_border"],
            "accent": c["accent"],
        })
        # Wikilänkar ska synas. Temana har egna länkfärger eftersom accenten
        # kan ligga mycket nära brödtexten (amber: 6 av 765 i RGB-avstånd).
        self.canvas.style_links(
            c.get("link", c["accent"]),
            c.get("link_missing", "#d97706"),
        )
        self.canvas.set_block_colors(c)
