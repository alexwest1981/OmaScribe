import html
from PyQt6.QtWidgets import (
    QToolBar, QComboBox, QColorDialog, QWidget,
    QHBoxLayout, QLabel, QMenu, QToolButton, QSizePolicy,
    QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QAction, QIcon, QFont, QTextCharFormat, QTextBlockFormat,
    QTextListFormat, QTextCursor, QTextTableFormat, QTextTableCellFormat,
    QTextLength, QTextFrameFormat, QBrush, QColor
)
from core.i18n import _, i18n
from core.font_manager import FontSelectorComboBox
from ui.table_dialog import TableDialog

class FormattingToolBar(QToolBar):
    magic_ai_clicked = pyqtSignal()
    dictation_clicked = pyqtSignal()
    sidebar_toggled = pyqtSignal()
    google_fonts_clicked = pyqtSignal()

    def __init__(self, editor_view, theme_mgr=None, parent=None):
        super().__init__(parent)
        self.editor = editor_view
        self.theme_mgr = theme_mgr
        self.setMovable(False)
        self.setFloatable(False)

        self.init_actions()
        self.retranslate_ui()
        i18n.language_changed.connect(self.retranslate_ui)
        self.editor.canvas.cursor_format_changed.connect(self.sync_toolbar_state)

    def init_actions(self):
        # ---------------------------------------------------------------------
        # 1. Quick Style Ribbon (Paragraph & Heading Pill Buttons)
        # ---------------------------------------------------------------------
        self.style_group = QButtonGroup(self)
        self.style_group.setExclusive(True)

        self.btn_style_normal = QToolButton(self)
        self.btn_style_normal.setCheckable(True)
        self.btn_style_normal.setChecked(True)
        self.btn_style_normal.setProperty("stylePill", "true")
        self.btn_style_normal.clicked.connect(lambda: self._apply_heading_level(0))
        self.style_group.addButton(self.btn_style_normal, 0)
        self.addWidget(self.btn_style_normal)

        self.btn_style_h1 = QToolButton(self)
        self.btn_style_h1.setCheckable(True)
        self.btn_style_h1.setProperty("stylePill", "true")
        self.btn_style_h1.clicked.connect(lambda: self._apply_heading_level(1))
        self.style_group.addButton(self.btn_style_h1, 1)
        self.addWidget(self.btn_style_h1)

        self.btn_style_h2 = QToolButton(self)
        self.btn_style_h2.setCheckable(True)
        self.btn_style_h2.setProperty("stylePill", "true")
        self.btn_style_h2.clicked.connect(lambda: self._apply_heading_level(2))
        self.style_group.addButton(self.btn_style_h2, 2)
        self.addWidget(self.btn_style_h2)

        self.btn_style_h3 = QToolButton(self)
        self.btn_style_h3.setCheckable(True)
        self.btn_style_h3.setProperty("stylePill", "true")
        self.btn_style_h3.clicked.connect(lambda: self._apply_heading_level(3))
        self.style_group.addButton(self.btn_style_h3, 3)
        self.addWidget(self.btn_style_h3)

        self.btn_style_quote = QToolButton(self)
        self.btn_style_quote.setCheckable(True)
        self.btn_style_quote.setProperty("stylePill", "true")
        self.btn_style_quote.clicked.connect(lambda: self._apply_heading_level(4))
        self.style_group.addButton(self.btn_style_quote, 4)
        self.addWidget(self.btn_style_quote)

        self.btn_style_code = QToolButton(self)
        self.btn_style_code.setCheckable(True)
        self.btn_style_code.setProperty("stylePill", "true")
        self.btn_style_code.clicked.connect(lambda: self._apply_heading_level(5))
        self.style_group.addButton(self.btn_style_code, 5)
        self.addWidget(self.btn_style_code)

        self.addSeparator()

        # ---------------------------------------------------------------------
        # 2. Font Family & Google Fonts
        # ---------------------------------------------------------------------
        self.combo_font = FontSelectorComboBox()
        self.combo_font.font_selected.connect(self._on_font_changed)
        self.addWidget(self.combo_font)

        self.act_gfonts = QAction("🌐", self)
        self.act_gfonts.triggered.connect(self.google_fonts_clicked.emit)
        self.addAction(self.act_gfonts)

        # ---------------------------------------------------------------------
        # 3. Font Size
        # ---------------------------------------------------------------------
        self.combo_size = QComboBox()
        self.combo_size.setFixedWidth(68)
        self.combo_size.setMaxVisibleItems(12)
        if self.combo_size.view():
            self.combo_size.view().setMaximumHeight(320)
        for sz in [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72]:
            self.combo_size.addItem(str(sz), sz)
        self.combo_size.setCurrentText("12")
        self.combo_size.currentTextChanged.connect(self._on_size_changed)
        self.addWidget(self.combo_size)

        self.addSeparator()

        # ---------------------------------------------------------------------
        # 4. Inline Character Styles (B, I, U, S, Sub, Super, Clear)
        # ---------------------------------------------------------------------
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

        self.act_subscript = QAction("X₂", self)
        self.act_subscript.setCheckable(True)
        self.act_subscript.triggered.connect(self._toggle_subscript)
        self.addAction(self.act_subscript)

        self.act_superscript = QAction("X²", self)
        self.act_superscript.setCheckable(True)
        self.act_superscript.triggered.connect(self._toggle_superscript)
        self.addAction(self.act_superscript)

        self.act_color = QAction("🎨 Color", self)
        self.act_color.triggered.connect(self._pick_text_color)
        self.addAction(self.act_color)

        self.act_highlight = QAction("🖍️ Highlight", self)
        self.act_highlight.triggered.connect(self._pick_highlight_color)
        self.addAction(self.act_highlight)

        self.act_clear_format = QAction("🧹 Tx", self)
        self.act_clear_format.triggered.connect(self._clear_formatting)
        self.addAction(self.act_clear_format)

        self.addSeparator()

        # ---------------------------------------------------------------------
        # 5. Alignment & Lists & Spacing
        # ---------------------------------------------------------------------
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

        self.act_bullet_list = QAction("• List", self)
        self.act_bullet_list.triggered.connect(lambda: self._create_list(QTextListFormat.Style.ListDisc))
        self.addAction(self.act_bullet_list)

        self.act_num_list = QAction("1. List", self)
        self.act_num_list.triggered.connect(lambda: self._create_list(QTextListFormat.Style.ListDecimal))
        self.addAction(self.act_num_list)

        self.act_indent = QAction("⇥", self)
        self.act_indent.triggered.connect(lambda: self._change_indent(1))
        self.addAction(self.act_indent)

        self.act_outdent = QAction("⇤", self)
        self.act_outdent.triggered.connect(lambda: self._change_indent(-1))
        self.addAction(self.act_outdent)

        # Spacing Menu Button
        self.btn_spacing = QToolButton(self)
        self.btn_spacing.setText("↕ Spacing")
        self.btn_spacing.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_spacing = QMenu(self.btn_spacing)
        self._build_spacing_menu()
        self.btn_spacing.setMenu(self.menu_spacing)
        self.addWidget(self.btn_spacing)

        self.addSeparator()

        # ---------------------------------------------------------------------
        # 6. Tables, Callouts & Horizontal Rule
        # ---------------------------------------------------------------------
        # Table Menu Button
        self.btn_table = QToolButton(self)
        self.btn_table.setText("📊 " + _("tb_table"))
        self.btn_table.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_table = QMenu(self.btn_table)
        self._build_table_menu()
        self.btn_table.setMenu(self.menu_table)
        self.addWidget(self.btn_table)

        # Callout Menu Button
        self.btn_callout = QToolButton(self)
        self.btn_callout.setText("💡 " + _("tb_callout"))
        self.btn_callout.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.menu_callout = QMenu(self.btn_callout)
        self._build_callout_menu()
        self.btn_callout.setMenu(self.menu_callout)
        self.addWidget(self.btn_callout)

        self.act_divider = QAction("─ Divider", self)
        self.act_divider.triggered.connect(self._insert_divider)
        self.addAction(self.act_divider)

        # Expanding spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        # ---------------------------------------------------------------------
        # 7. AI, Voice Dictation & Inspector Toggle
        # ---------------------------------------------------------------------
        self.act_magic = QAction("✨ " + _("tb_magic_ai"), self)
        self.act_magic.triggered.connect(self.magic_ai_clicked.emit)
        self.addAction(self.act_magic)

        self.act_dictate = QAction("🎙️ " + _("tb_dictation"), self)
        self.act_dictate.triggered.connect(self.dictation_clicked.emit)
        self.addAction(self.act_dictate)

        self.act_sidebar = QAction("📑 " + _("tb_sidebar_toggle"), self)
        self.act_sidebar.triggered.connect(self.sidebar_toggled.emit)
        self.addAction(self.act_sidebar)

    # -------------------------------------------------------------------------
    # Menus
    # -------------------------------------------------------------------------
    def _build_spacing_menu(self):
        self.menu_spacing.clear()
        self.menu_spacing.addAction("1.0 " + _("tb_spacing_10"), lambda: self._set_line_height(100))
        self.menu_spacing.addAction("1.15", lambda: self._set_line_height(115))
        self.menu_spacing.addAction("1.5", lambda: self._set_line_height(150))
        self.menu_spacing.addAction("2.0 " + _("tb_spacing_20"), lambda: self._set_line_height(200))

    def _build_table_menu(self):
        self.menu_table.clear()
        self.menu_table.addAction("➕ " + _("tb_table_insert"), self._open_insert_table_dialog)
        self.menu_table.addSeparator()
        
        # Quick grid presets
        preset_menu = self.menu_table.addMenu("⚡ Quick Grid")
        preset_menu.addAction("2 × 2 Grid", lambda: self.insert_table(2, 2, True))
        preset_menu.addAction("3 × 3 Grid", lambda: self.insert_table(3, 3, True))
        preset_menu.addAction("4 × 4 Grid", lambda: self.insert_table(4, 4, True))
        preset_menu.addAction("5 × 5 Grid", lambda: self.insert_table(5, 5, True))

        self.menu_table.addSeparator()
        self.menu_table.addAction("⬆️ " + _("tb_table_insert_rows_above"), self._table_insert_row_above)
        self.menu_table.addAction("⬇️ " + _("tb_table_insert_rows_below"), self._table_insert_row_below)
        self.menu_table.addAction("⬅️ " + _("tb_table_insert_cols_left"), self._table_insert_col_left)
        self.menu_table.addAction("➡️ " + _("tb_table_insert_cols_right"), self._table_insert_col_right)
        self.menu_table.addSeparator()
        self.menu_table.addAction("🗑️ " + _("tb_table_delete_row"), self._table_delete_row)
        self.menu_table.addAction("🗑️ " + _("tb_table_delete_col"), self._table_delete_col)
        self.menu_table.addAction("⚠️ " + _("tb_table_delete_table"), self._table_delete_table)

    def _build_callout_menu(self):
        self.menu_callout.clear()
        self.menu_callout.addAction(_("tb_callout_info"), lambda: self._insert_callout("info"))
        self.menu_callout.addAction(_("tb_callout_tip"), lambda: self._insert_callout("tip"))
        self.menu_callout.addAction(_("tb_callout_warning"), lambda: self._insert_callout("warning"))
        self.menu_callout.addAction(_("tb_callout_quote"), lambda: self._insert_callout("quote"))

    def retranslate_ui(self):
        self.btn_style_normal.setText(_("tb_style_normal"))
        self.btn_style_normal.setToolTip(_("tb_heading_normal") + " (Ctrl+Alt+0)")
        
        self.btn_style_h1.setText(_("tb_style_h1"))
        self.btn_style_h1.setToolTip(_("tb_heading_1") + " (Ctrl+Alt+1)")
        
        self.btn_style_h2.setText(_("tb_style_h2"))
        self.btn_style_h2.setToolTip(_("tb_heading_2") + " (Ctrl+Alt+2)")
        
        self.btn_style_h3.setText(_("tb_style_h3"))
        self.btn_style_h3.setToolTip(_("tb_heading_3") + " (Ctrl+Alt+3)")
        
        self.btn_style_quote.setText(_("tb_style_quote"))
        self.btn_style_quote.setToolTip(_("tb_heading_quote"))
        
        self.btn_style_code.setText(_("tb_style_code"))
        self.btn_style_code.setToolTip("Code Block")

        self.act_gfonts.setToolTip(_("menu_format_google_fonts"))
        self.act_bold.setToolTip(_("tb_bold"))
        self.act_italic.setToolTip(_("tb_italic"))
        self.act_underline.setToolTip(_("tb_underline"))
        self.act_strike.setToolTip(_("tb_strikethrough"))
        self.act_subscript.setToolTip(_("tb_subscript"))
        self.act_superscript.setToolTip(_("tb_superscript"))
        self.act_clear_format.setToolTip(_("tb_clear_format"))

        self.act_color.setToolTip(_("tb_text_color"))
        self.act_highlight.setToolTip(_("tb_highlight_color"))

        self.act_align_left.setToolTip(_("tb_align_left"))
        self.act_align_center.setToolTip(_("tb_align_center"))
        self.act_align_right.setToolTip(_("tb_align_right"))
        self.act_align_justify.setToolTip(_("tb_align_justify"))

        self.act_bullet_list.setToolTip(_("tb_bullet_list"))
        self.act_num_list.setToolTip(_("tb_numbered_list"))
        self.act_indent.setToolTip(_("tb_indent_more"))
        self.act_outdent.setToolTip(_("tb_indent_less"))

        self.btn_spacing.setText("↕ " + _("tb_spacing"))
        self.btn_table.setText("📊 " + _("tb_table"))
        self.btn_callout.setText("💡 " + _("tb_callout"))
        self.act_divider.setText("─ " + _("tb_divider"))

        self.act_magic.setText("✨ " + _("tb_magic_ai"))
        self.act_dictate.setText("🎙️ " + _("tb_dictation"))
        self.act_sidebar.setText("📑 " + _("tb_sidebar_toggle"))

        self._build_spacing_menu()
        self._build_table_menu()
        self._build_callout_menu()

    # -------------------------------------------------------------------------
    # State Synchronization
    # -------------------------------------------------------------------------
    def sync_toolbar_state(self):
        cursor = self.editor.textCursor()
        fmt = cursor.charFormat()

        self.act_bold.setChecked(fmt.fontWeight() == QFont.Weight.Bold.value)
        self.act_italic.setChecked(fmt.fontItalic())
        self.act_underline.setChecked(fmt.fontUnderline())
        self.act_strike.setChecked(fmt.fontStrikeOut())
        self.act_subscript.setChecked(fmt.verticalAlignment() == QTextCharFormat.VerticalAlignment.AlignSubScript)
        self.act_superscript.setChecked(fmt.verticalAlignment() == QTextCharFormat.VerticalAlignment.AlignSuperScript)

        # Safe font family check
        font_name = fmt.font().family()
        if font_name:
            self.combo_font.select_font_family(font_name)

        if fmt.fontPointSize() > 0:
            self.combo_size.blockSignals(True)
            self.combo_size.setCurrentText(str(int(fmt.fontPointSize())))
            self.combo_size.blockSignals(False)

        # Block heading & style sync
        block_fmt = cursor.blockFormat()
        level = block_fmt.headingLevel()
        
        self.style_group.blockSignals(True)
        if level == 1:
            self.btn_style_h1.setChecked(True)
        elif level == 2:
            self.btn_style_h2.setChecked(True)
        elif level == 3:
            self.btn_style_h3.setChecked(True)
        elif block_fmt.leftMargin() > 16:
            self.btn_style_quote.setChecked(True)
        else:
            self.btn_style_normal.setChecked(True)
        self.style_group.blockSignals(False)

    # -------------------------------------------------------------------------
    # Formatting Handlers
    # -------------------------------------------------------------------------
    def _apply_heading_level(self, level):
        cursor = self.editor.textCursor()
        block_fmt = QTextBlockFormat()
        char_fmt = QTextCharFormat()

        if level == 1:
            block_fmt.setHeadingLevel(1)
            char_fmt.setFontPointSize(22)
            char_fmt.setFontWeight(QFont.Weight.Bold.value)
            char_fmt.setFontItalic(False)
        elif level == 2:
            block_fmt.setHeadingLevel(2)
            char_fmt.setFontPointSize(18)
            char_fmt.setFontWeight(QFont.Weight.Bold.value)
            char_fmt.setFontItalic(False)
        elif level == 3:
            block_fmt.setHeadingLevel(3)
            char_fmt.setFontPointSize(15)
            char_fmt.setFontWeight(QFont.Weight.Bold.value)
            char_fmt.setFontItalic(False)
        elif level == 4: # Blockquote
            block_fmt.setHeadingLevel(0)
            block_fmt.setLeftMargin(24)
            char_fmt.setFontPointSize(12)
            char_fmt.setFontItalic(True)
        elif level == 5: # Code block
            block_fmt.setHeadingLevel(0)
            block_fmt.setLeftMargin(16)
            char_fmt.setFontFamily("JetBrains Mono")
            char_fmt.setFontPointSize(11)
            char_fmt.setFontItalic(False)
        else: # Normal Paragraph
            block_fmt.setHeadingLevel(0)
            block_fmt.setLeftMargin(0)
            char_fmt.setFontPointSize(12)
            char_fmt.setFontWeight(QFont.Weight.Normal.value)
            char_fmt.setFontItalic(False)

        cursor.mergeBlockFormat(block_fmt)
        cursor.mergeCharFormat(char_fmt)
        self.editor.setTextCursor(cursor)

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

    def _toggle_subscript(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        curr = cursor.charFormat().verticalAlignment()
        if curr == QTextCharFormat.VerticalAlignment.AlignSubScript:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
        else:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSubScript)
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

    def _toggle_superscript(self):
        cursor = self.editor.textCursor()
        fmt = QTextCharFormat()
        curr = cursor.charFormat().verticalAlignment()
        if curr == QTextCharFormat.VerticalAlignment.AlignSuperScript:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
        else:
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignSuperScript)
        cursor.mergeCharFormat(fmt)
        self.editor.setTextCursor(cursor)

    def _clear_formatting(self):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        
        clean_fmt = QTextCharFormat()
        clean_fmt.setFontPointSize(12)
        clean_fmt.setFontWeight(QFont.Weight.Normal.value)
        clean_fmt.setFontItalic(False)
        clean_fmt.setFontUnderline(False)
        clean_fmt.setFontStrikeOut(False)
        clean_fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal)
        clean_fmt.setBackground(QBrush(Qt.GlobalColor.transparent))
        if self.theme_mgr:
            clean_fmt.setForeground(QBrush(QColor(self.theme_mgr.get_color("text_color", "#1a1d24"))))
        
        cursor.setCharFormat(clean_fmt)
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

    def _set_alignment(self, align_flag):
        cursor = self.editor.textCursor()
        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(align_flag)
        cursor.mergeBlockFormat(block_fmt)
        self.editor.setTextCursor(cursor)

    def _change_indent(self, delta):
        cursor = self.editor.textCursor()
        block_fmt = cursor.blockFormat()
        new_margin = max(0, block_fmt.leftMargin() + (delta * 24))
        block_fmt.setLeftMargin(new_margin)
        cursor.mergeBlockFormat(block_fmt)
        self.editor.setTextCursor(cursor)

    def _set_line_height(self, height_pct):
        cursor = self.editor.textCursor()
        block_fmt = QTextBlockFormat()
        block_fmt.setLineHeight(height_pct, 1) # 1 = ProportionalHeight
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

    def _insert_divider(self):
        cursor = self.editor.textCursor()
        cursor.insertHtml('<hr style="border: 0; border-top: 1.5px solid #cbd5e1; margin: 16px 0;"/><p></p>')

    def _insert_callout(self, callout_type):
        cursor = self.editor.textCursor()
        bg = "#eff6ff" if callout_type == "info" else ("#f0fdf4" if callout_type == "tip" else ("#fffbeb" if callout_type == "warning" else "#f8fafc"))
        border = "#3b82f6" if callout_type == "info" else ("#22c55e" if callout_type == "tip" else ("#f59e0b" if callout_type == "warning" else "#64748b"))
        icon = "ℹ️" if callout_type == "info" else ("💡" if callout_type == "tip" else ("⚠️" if callout_type == "warning" else "❝"))
        title = "Note" if callout_type == "info" else ("Tip" if callout_type == "tip" else ("Warning" if callout_type == "warning" else "Quote"))
        
        html_content = f"""<table width="100%" style="background-color: {bg}; border-left: 4px solid {border}; border-radius: 4px; margin: 12px 0; padding: 10px 14px;">
            <tr>
                <td style="vertical-align: top; width: 24px; font-size: 16px;">{icon}</td>
                <td style="vertical-align: top; padding-left: 8px; color: #1e293b; font-size: 11pt;">
                    <b>{title}:</b> Type your text here...
                </td>
            </tr>
        </table><p></p>"""
        cursor.insertHtml(html_content)

    # -------------------------------------------------------------------------
    # Table Operations
    # -------------------------------------------------------------------------
    def _open_insert_table_dialog(self):
        dlg = TableDialog(self.theme_mgr, self)
        if dlg.exec():
            params = dlg.get_table_params()
            self.insert_table(params["rows"], params["cols"], params["has_header"])

    def insert_table(self, rows, cols, has_header=True):
        cursor = self.editor.textCursor()
        
        table_fmt = QTextTableFormat()
        table_fmt.setBorder(1)
        table_fmt.setBorderStyle(QTextFrameFormat.BorderStyle.BorderStyle_Solid)
        table_fmt.setBorderBrush(QBrush(QColor("#cbd5e1")))
        table_fmt.setCellPadding(8)
        table_fmt.setCellSpacing(0)
        table_fmt.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100))

        table = cursor.insertTable(rows, cols, table_fmt)
        
        if has_header and rows > 0:
            header_fmt = QTextTableCellFormat()
            header_fmt.setBackground(QBrush(QColor("#f1f5f9")))
            for c in range(cols):
                cell = table.cellAt(0, c)
                cell.setFormat(header_fmt)

        self.editor.setTextCursor(cursor)

    def _get_current_table(self):
        cursor = self.editor.textCursor()
        return cursor.currentTable()

    def _table_insert_row_above(self):
        table = self._get_current_table()
        if table:
            cursor = self.editor.textCursor()
            cell = table.cellAt(cursor)
            table.insertRows(cell.row(), 1)

    def _table_insert_row_below(self):
        table = self._get_current_table()
        if table:
            cursor = self.editor.textCursor()
            cell = table.cellAt(cursor)
            table.insertRows(cell.row() + 1, 1)

    def _table_insert_col_left(self):
        table = self._get_current_table()
        if table:
            cursor = self.editor.textCursor()
            cell = table.cellAt(cursor)
            table.insertColumns(cell.column(), 1)

    def _table_insert_col_right(self):
        table = self._get_current_table()
        if table:
            cursor = self.editor.textCursor()
            cell = table.cellAt(cursor)
            table.insertColumns(cell.column() + 1, 1)

    def _table_delete_row(self):
        table = self._get_current_table()
        if table:
            cursor = self.editor.textCursor()
            cell = table.cellAt(cursor)
            table.removeRows(cell.row(), 1)

    def _table_delete_col(self):
        table = self._get_current_table()
        if table:
            cursor = self.editor.textCursor()
            cell = table.cellAt(cursor)
            table.removeColumns(cell.column(), 1)

    def _table_delete_table(self):
        table = self._get_current_table()
        if table:
            cursor = self.editor.textCursor()
            cursor.setPosition(table.firstPosition())
            cursor.setPosition(table.lastPosition(), QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
