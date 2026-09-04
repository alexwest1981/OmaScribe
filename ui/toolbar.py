from PyQt6.QtWidgets import (
    QToolBar, QComboBox, QColorDialog, QWidget,
    QHBoxLayout, QLabel, QMenu, QToolButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QAction, QIcon, QFont, QTextCharFormat, QTextBlockFormat,
    QTextListFormat, QTextCursor, QColor
)
from core.i18n import _, i18n
from core.font_manager import FontSelectorComboBox

class FormattingToolBar(QToolBar):
    magic_ai_clicked = pyqtSignal()
    dictation_clicked = pyqtSignal()
    sidebar_toggled = pyqtSignal()

    def __init__(self, editor_view, parent=None):
        super().__init__(parent)
        self.editor = editor_view
        self.setMovable(False)
        self.setFloatable(False)

        self.init_actions()
        self.retranslate_ui()
        i18n.language_changed.connect(self.retranslate_ui)
        self.editor.canvas.cursor_format_changed.connect(self.sync_toolbar_state)

    def init_actions(self):
        # 1. Heading / Paragraph style
        self.combo_heading = QComboBox()
        self.combo_heading.addItem("Normal Text", 0)
        self.combo_heading.addItem("Heading 1", 1)
        self.combo_heading.addItem("Heading 2", 2)
        self.combo_heading.addItem("Heading 3", 3)
        self.combo_heading.addItem("Blockquote", 4)
        self.combo_heading.currentIndexChanged.connect(self._on_heading_changed)
        self.addWidget(self.combo_heading)

        self.addSeparator()

        # 2. Font Family with Curated Popular Fonts & Typography Previews
        self.combo_font = FontSelectorComboBox()
        self.combo_font.font_selected.connect(self._on_font_changed)
        self.addWidget(self.combo_font)

        # 3. Font Size
        self.combo_size = QComboBox()
        for sz in [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72]:
            self.combo_size.addItem(str(sz), sz)
        self.combo_size.setCurrentText("12")
        self.combo_size.currentTextChanged.connect(self._on_size_changed)
        self.addWidget(self.combo_size)

        self.addSeparator()

        # 4. Bold, Italic, Underline, Strikethrough
        self.act_bold = QAction("𝐁", self)
        self.act_bold.setCheckable(True)
        self.act_bold.triggered.connect(self._toggle_bold)
        self.addAction(self.act_bold)

        self.act_italic = QAction("𝐼", self)
        self.act_italic.setCheckable(True)
        self.act_italic.triggered.connect(self._toggle_italic)
        self.addAction(self.act_italic)

        self.act_underline = QAction("U̲", self)
        self.act_underline.setCheckable(True)
        self.act_underline.triggered.connect(self._toggle_underline)
        self.addAction(self.act_underline)

        self.act_strike = QAction("S̶", self)
        self.act_strike.setCheckable(True)
        self.act_strike.triggered.connect(self._toggle_strike)
        self.addAction(self.act_strike)

        self.addSeparator()

        # 5. Text color & Highlight color
        self.act_color = QAction("🎨 Color", self)
        self.act_color.triggered.connect(self._pick_text_color)
        self.addAction(self.act_color)

        self.act_highlight = QAction("🖍️ Highlight", self)
        self.act_highlight.triggered.connect(self._pick_highlight_color)
        self.addAction(self.act_highlight)

        self.addSeparator()

        # 6. Alignment
        self.act_align_left = QAction("⇤", self)
        self.act_align_left.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignLeft))
        self.addAction(self.act_align_left)

        self.act_align_center = QAction("≡", self)
        self.act_align_center.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignHCenter))
        self.addAction(self.act_align_center)

        self.act_align_right = QAction("⇥", self)
        self.act_align_right.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignRight))
        self.addAction(self.act_align_right)

        self.act_align_justify = QAction("⇹", self)
        self.act_align_justify.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignJustify))
        self.addAction(self.act_align_justify)

        self.addSeparator()

        # 7. Lists
        self.act_bullet_list = QAction("• List", self)
        self.act_bullet_list.triggered.connect(lambda: self._create_list(QTextListFormat.Style.ListDisc))
        self.addAction(self.act_bullet_list)

        self.act_num_list = QAction("1. List", self)
        self.act_num_list.triggered.connect(lambda: self._create_list(QTextListFormat.Style.ListDecimal))
        self.addAction(self.act_num_list)

        # Expanding spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        # 8. Magic AI, Dictation & Inspector Toggle
        self.act_magic = QAction("✨ " + _("tb_magic_ai"), self)
        self.act_magic.triggered.connect(self.magic_ai_clicked.emit)
        self.addAction(self.act_magic)

        self.act_dictate = QAction("🎙️ " + _("tb_dictation"), self)
        self.act_dictate.triggered.connect(self.dictation_clicked.emit)
        self.addAction(self.act_dictate)

        self.act_sidebar = QAction("📑 " + _("tb_sidebar_toggle"), self)
        self.act_sidebar.triggered.connect(self.sidebar_toggled.emit)
        self.addAction(self.act_sidebar)

    def retranslate_ui(self):
        self.combo_heading.setItemText(0, _("tb_heading_normal"))
        self.combo_heading.setItemText(1, _("tb_heading_1"))
        self.combo_heading.setItemText(2, _("tb_heading_2"))
        self.combo_heading.setItemText(3, _("tb_heading_3"))
        self.combo_heading.setItemText(4, _("tb_heading_quote"))
        
        self.act_bold.setToolTip(_("tb_bold"))
        self.act_italic.setToolTip(_("tb_italic"))
        self.act_underline.setToolTip(_("tb_underline"))
        self.act_strike.setToolTip(_("tb_strikethrough"))
        self.act_color.setToolTip(_("tb_text_color"))
        self.act_highlight.setToolTip(_("tb_highlight_color"))
        
        self.act_align_left.setToolTip(_("tb_align_left"))
        self.act_align_center.setToolTip(_("tb_align_center"))
        self.act_align_right.setToolTip(_("tb_align_right"))
        self.act_align_justify.setToolTip(_("tb_align_justify"))
        
        self.act_magic.setText("✨ " + _("tb_magic_ai"))
        self.act_dictate.setText("🎙️ " + _("tb_dictation"))
        self.act_sidebar.setText("📑 " + _("tb_sidebar_toggle"))

    def sync_toolbar_state(self):
        cursor = self.editor.textCursor()
        fmt = cursor.charFormat()

        self.act_bold.setChecked(fmt.fontWeight() == QFont.Weight.Bold.value)
        self.act_italic.setChecked(fmt.fontItalic())
        self.act_underline.setChecked(fmt.fontUnderline())
        self.act_strike.setChecked(fmt.fontStrikeOut())

        self.combo_font.select_font_family(fmt.fontFamily())

        if fmt.fontPointSize() > 0:
            self.combo_size.blockSignals(True)
            self.combo_size.setCurrentText(str(int(fmt.fontPointSize())))
            self.combo_size.blockSignals(False)

        # Block heading sync
        block_fmt = cursor.blockFormat()
        level = block_fmt.headingLevel()
        self.combo_heading.blockSignals(True)
        self.combo_heading.setCurrentIndex(level if level in {1, 2, 3} else 0)
        self.combo_heading.blockSignals(False)

    def _toggle_bold(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        is_bold = cursor.charFormat().fontWeight() == QFont.Weight.Bold.value
        fmt.setFontWeight(QFont.Weight.Normal.value if is_bold else QFont.Weight.Bold.value)
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

    def _toggle_italic(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not cursor.charFormat().fontItalic())
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

    def _toggle_underline(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not cursor.charFormat().fontUnderline())
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

    def _toggle_strike(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(not cursor.charFormat().fontStrikeOut())
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

    def _on_font_changed(self, font):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

    def _on_size_changed(self, size_str):
        try:
            sz = float(size_str)
            cursor = self.editor.textCursor()
            fmt = QTextCharFormat()
            fmt.setFontPointSize(sz)
            cursor.mergeCharFormat(fmt)
            self.editor.setTextCursor(cursor)
        except ValueError:
            pass

    def _on_heading_changed(self, idx):
        cursor = self.editor.textCursor()
        block_fmt = QTextBlockFormat()
        char_fmt = QTextCharFormat()

        if idx == 1:
            block_fmt.setHeadingLevel(1)
            char_fmt.setFontPointSize(22)
            char_fmt.setFontWeight(QFont.Weight.Bold.value)
        elif idx == 2:
            block_fmt.setHeadingLevel(2)
            char_fmt.setFontPointSize(18)
            char_fmt.setFontWeight(QFont.Weight.Bold.value)
        elif idx == 3:
            block_fmt.setHeadingLevel(3)
            char_fmt.setFontPointSize(15)
            char_fmt.setFontWeight(QFont.Weight.Bold.value)
        elif idx == 4: # Blockquote
            block_fmt.setLeftMargin(24)
            char_fmt.setFontItalic(True)
        else: # Normal
            block_fmt.setHeadingLevel(0)
            block_fmt.setLeftMargin(0)
            char_fmt.setFontPointSize(12)
            char_fmt.setFontWeight(QFont.Weight.Normal.value)
            char_fmt.setFontItalic(False)

        cursor.mergeBlockFormat(block_fmt)
        cursor.mergeCharFormat(char_fmt)
        self.editor.setTextCursor(cursor)

    def _set_alignment(self, align_flag):
        cursor = self.editor.textCursor()
        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(align_flag)
        cursor.mergeBlockFormat(block_fmt)
        self.editor.setTextCursor(cursor)

    def _pick_text_color(self):
        col = QColorDialog.getColor(Qt.GlobalColor.black, self, _("tb_text_color"))
        if col.isValid():
            cursor = self.editor.textCursor()
            fmt = QTextCharFormat()
            fmt.setForeground(col)
            cursor.mergeCharFormat(fmt)
            self.editor.setTextCursor(cursor)

    def _pick_highlight_color(self):
        col = QColorDialog.getColor(QColor("#fff59d"), self, _("tb_highlight_color"))
        if col.isValid():
            cursor = self.editor.textCursor()
            fmt = QTextCharFormat()
            fmt.setBackground(col)
            cursor.mergeCharFormat(fmt)
            self.editor.setTextCursor(cursor)

    def _create_list(self, style):
        cursor = self.editor.textCursor()
        cursor.createList(style)
        self.editor.setTextCursor(cursor)
