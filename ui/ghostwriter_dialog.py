"""
ui/ghostwriter_dialog.py — skriv vidare när det tar stopp.

Fyra lägen: fortsätt, bygg ut ett utkast, föreslå riktningar, eller ställ
frågor som låser upp. De tre första ger flera varianter att välja mellan —
tanken är att man ska välja riktning, inte förkasta ett enskilt förslag.

Röstreferensen kan hämtas från en anteckning i valvet, så att fortsättningen
matchar hur användaren skriver i allmänhet och inte bara det här dokumentet.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QCheckBox, QProgressBar, QFrame, QScrollArea, QWidget,
    QButtonGroup, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.i18n import _, i18n
from core.ghostwriter import GhostwriterWorker, StyleProfile


class GhostwriterDialog(QDialog):
    """Genererar fortsättningar i användarens egen röst."""

    insert_requested = pyqtSignal(str)

    MODES = ("continue", "expand", "angle", "unstick")

    def __init__(self, config, theme_mgr, document_text="", lang="en",
                 vault=None, parent=None, preset_mode=None):
        super().__init__(parent)
        self.config = config
        self.theme_mgr = theme_mgr
        self.document_text = document_text or ""
        self.lang = lang
        self.vault = vault
        self.worker = None
        self.reference_text = ""
        self.variants = []

        self.setWindowTitle(_("ghost_title"))
        self.setMinimumSize(720, 660)
        self.init_ui()
        self.apply_theme()
        self.theme_mgr.theme_changed.connect(self.apply_theme)
        i18n.language_changed.connect(self.retranslate_ui)
        if preset_mode in self.mode_buttons:
            self.mode_buttons[preset_mode].setChecked(True)
        self._on_mode_changed()
        self._load_reference_options()
        if preset_mode:
            # Den som valde "skapa stycke" vill skriva sin instruktion direkt
            self.input_instruction.setFocus()

    # ------------------------------------------------------------------ uppbyggnad

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.lbl_heading = QLabel("👻 " + _("ghost_title"))
        self.lbl_heading.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl_heading)

        self.lbl_sub = QLabel(_("ghost_subtitle"))
        self.lbl_sub.setWordWrap(True)
        self.lbl_sub.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.lbl_sub)

        # Lägesknappar
        mode_row = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_buttons = {}
        for key in self.MODES:
            btn = QPushButton(_(f"ghost_mode_{key}"))
            btn.setCheckable(True)
            btn.setToolTip(_(f"ghost_mode_{key}_hint"))
            btn.clicked.connect(self._on_mode_changed)
            self.mode_group.addButton(btn)
            mode_row.addWidget(btn)
            self.mode_buttons[key] = btn
        self.mode_buttons["continue"].setChecked(True)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Instruktion
        self.lbl_instruction = QLabel(_("ghost_instruction"))
        layout.addWidget(self.lbl_instruction)
        self.input_instruction = QLineEdit()
        self.input_instruction.setPlaceholderText(_("ghost_instruction_ph"))
        self.input_instruction.returnPressed.connect(self._start)
        layout.addWidget(self.input_instruction)

        # Röstreferens
        ref_row = QHBoxLayout()
        self.lbl_ref = QLabel(_("ghost_style_ref"))
        ref_row.addWidget(self.lbl_ref)
        self.combo_ref = QComboBox()
        self.combo_ref.currentIndexChanged.connect(self._on_ref_changed)
        ref_row.addWidget(self.combo_ref, 1)
        self.btn_ref_file = QPushButton("📂")
        self.btn_ref_file.setFixedWidth(30)
        self.btn_ref_file.setToolTip(_("ghost_style_ref_file"))
        self.btn_ref_file.clicked.connect(self._pick_reference_file)
        ref_row.addWidget(self.btn_ref_file)
        layout.addLayout(ref_row)

        self.lbl_ref_info = QLabel("")
        self.lbl_ref_info.setStyleSheet("font-size: 10px;")
        self.lbl_ref_info.setWordWrap(True)
        layout.addWidget(self.lbl_ref_info)

        # Kör
        run_row = QHBoxLayout()
        self.btn_run = QPushButton("✍ " + _("ghost_btn_generate"))
        self.btn_run.clicked.connect(self._start)
        run_row.addWidget(self.btn_run)
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

        # Resultat
        self.lbl_result = QLabel(_("ghost_result"))
        self.lbl_result.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(self.lbl_result)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.cards_host = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()
        self.scroll_area.setWidget(self.cards_host)
        layout.addWidget(self.scroll_area, 1)

        # Sidfot
        foot = QHBoxLayout()
        self.btn_insert_all = QPushButton("↓ " + _("ghost_btn_insert_all"))
        self.btn_insert_all.clicked.connect(self._insert_all)
        self.btn_insert_all.setEnabled(False)
        foot.addWidget(self.btn_insert_all)
        foot.addStretch()
        self.btn_close = QPushButton(_("ghost_btn_close"))
        self.btn_close.clicked.connect(self.reject)
        foot.addWidget(self.btn_close)
        layout.addLayout(foot)

    # ------------------------------------------------------------------ läge

    def _mode(self) -> str:
        for key, btn in self.mode_buttons.items():
            if btn.isChecked():
                return key
        return "continue"

    def _on_mode_changed(self):
        mode = self._mode()
        is_unstick = mode == "unstick"
        self.input_instruction.setVisible(not is_unstick)
        self.lbl_instruction.setVisible(not is_unstick)
        hint = _(f"ghost_mode_{mode}_hint")
        self.lbl_status.setText(hint)
        self.lbl_status.setStyleSheet(f"font-size: 11px; color: {self.theme_mgr.current['text_muted']};")

    # ------------------------------------------------------------------ röstreferens

    def _load_reference_options(self):
        self.combo_ref.blockSignals(True)
        self.combo_ref.clear()
        self.combo_ref.addItem(_("ghost_ref_current_doc"), "__doc__")
        if self.vault is not None:
            self.vault.scan_if_stale(10.0)
            for note in self.vault.notes[:80]:
                self.combo_ref.addItem(f"🗒 {note.title}", note.path)
        self.combo_ref.addItem(_("ghost_ref_pick_file"), "__file__")
        self.combo_ref.blockSignals(False)
        self._on_ref_changed()

    def _on_ref_changed(self):
        data = self.combo_ref.currentData()
        if data == "__doc__":
            self.reference_text = ""
            self._describe_reference(_("ghost_ref_current_doc"))
        elif data == "__file__":
            self.reference_text = ""
        elif isinstance(data, str):
            try:
                with open(data, "r", encoding="utf-8", errors="replace") as f:
                    self.reference_text = f.read(6000)
                self._describe_reference(os.path.basename(data))
            except Exception as e:
                self.reference_text = ""
                self.lbl_ref_info.setText("⚠ " + str(e))

    def _describe_reference(self, label):
        """Visar uppmätt stil för referensen så att den går att kontrollera."""
        source = self.reference_text or self.document_text
        profile = StyleProfile.analyze(source, self.lang)
        if not profile:
            self.lbl_ref_info.setText("")
            return
        desc = StyleProfile.describe(profile, self.lang)
        self.lbl_ref_info.setText(f"{label} — {desc}")

    def _pick_reference_file(self):
        start = self.vault.root if self.vault is not None else os.path.expanduser("~")
        path, _f = QFileDialog.getOpenFileName(
            self, _("ghost_style_ref_file"), start,
            "Text (*.md *.txt *.html *.docx);;Alla filer (*.*)"
        )
        if not path:
            return
        try:
            if path.lower().endswith(".docx"):
                import docx
                doc = docx.Document(path)
                self.reference_text = "\n".join(p.text for p in doc.paragraphs)[:6000]
            else:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    self.reference_text = f.read(6000)
            self._describe_reference(os.path.basename(path))
        except Exception as e:
            self.lbl_ref_info.setText("⚠ " + str(e))

    # ------------------------------------------------------------------ körning

    def _start(self):
        if self.worker is not None and self.worker.isRunning():
            return
        if not self.document_text.strip() and not self.input_instruction.text().strip():
            self._set_status("⚠ " + _("ghost_need_text"), error=True)
            return

        self._clear_cards()
        self.variants = []
        self.btn_insert_all.setEnabled(False)
        self.progress.setVisible(True)
        self.btn_run.setEnabled(False)
        self._set_status("✨ " + _("ghost_working"))

        self.worker = GhostwriterWorker(
            self.config,
            mode=self._mode(),
            document_text=self.document_text,
            instruction=self.input_instruction.text().strip(),
            reference_text=self.reference_text,
            lang=self.lang,
            variants=3,
        )
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_finished(self, data):
        self.progress.setVisible(False)
        self.btn_run.setEnabled(True)
        self.variants = data.get("variants", [])
        mode = data.get("mode", "continue")

        if not self.variants:
            self._set_status("⚠ " + _("ghost_empty"), error=True)
            return

        self._set_status("✓ " + _("ghost_done", n=len(self.variants)))
        for i, text in enumerate(self.variants, 1):
            self._add_card(i, text, mode)
        if len(self.variants) > 1:
            self.btn_insert_all.setEnabled(True)

    def _on_failed(self, message):
        self.progress.setVisible(False)
        self.btn_run.setEnabled(True)
        self._set_status("✕ " + message, error=True)

    def _add_card(self, index, text, mode):
        c = self.theme_mgr.current
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c["sidebar_card"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 6px;
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 8, 10, 8)
        cl.setSpacing(6)

        header = QHBoxLayout()
        lbl = QLabel(f"<b>{_('ghost_variant', n=index)}</b>")
        header.addWidget(lbl)
        header.addStretch()

        btn_insert = QPushButton("↓ " + _("ghost_btn_insert"))
        btn_insert.setFixedHeight(22)
        btn_insert.clicked.connect(lambda _c, t=text: self._insert_one(t))
        header.addWidget(btn_insert)

        btn_copy = QPushButton("📋")
        btn_copy.setFixedHeight(22)
        btn_copy.setToolTip(_("ghost_btn_copy"))
        btn_copy.clicked.connect(lambda _c, t=text: self._copy(t))
        header.addWidget(btn_copy)
        cl.addLayout(header)

        body = QTextEdit()
        body.setReadOnly(True)
        body.setPlainText(text)
        body.setMinimumHeight(110)
        body.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c["canvas_bg"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                font-size: 12px;
                padding: 6px;
            }}
        """)
        cl.addWidget(body)

        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _clear_cards(self):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    # ------------------------------------------------------------------ utdata

    def _insert_one(self, text):
        self.insert_requested.emit(text)

    def _insert_all(self):
        if self.variants:
            joined = "\n\n".join(v.strip() for v in self.variants if v.strip())
            self.insert_requested.emit(joined)

    def _copy(self, text):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)

    def _set_status(self, text, error=False):
        c = self.theme_mgr.current
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(
            f"font-size: 11px; color: {'#ef4444' if error else c['text_muted']};"
        )

    # ------------------------------------------------------------------ utseende

    def retranslate_ui(self):
        self.setWindowTitle(_("ghost_title"))
        self.lbl_heading.setText("👻 " + _("ghost_title"))
        self.lbl_sub.setText(_("ghost_subtitle"))
        self.lbl_instruction.setText(_("ghost_instruction"))
        self.input_instruction.setPlaceholderText(_("ghost_instruction_ph"))
        self.lbl_ref.setText(_("ghost_style_ref"))
        self.lbl_result.setText(_("ghost_result"))
        self.btn_run.setText("✍ " + _("ghost_btn_generate"))
        self.btn_insert_all.setText("↓ " + _("ghost_btn_insert_all"))
        self.btn_close.setText(_("ghost_btn_close"))
        for key, btn in self.mode_buttons.items():
            btn.setText(_(f"ghost_mode_{key}"))
            btn.setToolTip(_(f"ghost_mode_{key}_hint"))

    def apply_theme(self):
        c = self.theme_mgr.current
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c["dialog_bg"]}; color: {c["text_color"]}; }}
            QLabel {{ color: {c["text_color"]}; background: transparent; }}
            QLineEdit, QComboBox {{
                background-color: {c["canvas_bg"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 12px;
            }}
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
            QPushButton:checked {{
                background-color: {c["accent"]};
                color: {c["accent_text"]};
                border-color: {c["accent"]};
                font-weight: bold;
            }}
            QPushButton:pressed {{ background-color: {c["btn_active"]}; }}
            QPushButton:disabled {{ color: {c["text_muted"]}; }}
            QScrollArea, QWidget#qt_scrollarea_viewport {{ background: transparent; }}
            QProgressBar {{ border: none; background-color: {c["canvas_border"]}; border-radius: 1px; }}
            QProgressBar::chunk {{ background-color: {c["accent"]}; border-radius: 1px; }}
        """)
