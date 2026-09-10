"""
ui/research_dialog.py — hämta information in i dokumentet.

Tre lägen: fråga modellen, hämta en webbsida, eller sök via en egen
SearXNG-instans. Resultatet kan infogas vid markören, med eller utan
källförteckning, eller sparas som en anteckning i valvet.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QTextEdit, QComboBox, QListWidget, QListWidgetItem, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import QUrl

from core.i18n import _, i18n
from core.research import ResearchWorker, looks_like_url, sources_markdown


class ResearchDialog(QDialog):
    def __init__(self, config, theme_mgr, document_text="", lang="en", vault=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.theme_mgr = theme_mgr
        self.document_text = (document_text or "")[-4000:]
        self.lang = lang
        self.vault = vault
        self.worker = None
        self.result_text = ""
        self.result_sources = []
        self.result_warnings = []
        self._with_sources = False

        self.setWindowTitle(_("research_title"))
        self.setMinimumSize(680, 620)
        self.init_ui()
        self.apply_theme()
        self.theme_mgr.theme_changed.connect(self.apply_theme)
        i18n.language_changed.connect(self.retranslate_ui)
        self._update_mode_hint()

    # ------------------------------------------------------------------ uppbyggnad

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.lbl_heading = QLabel("🔎 " + _("research_title"))
        self.lbl_heading.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl_heading)

        # Lägesväljare
        mode_row = QHBoxLayout()
        self.lbl_mode = QLabel(_("research_mode"))
        mode_row.addWidget(self.lbl_mode)
        self.combo_mode = QComboBox()
        self.combo_mode.addItem(_("research_mode_ask"), "ask")
        self.combo_mode.addItem(_("research_mode_url"), "url")
        self.combo_mode.addItem(_("research_mode_search"), "search")
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.combo_mode, 1)
        layout.addLayout(mode_row)

        # Fråga / URL
        input_row = QHBoxLayout()
        self.input_query = QLineEdit()
        self.input_query.returnPressed.connect(self._start)
        input_row.addWidget(self.input_query, 1)
        self.btn_run = QPushButton("▶ " + _("research_btn_run"))
        self.btn_run.clicked.connect(self._start)
        input_row.addWidget(self.btn_run)
        layout.addLayout(input_row)

        self.lbl_hint = QLabel("")
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.lbl_hint)

        # Status
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(3)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.lbl_status)

        # Resultat
        self.lbl_result = QLabel(_("research_result"))
        self.lbl_result.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(self.lbl_result)

        self.box_result = QTextEdit()
        self.box_result.setReadOnly(True)
        layout.addWidget(self.box_result, 1)

        # Källor
        self.lbl_sources = QLabel(_("research_sources"))
        self.lbl_sources.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(self.lbl_sources)

        self.list_sources = QListWidget()
        self.list_sources.setFixedHeight(96)
        self.list_sources.itemDoubleClicked.connect(self._open_source)
        layout.addWidget(self.list_sources)

        # Åtgärder
        actions = QHBoxLayout()
        self.btn_insert = QPushButton("↓ " + _("research_btn_insert"))
        self.btn_insert.clicked.connect(lambda: self._finish(insert=True, with_sources=False))
        self.btn_insert_src = QPushButton("↓ " + _("research_btn_insert_sources"))
        self.btn_insert_src.clicked.connect(lambda: self._finish(insert=True, with_sources=True))
        self.btn_save_note = QPushButton("🗒 " + _("research_btn_save_note"))
        self.btn_save_note.clicked.connect(self._save_as_note)
        self.btn_close = QPushButton(_("research_btn_close"))
        self.btn_close.clicked.connect(self.reject)

        for b in (self.btn_insert, self.btn_insert_src, self.btn_save_note):
            b.setEnabled(False)
            actions.addWidget(b)
        actions.addStretch()
        actions.addWidget(self.btn_close)
        layout.addLayout(actions)

        self._inserted = False

    # ------------------------------------------------------------------ lägen

    def _mode(self) -> str:
        return self.combo_mode.currentData() or "ask"

    def _on_mode_changed(self):
        self._update_mode_hint()

    def _update_mode_hint(self):
        mode = self._mode()
        searxng = self.config.get("research_searxng_url", "")
        if mode == "ask":
            self.input_query.setPlaceholderText(_("research_ph_ask"))
            self.lbl_hint.setText("⚠ " + _("research_hint_ask"))
        elif mode == "url":
            self.input_query.setPlaceholderText(_("research_ph_url"))
            self.lbl_hint.setText(_("research_hint_url"))
        else:
            self.input_query.setPlaceholderText(_("research_ph_search"))
            if searxng:
                self.lbl_hint.setText(_("research_hint_search", url=searxng))
            else:
                self.lbl_hint.setText("⚠ " + _("research_no_searxng"))

    # ------------------------------------------------------------------ körning

    def _start(self):
        if self.worker is not None and self.worker.isRunning():
            return

        query = self.input_query.text().strip()
        mode = self._mode()
        urls = []

        if not query:
            self._set_status("⚠ " + _("research_need_input"), error=True)
            return

        if mode == "search" and not self.config.get("research_searxng_url", ""):
            self._set_status("⚠ " + _("research_no_searxng"), error=True)
            return

        if mode == "url":
            # Tillåt flera URL:er separerade med mellanslag eller komma
            raw = query.replace(",", " ").split()
            urls = [u for u in raw if looks_like_url(u)]
            if not urls:
                self._set_status("⚠ " + _("research_bad_url"), error=True)
                return
            query = urls[0]
        elif mode == "ask" and looks_like_url(query):
            # Användaren klistrade in en URL i frågeläget — byt automatiskt
            mode = "url"
            urls = [query]
            self.combo_mode.setCurrentIndex(1)

        self.result_text = ""
        self.result_sources = []
        self.result_warnings = []
        self.box_result.clear()
        self.list_sources.clear()
        for b in (self.btn_insert, self.btn_insert_src, self.btn_save_note):
            b.setEnabled(False)

        self.progress.setVisible(True)
        self.btn_run.setEnabled(False)
        self._set_status("✨ " + _("research_working"))

        self.worker = ResearchWorker(
            self.config, query, mode=mode, urls=urls,
            document_context=self.document_text[:2000], lang=self.lang
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_progress(self, what):
        self._set_status(f"⏳ {_('research_fetching')} {what[:60]}")

    def _on_finished(self, data):
        self.progress.setVisible(False)
        self.btn_run.setEnabled(True)

        self.result_text = data.get("text", "")
        self.result_sources = data.get("sources", [])
        self.result_warnings = data.get("warnings", [])

        self.box_result.setMarkdown(self.result_text)

        for i, s in enumerate(self.result_sources, 1):
            title = s.get("title") or s.get("url") or ""
            url = s.get("url") or ""
            item = QListWidgetItem(f"[{i}] {title}")
            item.setData(Qt.ItemDataRole.UserRole, url)
            item.setToolTip(url)
            self.list_sources.addItem(item)

        if not self.result_sources:
            self.lbl_sources.setText("⚠ " + _("research_no_sources_warn"))
        else:
            self.lbl_sources.setText(_("research_sources"))

        status = _("research_done")
        if self.result_warnings:
            status += "  ⚠ " + " · ".join(self.result_warnings[:2])
        self._set_status(status)

        has_text = bool(self.result_text.strip())
        for b in (self.btn_insert, self.btn_insert_src):
            b.setEnabled(has_text)
        self.btn_save_note.setEnabled(has_text and self.vault is not None)

    def _on_failed(self, message):
        self.progress.setVisible(False)
        self.btn_run.setEnabled(True)
        self._set_status("✕ " + _("research_failed") + ": " + message, error=True)

    def _set_status(self, text, error=False):
        c = self.theme_mgr.current
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(
            f"font-size: 11px; color: {'#ef4444' if error else c['text_muted']};"
        )

    def _open_source(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            QDesktopServices.openUrl(QUrl(url))

    # ------------------------------------------------------------------ utdata

    def _full_text(self, with_sources: bool) -> str:
        text = self.result_text
        if with_sources and self.result_sources:
            text += "\n" + sources_markdown(self.result_sources)
        return text

    def _finish(self, insert=True, with_sources=False):
        self._inserted = bool(insert)
        self._with_sources = bool(with_sources)
        self.accept()

    def _save_as_note(self):
        if self.vault is None or not self.result_text.strip():
            return
        from PyQt6.QtWidgets import QInputDialog
        default = self.input_query.text().strip()[:60] or _("research_note_default_title")
        title, ok = QInputDialog.getText(self, _("research_btn_save_note"),
                                         _("notes_new_prompt"), text=default)
        if not ok or not title.strip():
            return
        body = self.result_text + "\n" + sources_markdown(self.result_sources)
        note = self.vault.create_note(title.strip(), content=f"# {title.strip()}\n\n{body}")
        if note is not None:
            self._set_status("✓ " + _("research_saved_note", title=note.title))

    def inserted_text(self) -> str:
        return self._full_text(with_sources=getattr(self, "_with_sources", False))

    # ------------------------------------------------------------------ utseende

    def retranslate_ui(self):
        self.setWindowTitle(_("research_title"))
        self.lbl_heading.setText("🔎 " + _("research_title"))
        self.lbl_mode.setText(_("research_mode"))
        self.lbl_result.setText(_("research_result"))
        self.lbl_sources.setText(_("research_sources"))
        self.btn_run.setText("▶ " + _("research_btn_run"))
        self.btn_insert.setText("↓ " + _("research_btn_insert"))
        self.btn_insert_src.setText("↓ " + _("research_btn_insert_sources"))
        self.btn_save_note.setText("🗒 " + _("research_btn_save_note"))
        self.btn_close.setText(_("research_btn_close"))
        self.combo_mode.setItemText(0, _("research_mode_ask"))
        self.combo_mode.setItemText(1, _("research_mode_url"))
        self.combo_mode.setItemText(2, _("research_mode_search"))
        self._update_mode_hint()

    def apply_theme(self):
        c = self.theme_mgr.current
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c["dialog_bg"]}; color: {c["text_color"]}; }}
            QLabel {{ color: {c["text_color"]}; background: transparent; }}
            QLineEdit, QComboBox, QTextEdit, QListWidget {{
                background-color: {c["canvas_bg"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
            }}
            QListWidget {{ font-size: 11px; padding: 2px; }}
            QPushButton {{
                background-color: {c["btn_bg"]};
                color: {c["btn_text"]};
                border: 1px solid {c["btn_border"]};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {c["btn_hover"]};
                border-color: {c["accent"]};
            }}
            QPushButton:pressed {{ background-color: {c["btn_active"]}; }}
            QPushButton:disabled {{ color: {c["text_muted"]}; }}
            QProgressBar {{ border: none; background-color: {c["canvas_border"]}; border-radius: 1px; }}
            QProgressBar::chunk {{ background-color: {c["accent"]}; border-radius: 1px; }}
        """)
