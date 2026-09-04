import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog,
    QMessageBox, QLabel, QSplitter, QStatusBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QAction, QKeySequence, QTextCursor

from core.i18n import _, i18n
from core.doc_manager import DocumentManager
from ui.editor_view import EditorView
from ui.toolbar import FormattingToolBar
from ui.sidebar_inspector import SidebarInspector
from ui.inline_ai_popup import InlineAIPopup
from ui.settings_dialog import SettingsDialog
from ui.google_fonts_dialog import GoogleFontsDialog

class MainWindow(QMainWindow):
    def __init__(self, ai_client, dictation_engine, theme_mgr, config_mgr):
        super().__init__()
        self.ai = ai_client
        self.dictation = dictation_engine
        self.theme_mgr = theme_mgr
        self.config = config_mgr

        self.current_filepath = None
        self.is_modified = False

        self.setWindowTitle(_("app_title"))
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

        # Initial welcome sample text
        self._insert_welcome_sample()
        self._update_stats()

    def init_ui(self):
        central_widget = QWidget(self)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Editor View
        self.editor = EditorView(self.theme_mgr, self)

        # 2. Formatting Toolbar
        self.toolbar = FormattingToolBar(self.editor, self)
        self.toolbar.magic_ai_clicked.connect(lambda: self._open_inline_ai(self.editor.textCursor().selectedText(), None))
        self.toolbar.dictation_clicked.connect(self._toggle_dictation)
        self.toolbar.sidebar_toggled.connect(self._toggle_sidebar)
        self.toolbar.google_fonts_clicked.connect(self._open_google_fonts_dialog)
        self.addToolBar(self.toolbar)

        # 3. Main Splitter (Editor Canvas on Left + Sidebar Inspector on Right)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.editor)

        self.sidebar = SidebarInspector(self.ai, self.theme_mgr, self)
        self.sidebar.setVisible(self.config.get("show_ai_sidebar", True))
        self.splitter.addWidget(self.sidebar)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        root_layout.addWidget(self.splitter)
        self.setCentralWidget(central_widget)

        # 4. Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.lbl_stats = QLabel("0 words | 0 characters")
        self.lbl_cursor = QLabel("Ln 1, Col 1")
        self.lbl_ai_status = QLabel("✨ " + _("status_ai_ready"))
        self.lbl_dict_status = QLabel("🎙️ " + _("status_dictation_idle"))

        self.status_bar.addWidget(self.lbl_stats)
        self.status_bar.addPermanentWidget(self.lbl_ai_status)
        self.status_bar.addPermanentWidget(self.lbl_dict_status)
        self.status_bar.addPermanentWidget(self.lbl_cursor)

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
        self.act_new = self._add_action(self.menu_file, _("menu_file_new"), self.file_new, "Ctrl+N")
        self.act_open = self._add_action(self.menu_file, _("menu_file_open"), self.file_open, "Ctrl+O")
        self.act_save = self._add_action(self.menu_file, _("menu_file_save"), self.file_save, "Ctrl+S")
        self.act_save_as = self._add_action(self.menu_file, _("menu_file_save_as"), self.file_save_as, "Ctrl+Shift+S")
        self.menu_file.addSeparator()
        self.act_exp_pdf = self._add_action(self.menu_file, _("menu_file_export_pdf"), self.export_pdf, "Ctrl+P")
        self.act_exp_docx = self._add_action(self.menu_file, _("menu_file_export_docx"), self.export_docx)
        self.act_exp_md = self._add_action(self.menu_file, _("menu_file_export_md"), self.export_markdown)
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

        # Format Menu
        self.menu_format = mb.addMenu(_("menu_format"))
        self.act_fmt_bold = self._add_action(self.menu_format, _("menu_format_bold"), self.toolbar._toggle_bold, "Ctrl+B")
        self.act_fmt_italic = self._add_action(self.menu_format, _("menu_format_italic"), self.toolbar._toggle_italic, "Ctrl+I")
        self.act_fmt_underline = self._add_action(self.menu_format, _("menu_format_underline"), self.toolbar._toggle_underline, "Ctrl+U")
        self.act_fmt_strike = self._add_action(self.menu_format, _("menu_format_strikethrough"), self.toolbar._toggle_strike)
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

    def _insert_welcome_sample(self):
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
        doc_name = os.path.basename(self.current_filepath) if self.current_filepath else _("untitled_document")
        mod_flag = " •" if self.is_modified else ""
        self.setWindowTitle(f"{doc_name}{mod_flag} — {_('app_name')}")

    def _on_review_timer_fired(self):
        text = self.editor.document.toPlainText()
        lang = i18n.get_language()
        self.ai.review_document(text, lang=lang)

    def _on_autosave_timer_fired(self):
        if self.is_modified and self.current_filepath and self.config.get("autosave", True):
            try:
                DocumentManager.save_file(self.current_filepath, self.editor.document)
                self.is_modified = False
                self._update_window_title()
            except Exception as e:
                print(f"[Autosave] Error: {e}")

    def _open_inline_ai(self, selected_text, global_pos):
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
        self.ai.review_document(text, lang=i18n.get_language())

    def _toggle_sidebar(self):
        vis = not self.sidebar.isVisible()
        self.sidebar.setVisible(vis)
        self.config.set("show_ai_sidebar", vis)

    def _toggle_focus_mode(self):
        if self.isFullScreen():
            self.showNormal()
            self.toolbar.setVisible(True)
            self.menuBar().setVisible(True)
            self.status_bar.setVisible(True)
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
            f"<p>AI-Powered Rich Text Word-like Editor built for Linux & Omarchy with Python & Qt.</p>"
        )

    # -------------------------------------------------------------------------
    # File Operations
    # -------------------------------------------------------------------------
    def file_new(self):
        if not self._maybe_save_changes():
            return
        self.editor.document.clear()
        self.current_filepath = None
        self.is_modified = False
        self._update_window_title()

    def file_open(self):
        if not self._maybe_save_changes():
            return
        fpath, _filter = QFileDialog.getOpenFileName(
            self,
            _("menu_file_open"),
            "",
            "Documents (*.docx *.md *.markdown *.html *.htm *.txt);;Word Documents (*.docx);;Markdown (*.md);;All Files (*.*)"
        )
        if fpath:
            try:
                DocumentManager.load_file(fpath, self.editor.document)
                self.current_filepath = fpath
                self.is_modified = False
                self._update_window_title()
                self.config.add_recent_file(fpath)
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
        fpath, _filter = QFileDialog.getSaveFileName(
            self,
            _("menu_file_save_as"),
            "",
            "Word Document (*.docx);;Markdown (*.md);;HTML Document (*.html);;Plain Text (*.txt)"
        )
        if fpath:
            try:
                DocumentManager.save_file(fpath, self.editor.document)
                self.current_filepath = fpath
                self.is_modified = False
                self._update_window_title()
                self.config.add_recent_file(fpath)
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error Saving File", str(e))
        return False

    def export_pdf(self):
        fpath, _filter = QFileDialog.getSaveFileName(
            self,
            _("menu_file_export_pdf"),
            "",
            "PDF Document (*.pdf)"
        )
        if fpath:
            try:
                DocumentManager.save_file(fpath, self.editor.document)
                QMessageBox.information(self, "Export Successful", f"Document exported to:\n{fpath}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def export_docx(self):
        fpath, _filter = QFileDialog.getSaveFileName(
            self,
            _("menu_file_export_docx"),
            "",
            "Word Document (*.docx)"
        )
        if fpath:
            try:
                DocumentManager.save_file(fpath, self.editor.document)
                QMessageBox.information(self, "Export Successful", f"Document exported to:\n{fpath}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def export_markdown(self):
        fpath, _filter = QFileDialog.getSaveFileName(
            self,
            _("menu_file_export_md"),
            "",
            "Markdown Document (*.md)"
        )
        if fpath:
            try:
                DocumentManager.save_file(fpath, self.editor.document)
                QMessageBox.information(self, "Export Successful", f"Document exported to:\n{fpath}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

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
        if self._maybe_save_changes():
            event.accept()
        else:
            event.ignore()

    def retranslate_ui(self):
        self.menu_file.setTitle(_("menu_file"))
        self.act_new.setText(_("menu_file_new"))
        self.act_open.setText(_("menu_file_open"))
        self.act_save.setText(_("menu_file_save"))
        self.act_save_as.setText(_("menu_file_save_as"))
        self.act_exp_pdf.setText(_("menu_file_export_pdf"))
        self.act_exp_docx.setText(_("menu_file_export_docx"))
        self.act_exp_md.setText(_("menu_file_export_md"))
        self.act_exit.setText(_("menu_file_exit"))

        self.menu_edit.setTitle(_("menu_edit"))
        self.act_undo.setText(_("menu_edit_undo"))
        self.act_redo.setText(_("menu_edit_redo"))
        self.act_cut.setText(_("menu_edit_cut"))
        self.act_copy.setText(_("menu_edit_copy"))
        self.act_paste.setText(_("menu_edit_paste"))
        self.act_select_all.setText(_("menu_edit_select_all"))

        self.menu_format.setTitle(_("menu_format"))
        self.act_fmt_bold.setText(_("menu_format_bold"))
        self.act_fmt_italic.setText(_("menu_format_italic"))
        self.act_fmt_underline.setText(_("menu_format_underline"))
        self.act_fmt_strike.setText(_("menu_format_strikethrough"))
        self.act_gfonts.setText("🌐 " + _("menu_format_google_fonts"))

        self.menu_ai.setTitle(_("menu_ai"))
        self.act_inline_ai.setText(_("menu_ai_inline"))
        self.act_review_ai.setText(_("menu_ai_review"))
        self.act_dictation.setText(_("menu_ai_dictation"))
        self.act_settings.setText(_("menu_ai_settings"))

        self.menu_help.setTitle(_("menu_help"))
        self.act_about.setText(_("menu_help_about"))

        self._update_window_title()

    def apply_theme(self):
        self.setStyleSheet(self.theme_mgr.get_stylesheet())
