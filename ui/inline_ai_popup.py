from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QScrollArea, QWidget, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QColor
from core.i18n import _, i18n

class InlineAIPopup(QDialog):
    replace_requested = pyqtSignal(str)
    insert_below_requested = pyqtSignal(str)

    def __init__(self, ai_client, theme_mgr, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.ai = ai_client
        self.theme_mgr = theme_mgr
        self.selected_text = ""
        self.generated_text = ""

        self.setFixedWidth(540)
        self.init_ui()
        self.apply_theme()
        self.theme_mgr.theme_changed.connect(self.apply_theme)
        self.ai.transform_completed.connect(self._on_transform_received)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Header Title
        top = QHBoxLayout()
        lbl = QLabel(_("inline_ai_title"))
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        top.addWidget(lbl)
        top.addStretch()
        layout.addLayout(top)

        # Input Prompt Field
        input_row = QHBoxLayout()
        self.input_prompt = QLineEdit()
        self.input_prompt.setPlaceholderText(_("inline_ai_placeholder"))
        self.input_prompt.returnPressed.connect(self._on_custom_prompt)
        input_row.addWidget(self.input_prompt)

        self.btn_gen = QPushButton(_("inline_ai_btn_generate"))
        self.btn_gen.clicked.connect(self._on_custom_prompt)
        input_row.addWidget(self.btn_gen)
        layout.addLayout(input_row)

        # Quick action chips
        chip_row1 = QHBoxLayout()
        for key, text in [
            ("rephrase", _("inline_ai_opt_rephrase")),
            ("shorten", _("inline_ai_opt_shorten")),
            ("expand", _("inline_ai_opt_expand")),
            ("grammar", _("inline_ai_opt_fix_grammar"))
        ]:
            b = QPushButton(text)
            b.setFixedHeight(24)
            b.clicked.connect(lambda ch, t=text: self._on_quick_action(t))
            chip_row1.addWidget(b)
        layout.addLayout(chip_row1)

        chip_row2 = QHBoxLayout()
        for key, text in [
            ("formal", _("inline_ai_opt_tone_formal")),
            ("casual", _("inline_ai_opt_tone_casual")),
            ("translate_sv", _("inline_ai_opt_translate_sv")),
            ("translate_en", _("inline_ai_opt_translate_en"))
        ]:
            b = QPushButton(text)
            b.setFixedHeight(24)
            b.clicked.connect(lambda ch, t=text: self._on_quick_action(t))
            chip_row2.addWidget(b)
        layout.addLayout(chip_row2)

        # Result preview box (initially hidden)
        self.preview_box = QTextEdit()
        self.preview_box.setFixedHeight(120)
        self.preview_box.setVisible(False)
        layout.addWidget(self.preview_box)

        # Action Buttons (Accept / Insert / Discard)
        self.action_row = QHBoxLayout()
        self.btn_accept = QPushButton("✓ " + _("inline_ai_btn_accept"))
        self.btn_accept.clicked.connect(self._on_accept)
        self.btn_insert = QPushButton("↓ " + _("inline_ai_btn_insert_below"))
        self.btn_insert.clicked.connect(self._on_insert)
        self.btn_discard = QPushButton("✕ " + _("inline_ai_btn_discard"))
        self.btn_discard.clicked.connect(self.close)

        self.action_row.addWidget(self.btn_accept)
        self.action_row.addWidget(self.btn_insert)
        self.action_row.addWidget(self.btn_discard)
        self.action_row.addStretch()
        
        self.action_frame = QFrame()
        self.action_frame.setLayout(self.action_row)
        self.action_frame.setVisible(False)
        layout.addWidget(self.action_frame)

    def show_at(self, selected_text, pos: QPoint):
        self.selected_text = selected_text
        self.preview_box.setVisible(False)
        self.action_frame.setVisible(False)
        self.input_prompt.clear()
        self.move(pos)
        self.show()
        self.input_prompt.setFocus()

    def _on_custom_prompt(self):
        prompt = self.input_prompt.text().strip()
        if not prompt:
            return
        self.preview_box.setVisible(True)
        self.preview_box.setPlainText("✨ Thinking and crafting proposal...")
        self.ai.transform_text(self.selected_text, prompt)

    def _on_quick_action(self, instruction):
        self.input_prompt.setText(instruction)
        self.preview_box.setVisible(True)
        self.preview_box.setPlainText("✨ Thinking and crafting proposal...")
        self.ai.transform_text(self.selected_text, instruction)

    def _on_transform_received(self, text):
        self.generated_text = text
        self.preview_box.setPlainText(text)
        self.action_frame.setVisible(True)

    def _on_accept(self):
        self.replace_requested.emit(self.generated_text)
        self.close()

    def _on_insert(self):
        self.insert_below_requested.emit(self.generated_text)
        self.close()

    def apply_theme(self):
        c = self.theme_mgr.current
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c["sidebar_bg"]};
                border: 2px solid {c["accent"]};
                border-radius: 8px;
            }}
            QLineEdit {{
                background-color: {c["canvas_bg"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QPushButton {{
                background-color: {c["sidebar_card"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {c["btn_hover"]};
                border-color: {c["accent"]};
            }}
            QTextEdit {{
                background-color: {c["canvas_bg"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                font-size: 12px;
            }}
        """)
