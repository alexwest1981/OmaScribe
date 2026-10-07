"""ui/binder_panel.py — projektets träd: delar, kapitel och scener.

Panelen är projektmodellens ansikte utåt: den visar `core/project.py`:s noder,
låter dig skapa, döpa, flytta och ta bort dem, och säger till när en scen väljs
så att editorn byter text. Den rör ingen text själv.
"""

from html import escape

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QHBoxLayout, QInputDialog, QLabel, QMessageBox, QTabWidget, QToolButton,
    QTreeView, QVBoxLayout, QWidget,
)

from core import project as project_mod
from core.i18n import _, i18n
from ui.corkboard import Corkboard

ICONS = {
    project_mod.PART: "📁",
    project_mod.CHAPTER: "📂",
    project_mod.SCENE: "📄",
    project_mod.NOTE: "📝",
}


def _tal(antal: int) -> str:
    """1000 -> '1 000'. Svensk tusentalsgruppering, inte komma."""
    return f"{antal:,}".replace(",", " ")


# Vad knapparna skapar: mapptyp -> etikettnyckel
ADD_KINDS = (
    (project_mod.SCENE, "binder_new_scene"),
    (project_mod.CHAPTER, "binder_new_chapter"),
    (project_mod.PART, "binder_new_part"),
)


class _SceneTree(QTreeView):
    """Träd som rapporterar var ett släpp skedde i stället för att flytta raden själv.

    Låter Qt flytta raden skulle ge en vy som inte stämmer med projektmodellen —
    och nästa refresh skulle sudda ut flytten. Här är modellen enda ägaren av
    ordningen: trädet säger bara till, och bindern kör project.move_node.
    """

    dropped = pyqtSignal(str, str, str)      # nod, mål, plats (above/below/on/end)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        # Sätt läget sist: setDefaultDropAction(MoveAction) sätter Qt:s läge till
        # DropOnly och stänger av dragningen — och Qt flyttar ändå inget, för
        # dropEvent nedan låter bli att anropa super().
        self.setDragDropMode(QTreeView.DragDropMode.DragDrop)

    def dropEvent(self, event) -> None:
        dragged = self.currentIndex()
        if event.source() is not None and event.source() is not self:
            dragged = event.source().currentIndex()
        node_id = dragged.data(Qt.ItemDataRole.UserRole)
        if not node_id:
            event.ignore()
            return
        index = self.indexAt(event.position().toPoint())
        placement, target = "end", ""
        if index.isValid():
            where = self.dropIndicatorPosition()
            if where == QTreeView.DropIndicatorPosition.OnItem:
                placement = "on"
            elif where == QTreeView.DropIndicatorPosition.BelowItem:
                placement = "below"
            elif where == QTreeView.DropIndicatorPosition.AboveItem:
                placement = "above"
            if placement != "end":
                target = index.data(Qt.ItemDataRole.UserRole) or ""
        event.accept()
        self.dropped.emit(node_id, target, placement)


class BinderPanel(QWidget):
    """Trädet över manuset. Ett val säger till vilken scen som skall visas."""

    scene_selected = pyqtSignal(str)     # node_id
    structure_changed = pyqtSignal()     # trädet ändrades, spara manifestet

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project: project_mod.Project | None = None
        self._last_scene_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        header = QHBoxLayout()
        self.lbl_title = QLabel(_("binder_title"))
        self.lbl_title.setStyleSheet("font-weight: 600;")
        header.addWidget(self.lbl_title)
        header.addStretch(1)
        layout.addLayout(header)

        buttons = QHBoxLayout()
        buttons.setSpacing(2)
        self.buttons = []
        self._tip_widgets = []                 # [(widget, nyckel)] för översättning
        for kind, key in ADD_KINDS:
            button = QToolButton()
            button.setText(ICONS[kind])
            button.setToolTip(_(key))
            button.clicked.connect(lambda _checked=False, k=kind: self.add_node(k))
            buttons.addWidget(button)
            self.buttons.append(button)
            self._tip_widgets.append((button, key))
        self.btn_rename = QToolButton()
        self.btn_rename.setText("✏️")
        self.btn_rename.setToolTip(_("binder_rename"))
        self.btn_rename.clicked.connect(self.rename_current)
        buttons.addWidget(self.btn_rename)
        self._tip_widgets.append((self.btn_rename, "binder_rename"))
        self.btn_delete = QToolButton()
        self.btn_delete.setText("🗑")
        self.btn_delete.setToolTip(_("binder_delete"))
        self.btn_delete.clicked.connect(self.delete_current)
        buttons.addWidget(self.btn_delete)
        self._tip_widgets.append((self.btn_delete, "binder_delete"))
        self.btn_up = QToolButton()
        self.btn_up.setText("⬆")
        self.btn_up.setToolTip(_("binder_move_up"))
        self.btn_up.clicked.connect(lambda: self.move_current(-1))
        buttons.addWidget(self.btn_up)
        self._tip_widgets.append((self.btn_up, "binder_move_up"))
        self.btn_down = QToolButton()
        self.btn_down.setText("⬇")
        self.btn_down.setToolTip(_("binder_move_down"))
        self.btn_down.clicked.connect(lambda: self.move_current(1))
        buttons.addWidget(self.btn_down)
        self._tip_widgets.append((self.btn_down, "binder_move_down"))
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.buttons.extend([self.btn_rename, self.btn_delete, self.btn_up, self.btn_down])

        self.tree = _SceneTree()
        self.tree.setHeaderHidden(True)
        self.tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)  # namn byts via knappen
        self.tree.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.tree.setExpandsOnDoubleClick(False)
        self.model = QStandardItemModel(self.tree)
        self.tree.setModel(self.model)
        self.tree.doubleClicked.connect(self._on_double_clicked)
        self.tree.dropped.connect(self.move_by_drop)
        self.tree.selectionModel().currentChanged.connect(self._on_current_changed)

        # Trädet och korktavlan är två vyer av samma projekt. De ligger i samma
        # panel med flit: då delar de markering, och skrivvyn står kvar bredvid
        # tavlan i stället för att bytas ut. Vill du ha en tavla över hela
        # fönstret är det en egen vy — säg till.
        self.tabs = QTabWidget()
        self.tabs.addTab(self.tree, _("binder_tab_tree"))
        self.corkboard = Corkboard(self)
        self.corkboard.scene_selected.connect(self._on_card_clicked)
        self.corkboard.card_dropped.connect(self.move_by_drop)
        self.tabs.addTab(self.corkboard, _("binder_tab_cards"))
        i18n.language_changed.connect(self.retranslate_ui)
        layout.addWidget(self.tabs, 1)

        self.set_project(None)

    # ------------------------------------------------------------------ projektet

    def set_project(self, project: project_mod.Project | None) -> None:
        self.project = project
        self._last_scene_id = None
        self.corkboard.set_project(project)
        self.refresh()
        for widget in self.buttons:
            widget.setEnabled(project is not None)
        self._refresh_header()

    def refresh(self, select_id: str | None = None) -> None:
        """Bygger om trädet ur modellen och behåller markeringen."""
        keep = select_id or self.current_node_id()
        self.model.clear()
        self.model.setHorizontalHeaderLabels([_("binder_title")])
        if self.project is None:
            return

        def add(parent_item, parent_id):
            for node in self.project.children(parent_id):
                item = QStandardItem(self._label_for(node))
                item.setData(node.id, Qt.ItemDataRole.UserRole)
                if node.synopsis:
                    item.setToolTip(node.synopsis)
                if parent_item is None:
                    self.model.appendRow(item)
                else:
                    parent_item.appendRow(item)
                add(item, node.id)

        add(None, None)
        self.tree.expandAll()
        self.corkboard.refresh()
        self._refresh_header()
        if keep:
            self.select_node(keep)

    def _label_for(self, node) -> str:
        """Trädraden: ikon, titel och ord mot mål (summerat för behållare)."""
        icon = ICONS.get(node.type, "•")
        progress = self.project.node_progress(node.id)
        if not progress["words"] and not progress["target"]:
            return f"{icon} {node.title}"
        if progress["target"]:
            ord_text = f"{_tal(progress['words'])}/{_tal(progress['target'])}"
        else:
            ord_text = _tal(progress["words"])
        return f"{icon} {node.title}   {ord_text}"

    def refresh_labels(self) -> None:
        """Uppdaterar bara texterna — ordtalen ändras när en scen sparas.

        Trädet byggs inte om, så hopfällning, rullning och markering står kvar.
        """
        if self.project is None:
            return
        for item in self._iter_items():
            node_id = item.data(Qt.ItemDataRole.UserRole)
            try:
                node = self.project.by_id(node_id)
            except KeyError:
                continue
            item.setText(self._label_for(node))
        self._refresh_header()

    def _refresh_header(self) -> None:
        if self.project is None:
            self.lbl_title.setText(_("binder_title"))
            return
        progress = self.project.progress()
        if progress["target"]:
            detalj = _("binder_progress_of", words=_tal(progress["words"]),
                       target=_tal(progress["target"]), percent=progress["percent"])
        else:
            detalj = _("binder_words", words=_tal(progress["words"]))
        self.lbl_title.setText(
            f"{escape(self.project.title)}<br>"
            f"<span style='font-weight:400;'>{escape(detalj)}</span>")

    def current_node_id(self) -> str | None:
        indexes = self.tree.selectionModel().selectedIndexes()
        if not indexes:
            return None
        return indexes[0].data(Qt.ItemDataRole.UserRole)

    def select_node(self, node_id: str) -> bool:
        self.corkboard.select_node(node_id)
        for row in self._iter_items():
            if row.data(Qt.ItemDataRole.UserRole) == node_id:
                self.tree.setCurrentIndex(row.index())
                return True
        return False

    def _iter_items(self):
        def walk(item):
            for row in range(item.rowCount()):
                child = item.child(row)
                yield child
                yield from walk(child)

        for row in range(self.model.rowCount()):
            top = self.model.item(row)
            yield top
            yield from walk(top)

    def _item_for(self, node_id: str):
        for item in self._iter_items():
            if item.data(Qt.ItemDataRole.UserRole) == node_id:
                return item
        return None

    # ------------------------------------------------------------------- ändringar

    def add_node(self, kind: str) -> None:
        if self.project is None:
            return
        parent_id = self.current_node_id()
        parent = self.project.by_id(parent_id) if parent_id else None
        # En ny scen hamnar i markeringen om den är en behållare, annars bredvid.
        if kind == project_mod.SCENE:
            if parent is None:
                containers = self.project.children(None)
                parent = next((n for n in containers if n.type == project_mod.CHAPTER), None)
                parent_id = parent.id if parent else None
        elif parent is not None and parent.type == project_mod.SCENE:
            parent_id = parent.parent      # nya kapitel/delar hamnar inte inuti en scen

        prefix = {
            project_mod.SCENE: "binder_default_scene",
            project_mod.CHAPTER: "binder_default_chapter",
            project_mod.PART: "binder_default_part",
        }[kind]
        siblings = self.project.children(parent_id)
        title = f"{_(prefix)} {len(siblings) + 1}"
        position = None
        if parent is not None and parent.type == project_mod.SCENE:
            position = parent.order + 1
            parent_id = parent.parent
        node = self.project.add_node(kind, title, parent=parent_id, position=position)
        self.structure_changed.emit()
        self.refresh(select_id=node.id)

    def rename_current(self, node_id: str | None = None) -> None:
        node_id = node_id or self.current_node_id()
        if self.project is None or node_id is None:
            return
        node = self.project.by_id(node_id)
        title, accepted = QInputDialog.getText(
            self, _("binder_rename_title"), _("binder_rename_label"), text=node.title
        )
        if accepted and title.strip():
            self.project.rename(node_id, title.strip())
            self.structure_changed.emit()
            self.refresh(select_id=node_id)

    def delete_current(self) -> None:
        node_id = self.current_node_id()
        if self.project is None or node_id is None:
            return
        node = self.project.by_id(node_id)
        count = 1 + len(self.project.walk(node_id))
        answer = QMessageBox.question(
            self,
            _("binder_delete_title"),
            _("binder_delete_text", title=node.title, count=count),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        parent = node.parent
        self.project.delete_node(node_id, delete_files=True)
        self.structure_changed.emit()
        siblings = self.project.children(parent)
        self.refresh(select_id=siblings[0].id if siblings else None)

    def move_current(self, delta: int) -> None:
        node_id = self.current_node_id()
        if self.project is None or node_id is None:
            return
        node = self.project.by_id(node_id)
        target = node.order + delta
        if target < 0:
            return
        self.project.move_node(node_id, node.parent, target)
        self.structure_changed.emit()
        self.refresh(select_id=node_id)

    def move_by_drop(self, node_id: str, target_id: str, placement: str) -> bool:
        """Flyttar en nod dit den släpptes. False om släppet avvisas.

        Trädet och kortvyn rapporterar samma sak — nod, mål och plats — så båda
        hamnar här. Modellen avgör vad som är tillåtet (t.ex. inte in i sig
        själv); avvisas det får vyn ingen flytt, vilket är rätt svar.
        """
        if self.project is None or not node_id or target_id == node_id:
            return False
        if not target_id:
            parent, position = None, len(self.project.children(None))
        else:
            try:
                target = self.project.by_id(target_id)
            except KeyError:
                return False
            if placement == "on" and target.type in project_mod.CONTAINERS:
                parent, position = target.id, len(self.project.children(target.id))
            else:
                if placement == "on":          # släppt på en scen: hamnar efter den
                    placement = "below"
                parent = target.parent
                siblings = [n for n in self.project.children(parent) if n.id != node_id]
                where = next((i for i, n in enumerate(siblings) if n.id == target.id), None)
                if where is None:
                    return False
                position = where + (1 if placement == "below" else 0)
        try:
            self.project.move_node(node_id, parent, position)
        except ValueError:
            return False
        self.structure_changed.emit()
        self.refresh(select_id=node_id)
        return True

    # ---------------------------------------------------------------------- signaler

    def _on_current_changed(self, current, _previous) -> None:
        node_id = current.data(Qt.ItemDataRole.UserRole) if current.isValid() else None
        if not node_id or self.project is None:
            return
        node = self.project.by_id(node_id)
        if not node.is_writable:
            return
        if node_id != self._last_scene_id:
            self._last_scene_id = node_id
            self.scene_selected.emit(node_id)

    def _on_double_clicked(self, index) -> None:
        node_id = index.data(Qt.ItemDataRole.UserRole)
        if node_id:
            self.rename_current(node_id)

    def _on_card_clicked(self, node_id: str) -> None:
        """Ett kort markerar samma nod i trädet — en väg till signalen, inte två."""
        self.select_node(node_id)

    def retranslate_ui(self) -> None:
        self.tabs.setTabText(0, _("binder_tab_tree"))
        self.tabs.setTabText(1, _("binder_tab_cards"))
        for widget, key in self._tip_widgets:
            widget.setToolTip(_(key))
        self._refresh_header()
