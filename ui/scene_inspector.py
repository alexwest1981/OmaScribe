"""ui/scene_inspector.py — scenens uppgifter: synopsis, status, etiketter, mål.

Panelen äger ingen data. MainWindow skapar den, säger till vilken scen som är
öppen med set_scene() och sparar det som ändras. Panelen rör aldrig texten.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMenu, QPlainTextEdit, QPushButton, QSpinBox, QToolButton,
    QVBoxLayout, QWidget,
)

from core.i18n import _, i18n
from core.project import html_to_text
from core import story_elements


class SceneInspector(QWidget):
    """Redigerar metadata för den scen som är öppen."""

    meta_changed = pyqtSignal()          # något ändrades, spara manifestet
    open_node = pyqtSignal(str)          # öppna en nod (material) i editorn
    comment_requested = pyqtSignal()     # ny kommentar på det som är markerat
    comment_activated = pyqtSignal(str, str)   # (nod-id, kommentars-id) — gå dit
    reply_requested = pyqtSignal(str, str)     # (nod-id, kommentars-id) — svara i tråden

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.node = None
        self.codex = None                # projektets entiteter (core.storybible)
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

        # Story-elementen (2.19): Fictionarys frågor per scen, i en egen dialog —
        # tjugo fält i en formkolumn skulle göra inspektören till en blankett.
        self.btn_elements = QPushButton("")
        self.btn_elements.clicked.connect(self._open_elements)
        form.addRow(_("elements_button"), self.btn_elements)

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

        # Entiteter: vilka som är med i scenen (R04.2). Kopplingen ligger i
        # projektets codex (codex.sqlite), inte i manifestet.
        self.lst_entities = QListWidget()
        self.lst_entities.setMaximumHeight(72)
        self.lst_entities.setToolTip(_("scene_entities_hint"))
        form.addRow(_("scene_entities"), self.lst_entities)

        entity_row = QHBoxLayout()
        entity_row.setSpacing(2)
        self.btn_entity_link = QToolButton()
        self.btn_entity_link.setText("📎")
        self.btn_entity_link.setToolTip(_("scene_entity_link"))
        self.btn_entity_link.clicked.connect(self._show_entity_candidates)
        entity_row.addWidget(self.btn_entity_link)
        self.btn_entity_unlink = QToolButton()
        self.btn_entity_unlink.setText("✂️")
        self.btn_entity_unlink.setToolTip(_("scene_entity_unlink"))
        self.btn_entity_unlink.clicked.connect(self._unlink_selected_entity)
        entity_row.addWidget(self.btn_entity_unlink)
        entity_row.addStretch(1)
        self.lbl_entities = QLabel("")
        self.lbl_entities.setStyleSheet("color: palette(mid);")
        entity_row.addWidget(self.lbl_entities)
        form.addRow("", self._wrap(entity_row))

        # Kommentarer fästa i texten (R01.12). Ankaret är citatet, så en
        # kommentar hittar tillbaka även när texten runtom har ändrats.
        self.lst_comments = QListWidget()
        self.lst_comments.setMaximumHeight(96)     # utgångsläget; växer med trådarna
        self.lst_comments.setToolTip(_("scene_comments_hint"))
        self.lst_comments.itemClicked.connect(self._activate_comment)
        self.lst_comments.itemActivated.connect(self._activate_comment)
        form.addRow(_("scene_comments"), self.lst_comments)

        comment_row = QHBoxLayout()
        comment_row.setSpacing(2)
        self.btn_comment_new = QToolButton()
        self.btn_comment_new.setText("💬")
        self.btn_comment_new.setToolTip(_("scene_comment_new"))
        self.btn_comment_new.clicked.connect(self.comment_requested.emit)
        comment_row.addWidget(self.btn_comment_new)
        self.btn_comment_reply = QToolButton()
        self.btn_comment_reply.setText("↳")
        self.btn_comment_reply.setToolTip(_("scene_comment_reply"))
        self.btn_comment_reply.clicked.connect(self._reply_to_selected)
        comment_row.addWidget(self.btn_comment_reply)
        self.btn_comment_resolve = QToolButton()
        self.btn_comment_resolve.setText("✓")
        self.btn_comment_resolve.setToolTip(_("scene_comment_resolve"))
        self.btn_comment_resolve.clicked.connect(self._toggle_resolved)
        comment_row.addWidget(self.btn_comment_resolve)
        self.btn_comment_delete = QToolButton()
        self.btn_comment_delete.setText("🗑️")
        self.btn_comment_delete.setToolTip(_("scene_comment_delete"))
        self.btn_comment_delete.clicked.connect(self._delete_selected_comment)
        comment_row.addWidget(self.btn_comment_delete)
        comment_row.addStretch(1)
        self.lbl_comments = QLabel("")
        self.lbl_comments.setStyleSheet("color: palette(mid);")
        comment_row.addWidget(self.lbl_comments)
        form.addRow("", self._wrap(comment_row))

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
                self.btn_elements.setText("")
                self.lst_material.clear()
                self.lst_entities.clear()
                self.lbl_entities.setText("")
                self.lst_comments.clear()
                self.lbl_comments.setText("")
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
            self._refresh_elements_button()
            self._update_words()
            self._refresh_material()
            self._refresh_entities()
            self._refresh_comments()
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

    # ------------------------------------------------------------- entiteterna

    def set_codex(self, codex) -> None:
        """Projektets codex (core.storybible). Byts när projektet byts."""
        self.codex = codex
        self._refresh_entities()

    def _refresh_entities(self) -> None:
        """Entiteterna i scenen, och hur många som nämns utan att vara kopplade."""
        self.lst_entities.clear()
        has = self.codex is not None and self.project is not None and self.node is not None
        self.btn_entity_link.setEnabled(has)
        self.btn_entity_unlink.setEnabled(has)
        self.lbl_entities.setText("")
        if not has:
            return
        linked = self.codex.for_node(self.node.id)
        for entity in linked:
            item = QListWidgetItem(f"{entity.name} · {_(f'entity_type_{entity.type}')}")
            item.setData(Qt.ItemDataRole.UserRole, entity.id)
            item.setToolTip(entity.summary or entity.name)
            self.lst_entities.addItem(item)
        namnda = self._mentioned_unlinked()
        if namnda:
            self.lbl_entities.setText(_("scene_entities_mentioned", count=len(namnda)))

    def _mentioned_unlinked(self) -> list:
        """Entiteter som nämns i scenens text men inte är kopplade till den."""
        if not self.node.is_writable:
            return []
        text = html_to_text(self.project.read(self.node.id))
        linked = {e.id for e in self.codex.for_node(self.node.id)}
        return [e for e in self.codex.mentions(text) if e.id not in linked]

    def _show_entity_candidates(self) -> None:
        """📎: koppla en entitet som finns i codex, eller skapa en ny."""
        if self.codex is None or self.node is None:
            return
        linked = {e.id for e in self.codex.for_node(self.node.id)}
        menu = QMenu(self)
        namnda = {e.id for e in self._mentioned_unlinked()}
        for entity in self.codex.entities():
            if entity.id in linked:
                continue
            text = f"{entity.name} · {_(f'entity_type_{entity.type}')}"
            if entity.id in namnda:
                text = f"★ {text}"          # nämnd i texten, men inte kopplad
            menu.addAction(text, lambda eid=entity.id: self.link_entity(eid))
        if menu.actions():
            menu.addSeparator()
        menu.addAction(f"+ {_('scene_entity_new')}", self._new_entity)
        menu.exec(self.btn_entity_link.mapToGlobal(self.btn_entity_link.rect().bottomLeft()))

    def _new_entity(self) -> None:
        """Skapar en entitet i projektets codex och kopplar den till scenen."""
        from ui.entity_dialog import EntityDialog

        dialog = EntityDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        name, entity_type, summary = dialog.values()
        if not name:
            return
        entity = self.codex.add_entity(name, type=entity_type, summary=summary)
        self.link_entity(entity.id)

    def link_entity(self, entity_id: str) -> bool:
        if self.codex is None or self.node is None:
            return False
        self.codex.link(entity_id, self.node.id)
        self._refresh_entities()
        return True

    def unlink_entity(self, entity_id: str) -> bool:
        if self.codex is None or self.node is None:
            return False
        self.codex.unlink(entity_id, self.node.id)
        self._refresh_entities()
        return True

    def _unlink_selected_entity(self) -> bool:
        item = self.lst_entities.currentItem() or (
            self.lst_entities.item(0) if self.lst_entities.count() else None)
        if item is None:
            return False
        return self.unlink_entity(item.data(Qt.ItemDataRole.UserRole))

    # ------------------------------------------------------------ kommentarerna

    def _refresh_comments(self) -> None:
        """Kommentarerna på scenen: ogiltiga först, lösta nedtonade.

        Citatet visas kort, så raden går att känna igen utan att gå till texten.
        """
        self.lst_comments.clear()
        has = self.project is not None and self.node is not None
        for knapp in (self.btn_comment_new, self.btn_comment_resolve,
                      self.btn_comment_delete, self.btn_comment_reply):
            knapp.setEnabled(has)
        self.lbl_comments.setText("")
        if not has:
            return
        muted = self.palette().color(QPalette.ColorRole.PlaceholderText)
        comments = self.project.comments_for(self.node.id)
        for comment in comments:
            quote = comment["quote"].replace("\n", " ")
            text = comment["text"] or quote
            item = QListWidgetItem(f"{'✓' if comment['resolved'] else '💬'} {text}")
            item.setData(Qt.ItemDataRole.UserRole, comment["id"])
            item.setToolTip(_("scene_comment_tooltip", quote=quote[:80], text=comment["text"]))
            if comment["resolved"]:
                item.setForeground(muted)
            self.lst_comments.addItem(item)
            # Tråden ligger som indragna rader direkt efter sin kommentar, med
            # kommentarens id: ett klick på ett svar går till samma citat, för det
            # är där samtalet hör hemma.
            # ponytail: platt lista med ↳-rader i stället för ett QTreeWidget — en
            # listrad per svar räcker för en samtalsnot. Byt till träd om trådarna
            # blir långa nog att fällas ihop.
            for svar in comment.get("replies") or []:
                rad = QListWidgetItem("↳ " + (svar.get("text") or ""))
                rad.setData(Qt.ItemDataRole.UserRole, comment["id"])
                rad.setToolTip(svar.get("text") or "")
                if comment["resolved"]:
                    rad.setForeground(muted)
                self.lst_comments.addItem(rad)
        # Rutan växer med trådarna och kapas högt: med en tråd under en kommentar
        # räcker inte 96 px, och en kommentar som är avklippt går inte att läsa.
        rader = self.lst_comments.count()
        self.lst_comments.setMaximumHeight(max(96, min(260, 28 + rader * 22)))
        ogiltiga = len([c for c in comments if not c["resolved"]])
        if ogiltiga:
            self.lbl_comments.setText(_("scene_comments_open", count=ogiltiga))

    def _selected_comment_id(self):
        item = self.lst_comments.currentItem() or (
            self.lst_comments.item(0) if self.lst_comments.count() else None)
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    def _activate_comment(self, item) -> None:
        comment_id = item.data(Qt.ItemDataRole.UserRole)
        if comment_id and self.node is not None:
            self.comment_activated.emit(self.node.id, comment_id)

    def _reply_to_selected(self) -> bool:
        """Ber fönstret om svaret — rutan för texten hör dit, inte hit."""
        comment_id = self._selected_comment_id()
        if comment_id is None or self.node is None:
            return False
        self.reply_requested.emit(self.node.id, comment_id)
        return True

    def _toggle_resolved(self) -> bool:
        """Markera som löst — eller tillbaka till arbetsnot."""
        comment_id = self._selected_comment_id()
        if comment_id is None or self.project is None:
            return False
        comment = self.project.comment(self.node.id, comment_id)
        if comment is None:
            return False
        self.project.resolve_comment(self.node.id, comment_id,
                                     not comment["resolved"])
        self._refresh_comments()
        self.meta_changed.emit()
        return True

    def _delete_selected_comment(self) -> bool:
        comment_id = self._selected_comment_id()
        if comment_id is None or self.project is None:
            return False
        if not self.project.delete_comment(self.node.id, comment_id):
            return False
        self._refresh_comments()
        self.meta_changed.emit()
        return True

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

    def _open_elements(self) -> None:
        """Fyller scenens story-element. Panelen skriver, fönstret sparar."""
        if self.project is None or self.node is None:
            return
        from ui.elements_dialog import ElementsDialog

        dialog = ElementsDialog(self.node, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.node.elements = dialog.values()
        self.meta_changed.emit()
        self._refresh_elements_button()

    def _refresh_elements_button(self) -> None:
        if self.node is None:
            self.btn_elements.setText("")
            return
        rad = story_elements.scene_row(self.node)
        self.btn_elements.setText(_("elements_button_count", filled=rad["filled"],
                                    total=rad["total"]))

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
        self._refresh_elements_button()
        self._update_words()
