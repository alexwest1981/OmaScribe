"""
ui/code_dialog.py — granskar och formaterar ett kodblock i dokumentet.

Visar vad koden gör, vilka problem som finns och en formaterad version.
Den formaterade koden kan ersätta blocket i dokumentet eller läggas in
under det — användaren bestämmer, ingenting ändras av sig själv.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QListWidget, QListWidgetItem, QProgressBar, QFrame, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontDatabase

from core.i18n import _, i18n
from core.code_analyzer import CodeAnalysisWorker
from core import richtext

SEVERITY_COLORS = {"error": "#ef4444", "warning": "#f59e0b", "style": "#64748b"}


class CodeDialog(QDialog):
    replace_requested = pyqtSignal(str)
    insert_requested = pyqtSignal(str)

    def __init__(self, config, theme_mgr, code: str, lang: str = "",
                 doc_context: str = "", lang_ui: str = "sv", parent=None):
        super().__init__(parent)
        self.config = config
        self.theme_mgr = theme_mgr
        self.code = code
        self.lang = lang
        self.doc_context = doc_context
        self.lang_ui = lang_ui
        self.worker = None
        self.result = None

        self.setWindowTitle(_("code_title"))
        self.setMinimumSize(760, 680)
        self.init_ui()
        self.apply_theme()
        self.theme_mgr.theme_changed.connect(self.apply_theme)
        i18n.language_changed.connect(self.retranslate_ui)

    # ------------------------------------------------------------------ uppbyggnad

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.lbl_heading = QLabel("⌨ " + _("code_title"))
        self.lbl_heading.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl_heading)

        # Vad koden är
        info = QHBoxLayout()
        self.lbl_lang = QLabel(_("code_lang"))
        info.addWidget(self.lbl_lang)
        self.lbl_lang_value = QLabel(self.lang or "—")
        self.lbl_lang_value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        info.addWidget(self.lbl_lang_value)
        info.addStretch()
        layout.addLayout(info)

        self.lbl_purpose = QLabel("")
        self.lbl_purpose.setWordWrap(True)
        layout.addWidget(self.lbl_purpose)

        # Kör-knappar
        run_row = QHBoxLayout()
        self.btn_review = QPushButton("🔍 " + _("code_btn_review"))
        self.btn_review.clicked.connect(lambda: self._start(format_only=False))
        self.btn_format = QPushButton("≡ " + _("code_btn_format"))
        self.btn_format.clicked.connect(lambda: self._start(format_only=True))
        run_row.addWidget(self.btn_review)
        run_row.addWidget(self.btn_format)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(3)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)
        run_row.addWidget(self.progress, 1)
        layout.addLayout(run_row)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.lbl_status)

        # Problem
        self.lbl_issues = QLabel(_("code_issues"))
        self.lbl_issues.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(self.lbl_issues)

        self.list_issues = QListWidget()
        self.list_issues.setWordWrap(True)
        self.list_issues.setMinimumHeight(120)
        self.list_issues.itemClicked.connect(self._copy_issue)
        layout.addWidget(self.list_issues, 1)

        # Formaterad kod
        self.lbl_formatted = QLabel(_("code_formatted"))
        self.lbl_formatted.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(self.lbl_formatted)

        self.box_code = QPlainTextEdit()
        self.box_code.setReadOnly(True)
        try:
            self.box_code.setFont(QFont(richtext.mono_family(), 10))
        except Exception:
            pass
        layout.addWidget(self.box_code, 2)

        # Åtgärder
        actions = QHBoxLayout()
        self.btn_replace = QPushButton("↺ " + _("code_btn_replace"))
        self.btn_replace.clicked.connect(lambda: self._finish("replace"))
        self.btn_insert = QPushButton("↓ " + _("code_btn_insert"))
        self.btn_insert.clicked.connect(lambda: self._finish("insert"))
        self.btn_copy = QPushButton("📋 " + _("code_btn_copy"))
        self.btn_copy.clicked.connect(self._copy_code)
        self.btn_close = QPushButton(_("code_btn_close"))
        self.btn_close.clicked.connect(self.reject)
        for b in (self.btn_replace, self.btn_insert, self.btn_copy):
            b.setEnabled(False)
            actions.addWidget(b)
        actions.addStretch()
        actions.addWidget(self.btn_close)
        layout.addLayout(actions)

    # ------------------------------------------------------------------ körning

    def _start(self, format_only: bool):
        if self.worker is not None and self.worker.isRunning():
            return
        self.progress.setVisible(True)
        self.btn_review.setEnabled(False)
        self.btn_format.setEnabled(False)
        self._set_status("✨ " + _("code_working"))

        self.worker = CodeAnalysisWorker(
            self.config, self.code, self.lang, self.doc_context,
            self.lang_ui, format_only=format_only)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_finished(self, data):
        self.result = data
        self.progress.setVisible(False)
        self.btn_review.setEnabled(True)
        self.btn_format.setEnabled(True)

        if data.get("language"):
            self.lbl_lang_value.setText(data["language"])
        if data.get("purpose"):
            self.lbl_purpose.setText(data["purpose"])
        elif not self.lbl_purpose.text():
            self.lbl_purpose.setText("")

        self.list_issues.clear()
        issues = data.get("issues") or []
        if not issues:
            item = QListWidgetItem("✓ " + _("code_no_issues"))
            item.setForeground(Qt.GlobalColor.gray)
            self.list_issues.addItem(item)
        for iss in issues:
            line = f"rad {iss['line']}: " if iss.get("line") else ""
            sev = iss["severity"]
            text = f"[{_('code_sev_' + sev)}] {line}{iss['message']}"
            if iss.get("suggestion"):
                text += f"\n    → {iss['suggestion']}"
            item = QListWidgetItem(text)
            item.setForeground(Qt.GlobalColor.gray)
            item.setData(Qt.ItemDataRole.UserRole, iss)
            self.list_issues.addItem(item)

        formatted = data.get("formatted") or ""
        self.box_code.setPlainText(formatted if formatted else self.code)

        counts = data.get("counts", {})
        parts = [f"{counts.get('error', 0)} {_('code_sev_error')}",
                 f"{counts.get('warning', 0)} {_('code_sev_warning')}",
                 f"{counts.get('style', 0)} {_('code_sev_style')}"]
        status = "✓ " + " · ".join(parts)
        if not data.get("changed"):
            status += "  —  " + _("code_unchanged")
        self._set_status(status)

        has_code = bool(formatted.strip())
        for b in (self.btn_replace, self.btn_insert, self.btn_copy):
            b.setEnabled(has_code)
        self.btn_replace.setEnabled(has_code)

    def _on_failed(self, message):
        self.progress.setVisible(False)
        self.btn_review.setEnabled(True)
        self.btn_format.setEnabled(True)
        self._set_status("✕ " + _("code_failed") + ": " + message, error=True)

    def _set_status(self, text, error=False):
        c = self.theme_mgr.current
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(
            f"font-size: 11px; color: {'#ef4444' if error else c['text_muted']};")

    # ------------------------------------------------------------------ utdata

    def _copy_issue(self, item):
        iss = item.data(Qt.ItemDataRole.UserRole)
        if not iss:
            return
        text = iss.get("message", "")
        if iss.get("suggestion"):
            text += f"\n→ {iss['suggestion']}"
        QApplication.clipboard().setText(text)

    def _copy_code(self):
        QApplication.clipboard().setText(self.box_code.toPlainText())

    def _finish(self, action: str):
        code = self.box_code.toPlainText()
        if not code.strip():
            return
        self.setProperty("action", action)
        if action == "replace":
            self.replace_requested.emit(code)
        else:
            self.insert_requested.emit(code)
        self.accept()

    def retranslate_ui(self):
        self.setWindowTitle(_("code_title"))
        self.lbl_heading.setText("⌨ " + _("code_title"))
        self.lbl_lang.setText(_("code_lang"))
        self.lbl_issues.setText(_("code_issues"))
        self.lbl_formatted.setText(_("code_formatted"))
        self.btn_review.setText("🔍 " + _("code_btn_review"))
        self.btn_format.setText("≡ " + _("code_btn_format"))
        self.btn_replace.setText("↺ " + _("code_btn_replace"))
        self.btn_insert.setText("↓ " + _("code_btn_insert"))
        self.btn_copy.setText("📋 " + _("code_btn_copy"))
        self.btn_close.setText(_("code_btn_close"))

    def apply_theme(self):
        c = self.theme_mgr.current
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c["dialog_bg"]}; color: {c["text_color"]}; }}
            QLabel {{ color: {c["text_color"]}; background: transparent; }}
            QPlainTextEdit, QListWidget {{
                background-color: {c.get("code_bg", c["canvas_bg"])};
                color: {c.get("code_text", c["text_color"])};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 6px;
            }}
            QListWidget {{ background-color: {c["canvas_bg"]}; color: {c["text_color"]};
                           font-size: 11px; }}
            QPushButton {{
                background-color: {c["btn_bg"]};
                color: {c["btn_text"]};
                border: 1px solid {c["btn_border"]};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {c["btn_hover"]}; border-color: {c["accent"]}; }}
            QPushButton:disabled {{ color: {c["text_muted"]}; }}
            QProgressBar {{ border: none; background-color: {c["canvas_border"]}; border-radius: 1px; }}
            QProgressBar::chunk {{ background-color: {c["accent"]}; border-radius: 1px; }}
        """)
