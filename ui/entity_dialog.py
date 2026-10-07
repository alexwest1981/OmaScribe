"""
ui/entity_dialog.py — Ny entitet i projektets codex.

Bara det nödvändiga: namn, typ och en rad om vem det är. Resten av
karaktärsbladet hör till fas 2 (R03.9) — här behövs bara något att koppla en
scen till (R04.2).
"""

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QPlainTextEdit,
    QVBoxLayout,
)

from core.i18n import _, i18n
from core.storybible import ENTITY_TYPES


class EntityDialog(QDialog):
    """Namn, typ och sammanfattning för en ny entitet."""

    def __init__(self, default_name: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("entity_dialog_title"))
        self.setModal(True)
        self.resize(400, 0)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.input_name = QLineEdit(default_name)
        self.input_name.setPlaceholderText(_("entity_name_hint"))
        form.addRow(_("entity_name"), self.input_name)

        self.combo_type = QComboBox()
        for key in ENTITY_TYPES:
            self.combo_type.addItem(_(f"entity_type_{key}"), key)
        form.addRow(_("entity_type"), self.combo_type)

        self.input_summary = QPlainTextEdit()
        self.input_summary.setPlaceholderText(_("entity_summary_hint"))
        self.input_summary.setFixedHeight(64)
        form.addRow(_("entity_summary"), self.input_summary)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.input_name.setFocus()

    def values(self) -> tuple[str, str, str]:
        """(namn, typ, sammanfattning)."""
        return (
            self.input_name.text().strip(),
            self.combo_type.currentData() or ENTITY_TYPES[0],
            self.input_summary.toPlainText().strip(),
        )

    def retranslate_ui(self) -> None:
        self.setWindowTitle(_("entity_dialog_title"))
        self.input_name.setPlaceholderText(_("entity_name_hint"))
        self.input_summary.setPlaceholderText(_("entity_summary_hint"))
        for index in range(self.combo_type.count()):
            self.combo_type.setItemText(index, _(f"entity_type_{self.combo_type.itemData(index)}"))
