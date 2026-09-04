from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QScrollArea, QFrame, QMenu, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import (
    QTextDocument, QTextCursor, QTextCharFormat, QTextBlockFormat,
    QFont, QColor, QPainter, QAction, QKeySequence, QPalette
)
from core.i18n import _

class DocumentCanvas(QTextEdit):
    cursor_format_changed = pyqtSignal()
    magic_ai_requested = pyqtSignal(str, QPoint) # (selected_text, global_pos)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Document page settings
        doc = self.document()
        doc.setDocumentMargin(36) # ~25mm page padding
        
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
        super().keyPressEvent(event)

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
        self.page_frame.setFixedWidth(820)
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
