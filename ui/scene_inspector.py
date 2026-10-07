"""ui/scene_inspector.py — scenens uppgifter: synopsis, status, etiketter, mål.

Panelen äger ingen data. MainWindow skapar den, säger till vilken scen som är
öppen med set_scene() och sparar det som ändras. Panelen rör aldrig texten.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QComboBox, QFormLayout, QLabel, QLineEdit, QPlainTextEdit, QSpinBox,
    QVBoxLayout, QWidget,
)

from core.i18n import _, i18n


class SceneInspector(QWidget):
    """Redigerar metadata för den scen som är öppen."""

    meta_changed = pyqtSignal()          # något ändrades, spara manifestet

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.node = None
        self._loading = False            # hindrar att ifyllning ser ut som en ändring

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self.lbl_hint = QLabel(_("scene_no_project"))
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.lbl_hint)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(6)
        layout.addLayout(form)

        self.input_title = QLineEdit()
        self.input_title.editingFinished.connect(self._apply_title)
        form.addRow(_("scene_title"), self.input_title)

        self.input_synopsis = QPlainTextEdit()
        self.input_synopsis.setPlaceholderText(_("scene_synopsis_hint"))
        self.input_synopsis.setFixedHeight(72)
        # Synopsis skrivs i ett svep — spara en stund efter sista tangenten.
        self._synopsis_timer = QTimer(self)
        self._synopsis_timer.setSingleShot(True)
        self._synopsis_timer.setInterval(600)
        self._synopsis_timer.timeout.connect(self._apply_synopsis)
        self.input_synopsis.textChanged.connect(self._on_synopsis_edited)
        form.addRow(_("scene_synopsis"), self.input_synopsis)

        self.combo_status = QComboBox()
        self.combo_status.setEditable(True)
        self.combo_status.currentTextChanged.connect(self._apply_status)
        form.addRow(_("scene_status"), self.combo_status)

        self.input_labels = QLineEdit()
        self.input_labels.setPlaceholderText(_("scene_labels_hint"))
        self.input_labels.editingFinished.connect(self._apply_labels)
        form.addRow(_("scene_labels"), self.input_labels)

        self.input_pov = QLineEdit()
        self.input_pov.editingFinished.connect(self._apply_pov)
        form.addRow(_("scene_pov"), self.input_pov)

        self.spin_target = QSpinBox()
        self.spin_target.setRange(0, 500_000)
        self.spin_target.setSingleStep(100)
        self.spin_target.setSpecialValueText(_("scene_target_none"))
        self.spin_target.valueChanged.connect(self._apply_target)
        form.addRow(_("scene_target"), self.spin_target)

        self.spin_revision = QSpinBox()
        self.spin_revision.setRange(1, 9)
        self.spin_revision.valueChanged.connect(self._apply_revision)
        form.addRow(_("scene_revision"), self.spin_revision)

        self.lbl_words = QLabel("")
        self.lbl_words.setWordWrap(True)
        layout.addWidget(self.lbl_words)
        layout.addStretch(1)

        i18n.language_changed.connect(self.retranslate_ui)
        self.set_scene(None, None)

    # ------------------------------------------------------------------- data

    def set_scene(self, project, node) -> None:
        """Fyller panelen från noden. project=None eller node=None tömmer den."""
        self.project = project
        self.node = node
        self._loading = True
        try:
            has = project is not None and node is not None
            for widget in (self.input_title, self.input_synopsis, self.combo_status,
                           self.input_labels, self.input_pov, self.spin_target,
                           self.spin_revision):
                widget.setEnabled(has)
            self.lbl_hint.setVisible(not has)
            if not has:
                self.input_title.clear()
                self.input_synopsis.setPlainText("")
                self.input_labels.clear()
                self.input_pov.clear()
                self.lbl_words.setText("")
                return
            self.input_title.setText(node.title)
            self.input_synopsis.setPlainText(node.synopsis)
            statuses = list(project.settings.get("statuses") or [])
            self.combo_status.clear()
            self.combo_status.addItem("")
            for status in statuses:
                self.combo_status.addItem(status)
            self.combo_status.setCurrentText(node.status)
            self.input_labels.setText(", ".join(node.labels))
            self.input_pov.setText(node.pov)
            self.spin_target.setValue(int(node.target_words or 0))
            self.spin_revision.setValue(int(node.revision or 1))
            self._update_words()
        finally:
            self._loading = False

    def refresh_words(self) -> None:
        self._update_words()

    def _update_words(self) -> None:
        if self.project is None or self.node is None:
            return
        words = self.project.words(self.node.id)
        target = int(self.node.target_words or 0)
        if target:
            percent = round(words * 100 / target)
            self.lbl_words.setText(_("scene_words_of", words=words, target=target, percent=percent))
        else:
            self.lbl_words.setText(_("scene_words", words=words))

    # --------------------------------------------------------------- ändringar

    def _apply_title(self) -> None:
        if self._loading or self.node is None:
            return
        title = self.input_title.text().strip()
        if title and title != self.node.title:
            self.node.title = title
            self.meta_changed.emit()

    def _on_synopsis_edited(self) -> None:
        if self._loading:
            return
        self._synopsis_timer.start()

    def _apply_synopsis(self) -> None:
        if self._loading or self.node is None:
            return
        text = self.input_synopsis.toPlainText()
        if text != self.node.synopsis:
            self.node.synopsis = text
            self.meta_changed.emit()

    def _apply_status(self, value) -> None:
        if self._loading or self.node is None:
            return
        value = (value or "").strip()
        if value != self.node.status:
            self.node.status = value
            if value and value not in self.project.settings["statuses"]:
                self.project.settings["statuses"].append(value)
            self.meta_changed.emit()

    def _apply_labels(self) -> None:
        if self._loading or self.node is None:
            return
        labels = [part.strip() for part in self.input_labels.text().split(",") if part.strip()]
        if labels != self.node.labels:
            self.node.labels = labels
            self.meta_changed.emit()

    def _apply_pov(self) -> None:
        if self._loading or self.node is None:
            return
        pov = self.input_pov.text().strip()
        if pov != self.node.pov:
            self.node.pov = pov
            self.meta_changed.emit()

    def _apply_target(self, value) -> None:
        if self._loading or self.node is None:
            return
        if int(value) != int(self.node.target_words or 0):
            self.node.target_words = int(value)
            self._update_words()
            self.meta_changed.emit()

    def _apply_revision(self, value) -> None:
        if self._loading or self.node is None:
            return
        if int(value) != int(self.node.revision or 1):
            self.node.revision = int(value)
            self.meta_changed.emit()

    # ------------------------------------------------------------------ språk

    def retranslate_ui(self) -> None:
        self.lbl_hint.setText(_("scene_no_project"))
        self.input_synopsis.setPlaceholderText(_("scene_synopsis_hint"))
        self.input_labels.setPlaceholderText(_("scene_labels_hint"))
        self.spin_target.setSpecialValueText(_("scene_target_none"))
        self._update_words()
