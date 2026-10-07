"""ui/scene_inspector.py — scenens uppgifter: synopsis, status, etiketter, mål.

Panelen äger ingen data. MainWindow skapar den, säger till vilken scen som är
öppen med set_scene() och sparar det som ändras. Panelen rör aldrig texten.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMenu, QPlainTextEdit, QSpinBox, QToolButton, QVBoxLayout,
    QWidget,
)

from core.i18n import _, i18n


class SceneInspector(QWidget):
    """Redigerar metadata för den scen som är öppen."""

    meta_changed = pyqtSignal()          # något ändrades, spara manifestet
    open_node = pyqtSignal(str)          # öppna en nod (material) i editorn

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

        self.input_note = QPlainTextEdit()
        self.input_note.setPlaceholderText(_("scene_note_hint"))
        self.input_note.setFixedHeight(60)
        self._note_timer = QTimer(self)
        self._note_timer.setSingleShot(True)
        self._note_timer.setInterval(600)
        self._note_timer.timeout.connect(self._apply_note)
        self.input_note.textChanged.connect(self._on_note_edited)
        form.addRow(_("scene_note"), self.input_note)

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

        # Material: researchanteckningar som hör till scenen. Kopplingen är ett
        # id i manifestet, inte en kopia, så anteckningen ligger kvar i research.
        self.lst_material = QListWidget()
        self.lst_material.setMaximumHeight(84)
        self.lst_material.setToolTip(_("scene_material_hint"))
        self.lst_material.itemDoubleClicked.connect(self._open_material)
        form.addRow(_("scene_material"), self.lst_material)

        material_row = QHBoxLayout()
        material_row.setSpacing(2)
        self.btn_link = QToolButton()
        self.btn_link.setText("📎")
        self.btn_link.setToolTip(_("scene_material_link"))
        self.btn_link.clicked.connect(self._show_candidates)
        material_row.addWidget(self.btn_link)
        self.btn_unlink = QToolButton()
        self.btn_unlink.setText("✂️")
        self.btn_unlink.setToolTip(_("scene_material_unlink"))
        self.btn_unlink.clicked.connect(self._unlink_selected)
        material_row.addWidget(self.btn_unlink)
        material_row.addStretch(1)
        self.lbl_material = QLabel("")
        self.lbl_material.setStyleSheet("color: palette(mid);")
        material_row.addWidget(self.lbl_material)
        form.addRow("", self._wrap(material_row))

        layout.addStretch(1)

        i18n.language_changed.connect(self.retranslate_ui)
        self.set_scene(None, None)

    # ------------------------------------------------------------------- data

    @staticmethod
    def _wrap(layout) -> QWidget:
        """Lägger en rad med knappar i en widget — QFormLayout vill ha en widget."""
        holder = QWidget()
        holder.setLayout(layout)
        return holder

    def set_scene(self, project, node) -> None:
        """Fyller panelen från noden. project=None eller node=None tömmer den."""
        self.project = project
        self.node = node
        self._loading = True
        try:
            has = project is not None and node is not None
            for widget in (self.input_title, self.input_synopsis, self.input_note,
                           self.combo_status, self.input_labels, self.input_pov,
                           self.spin_target, self.spin_revision):
                widget.setEnabled(has)
            self.lbl_hint.setVisible(not has)
            if not has:
                self.input_title.clear()
                self.input_synopsis.setPlainText("")
                self.input_note.setPlainText("")
                self.input_labels.clear()
                self.input_pov.clear()
                self.lbl_words.setText("")
                return
            self.input_title.setText(node.title)
            self.input_synopsis.setPlainText(node.synopsis)
            self.input_note.setPlainText(node.note)
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
            self._refresh_material()
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

    # ------------------------------------------------------------- materialet

    def _refresh_material(self) -> None:
        """Materialet som hör till scenen, och förslagen som ännu inte gör det."""
        self.lst_material.clear()
        has = self.project is not None and self.node is not None
        self.btn_link.setEnabled(has)
        self.btn_unlink.setEnabled(has)
        if not has:
            self.lbl_material.setText("")
            return
        for note in self.project.material_for(self.node.id):
            item = QListWidgetItem(note.title)
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            item.setToolTip(_("scene_material_open"))
            self.lst_material.addItem(item)
        kvar = len(self.project.material_candidates(self.node.id))
        self.lbl_material.setText(_("scene_material_left", count=kvar) if kvar else "")

    def _show_candidates(self) -> None:
        """📎: välj bland materialet som ännu inte hör till scenen."""
        if self.project is None or self.node is None:
            return
        candidates = self.project.material_candidates(self.node.id)
        if not candidates:
            return
        menu = QMenu(self)
        for note in candidates:
            menu.addAction(note.title, lambda nid=note.id: self.link_material(nid))
        menu.exec(self.btn_link.mapToGlobal(self.btn_link.rect().bottomLeft()))

    def link_material(self, material_id: str) -> bool:
        if self.project is None or self.node is None:
            return False
        if not self.project.link_material(self.node.id, material_id):
            return False
        self._refresh_material()
        self.meta_changed.emit()
        return True

    def unlink_material(self, material_id: str) -> bool:
        if self.project is None or self.node is None:
            return False
        if not self.project.unlink_material(self.node.id, material_id):
            return False
        self._refresh_material()
        self.meta_changed.emit()
        return True

    def _unlink_selected(self) -> bool:
        item = self.lst_material.currentItem() or (
            self.lst_material.item(0) if self.lst_material.count() else None)
        if item is None:
            return False
        return self.unlink_material(item.data(Qt.ItemDataRole.UserRole))

    def _open_material(self, item) -> None:
        node_id = item.data(Qt.ItemDataRole.UserRole)
        if node_id:
            self.open_node.emit(node_id)

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

    def _on_note_edited(self) -> None:
        if self._loading:
            return
        self._note_timer.start()

    def _apply_note(self) -> None:
        """Scenanteckningen sparas som allt annat i noden — den rör inte prosan."""
        if self._loading or self.node is None:
            return
        text = self.input_note.toPlainText()
        if text != self.node.note:
            self.node.note = text
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
        self.input_note.setPlaceholderText(_("scene_note_hint"))
        self.input_labels.setPlaceholderText(_("scene_labels_hint"))
        self.spin_target.setSpecialValueText(_("scene_target_none"))
        self._update_words()
