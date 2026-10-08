"""
ui/codex_panel.py — story bible: karaktärsblad, relationer och scener.

Fas 2.8. Panelen visar projektets codex (`core.storybible`): en lista över
personer, platser, föremål och grupper, med sökning och typfilter, och ett blad
för den valda entiteten — namn, alias, vem det är, relationer till andra i
boken, vilka scener den är kopplad till och hur många gånger den nämns i
manuset. Klick på en scen öppnar den.

Allt innehåll ligger i projektets codex (codex.sqlite i projektmappen), inte i
manifestet: anteckningar om personer är inte manus.

Alias och sammanfattning sparas med en kort fördröjning medan man skriver —
lika bra som en spara-knapp, och man glömmer inte att trycka på den.
"""

import re

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QHeaderView, QInputDialog, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMenu, QMessageBox, QPlainTextEdit, QPushButton,
    QScrollArea, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core.i18n import _, i18n
from core.storybible import ENTITY_TYPES
from ui.entity_dialog import EntityDialog

SAVE_MS = 700


def count_mentions(text: str, names) -> int:
    """Hur många gånger namnen nämns i texten, hela ord i taget."""
    antal = 0
    for namn in names:
        namn = (namn or "").strip()
        if namn:
            antal += len(re.findall(r"(?<!\w)" + re.escape(namn) + r"(?!\w)", text,
                                    re.IGNORECASE | re.UNICODE))
    return antal


class CodexPanel(QWidget):
    """Story bible i sidopanelen: listan över entiteter och ett blad per vald."""

    status_message = pyqtSignal(str)
    open_scene = pyqtSignal(str)                # node_id

    def __init__(self, config, theme_mgr, parent=None):
        super().__init__(parent)
        self.setObjectName("CodexPanel")
        self.config = config
        self.theme_mgr = theme_mgr

        self.project = None
        self.codex = None
        self.current = None
        self._relation_of_row = []
        self._scene_of_row = []
        self._loading = False            # hindrar att ifyllning ser ut som en ändring

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(SAVE_MS)
        self._save_timer.timeout.connect(self._save_fields)

        self._build_ui()
        if theme_mgr is not None:
            theme_mgr.theme_changed.connect(self.apply_theme)
        i18n.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()
        self.apply_theme()

    # ------------------------------------------------------------- gränssnitt

    def _build_ui(self) -> None:
        yttre = QVBoxLayout(self)
        yttre.setContentsMargins(0, 0, 0, 0)
        ruta = QScrollArea()
        ruta.setWidgetResizable(True)
        ruta.setFrameShape(QScrollArea.Shape.NoFrame)
        inre = QWidget()
        ruta.setWidget(inre)
        yttre.addWidget(ruta)

        kolumn = QVBoxLayout(inre)
        kolumn.setContentsMargins(14, 12, 14, 16)
        kolumn.setSpacing(7)

        self.lbl_head = QLabel()
        self.lbl_head.setObjectName("InspectorEyebrow")
        kolumn.addWidget(self.lbl_head)

        self.input_search = QLineEdit()
        self.input_search.textChanged.connect(lambda *_: self._fill_list())
        kolumn.addWidget(self.input_search)

        self.combo_type = QComboBox()
        self.combo_type.currentIndexChanged.connect(lambda *_: self._fill_list())
        kolumn.addWidget(self.combo_type)

        self.list_entities = QListWidget()
        self.list_entities.setFixedHeight(118)
        self.list_entities.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_entities.currentItemChanged.connect(lambda *_: self._show_sheet())
        kolumn.addWidget(self.list_entities)

        knapprad = QHBoxLayout()
        knapprad.setSpacing(4)
        self.btn_new = QPushButton()
        self.btn_new.clicked.connect(self._new_entity)
        knapprad.addWidget(self.btn_new)
        self.btn_edit = QPushButton()
        self.btn_edit.clicked.connect(self._edit_entity)
        knapprad.addWidget(self.btn_edit)
        self.btn_delete = QPushButton()
        self.btn_delete.clicked.connect(lambda: self.remove_current(ask=True))
        knapprad.addWidget(self.btn_delete)
        kolumn.addLayout(knapprad)

        self.lbl_name = QLabel()
        self.lbl_name.setObjectName("InspectorTitle")
        self.lbl_name.setWordWrap(True)
        self.chip_type = QLabel()
        self.chip_type.setObjectName("Chip")
        namnrad = QHBoxLayout()
        namnrad.setSpacing(8)
        namnrad.addWidget(self.lbl_name, 1)
        namnrad.addWidget(self.chip_type)
        kolumn.addLayout(namnrad)

        self.lbl_aliases = QLabel()
        kolumn.addWidget(self.lbl_aliases)
        self.input_aliases = QLineEdit()
        self.input_aliases.textEdited.connect(self._schedule_save)
        kolumn.addWidget(self.input_aliases)

        self.lbl_summary = QLabel()
        kolumn.addWidget(self.lbl_summary)
        self.input_summary = QPlainTextEdit()
        self.input_summary.setFixedHeight(72)
        self.input_summary.textChanged.connect(self._schedule_save)
        kolumn.addWidget(self.input_summary)

        # Fria attribut (6.1): "Ålder", "Ögonfärg", "Hemvist" — namn och värde,
        # för det ett karaktärsblad behöver men som inte är samma för alla.
        self.lbl_attributes = QLabel()
        kolumn.addWidget(self.lbl_attributes)
        self.table_attributes = QTableWidget(0, 2)
        self.table_attributes.setFixedHeight(90)
        self.table_attributes.verticalHeader().setVisible(False)
        self.table_attributes.horizontalHeader().setVisible(False)
        self.table_attributes.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self.table_attributes.itemChanged.connect(self._save_attributes)
        kolumn.addWidget(self.table_attributes)
        attrrad = QHBoxLayout()
        attrrad.setSpacing(4)
        self.btn_attr_add = QPushButton("+")
        self.btn_attr_add.clicked.connect(self.add_attribute)
        attrrad.addWidget(self.btn_attr_add)
        self.btn_attr_del = QPushButton("−")
        self.btn_attr_del.clicked.connect(self.remove_attribute)
        attrrad.addWidget(self.btn_attr_del)
        kolumn.addLayout(attrrad)

        self.lbl_relations = QLabel()
        kolumn.addWidget(self.lbl_relations)
        self.list_relations = QListWidget()
        self.list_relations.setFixedHeight(64)
        # Långa relationsrader ("→ Hamnstaden · återvänder till — …") skall radbrytas,
        # inte skjuta in en vågrät skrollist i en 312 px bred panel.
        self.list_relations.setWordWrap(True)
        self.list_relations.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        kolumn.addWidget(self.list_relations)
        relrad = QHBoxLayout()
        relrad.setSpacing(4)
        self.btn_relation_add = QPushButton()
        self.btn_relation_add.clicked.connect(self._pick_relation)
        relrad.addWidget(self.btn_relation_add)
        self.btn_relation_del = QPushButton()
        self.btn_relation_del.clicked.connect(self.remove_selected_relation)
        relrad.addWidget(self.btn_relation_del)
        # Relationsgraf (2.22): samma data ritad, så mönstret syns — vem hänger
        # ihop med vem, och vem står ensam.
        self.btn_graph = QPushButton("🕸")
        self.btn_graph.setToolTip(_("codex_graph_tooltip"))
        self.btn_graph.setFixedWidth(32)
        self.btn_graph.clicked.connect(self.show_graph)
        relrad.addWidget(self.btn_graph)
        kolumn.addLayout(relrad)

        self.lbl_scenes = QLabel()
        kolumn.addWidget(self.lbl_scenes)
        self.list_scenes = QListWidget()
        self.list_scenes.setFixedHeight(84)
        self.list_scenes.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_scenes.itemClicked.connect(self._open_scene)
        kolumn.addWidget(self.list_scenes)
        self.btn_scene_unlink = QPushButton()
        self.btn_scene_unlink.clicked.connect(self.unlink_selected_scene)
        kolumn.addWidget(self.btn_scene_unlink)

        self.lbl_mentions = QLabel()
        self.lbl_mentions.setWordWrap(True)
        kolumn.addWidget(self.lbl_mentions)
        kolumn.addStretch(1)

    # --------------------------------------------------------------- projektet

    def set_project(self, project, codex) -> None:
        """Byter codex när projektet byts. Utan projekt visas ingenting."""
        self.project = project
        self.codex = codex
        self.current = None
        self.refresh()

    def refresh(self) -> None:
        """Fyller listan och visar bladet för den valda entiteten (om någon)."""
        if self.codex is None:
            self.list_entities.clear()
            self._show_sheet()
            return
        valt = self.current.id if self.current is not None else None
        self._fill_list(valt)

    def show_graph(self) -> None:
        """Ritar codexet som en graf. Ett klick i grafen väljer posten här."""
        if self.codex is None:
            return
        from ui.codex_graph_dialog import CodexGraphDialog

        dialog = CodexGraphDialog(self.codex, self.theme_mgr, parent=self)
        dialog.entity_activated.connect(self.select)
        dialog.exec()

    def _visible_entities(self) -> list:
        if self.codex is None:
            return []
        text = self.input_search.text().strip()
        typ = self.combo_type.currentData()
        poster = self.codex.search(text) if text else self.codex.entities()
        # search() letar i namn, alias och sammanfattning — filtret gäller ändå
        return [e for e in poster if typ in (None, e.type)]

    def _fill_list(self, keep=None) -> None:
        if self.codex is None:
            return
        if isinstance(keep, str):
            valt = keep
        else:
            valt = self.current.id if self.current is not None else None
        self.list_entities.blockSignals(True)
        self.list_entities.clear()
        for entity in self._visible_entities():
            item = QListWidgetItem(f"{entity.name} · {_(f'entity_type_{entity.type}')}")
            item.setData(Qt.ItemDataRole.UserRole, entity.id)
            self.list_entities.addItem(item)
            if entity.id == valt:
                self.list_entities.setCurrentItem(item)
        if self.list_entities.currentItem() is None and self.list_entities.count():
            self.list_entities.setCurrentRow(0)
        self.list_entities.blockSignals(False)
        self._show_sheet()

    def select(self, entity_id: str) -> None:
        """Väljer en entitet i listan (används av proven och av kopplingen)."""
        for rad in range(self.list_entities.count()):
            item = self.list_entities.item(rad)
            if item.data(Qt.ItemDataRole.UserRole) == entity_id:
                self.list_entities.setCurrentItem(item)
                return
        self._fill_list(entity_id)

    # ------------------------------------------------------------------ bladet

    def _show_sheet(self) -> None:
        item = self.list_entities.currentItem()
        entity = self.codex.entity(item.data(Qt.ItemDataRole.UserRole)) if (item and self.codex) else None
        self.current = entity
        har = entity is not None

        for w in (self.input_aliases, self.input_summary, self.list_relations,
                  self.btn_relation_add, self.btn_relation_del, self.list_scenes,
                  self.btn_scene_unlink, self.btn_edit, self.btn_delete,
                  self.table_attributes, self.btn_attr_add, self.btn_attr_del):
            w.setEnabled(har)
        self.lbl_name.setVisible(har)
        self.chip_type.setVisible(har)
        self.lbl_aliases.setVisible(har)
        self.input_aliases.setVisible(har)
        self.lbl_summary.setVisible(har)
        self.input_summary.setVisible(har)
        self.lbl_attributes.setVisible(har)
        self.table_attributes.setVisible(har)
        self.btn_attr_add.setVisible(har)
        self.btn_attr_del.setVisible(har)
        self.lbl_relations.setVisible(har)
        self.list_relations.setVisible(har)
        self.lbl_scenes.setVisible(har)
        self.list_scenes.setVisible(har)
        self.btn_scene_unlink.setVisible(har)
        self.lbl_mentions.setVisible(har)
        if not har:
            self.lbl_name.setText(_("codex_no_selection"))
            return

        self._save_timer.stop()
        self.lbl_name.setText(entity.name)
        self.chip_type.setText(_(f"entity_type_{entity.type}"))
        self.input_aliases.setText(", ".join(entity.aliases))
        self.input_summary.blockSignals(True)
        self.input_summary.setPlainText(entity.summary)
        self.input_summary.blockSignals(False)
        self._fill_attributes(entity)
        self._fill_relations(entity)
        self._fill_scenes(entity)
        self._fill_mentions(entity)

    def _fill_relations(self, entity) -> None:
        self.list_relations.clear()
        self._relation_of_row = []
        namn = {e.id: e.name for e in self.codex.entities()}
        for rel in self.codex.relations(entity.id):
            andra = rel.to_id if rel.from_id == entity.id else rel.from_id
            pil = "→" if rel.from_id == entity.id else "←"
            text = f"{pil} {namn.get(andra, '?')} · {rel.kind}"
            if rel.note:
                text += f" — {rel.note}"
            item = QListWidgetItem(text)
            self.list_relations.addItem(item)
            self._relation_of_row.append(rel)

    def _fill_scenes(self, entity) -> None:
        self.list_scenes.clear()
        self._scene_of_row = []
        titlar = {n.id: n.title for n in (self.project.walk() if self.project else [])}
        for node_id in self._scenes_of(entity):
            scen = titlar.get(node_id)
            if scen is None:
                continue                       # scenen finns inte längre
            item = QListWidgetItem(scen)
            self.list_scenes.addItem(item)
            self._scene_of_row.append(node_id)
        self.lbl_scenes.setText(_("codex_scenes", n=len(self._scene_of_row)))

    def _scenes_of(self, entity) -> list[str]:
        """Scenerna entiteten är kopplad till, i manusets ordning."""
        if self.project is None:
            return []
        ordning = [n.id for n in self.project.walk()]
        kopplade = [n.id for n in self.project.walk()
                    if entity.id in {e.id for e in self.codex.for_node(n.id)}]
        return sorted(kopplade, key=ordning.index)

    def _fill_mentions(self, entity) -> None:
        antal = count_mentions(self.manuscript_text(), [entity.name, *entity.aliases])
        self.lbl_mentions.setText(_("codex_mentions", n=antal))

    def manuscript_text(self) -> str:
        """Hela manuset som text — läses om varje gång ett blad visas.

        ponytail: ingen cache. En bok är små textfiler, läsningen kostar
        millisekunder, och en cachad siffra som ljuger när man just ändrat en
        scen är värre än att läsa en gång för mycket.
        """
        if self.project is None:
            return ""
        return "\n\n".join(self.project.read(n.id) for n in self.project.manuscript())

    # --------------------------------------------------------------- skrivandet

    def _schedule_save(self) -> None:
        if self.current is not None:
            self._save_timer.start()

    def _fill_attributes(self, entity) -> None:
        """Fria attribut: namn och värde i en tabell, tomma rader sparas inte."""
        self._loading = True
        try:
            self.table_attributes.setRowCount(0)
            for key, value in (entity.fields or {}).items():
                self._append_attribute_row(key, value)
        finally:
            self._loading = False

    def _append_attribute_row(self, key: str, value: str) -> None:
        rad = self.table_attributes.rowCount()
        self.table_attributes.insertRow(rad)
        self.table_attributes.setItem(rad, 0, QTableWidgetItem(str(key)))
        self.table_attributes.setItem(rad, 1, QTableWidgetItem(str(value)))

    def attributes(self) -> dict:
        """Tabellens par, utan tomma namn — en ny rad är inte ett attribut."""
        ut = {}
        for rad in range(self.table_attributes.rowCount()):
            namn = self.table_attributes.item(rad, 0)
            varde = self.table_attributes.item(rad, 1)
            nyckel = (namn.text() if namn else "").strip()
            if nyckel:
                ut[nyckel] = (varde.text() if varde else "").strip()
        return ut

    def add_attribute(self) -> None:
        if self.current is None:
            return
        self._append_attribute_row("", "")
        sista = self.table_attributes.rowCount() - 1
        self.table_attributes.setCurrentCell(sista, 0)
        objekt = self.table_attributes.item(sista, 0)
        if objekt is not None:
            self.table_attributes.editItem(objekt)

    def remove_attribute(self) -> None:
        rad = self.table_attributes.currentRow()
        if rad < 0:
            return
        self.table_attributes.removeRow(rad)
        self._save_attributes()

    def _save_attributes(self, *_args) -> None:
        if self.current is None or self.codex is None or self._loading:
            return
        par = self.attributes()
        if par == (self.current.fields or {}):
            return
        try:
            self.current = self.codex.update_entity(self.current.id, fields=par)
        except (KeyError, TypeError, ValueError) as exc:
            self.status_message.emit(_("codex_save_failed", error=exc))

    def _save_fields(self) -> None:
        """Alias och sammanfattning skrivs till codex någon sekund efter tangenten."""
        if self.current is None or self.codex is None:
            return
        alias = [a.strip() for a in self.input_aliases.text().split(",") if a.strip()]
        if alias == self.current.aliases and self.input_summary.toPlainText() == self.current.summary:
            return
        try:
            self.current = self.codex.update_entity(
                self.current.id, aliases=alias, summary=self.input_summary.toPlainText().strip())
        except (KeyError, TypeError, ValueError) as exc:
            self.status_message.emit(_("codex_save_failed", error=exc))
        else:
            self._fill_list(self.current.id)

    # ----------------------------------------------------------------- åtgärder

    def _new_entity(self) -> None:
        if self.codex is None:
            self.status_message.emit(_("codex_no_project"))
            return
        dialog = EntityDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        namn, typ, sammanfattning = dialog.values()
        if not namn:
            return
        entity = self.codex.add_entity(namn, type=typ, summary=sammanfattning)
        self._fill_list(entity.id)
        self.status_message.emit(_("codex_created", name=entity.name))

    def _edit_entity(self) -> None:
        if self.current is None:
            return
        dialog = EntityDialog(parent=self, entity=self.current)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        namn, typ, sammanfattning = dialog.values()
        if not namn:
            return
        self.current = self.codex.update_entity(self.current.id, name=namn, type=typ,
                                                summary=sammanfattning)
        self._fill_list(self.current.id)

    def remove_current(self, ask: bool = True) -> None:
        """Tar bort entiteten. `ask=False` används av proven — ingen modal där."""
        if self.current is None or self.codex is None:
            return
        if ask:
            svar = QMessageBox.question(
                self, _("codex_delete_title"),
                _("codex_delete_ask", name=self.current.name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if svar != QMessageBox.StandardButton.Yes:
                return
        namn = self.current.name
        self.codex.delete_entity(self.current.id)
        self.current = None
        self._fill_list()
        self.status_message.emit(_("codex_deleted", name=namn))

    def add_relation_to(self, other_id: str, kind: str, note: str = "") -> None:
        """Relation från den valda entiteten till en annan. Ingen dialog här."""
        if self.current is None or self.codex is None or not kind.strip():
            return
        self.codex.add_relation(self.current.id, other_id, kind.strip(), note)
        self._fill_relations(self.current)

    def _pick_relation(self) -> None:
        if self.current is None:
            return
        andra = [e for e in self.codex.entities() if e.id != self.current.id]
        if not andra:
            self.status_message.emit(_("codex_relation_none"))
            return
        meny = QMenu(self)
        for entity in andra:
            meny.addAction(f"{entity.name} · {_(f'entity_type_{entity.type}')}",
                           lambda eid=entity.id: self._ask_kind(eid))
        meny.exec(self.btn_relation_add.mapToGlobal(self.btn_relation_add.rect().bottomLeft()))

    def _ask_kind(self, other_id: str) -> None:
        kind, ok = QInputDialog.getText(self, _("codex_relation_kind_title"),
                                        _("codex_relation_kind"))
        if ok and kind.strip():
            self.add_relation_to(other_id, kind)

    def current_relation(self):
        rad = self.list_relations.currentRow()
        return self._relation_of_row[rad] if 0 <= rad < len(self._relation_of_row) else None

    def remove_selected_relation(self) -> None:
        rel = self.current_relation()
        if rel is None or self.codex is None:
            return
        self.codex.remove_relation(rel.from_id, rel.to_id, rel.kind)
        self._fill_relations(self.current)

    def _open_scene(self, item) -> None:
        rad = self.list_scenes.row(item)
        if 0 <= rad < len(self._scene_of_row):
            self.open_scene.emit(self._scene_of_row[rad])

    def unlink_selected_scene(self) -> None:
        rad = self.list_scenes.currentRow()
        if self.current is None or not (0 <= rad < len(self._scene_of_row)):
            return
        self.codex.unlink(self.current.id, self._scene_of_row[rad])
        self._fill_scenes(self.current)

    # -------------------------------------------------------------- tema/språk

    def apply_theme(self) -> None:
        if self.theme_mgr is None:
            return
        c = self.theme_mgr.tokens()
        for lbl in (self.lbl_aliases, self.lbl_relations, self.lbl_scenes,
                    self.lbl_mentions, self.lbl_head):
            lbl.setStyleSheet(f"color: {c['text_muted']};")

    def retranslate_ui(self) -> None:
        self.lbl_head.setText(_("codex_title").upper())
        self.input_search.setPlaceholderText(_("codex_search_hint"))
        self.input_aliases.setPlaceholderText(_("codex_aliases_hint"))
        self.input_summary.setPlaceholderText(_("codex_summary_hint"))
        self.btn_new.setText(_("codex_new"))
        self.btn_edit.setText(_("codex_edit"))
        self.btn_delete.setText(_("codex_delete"))
        self.btn_relation_add.setText(_("codex_relation_add"))
        self.btn_relation_del.setText(_("codex_relation_del"))
        self.btn_scene_unlink.setText(_("codex_scene_unlink"))
        self.lbl_aliases.setText(_("codex_aliases"))
        self.lbl_summary.setText(_("codex_summary"))
        self.lbl_relations.setText(_("codex_relations"))
        self.lbl_attributes.setText(_("codex_attributes"))
        self.btn_attr_add.setToolTip(_("codex_attribute_add"))
        self.btn_attr_del.setToolTip(_("codex_attribute_del"))
        self.lbl_scenes.setText(_("codex_scenes", n=0))
        valt = self.combo_type.currentData()
        self.combo_type.blockSignals(True)
        self.combo_type.clear()
        self.combo_type.addItem(_("codex_filter_all"), None)
        for typ in ENTITY_TYPES:
            self.combo_type.addItem(_(f"entity_type_{typ}"), typ)
        index = self.combo_type.findData(valt)
        self.combo_type.setCurrentIndex(index if index >= 0 else 0)
        self.combo_type.blockSignals(False)
        self.refresh()
