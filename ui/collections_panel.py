"""ui/collections_panel.py — samlingar: handplockade grupper och sparade sökningar.

En samling är en vy över manuset. Den pekar på scenerna där de ligger, så
binderordningen rörs aldrig — panelen visar samma scener i läsordning, och ett
klick öppnar scenen i editorn.

    python -m ui.collections_panel      kör självprovet (offscreen)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QMessageBox, QToolButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from core import collections as collections_mod
from core.i18n import _, i18n

NODE_ROLE = Qt.ItemDataRole.UserRole
KIND_ROLE = Qt.ItemDataRole.UserRole + 1


class SearchDialog(QDialog):
    """Namn och fråga i ett steg — två fält i samma ruta i stället för två rutor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("collections_search_title"))
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.input_name = QLineEdit()
        self.input_query = QLineEdit()
        self.input_query.setPlaceholderText(_("collections_query_hint"))
        form.addRow(_("collections_name"), self.input_name)
        form.addRow(_("collections_query"), self.input_query)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self) -> tuple[str, str]:
        return self.input_name.text().strip(), self.input_query.text().strip()


class CollectionsPanel(QWidget):
    """Träd över projektets samlingar. Ett klick på en scen öppnar den."""

    scene_selected = pyqtSignal(str)     # node_id
    changed = pyqtSignal()               # samlingarna ändrades, spara manifestet
    read_requested = pyqtSignal(str)     # läs samlingen som en sammanhängande text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.active_scene_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.lbl_hint = QLabel(_("collections_empty"))
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.lbl_hint)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._on_clicked)
        self.tree.itemDoubleClicked.connect(self._on_double_clicked)
        layout.addWidget(self.tree, 1)

        row = QHBoxLayout()
        row.setSpacing(2)
        self.buttons: list[QToolButton] = []
        self._tip_widgets: list[tuple[QToolButton, str]] = []
        for icon, key, slot in (
            ("＋", "collections_new", self.new_manual),
            ("🔍", "collections_new_search", self.new_search),
            ("★", "collections_toggle", self.toggle_active_scene),
            ("✏️", "collections_rename", self.rename_current),
            ("🗑", "collections_delete", self.delete_current),
            ("▶", "collections_read", self.read_current),
        ):
            button = QToolButton()
            button.setText(icon)
            button.setToolTip(_(key))
            button.clicked.connect(lambda _checked=False, fn=slot: fn())
            row.addWidget(button)
            self.buttons.append(button)
            self._tip_widgets.append((button, key))
        row.addStretch(1)
        layout.addLayout(row)

        i18n.language_changed.connect(self.retranslate_ui)
        self.set_project(None)

    # ------------------------------------------------------------------ data

    def set_project(self, project) -> None:
        self.project = project
        self.refresh()

    def set_active_scene(self, node_id) -> None:
        """Vilken scen som är markerad i manuset — ★ lägger den i samlingen."""
        self.active_scene_id = node_id

    def refresh(self) -> None:
        vald = self.current_collection_id()
        self.tree.clear()
        has = self.project is not None
        self.lbl_hint.setVisible(not has or not self.project.collections)
        self.lbl_hint.setText(_("collections_no_project") if not has else _("collections_empty"))
        for button in self.buttons:
            button.setEnabled(has)
        if not has:
            return
        for collection in self.project.collections:
            nodes = self.project.select_collection(collection.id)
            topp = QTreeWidgetItem([
                f"{collection.name}  ({len(nodes)})"])
            topp.setData(0, NODE_ROLE, collection.id)
            topp.setData(0, KIND_ROLE, collection.kind)
            beskrivning = collections_mod.describe(collection)
            if beskrivning:
                topp.setToolTip(0, beskrivning)
            for node in nodes:
                barn = QTreeWidgetItem([f"{node.title}   {node_meta(self.project, node)}"])
                barn.setData(0, NODE_ROLE, node.id)
                barn.setData(0, KIND_ROLE, "scene")
                topp.addChild(barn)
            self.tree.addTopLevelItem(topp)
        self.tree.expandAll()
        if vald:
            self.select_collection(vald)

    # ------------------------------------------------------------- markering

    def current_collection_id(self):
        item = self.tree.currentItem()
        if item is None:
            return None
        while item.parent() is not None:
            item = item.parent()
        return item.data(0, NODE_ROLE)

    def select_collection(self, collection_id: str) -> bool:
        for row in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(row)
            if item.data(0, NODE_ROLE) == collection_id:
                self.tree.setCurrentItem(item)
                return True
        return False

    # -------------------------------------------------------------- ändringar

    def new_manual(self, name: str = "") -> str | None:
        if self.project is None:
            return None
        if not name:
            name, ok = QInputDialog.getText(self, _("collections_new"), _("collections_name"))
            if not ok or not name.strip():
                return None
        collection = self.project.add_collection(name)
        if self.active_scene_id:
            self.project.toggle_in_collection(collection.id, self.active_scene_id)
        self.changed.emit()
        self.refresh()
        self.select_collection(collection.id)
        return collection.id

    def new_search(self, name: str = "", query: str = "") -> str | None:
        if self.project is None:
            return None
        if not name and not query:
            dialog = SearchDialog(self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return None
            name, query = dialog.values()
            if not name and not query:
                return None
        collection = self.project.add_collection(
            name, kind=collections_mod.SEARCH, query=query)
        self.changed.emit()
        self.refresh()
        self.select_collection(collection.id)
        return collection.id

    def rename_current(self) -> bool:
        collection_id = self.current_collection_id()
        if self.project is None or collection_id is None:
            return False
        collection = self.project.collection(collection_id)
        name, ok = QInputDialog.getText(self, _("collections_rename"),
                                        _("collections_name"), text=collection.name)
        if not ok or not name.strip():
            return False
        return self.rename(collection_id, name)

    def rename(self, collection_id: str, name: str) -> bool:
        if self.project is None or not name.strip():
            return False
        self.project.collection(collection_id).name = name.strip()
        self.changed.emit()
        self.refresh()
        return True

    def delete_current(self) -> bool:
        return self.delete(self.current_collection_id())

    def delete(self, collection_id, ask: bool = True) -> bool:
        if self.project is None or collection_id is None:
            return False
        if ask:
            answer = QMessageBox.question(
                self, _("collections_delete"),
                _("collections_delete_ask", name=self.project.collection(collection_id).name))
            if answer != QMessageBox.StandardButton.Yes:
                return False
        gone = self.project.remove_collection(collection_id)
        if gone:
            self.changed.emit()
            self.refresh()
        return gone

    def toggle_active_scene(self) -> bool:
        """Lägger den scen som är markerad i manuset i den valda samlingen."""
        collection_id = self.current_collection_id()
        if self.project is None or collection_id is None or not self.active_scene_id:
            return False
        if self.project.collection(collection_id).kind != collections_mod.MANUAL:
            QMessageBox.information(self, _("collections_toggle"),
                                    _("collections_search_readonly"))
            return False
        return self.toggle(collection_id, self.active_scene_id)

    def toggle(self, collection_id, node_id) -> bool:
        """Tyst: lägger till eller tar bort. En sökning äger sina träffar själv."""
        if self.project is None or collection_id is None or not node_id:
            return False
        try:
            collection = self.project.collection(collection_id)
        except KeyError:
            return False
        if collection.kind != collections_mod.MANUAL:
            return False
        inside = self.project.toggle_in_collection(collection_id, node_id)
        self.changed.emit()
        self.refresh()
        return inside

    # ---------------------------------------------------------------- signaler

    def read_current(self) -> bool:
        """Ber läsaren visa samlingens scener som en sammanhängande text.

        Det är arbetsflödet ur forskningen: filtrera fram det som saknar
        redigering och arbeta igenom dem i tur och ordning utan att lämna texten.
        """
        cid = self.current_collection_id()
        if cid is None:
            return False
        self.read_requested.emit(cid)
        return True

    def _on_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        if item.data(0, KIND_ROLE) == "scene":
            self.scene_selected.emit(item.data(0, NODE_ROLE))

    def _on_double_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        if item.data(0, KIND_ROLE) != "scene":
            self.rename_current()

    def retranslate_ui(self) -> None:
        for widget, key in self._tip_widgets:
            widget.setToolTip(_(key))
        self.lbl_hint.setText(_("collections_no_project") if self.project is None
                              else _("collections_empty"))


def node_meta(project, node) -> str:
    """'1 200 ord' vid scenen i samlingen."""
    return _("scene_words", words=project.words(node.id))


# ------------------------------------------------------------------ självprov

def _self_check() -> int:
    import os
    import tempfile
    from pathlib import Path

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from core.project import Project, SCENE

    checks = 0
    failures: list[str] = []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    def rader(panel) -> list[str]:
        """Översta nivån och barnen, som text — vad ögat ser."""
        ut = []
        for i in range(panel.tree.topLevelItemCount()):
            topp = panel.tree.topLevelItem(i)
            ut.append(topp.text(0))
            for j in range(topp.childCount()):
                ut.append("  " + topp.child(j).text(0))
        return ut

    def topp(panel, nummer: int) -> str:
        return panel.tree.topLevelItem(nummer).text(0)

    def barn(panel, nummer: int, plats: int) -> str:
        return panel.tree.topLevelItem(nummer).child(plats).text(0)

    tmp = Path(tempfile.mkdtemp())
    book = Project.create(tmp / "bok", "Boken")
    kapitel = book.children(None)[0]
    ett = book.children(kapitel.id)[0]
    book.write(ett.id, "<p>Alfa beta gamma.</p>")
    book.set_meta(ett.id, status="Utkast")
    tva = book.add_node(SCENE, "Scen två", parent=kapitel.id)
    book.write(tva.id, "<p>Delta epsilon.</p>")
    book.set_meta(tva.id, status="Klar")

    panel = CollectionsPanel()
    check(panel.lbl_hint.isVisibleTo(panel) and panel.tree.topLevelItemCount() == 0,
          "utan projekt visas bara förklaringen")
    check(not panel.buttons[0].isEnabled(), "knapparna är avstängda utan projekt")

    panel.set_project(book)
    check(panel.tree.topLevelItemCount() == 0, "ett projekt utan samlingar är tomt i trädet")

    # handplockad samling: ★ lägger in den markerade scenen
    panel.set_active_scene(ett.id)
    manuell = panel.new_manual("Tråd A")
    check(panel.tree.topLevelItemCount() == 1, "samlingen skapas")
    check(topp(panel, 0).startswith("Tråd A"), f"den heter vad den skall ({topp(panel, 0)!r})")
    from core.i18n import _ as __

    check(barn(panel, 0, 0) == f"Scen 1   {__('scene_words', words=3)}",
          f"scenen står i samlingen med sitt ordantal ({barn(panel, 0, 0)!r})")
    check("(1)" in topp(panel, 0), f"antalet står i rubriken ({topp(panel, 0)!r})")

    panel.set_active_scene(tva.id)
    panel.toggle_active_scene()
    check("(2)" in topp(panel, 0), f"en scen till läggs in ({topp(panel, 0)!r})")
    check(barn(panel, 0, 1).startswith("Scen två"), f"i manusets ordning ({barn(panel, 0, 1)!r})")
    panel.toggle_active_scene()
    check("(1)" in topp(panel, 0), "och kan tas ur igen")

    # sparad sökning
    sok = panel.new_search("Utkast", "status:Utkast")
    check(panel.tree.topLevelItemCount() == 2, "sökningen blir en egen samling")
    check(barn(panel, 1, 0).startswith("Scen 1"), f"sökningen visar sin träff ({barn(panel, 1, 0)!r})")
    check(panel.tree.topLevelItem(1).toolTip(0) == "status:Utkast",
          f"frågan syns i tipset ({panel.tree.topLevelItem(1).toolTip(0)!r})")

    # en sökning äger sina träffar
    panel.set_active_scene(tva.id)
    check(panel.toggle(sok, tva.id) is False, "en sökning kan inte fyllas på för hand")
    check("(1)" in topp(panel, 1), f"och antalet står kvar ({topp(panel, 1)!r})")

    # klick på en scen i samlingen öppnar den
    sedda: list[str] = []
    panel.scene_selected.connect(sedda.append)
    panel._on_clicked(panel.tree.topLevelItem(0).child(0), 0)
    check(sedda == [ett.id], f"klicket ger scenens id ({sedda})")

    # byta namn och ta bort
    check(panel.rename(manuell, "Tråd B") is True, "samlingen kan byta namn")
    check(topp(panel, 0).startswith("Tråd B"), f"och heter det nya ({topp(panel, 0)!r})")
    check(panel.project.collection(manuell).name == "Tråd B", "namnet ligger i modellen")

    kast = panel.new_manual("Kastas")
    check(panel.tree.topLevelItemCount() == 3, "en tredje samling skapas")
    check(panel.delete(kast, ask=False) is True, "en samling kan tas bort")
    check(panel.tree.topLevelItemCount() == 2, "och försvinner ur trädet")
    check(panel.delete("finns_inte", ask=False) is False, "okänt id ger inget")

    # en scen som tas bort ur projektet faller ur samlingen
    book.delete_node(tva.id)
    panel.refresh()
    check("(1)" in topp(panel, 0), f"borttagen scen faller ur samlingen ({topp(panel, 0)!r})")

    # projektet stängt: panelen tömmer sig
    panel.set_project(None)
    check(panel.tree.topLevelItemCount() == 0 and not panel.buttons[0].isEnabled(),
          "panelen tömmer sig när projektet stängs")

    print(f"collections_panel: {checks - len(failures)} av {checks} kontroller gröna")
    for failure in failures:
        print(f"  ✗ {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
