import re
import math
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QScrollArea, QFrame, QMenu, QApplication,
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRectF, QPointF, QByteArray, QBuffer, QIODevice, QUrl
from PyQt6.QtGui import (
    QTextDocument, QTextCursor, QTextCharFormat, QTextBlockFormat,
    QTextTableFormat, QTextTableCellFormat, QTextFrameFormat, QTextLength,
    QFont, QColor, QPainter, QAction, QKeySequence, QPalette,
    QSyntaxHighlighter, QImage, QPixmap, QPen, QBrush, QTextFormat
)
from core.i18n import _
from core.vault import WIKILINK_RE, split_link_target, slugify
from core import directives, richtext
from core.doc_manager import DEFAULT_PAGE_SETTINGS


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

    # Sidhöjd i pixlar för A4-simulering vid visning
    PAGE_HEIGHT_PX = 1080

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Document page settings
        doc = self.document()
        doc.setDocumentMargin(36) # ~25mm page padding

        # Sidlayout och sidnummer
        self.page_settings = DEFAULT_PAGE_SETTINGS.copy()
        self.paged_view_enabled = True

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

    def set_page_settings(self, settings: dict):
        if settings:
            self.page_settings.update(settings)
            vp = self.viewport()
            if vp is not None:
                vp.update()

    def keyPressEvent(self, event):
        # Trigger inline Magic AI with Ctrl+K
        if event.key() == Qt.Key.Key_K and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            cursor = self.textCursor()
            selected = cursor.selectedText()
            rect = self.cursorRect()
            global_pos = self.mapToGlobal(rect.bottomLeft())
            self.magic_ai_requested.emit(selected, global_pos)
            event.accept()
            return

        # Infoga sidbrytning med Ctrl+Enter
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.insert_page_break()
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

    # ---------------------------------------------------------------- Drag & Drop / Urklipp
    def dragEnterEvent(self, e):
        if e is not None:
            mime = e.mimeData()
            if mime is not None and (mime.hasUrls() or mime.hasImage() or mime.hasText()):
                e.acceptProposedAction()
            else:
                super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e is not None:
            mime = e.mimeData()
            if mime is not None and (mime.hasUrls() or mime.hasImage() or mime.hasText()):
                e.acceptProposedAction()
            else:
                super().dragMoveEvent(e)

    def dropEvent(self, e):
        if e is None:
            return
        mime = e.mimeData()
        if mime is not None and mime.hasUrls():
            for url in mime.urls():
                fpath = url.toLocalFile()
                if fpath and fpath.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".bmp")):
                    self.insert_image(fpath)
                    e.acceptProposedAction()
                    return
        elif mime is not None and mime.hasImage():
            img = mime.imageData()
            if isinstance(img, QImage) and not img.isNull():
                self.insert_image(img)
                e.acceptProposedAction()
                return
        super().dropEvent(e)

    def insertFromMimeData(self, source):
        if source is None:
            return
        # 1. Klistra in bild från urklipp
        if source.hasImage():
            img = source.imageData()
            if isinstance(img, QImage) and not img.isNull():
                self.insert_image(img)
                return
            elif isinstance(img, QPixmap) and not img.isNull():
                self.insert_image(img.toImage())
                return

        # 2. Klistra in tabulär data (TSV från Excel, Google Sheets eller LibreOffice Calc)
        if source.hasText():
            text = source.text()
            if "\t" in text and "\n" in text:
                lines = [ln for ln in text.splitlines() if ln.strip()]
                if len(lines) >= 2 and all("\t" in ln for ln in lines[:min(3, len(lines))]):
                    if self._try_insert_tsv_table(lines):
                        return

        super().insertFromMimeData(source)

    def _try_insert_tsv_table(self, lines: list[str]) -> bool:
        """Konverterar inklistrad TSV-data till en formaterad tabell."""
        matrix = [line.split("\t") for line in lines]
        num_rows = len(matrix)
        num_cols = max(len(row) for row in matrix)
        if num_rows < 1 or num_cols < 1:
            return False

        cursor = self.textCursor()
        cursor.beginEditBlock()
        try:
            table_fmt = QTextTableFormat()
            table_fmt.setBorder(1)
            table_fmt.setBorderStyle(QTextFrameFormat.BorderStyle.BorderStyle_Solid)
            table_fmt.setBorderBrush(QBrush(QColor("#cbd5e1")))
            table_fmt.setCellPadding(8)
            table_fmt.setCellSpacing(0)
            table_fmt.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))

            table = cursor.insertTable(num_rows, num_cols, table_fmt)
            if table is None:
                return False
            
            # Header-styling på första raden
            header_fmt = QTextTableCellFormat()
            header_fmt.setBackground(QBrush(QColor("#f1f5f9")))

            for r, row in enumerate(matrix):
                for c, val in enumerate(row):
                    if c < num_cols:
                        cell = table.cellAt(r, c)
                        if cell is not None and cell.isValid():
                            if r == 0:
                                cell.setFormat(header_fmt)
                            cell_cursor = cell.firstCursorPosition()
                            cell_cursor.insertText(val.strip())
        finally:
            cursor.endEditBlock()
        self.setTextCursor(cursor)
        return True

    # ---------------------------------------------------------------- Infogning av media
    def insert_image(self, filepath_or_qimage, width_px: int = 480, align: str = "center", caption: str = ""):
        """Infogar en bild i dokumentet med angiven bredd, justering och bildtext."""
        if isinstance(filepath_or_qimage, str):
            qimg = QImage(filepath_or_qimage)
            if qimg.isNull():
                return
        elif isinstance(filepath_or_qimage, QImage):
            qimg = filepath_or_qimage
        elif isinstance(filepath_or_qimage, QPixmap):
            qimg = filepath_or_qimage.toImage()
        else:
            return

        disp_w = min(qimg.width(), width_px) if width_px else min(qimg.width(), 680)

        # Koda till base64 för direkt inbäddning i HTML och dokumentresurser
        ba = QByteArray()
        buff = QBuffer(ba)
        buff.open(QIODevice.OpenModeFlag.WriteOnly)
        qimg.save(buff, "PNG")
        b64_str = ba.toBase64().data().decode("utf-8")
        data_url = f"data:image/png;base64,{b64_str}"

        res_id = f"qrc:///images/{uuid.uuid4().hex[:12]}.png"
        doc = self.document()
        if doc is not None:
            doc.addResource(QTextDocument.ResourceType.ImageResource, QUrl(res_id), qimg)

        cursor = self.textCursor()
        cursor.beginEditBlock()
        try:
            caption_html = f'<br/><span style="font-size: 10pt; color: #64748b; font-style: italic;">{caption}</span>' if caption else ""
            html_chunk = f'<p style="text-align: {align}; margin: 14px 0;"><img src="{data_url}" width="{disp_w}" />{caption_html}</p><p></p>'
            cursor.insertHtml(html_chunk)
        finally:
            cursor.endEditBlock()
        self.setTextCursor(cursor)

    def insert_chart(self, qimage: QImage, align: str = "center"):
        """Infogar ett genererat diagram."""
        self.insert_image(qimage, width_px=680, align=align)

    def insert_page_break(self):
        """Infogar en visuell och utskriftsmässig sidbrytning."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        try:
            cursor.insertBlock()
            bfmt = QTextBlockFormat()
            bfmt.setPageBreakPolicy(QTextFormat.PageBreakFlag.PageBreak_AlwaysBefore)
            cursor.setBlockFormat(bfmt)
            cursor.insertHtml('<p style="page-break-before: always; margin-top: 16px;"><br/></p>')
        finally:
            cursor.endEditBlock()
        self.setTextCursor(cursor)

    # ---------------------------------------------------------------- Siduppdelning & Sidnummer
    def paintEvent(self, e):
        super().paintEvent(e)

        # Rita siduppdelning, sidbrytningslinjer och sidnummer i editorn
        if not self.paged_view_enabled:
            return

        doc = self.document()
        if doc is None:
            return
        doc_height = doc.size().height()
        page_h = self.PAGE_HEIGHT_PX
        page_count = max(1, int(math.ceil(doc_height / float(page_h))))

        vp = self.viewport()
        if vp is None:
            return
        viewport_w = vp.width()
        sb = self.verticalScrollBar()
        scroll_y = sb.value() if sb is not None else 0

        painter = QPainter(vp)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        try:
            for i in range(page_count):
                page_num = i + 1
                page_bottom_y = int((i + 1) * page_h - scroll_y)
                page_top_y = int(i * page_h - scroll_y)

                # 1. Rita sidfot med sidnummer
                if self.page_settings.get("page_numbering", True):
                    skip_first = bool(self.page_settings.get("skip_first_page", False)) and (i == 0)
                    if not skip_first:
                        fmt_type = self.page_settings.get("page_number_format", "page_of_total")
                        if fmt_type == "number":
                            page_str = str(page_num)
                        elif fmt_type == "hyphen":
                            page_str = f"— {page_num} —"
                        elif fmt_type == "slash":
                            page_str = f"{page_num} / {page_count}"
                        else:
                            page_str = _("pdf_page_n_of_total", n=page_num, total=page_count)

                        num_pos = str(self.page_settings.get("page_number_pos", "bottom-center"))
                        if num_pos in ("bottom-alternating", "top-alternating"):
                            is_right = (page_num % 2 == 1)
                            align = Qt.AlignmentFlag.AlignRight if is_right else Qt.AlignmentFlag.AlignLeft
                        elif "right" in num_pos:
                            align = Qt.AlignmentFlag.AlignRight
                        elif "left" in num_pos:
                            align = Qt.AlignmentFlag.AlignLeft
                        else:
                            align = Qt.AlignmentFlag.AlignHCenter

                        painter.setFont(QFont("sans-serif", 9))
                        painter.setPen(QColor("#94a3b8"))
                        
                        # Footer-yta
                        footer_rect = QRectF(24, page_bottom_y - 28, viewport_w - 48, 20)
                        painter.drawText(footer_rect, align | Qt.AlignmentFlag.AlignVCenter, page_str)

                # 2. Rita tydlig sidseparation mellan sidorna
                if i < page_count - 1:
                    # Skuggad separationslinje
                    pen_sep = QPen(QColor("#cbd5e1"), 1.0, Qt.PenStyle.DashLine)
                    painter.setPen(pen_sep)
                    painter.drawLine(18, page_bottom_y, viewport_w - 18, page_bottom_y)

                    # Bricka med sidmarkör i mitten
                    badge_text = f" Sida {page_num + 1} "
                    painter.setFont(QFont("sans-serif", 8, QFont.Weight.Bold))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(QColor("#f1f5f9")))
                    
                    bw = len(badge_text) * 7.5 + 16
                    bx = (viewport_w - bw) / 2.0
                    by = page_bottom_y - 9
                    painter.drawRoundedRect(QRectF(bx, by, bw, 18), 9, 9)

                    painter.setPen(QColor("#64748b"))
                    painter.drawText(QRectF(bx, by, bw, 18), Qt.AlignmentFlag.AlignCenter, badge_text)
        finally:
            painter.end()

    # ---------------------------------------------------------------- markeringar

    def set_block_colors(self, colors: dict):
        """Temafärger för kod- och citatblock."""
        self._colors = dict(colors or {})

    def format_directives(self) -> int:
        """Gör om [kodblock] och [citat] till riktiga block. Returnerar antalet."""
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
        self.page_frame.setMinimumWidth(360)
        self.page_frame.setMaximumWidth(840)
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

    def set_page_settings(self, settings: dict):
        self.canvas.set_page_settings(settings)

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
        self.canvas.style_links(
            c.get("link", c["accent"]),
            c.get("link_missing", "#d97706"),
        )
        self.canvas.set_block_colors(c)
