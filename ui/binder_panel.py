"""ui/binder_panel.py — projektets träd: delar, kapitel och scener.

Panelen är projektmodellens ansikte utåt: den visar `core/project.py`:s noder,
låter dig skapa, döpa, flytta och ta bort dem, och säger till när en scen väljs
så att editorn byter text. Den rör ingen text själv.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QHBoxLayout, QInputDialog, QLabel, QMessageBox, QToolButton, QTreeView,
    QVBoxLayout, QWidget,
)

from core import project as project_mod
from core.i18n import _

ICONS = {
    project_mod.PART: "📁",
    project_mod.CHAPTER: "📂",
    project_mod.SCENE: "📄",
    project_mod.NOTE: "📝",
}
# Vad knapparna skapar: mapptyp -> etikettnyckel
ADD_KINDS = (
    (project_mod.SCENE, "binder_new_scene"),
    (project_mod.CHAPTER, "binder_new_chapter"),
    (project_mod.PART, "binder_new_part"),
)


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
        for kind, key in ADD_KINDS:
            button = QToolButton()
            button.setText(ICONS[kind])
            button.setToolTip(_(key))
            button.clicked.connect(lambda _checked=False, k=kind: self.add_node(k))
            buttons.addWidget(button)
            self.buttons.append(button)
        self.btn_rename = QToolButton()
        self.btn_rename.setText("✏️")
        self.btn_rename.setToolTip(_("binder_rename"))
        self.btn_rename.clicked.connect(self.rename_current)
        buttons.addWidget(self.btn_rename)
        self.btn_delete = QToolButton()
        self.btn_delete.setText("🗑")
        self.btn_delete.setToolTip(_("binder_delete"))
        self.btn_delete.clicked.connect(self.delete_current)
        buttons.addWidget(self.btn_delete)
        self.btn_up = QToolButton()
        self.btn_up.setText("⬆")
        self.btn_up.setToolTip(_("binder_move_up"))
        self.btn_up.clicked.connect(lambda: self.move_current(-1))
        buttons.addWidget(self.btn_up)
        self.btn_down = QToolButton()
        self.btn_down.setText("⬇")
        self.btn_down.setToolTip(_("binder_move_down"))
        self.btn_down.clicked.connect(lambda: self.move_current(1))
        buttons.addWidget(self.btn_down)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        self.buttons.extend([self.btn_rename, self.btn_delete, self.btn_up, self.btn_down])

        self.tree = QTreeView()
        self.tree.setHeaderHidden(True)
        self.tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)  # namn byts via knappen
        self.tree.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.tree.setExpandsOnDoubleClick(False)
        self.model = QStandardItemModel(self.tree)
        self.tree.setModel(self.model)
        self.tree.doubleClicked.connect(self._on_double_clicked)
        self.tree.selectionModel().currentChanged.connect(self._on_current_changed)
        layout.addWidget(self.tree, 1)

        self.set_project(None)

    # ------------------------------------------------------------------ projektet

    def set_project(self, project: project_mod.Project | None) -> None:
        self.project = project
        self._last_scene_id = None
        self.refresh()
        for widget in self.buttons:
            widget.setEnabled(project is not None)
        self.lbl_title.setText(project.title if project else _("binder_title"))

    def refresh(self, select_id: str | None = None) -> None:
        """Bygger om trädet ur modellen och behåller markeringen."""
        keep = select_id or self.current_node_id()
        self.model.clear()
        self.model.setHorizontalHeaderLabels([_("binder_title")])
        if self.project is None:
            return

        def add(parent_item, parent_id):
            for node in self.project.children(parent_id):
                item = QStandardItem(f"{ICONS.get(node.type, '•')} {node.title}")
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
        if keep:
            self.select_node(keep)

    def current_node_id(self) -> str | None:
        indexes = self.tree.selectionModel().selectedIndexes()
        if not indexes:
            return None
        return indexes[0].data(Qt.ItemDataRole.UserRole)

    def select_node(self, node_id: str) -> bool:
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
