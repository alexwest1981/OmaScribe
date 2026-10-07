"""
ui/project_dialog.py — Nytt projekt: namn, mall och ordmål.

Ett steg i stället för tre dialogrutor: mappen väljs först (den är filsystemets
sak), sedan namn, mall och ordmål här. Mallen är projektets struktur — skild
från dokumentmallarna i core/templates.py, som är färdiga texter (R01.13).
"""

from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QSpinBox, QVBoxLayout,
)

from core.i18n import _, i18n
from core.project import DEFAULT_TEMPLATE, PROJECT_TEMPLATES


class NewProjectDialog(QDialog):
    """Namn, mall och ordmål för ett nytt projekt."""

    def __init__(self, default_name: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("project_dialog_title"))
        self.setModal(True)
        self.resize(420, 0)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.input_name = QLineEdit(default_name)
        self.input_name.setPlaceholderText(_("project_name_hint"))
        form.addRow(_("project_name"), self.input_name)

        self.combo_template = QComboBox()
        for key, spec in PROJECT_TEMPLATES.items():
            self.combo_template.addItem(_(f"project_tpl_{key}"), key)
        self.combo_template.setCurrentIndex(
            max(0, self.combo_template.findData(DEFAULT_TEMPLATE)))
        self.combo_template.currentIndexChanged.connect(self._on_template_changed)
        form.addRow(_("project_template"), self.combo_template)

        self.lbl_description = QLabel("")
        self.lbl_description.setWordWrap(True)
        self.lbl_description.setStyleSheet("color: palette(mid);")
        form.addRow("", self.lbl_description)

        self.spin_target = QSpinBox()
        self.spin_target.setRange(0, 10_000_000)
        self.spin_target.setSingleStep(1000)
        self.spin_target.setSpecialValueText(_("project_target_none"))
        form.addRow(_("project_target"), self.spin_target)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._on_template_changed()
        self.input_name.setFocus()

    def _on_template_changed(self) -> None:
        """Mallens beskrivning och dess ordmål — utgångsvärden att ändra fritt."""
        key = self.combo_template.currentData()
        spec = PROJECT_TEMPLATES.get(key or "", {})
        self.lbl_description.setText(_(f"project_tpl_{key}_desc"))
        self.spin_target.setValue(int(spec.get("target_words") or 0))

    def values(self) -> tuple[str, str, int]:
        """(namn, mallnyckel, ordmål) — det new_project behöver."""
        return (
            self.input_name.text().strip(),
            self.combo_template.currentData() or DEFAULT_TEMPLATE,
            self.spin_target.value(),
        )

    def retranslate_ui(self) -> None:
        self.setWindowTitle(_("project_dialog_title"))
        self.input_name.setPlaceholderText(_("project_name_hint"))
        self.spin_target.setSpecialValueText(_("project_target_none"))
        for index in range(self.combo_template.count()):
            key = self.combo_template.itemData(index)
            self.combo_template.setItemText(index, _(f"project_tpl_{key}"))
        self._on_template_changed()
