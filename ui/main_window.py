import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog,
    QMessageBox, QLabel, QSplitter, QStatusBar, QApplication,
    QStackedWidget, QMenu, QDialog, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QMarginsF
from PyQt6.QtGui import QAction, QKeySequence, QTextCursor, QPageLayout, QPageSize, QCursor
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

from core.i18n import _, i18n
from core.doc_manager import DocumentManager
from ui.editor_view import EditorView
from ui.toolbar import FormattingToolBar
from ui.sidebar_inspector import SidebarInspector
from ui.inline_ai_popup import InlineAIPopup
from ui.settings_dialog import SettingsDialog
from ui.google_fonts_dialog import GoogleFontsDialog
from ui.start_screen import StartScreen

class MainWindow(QMainWindow):
    def __init__(self, ai_client, dictation_engine, theme_mgr, config_mgr):
        super().__init__()
        self.ai = ai_client
        self.dictation = dictation_engine
        self.theme_mgr = theme_mgr
        self.config = config_mgr

        self.current_filepath = None
        self.is_modified = False

        self.setWindowTitle(_("app_name"))
        self.resize(1200, 850)

        self.init_ui()
        self.init_menus()
        self.apply_theme()
        self.retranslate_ui()

        # Connect signals
        self.theme_mgr.theme_changed.connect(self.apply_theme)
        i18n.language_changed.connect(self.retranslate_ui)

        # Text change debouncer for autosave & stats & AI
        self.review_timer = QTimer(self)
        self.review_timer.setSingleShot(True)
        self.review_timer.setInterval(2500)
        self.review_timer.timeout.connect(self._on_review_timer_fired)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(self.config.get("autosave_interval_sec", 30) * 1000)
        self.autosave_timer.timeout.connect(self._on_autosave_timer_fired)
        self.autosave_timer.start()

        self.editor.canvas.textChanged.connect(self._on_text_changed)
        self.editor.canvas.cursorPositionChanged.connect(self._update_cursor_pos)
        self.editor.canvas.magic_ai_requested.connect(self._open_inline_ai)

        # Dictation engine connections
        self.dictation.state_changed.connect(self._on_dictation_state_changed)
        self.dictation.transcription_ready.connect(self._on_transcription_ready)

        # AI Status
        self.ai.ai_status_changed.connect(self._on_ai_status_changed)

        # Sidebar interactions
        self.sidebar.apply_suggestion_requested.connect(self._apply_ai_suggestion)
        self.sidebar.outline_item_clicked.connect(self._navigate_to_position)
        self.sidebar.btn_refresh.clicked.connect(self._trigger_ai_review)

        # Popups
        self.inline_ai = InlineAIPopup(self.ai, self.theme_mgr, self)
        self.inline_ai.replace_requested.connect(self._on_inline_ai_replace)
        self.inline_ai.insert_below_requested.connect(self._on_inline_ai_insert_below)

        # Initial screen state: first run gets welcome sample; subsequent runs show start page
        has_run_before = self.config.get("has_run_before", False)
        if not has_run_before:
            self.config.set("has_run_before", True)
            self._insert_welcome_sample()
            self.show_editor_screen()
        else:
            self.show_start_screen()

    def init_ui(self):
        self.stack = QStackedWidget(self)

        # 1. Start Screen (Index 0)
        self.start_screen = StartScreen(self.config, self.theme_mgr, self)
        self.start_screen.new_document_requested.connect(self.file_new)
        self.start_screen.open_document_requested.connect(self.file_open)
        self.start_screen.open_recent_requested.connect(self.open_recent_file)
        self.stack.addWidget(self.start_screen)

        # 2. Editor & Sidebar Container (Index 1)
        self.editor = EditorView(self.theme_mgr, self)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.editor)

        self.sidebar = SidebarInspector(self.ai, self.theme_mgr, self)
        self.sidebar.setVisible(self.config.get("show_ai_sidebar", True))
        self.splitter.addWidget(self.sidebar)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        self.stack.addWidget(self.splitter)

        self.setCentralWidget(self.stack)

        # 3. Formatting Toolbar
        self.toolbar = FormattingToolBar(self.editor, self.theme_mgr, self)
        self.toolbar.magic_ai_clicked.connect(lambda: self._open_inline_ai(self.editor.textCursor().selectedText(), None))
        self.toolbar.dictation_clicked.connect(self._toggle_dictation)
        self.toolbar.sidebar_toggled.connect(self._toggle_sidebar)
        self.toolbar.google_fonts_clicked.connect(self._open_google_fonts_dialog)
        self.addToolBar(self.toolbar)

        # 4. Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.lbl_stats = QLabel("0 words | 0 characters")
        self.lbl_cursor = QLabel("Ln 1, Col 1")
        self.lbl_ai_status = QLabel("✨ " + _("status_ai_ready"))
        self.lbl_dict_status = QLabel("🎙️ " + _("status_dictation_idle"))

        self.btn_lang_toggle = QPushButton()
        self.btn_lang_toggle.setObjectName("StatusBarLangBtn")
        self.btn_lang_toggle.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_lang_toggle.clicked.connect(self._toggle_language)
        self.btn_lang_toggle.setStyleSheet("""
            QPushButton#StatusBarLangBtn {
                background-color: transparent;
                border: 1px solid rgba(128, 128, 128, 0.3);
                border-radius: 4px;
                padding: 2px 6px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton#StatusBarLangBtn:hover {
                background-color: rgba(128, 128, 128, 0.15);
            }
        """)
        self._update_lang_toggle_btn()

        self.status_bar.addWidget(self.lbl_stats)
        self.status_bar.addPermanentWidget(self.lbl_ai_status)
        self.status_bar.addPermanentWidget(self.lbl_dict_status)
        self.status_bar.addPermanentWidget(self.lbl_cursor)
        self.status_bar.addPermanentWidget(self.btn_lang_toggle)

    def _add_action(self, menu, text, slot, shortcut=None):
        act = QAction(text, self)
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        if slot:
            act.triggered.connect(slot)
        menu.addAction(act)
        return act

    def init_menus(self):
        mb = self.menuBar()

        # File Menu
        self.menu_file = mb.addMenu(_("menu_file"))
        self.act_start_page = self._add_action(self.menu_file, _("menu_file_start_page"), self.show_start_screen, "Ctrl+H")
        self.act_new = self._add_action(self.menu_file, _("menu_file_new"), self.file_new, "Ctrl+N")
        self.act_open = self._add_action(self.menu_file, _("menu_file_open"), self.file_open, "Ctrl+O")
        
        # Recent Files submenu
        self.menu_recent = self.menu_file.addMenu(_("menu_file_recent"))
        self._update_recent_menu()

        self.menu_file.addSeparator()
        self.act_save = self._add_action(self.menu_file, _("menu_file_save"), self.file_save, "Ctrl+S")
        self.act_save_as = self._add_action(self.menu_file, _("menu_file_save_as"), self.file_save_as, "Ctrl+Shift+S")
        self.menu_file.addSeparator()
        self.act_print = self._add_action(self.menu_file, _("menu_file_print"), self.file_print, "Ctrl+P")
        self.act_print_prev = self._add_action(self.menu_file, _("menu_file_print_preview"), self.file_print_preview, "Ctrl+Shift+P")
        self.menu_file.addSeparator()
        self.act_exp_pdf = self._add_action(self.menu_file, _("menu_file_export_pdf"), self.export_pdf, "Ctrl+Shift+E")
        self.act_exp_docx = self._add_action(self.menu_file, _("menu_file_export_docx"), self.export_docx)
        self.act_exp_md = self._add_action(self.menu_file, _("menu_file_export_md"), self.export_markdown)
        self.act_exp_html = self._add_action(self.menu_file, _("menu_file_export_html"), self.export_html)
        self.menu_file.addSeparator()
        self.act_exit = self._add_action(self.menu_file, _("menu_file_exit"), self.close, "Ctrl+Q")

        # Edit Menu
        self.menu_edit = mb.addMenu(_("menu_edit"))
        self.act_undo = self._add_action(self.menu_edit, _("menu_edit_undo"), self.editor.canvas.undo, "Ctrl+Z")
        self.act_redo = self._add_action(self.menu_edit, _("menu_edit_redo"), self.editor.canvas.redo, "Ctrl+Y")
        self.menu_edit.addSeparator()
        self.act_cut = self._add_action(self.menu_edit, _("menu_edit_cut"), self.editor.canvas.cut, "Ctrl+X")
        self.act_copy = self._add_action(self.menu_edit, _("menu_edit_copy"), self.editor.canvas.copy, "Ctrl+C")
        self.act_paste = self._add_action(self.menu_edit, _("menu_edit_paste"), self.editor.canvas.paste, "Ctrl+V")
        self.act_select_all = self._add_action(self.menu_edit, _("menu_edit_select_all"), self.editor.canvas.selectAll, "Ctrl+A")

        # View Menu
        self.menu_view = mb.addMenu(_("menu_view"))
        self.act_view_sidebar = self._add_action(self.menu_view, _("menu_view_ai_sidebar"), self._toggle_sidebar, "Ctrl+Shift+I")
        self.act_view_focus = self._add_action(self.menu_view, _("menu_view_focus_mode"), self._toggle_focus_mode, "F11")
        self.menu_view.addSeparator()
        self.act_zoom_in = self._add_action(self.menu_view, _("menu_view_zoom_in"), self._zoom_in, "Ctrl++")
        self.act_zoom_out = self._add_action(self.menu_view, _("menu_view_zoom_out"), self._zoom_out, "Ctrl+-")
        self.act_zoom_reset = self._add_action(self.menu_view, _("menu_view_zoom_reset"), self._zoom_reset, "Ctrl+0")
        self.menu_view.addSeparator()
        
        # Language submenu
        self.menu_language = self.menu_view.addMenu("🌐 " + _("menu_view_language"))
        self.act_lang_sv = QAction(_("lang_sv"), self)
        self.act_lang_sv.setCheckable(True)
        self.act_lang_sv.triggered.connect(lambda: self._set_language("sv"))
        self.menu_language.addAction(self.act_lang_sv)

        self.act_lang_en = QAction(_("lang_en"), self)
        self.act_lang_en.setCheckable(True)
        self.act_lang_en.triggered.connect(lambda: self._set_language("en"))
        self.menu_language.addAction(self.act_lang_en)
        self._update_lang_menu_actions()

        # Insert Menu
        self.menu_insert = mb.addMenu(_("menu_insert"))
        self.act_ins_table = self._add_action(self.menu_insert, "📊 " + _("menu_insert_table"), self.toolbar._open_insert_table_dialog)
        self.act_ins_divider = self._add_action(self.menu_insert, "─ " + _("menu_insert_horizontal_rule"), self.toolbar._insert_divider)
        
        self.menu_ins_callout = self.menu_insert.addMenu("💡 " + _("tb_callout"))
        self.act_callout_info = self.menu_ins_callout.addAction(_("tb_callout_info"), lambda: self.toolbar._insert_callout("info"))
        self.act_callout_tip = self.menu_ins_callout.addAction(_("tb_callout_tip"), lambda: self.toolbar._insert_callout("tip"))
        self.act_callout_warning = self.menu_ins_callout.addAction(_("tb_callout_warning"), lambda: self.toolbar._insert_callout("warning"))
        self.act_callout_quote = self.menu_ins_callout.addAction(_("tb_callout_quote"), lambda: self.toolbar._insert_callout("quote"))

        # Format Menu
        self.menu_format = mb.addMenu(_("menu_format"))
        self.act_fmt_bold = self._add_action(self.menu_format, _("menu_format_bold"), self.toolbar._toggle_bold, "Ctrl+B")
        self.act_fmt_italic = self._add_action(self.menu_format, _("menu_format_italic"), self.toolbar._toggle_italic, "Ctrl+I")
        self.act_fmt_underline = self._add_action(self.menu_format, _("menu_format_underline"), self.toolbar._toggle_underline, "Ctrl+U")
        self.act_fmt_strike = self._add_action(self.menu_format, _("menu_format_strikethrough"), self.toolbar._toggle_strike)
        self.act_fmt_sub = self._add_action(self.menu_format, _("tb_subscript"), self.toolbar._toggle_subscript)
        self.act_fmt_super = self._add_action(self.menu_format, _("tb_superscript"), self.toolbar._toggle_superscript)
        self.act_fmt_clear = self._add_action(self.menu_format, _("menu_format_clear"), self.toolbar._clear_formatting, "Ctrl+\\")
        self.menu_format.addSeparator()
        self.act_gfonts = self._add_action(self.menu_format, "🌐 " + _("menu_format_google_fonts"), self._open_google_fonts_dialog)

        # AI Assistant Menu
        self.menu_ai = mb.addMenu(_("menu_ai"))
        self.act_inline_ai = self._add_action(self.menu_ai, _("menu_ai_inline"), lambda: self._open_inline_ai(self.editor.textCursor().selectedText(), None), "Ctrl+K")
        self.act_review_ai = self._add_action(self.menu_ai, _("menu_ai_review"), self._trigger_ai_review)
        self.act_dictation = self._add_action(self.menu_ai, _("menu_ai_dictation"), self._toggle_dictation, "F8")
        self.menu_ai.addSeparator()
        self.act_settings = self._add_action(self.menu_ai, _("menu_ai_settings"), self._open_settings)

        # Help Menu
        self.menu_help = mb.addMenu(_("menu_help"))
        self.act_about = self._add_action(self.menu_help, _("menu_help_about"), self._show_about)

    def _update_recent_menu(self):
        self.menu_recent.clear()
        recents = self.config.get("recent_files", [])
        if not recents:
            act = self.menu_recent.addAction(_("menu_file_no_recents"))
            act.setEnabled(False)
            return

        for fpath in recents[:10]:
            fname = os.path.basename(fpath)
            act = self.menu_recent.addAction(f"{fname} ({fpath})")
            act.triggered.connect(lambda checked, fp=fpath: self.open_recent_file(fp))

        self.menu_recent.addSeparator()
        act_clear = self.menu_recent.addAction(_("menu_file_clear_recents"))
        act_clear.triggered.connect(self._clear_recent_files)

    def _clear_recent_files(self):
        self.config.clear_recent_files()
        self._update_recent_menu()
        self.start_screen.refresh_recents()

    def show_start_screen(self):
        if self.stack.currentIndex() == 1 and not self._maybe_save_changes():
            return
        self.start_screen.refresh_recents()
        self.stack.setCurrentIndex(0)
        self.toolbar.setVisible(False)
        self.status_bar.setVisible(False)
        self.setWindowTitle(_("app_name"))

    def show_editor_screen(self):
        self.stack.setCurrentIndex(1)
        self.toolbar.setVisible(True)
        self.sidebar.setVisible(self.config.get("show_ai_sidebar", True))
        self.status_bar.setVisible(True)
        self._update_window_title()
        self._update_stats()
        self.editor.canvas.setFocus()

    def _toggle_language(self):
        curr = i18n.get_language()
        new_lang = "sv" if curr == "en" else "en"
        self._set_language(new_lang)

    def _set_language(self, lang_code):
        if lang_code != i18n.get_language():
            i18n.set_language(lang_code)
            self.config.set("language", lang_code)

    def _update_lang_toggle_btn(self):
        curr = i18n.get_language()
        if curr == "sv":
            self.btn_lang_toggle.setText("🇸🇪 SV")
        else:
            self.btn_lang_toggle.setText("🇬🇧 EN")
        self.btn_lang_toggle.setToolTip(_("status_lang_switch_tooltip"))

    def _update_lang_menu_actions(self):
        curr = i18n.get_language()
        if hasattr(self, "act_lang_sv"):
            self.act_lang_sv.setChecked(curr == "sv")
        if hasattr(self, "act_lang_en"):
            self.act_lang_en.setChecked(curr == "en")

    def _toggle_focus_mode(self):
        if self.isFullScreen():
            self.showNormal()
            self.toolbar.setVisible(True)
            self.sidebar.setVisible(self.config.get("show_ai_sidebar", True))
        else:
            self.showFullScreen()
            self.toolbar.setVisible(False)
            self.sidebar.setVisible(False)

    def _zoom_in(self):
        self.editor.canvas.zoomIn(1)

    def _zoom_out(self):
        self.editor.canvas.zoomOut(1)

    def _zoom_reset(self):
        font = self.editor.canvas.font()
        font.setPointSize(self.config.get("default_font_size", 12))
        self.editor.canvas.setFont(font)

    def _insert_welcome_sample(self):
        lang = i18n.get_language()
        if lang == "sv":
            html = f"""
            <h1>{_("app_title")}</h1>
            <p>Välkommen till <b>OmaScribe</b>, din moderna och intelligenta skrivmiljö för Linux & Omarchy.</p>
            
            <h2>🚀 Vad gör OmaScribe unikt?</h2>
            <p>OmaScribe kombinerar en ren och fokuserad ordbehandlare med inbyggd AI-granskning, interaktiv omskrivning och lokal röst-diktering:</p>
            
            <ul>
              <li><b>✨ Magisk Co-Writer:</b> Markera valfri text och tryck <code>Ctrl + K</code> för att skriva om, förbättra tonläge, översätta eller utveckla.</li>
              <li><b>📑 AI-Granskare & Statistik:</b> Få förslag i realtid, LIX-läsbarhet, tonanalys och automatisk disposition.</li>
              <li><b>🎙️ Röst-diktering:</b> Tryck <code>F8</code> för att tala in din text med automatisk transkribering.</li>
              <li><b>📄 Full kompatibilitet:</b> Öppna och spara direkt i Word <code>.docx</code>, <code>.md</code> (Markdown) och skriv ut till <code>.pdf</code>.</li>
            </ul>
            
            <blockquote>"Det mest skrämmande ögonblicket är alltid precis innan du börjar. Därefter kan det bara bli bättre." — Stephen King</blockquote>
            <p>Börja skriva eller radera denna text för att påbörja ditt mästerverk!</p>
            """
        else:
            html = f"""
            <h1>{_("app_title")}</h1>
            <p>Welcome to <b>OmaScribe</b>, your next-generation intelligent writing environment designed for Linux and Omarchy.</p>
            
            <h2>🚀 What makes OmaScribe unique?</h2>
            <p>OmaScribe combines standard WYSIWYG document editing with built-in AI review, intelligent rephrasing, and local voice dictation:</p>
            
            <ul>
              <li><b>✨ Magic Co-Writer:</b> Highlight any phrase or sentence and press <code>Ctrl + K</code> to rewrite, polish, translate, or expand.</li>
              <li><b>📑 AI Inspector Sidebar:</b> Get live suggestions, readability grading (LIX), tone analysis, and automatic heading outline.</li>
              <li><b>🎙️ Voice Dictation:</b> Press <code>F8</code> to speak and dictate your thoughts naturally.</li>
              <li><b>📄 Native Export:</b> Export your documents directly to Word <code>.docx</code>, print-ready <code>.pdf</code>, and <code>.md</code>.</li>
            </ul>
            
            <blockquote>"The scariest moment is always just before you start. After that, things can only get better." — Stephen King</blockquote>
            <p>Start typing or deleting this text to draft your masterwork!</p>
            """
        self.editor.document.setHtml(html)
        self.is_modified = False
        self._update_window_title()

    def _on_text_changed(self):
        if self.stack.currentIndex() == 1:
            self.is_modified = True
            self._update_window_title()
            self._update_stats()
            self.review_timer.start()

    def _update_cursor_pos(self):
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.positionInBlock() + 1
        self.lbl_cursor.setText(f"Ln {line}, Col {col}")

    def _update_stats(self):
        self.sidebar.update_metrics_and_outline(self.editor.document)
        stats = self.sidebar.lbl_words.text()
        chars = self.sidebar.lbl_chars.text()
        self.lbl_stats.setText(f"{stats} | {chars}")

    def _update_window_title(self):
        if self.stack.currentIndex() == 0:
            self.setWindowTitle(_("app_name"))
            return
        doc_name = os.path.basename(self.current_filepath) if self.current_filepath else _("untitled_document")
        mod_flag = " •" if self.is_modified else ""
        self.setWindowTitle(f"{doc_name}{mod_flag} — {_('app_name')}")

    def _on_review_timer_fired(self):
        if self.stack.currentIndex() == 1:
            text = self.editor.document.toPlainText()
            lang = i18n.get_language()
            self.ai.review_document(text, lang=lang)

    def _on_autosave_timer_fired(self):
        if self.stack.currentIndex() == 1 and self.is_modified and self.current_filepath and self.config.get("autosave", True):
            try:
                DocumentManager.save_file(self.current_filepath, self.editor.document)
                self.is_modified = False
                self._update_window_title()
            except Exception as e:
                print(f"[Autosave] Error: {e}")

    def _open_inline_ai(self, selected_text, global_pos):
        if self.stack.currentIndex() != 1:
            return
        if global_pos is None:
            rect = self.editor.canvas.cursorRect()
            global_pos = self.editor.canvas.mapToGlobal(rect.bottomLeft())
        self.inline_ai.show_at(selected_text, global_pos)

    def _on_inline_ai_replace(self, new_text):
        cursor = self.editor.textCursor()
        cursor.insertText(new_text)
        self.editor.setTextCursor(cursor)

    def _on_inline_ai_insert_below(self, new_text):
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        cursor.insertBlock()
        cursor.insertText(new_text)
        self.editor.setTextCursor(cursor)

    def _apply_ai_suggestion(self, original, replacement):
        cursor = self.editor.document.find(original)
        if not cursor.isNull():
            cursor.insertText(replacement)
            self.editor.setTextCursor(cursor)

    def _navigate_to_position(self, pos):
        cursor = QTextCursor(self.editor.document)
        cursor.setPosition(pos)
        self.editor.setTextCursor(cursor)
        self.editor.canvas.setFocus()

    def _trigger_ai_review(self):
        text = self.editor.document.toPlainText()
        self.sidebar.update_metrics_and_outline(self.editor.document)
        self._update_stats()
        if not text or len(text.strip()) < 10:
            self.sidebar.show_short_message()
            return
        self.sidebar.set_loading(True)
        self.ai.review_document(text, lang=i18n.get_language())

    def _toggle_sidebar(self):
        vis = not self.sidebar.isVisible()
        self.sidebar.setVisible(vis)
        self.config.set("show_ai_sidebar", vis)

    def _toggle_focus_mode(self):
        if self.isFullScreen():
            self.showNormal()
            if self.stack.currentIndex() == 1:
                self.toolbar.setVisible(True)
                self.status_bar.setVisible(True)
            self.menuBar().setVisible(True)
        else:
            self.showFullScreen()
            self.toolbar.setVisible(False)
            self.menuBar().setVisible(False)
            self.status_bar.setVisible(False)

    def _toggle_dictation(self):
        self.dictation.toggle_recording()

    def _on_dictation_state_changed(self, state):
        if state == "listening":
            self.lbl_dict_status.setText("🎙️ " + _("status_dictation_listening"))
        elif state == "transcribing":
            self.lbl_dict_status.setText("⏳ " + _("status_dictation_transcribing"))
        else:
            self.lbl_dict_status.setText("🎙️ " + _("status_dictation_idle"))

    def _on_transcription_ready(self, text):
        if self.stack.currentIndex() == 1:
            cursor = self.editor.textCursor()
            cursor.insertText(text + " ")
            self.editor.setTextCursor(cursor)

    def _on_ai_status_changed(self, status):
        if status == "analyzing":
            self.lbl_ai_status.setText("✨ " + _("status_ai_analyzing"))
        else:
            self.lbl_ai_status.setText("✨ " + _("status_ai_ready"))

    def _open_google_fonts_dialog(self):
        dlg = GoogleFontsDialog(self.theme_mgr, self)
        dlg.font_list_changed.connect(self.toolbar.combo_font.populate_fonts)
        dlg.exec()

    def _open_settings(self):
        dlg = SettingsDialog(self.config, self.theme_mgr, self)
        dlg.exec()

    def _show_about(self):
        QMessageBox.about(
            self,
            _("app_name"),
            f"<h3>{_('app_title')}</h3>"
            f"<p>Version 0.1.0</p>"
            f"<p>{_('about_desc')}</p>"
        )

    # -------------------------------------------------------------------------
    # Extension enforcement helper
    # -------------------------------------------------------------------------
    def _ensure_extension(self, filepath: str, selected_filter: str, default_ext: str = ".docx") -> str:
        if not filepath:
            return filepath
        root, ext = os.path.splitext(filepath)
        valid_extensions = {".docx", ".md", ".markdown", ".html", ".htm", ".txt", ".pdf"}
        if ext.lower() in valid_extensions:
            return filepath
        
        filter_lower = (selected_filter or "").lower()
        if "*.docx" in filter_lower:
            target_ext = ".docx"
        elif "*.md" in filter_lower or "*.markdown" in filter_lower:
            target_ext = ".md"
        elif "*.html" in filter_lower or "*.htm" in filter_lower:
            target_ext = ".html"
        elif "*.txt" in filter_lower:
            target_ext = ".txt"
        elif "*.pdf" in filter_lower:
            target_ext = ".pdf"
        else:
            target_ext = default_ext
        return f"{filepath}{target_ext}"

    # -------------------------------------------------------------------------
    # File Operations & Printing
    # -------------------------------------------------------------------------
    def file_new(self):
        if self.stack.currentIndex() == 1 and not self._maybe_save_changes():
            return
        self.editor.document.clear()
        self.current_filepath = None
        self.is_modified = False
        self.show_editor_screen()

    def file_open(self):
        if self.stack.currentIndex() == 1 and not self._maybe_save_changes():
            return
        fpath, _filter = QFileDialog.getOpenFileName(
            self,
            _("menu_file_open"),
            "",
            "Documents (*.docx *.md *.markdown *.html *.htm *.txt);;Word Documents (*.docx);;Markdown (*.md);;HTML Files (*.html *.htm);;Plain Text (*.txt);;All Files (*.*)"
        )
        if fpath:
            self.open_recent_file(fpath)

    def open_recent_file(self, filepath):
        if self.stack.currentIndex() == 1 and not self._maybe_save_changes():
            return
        if not os.path.exists(filepath):
            QMessageBox.warning(self, _("menu_file_open"), f"{_('start_file_not_found')}:\n{filepath}")
            self.config.remove_recent_file(filepath)
            self._update_recent_menu()
            self.start_screen.refresh_recents()
            return
        try:
            DocumentManager.load_file(filepath, self.editor.document)
            self.current_filepath = filepath
            self.is_modified = False
            self.config.add_recent_file(filepath)
            self._update_recent_menu()
            self.show_editor_screen()
        except Exception as e:
            QMessageBox.critical(self, "Error Opening File", str(e))

    def file_save(self):
        if self.current_filepath:
            try:
                DocumentManager.save_file(self.current_filepath, self.editor.document)
                self.is_modified = False
                self._update_window_title()
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error Saving File", str(e))
                return False
        else:
            return self.file_save_as()

    def file_save_as(self):
        fpath, selected_filter = QFileDialog.getSaveFileName(
            self,
            _("menu_file_save_as"),
            "",
            "Word Document (*.docx);;Markdown (*.md);;HTML Document (*.html);;Plain Text (*.txt)"
        )
        if fpath:
            fpath = self._ensure_extension(fpath, selected_filter, ".docx")
            try:
                DocumentManager.save_file(fpath, self.editor.document)
                self.current_filepath = fpath
                self.is_modified = False
                self._update_window_title()
                self.config.add_recent_file(fpath)
                self._update_recent_menu()
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error Saving File", str(e))
        return False

    def file_print(self):
        if self.stack.currentIndex() == 0:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        page_layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            QMarginsF(20, 20, 20, 20),
            QPageLayout.Unit.Millimeter
        )
        printer.setPageLayout(page_layout)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle(_("menu_file_print"))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.editor.document.print(printer)

    def file_print_preview(self):
        if self.stack.currentIndex() == 0:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        page_layout = QPageLayout(
            QPageSize(QPageSize.PageSizeId.A4),
            QPageLayout.Orientation.Portrait,
            QMarginsF(20, 20, 20, 20),
            QPageLayout.Unit.Millimeter
        )
        printer.setPageLayout(page_layout)
        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle(_("menu_file_print_preview"))
        preview.setMinimumSize(800, 600)
        preview.resize(1050, 850)
        preview.paintRequested.connect(lambda p: self.editor.document.print(p))
        preview.exec()

    def export_pdf(self):
        fpath, selected_filter = QFileDialog.getSaveFileName(
            self,
            _("menu_file_export_pdf"),
            "",
            "PDF Document (*.pdf)"
        )
        if fpath:
            fpath = self._ensure_extension(fpath, "*.pdf", ".pdf")
            try:
                DocumentManager.save_file(fpath, self.editor.document)
                QMessageBox.information(self, _("export_success_title"), _("export_success_text", path=fpath))
            except Exception as e:
                QMessageBox.critical(self, _("export_error_title"), str(e))

    def export_docx(self):
        fpath, selected_filter = QFileDialog.getSaveFileName(
            self,
            _("menu_file_export_docx"),
            "",
            "Word Document (*.docx)"
        )
        if fpath:
            fpath = self._ensure_extension(fpath, "*.docx", ".docx")
            try:
                DocumentManager.save_file(fpath, self.editor.document)
                QMessageBox.information(self, _("export_success_title"), _("export_success_text", path=fpath))
            except Exception as e:
                QMessageBox.critical(self, _("export_error_title"), str(e))

    def export_markdown(self):
        fpath, selected_filter = QFileDialog.getSaveFileName(
            self,
            _("menu_file_export_md"),
            "",
            "Markdown Document (*.md)"
        )
        if fpath:
            fpath = self._ensure_extension(fpath, "*.md", ".md")
            try:
                DocumentManager.save_file(fpath, self.editor.document)
                QMessageBox.information(self, _("export_success_title"), _("export_success_text", path=fpath))
            except Exception as e:
                QMessageBox.critical(self, _("export_error_title"), str(e))

    def export_html(self):
        fpath, selected_filter = QFileDialog.getSaveFileName(
            self,
            _("menu_file_export_html"),
            "",
            "HTML Document (*.html)"
        )
        if fpath:
            fpath = self._ensure_extension(fpath, "*.html", ".html")
            try:
                DocumentManager.save_file(fpath, self.editor.document)
                QMessageBox.information(self, _("export_success_title"), _("export_success_text", path=fpath))
            except Exception as e:
                QMessageBox.critical(self, _("export_error_title"), str(e))

    def _maybe_save_changes(self):
        if not self.is_modified:
            return True
        doc_name = os.path.basename(self.current_filepath) if self.current_filepath else _("untitled_document")
        ret = QMessageBox.question(
            self,
            _("dlg_save_changes_title"),
            _("dlg_save_changes_text", name=doc_name),
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        if ret == QMessageBox.StandardButton.Save:
            return self.file_save()
        elif ret == QMessageBox.StandardButton.Discard:
            return True
        return False

    def closeEvent(self, event):
        if self.stack.currentIndex() == 0:
            event.accept()
            return
        if self._maybe_save_changes():
            event.accept()
        else:
            event.ignore()

    def retranslate_ui(self):
        self.lbl_ai_status.setText("✨ " + _("status_ai_ready"))
        self.lbl_dict_status.setText("🎙️ " + _("status_dictation_idle"))
        self._update_lang_toggle_btn()
        self._update_lang_menu_actions()

        self.menu_file.setTitle(_("menu_file"))
        self.act_start_page.setText(_("menu_file_start_page"))
        self.act_new.setText(_("menu_file_new"))
        self.act_open.setText(_("menu_file_open"))
        self.menu_recent.setTitle(_("menu_file_recent"))
        self.act_save.setText(_("menu_file_save"))
        self.act_save_as.setText(_("menu_file_save_as"))
        self.act_print.setText(_("menu_file_print"))
        self.act_print_prev.setText(_("menu_file_print_preview"))
        self.act_exp_pdf.setText(_("menu_file_export_pdf"))
        self.act_exp_docx.setText(_("menu_file_export_docx"))
        self.act_exp_md.setText(_("menu_file_export_md"))
        self.act_exp_html.setText(_("menu_file_export_html"))
        self.act_exit.setText(_("menu_file_exit"))

        self.menu_edit.setTitle(_("menu_edit"))
        self.act_undo.setText(_("menu_edit_undo"))
        self.act_redo.setText(_("menu_edit_redo"))
        self.act_cut.setText(_("menu_edit_cut"))
        self.act_copy.setText(_("menu_edit_copy"))
        self.act_paste.setText(_("menu_edit_paste"))
        self.act_select_all.setText(_("menu_edit_select_all"))

        self.menu_view.setTitle(_("menu_view"))
        self.act_view_sidebar.setText(_("menu_view_ai_sidebar"))
        self.act_view_focus.setText(_("menu_view_focus_mode"))
        self.act_zoom_in.setText(_("menu_view_zoom_in"))
        self.act_zoom_out.setText(_("menu_view_zoom_out"))
        self.act_zoom_reset.setText(_("menu_view_zoom_reset"))
        self.menu_language.setTitle("🌐 " + _("menu_view_language"))
        self.act_lang_sv.setText(_("lang_sv"))
        self.act_lang_en.setText(_("lang_en"))

        self.menu_insert.setTitle(_("menu_insert"))
        self.act_ins_table.setText("📊 " + _("menu_insert_table"))
        self.act_ins_divider.setText("─ " + _("menu_insert_horizontal_rule"))
        self.menu_ins_callout.setTitle("💡 " + _("tb_callout"))
        self.act_callout_info.setText(_("tb_callout_info"))
        self.act_callout_tip.setText(_("tb_callout_tip"))
        self.act_callout_warning.setText(_("tb_callout_warning"))
        self.act_callout_quote.setText(_("tb_callout_quote"))

        self.menu_format.setTitle(_("menu_format"))
        self.act_fmt_bold.setText(_("menu_format_bold"))
        self.act_fmt_italic.setText(_("menu_format_italic"))
        self.act_fmt_underline.setText(_("menu_format_underline"))
        self.act_fmt_strike.setText(_("menu_format_strikethrough"))
        self.act_fmt_sub.setText(_("tb_subscript"))
        self.act_fmt_super.setText(_("tb_superscript"))
        self.act_fmt_clear.setText(_("menu_format_clear"))
        self.act_gfonts.setText("🌐 " + _("menu_format_google_fonts"))

        self.menu_ai.setTitle(_("menu_ai"))
        self.act_inline_ai.setText(_("menu_ai_inline"))
        self.act_review_ai.setText(_("menu_ai_review"))
        self.act_dictation.setText(_("menu_ai_dictation"))
        self.act_settings.setText(_("menu_ai_settings"))

        self.menu_help.setTitle(_("menu_help"))
        self.act_about.setText(_("menu_help_about"))

        self._update_recent_menu()
        self._update_window_title()

    def apply_theme(self):
        self.theme_mgr.apply_theme_to_app()
