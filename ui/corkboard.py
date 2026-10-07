"""ui/corkboard.py — scenerna som kort: överblick och omordning av manuset.

Korten är samma noder som i trädet, i samma ordning. Ett klick öppnar scenen.
Kortvyn äger ingen data — den läser projektmodellen och säger till när ett kort
väljs.

    python -m ui.corkboard       kör självprovet (offscreen)
"""

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from core.i18n import _, i18n

CARD_WIDTH = 168
CARD_HEIGHT = 112


class Corkboard(QWidget):
    """Manusets scener som kort, i läsordning."""

    scene_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.list = QListWidget()
        self.list.setViewMode(QListWidget.ViewMode.IconMode)
        self.list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list.setMovement(QListWidget.Movement.Static)   # ordningen ägs av modellen
        self.list.setWordWrap(True)
        self.list.setSpacing(6)
        self.list.setGridSize(QSize(CARD_WIDTH, CARD_HEIGHT))
        self.list.setUniformItemSizes(True)
        self.list.itemClicked.connect(self._on_clicked)
        layout.addWidget(self.list)

        i18n.language_changed.connect(self.refresh)
        self.refresh()

    def set_project(self, project) -> None:
        self.project = project
        self.refresh()

    def refresh(self) -> None:
        """Bygger om korten ur modellen — manusets scener, i läsordning."""
        self.list.clear()
        if self.project is None:
            self.list.addItem(QListWidgetItem(_("corkboard_empty")))
            return
        scenes = self.project.manuscript()
        if not scenes:
            self.list.addItem(QListWidgetItem(_("corkboard_empty")))
            return
        for node in scenes:
            self.list.addItem(self._card_for(node))

    def _card_for(self, node) -> QListWidgetItem:
        # ponytail: kortet är text, inte en egen widget med layout — färre rader
        # och mindre som kan gå sönder. Byt till en QStyledItemDelegate när
        # korten behöver färg per status eller bild.
        lines = [node.title]
        if node.status:
            lines.append(f"• {node.status}")
        if node.synopsis:
            lines.append(node.synopsis.strip().replace("\n", " ")[:80])
        item = QListWidgetItem("\n".join(lines))
        item.setData(Qt.ItemDataRole.UserRole, node.id)
        item.setToolTip(node.synopsis or node.title)
        return item

    def select_node(self, node_id: str) -> bool:
        for row in range(self.list.count()):
            item = self.list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == node_id:
                self.list.setCurrentItem(item)
                return True
        return False

    def current_node_id(self):
        item = self.list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_clicked(self, item) -> None:
        node_id = item.data(Qt.ItemDataRole.UserRole)
        if node_id:
            self.scene_selected.emit(node_id)


def _self_check() -> int:
    import os
    import tempfile
    from pathlib import Path
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from core.project import Project, SCENE

    checks = 0
    failures = []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    tmp = tempfile.mkdtemp()
    board = Corkboard()
    check(board.list.count() == 1, f"utan projekt visas en förklaring ({board.list.count()})")

    book = Project.create(Path(tmp) / "bok", "Bok")
    kapitel = book.children(None)[0]
    forsta = book.children(kapitel.id)[0]
    forsta.synopsis = "Hon kommer hem."
    forsta.status = "Utkast"
    andra = book.add_node(SCENE, "Scen 2", parent=kapitel.id)

    board.set_project(book)
    check(board.list.count() == 2, f"ett kort per scen ({board.list.count()})")
    text0 = board.list.item(0).text()
    check("Scen 1" in text0 and "Utkast" in text0 and "Hon kommer hem." in text0,
          f"kortet visar titel, status och synopsis ({text0!r})")
    check(board.list.item(1).data(Qt.ItemDataRole.UserRole) == andra.id,
          "kortet bär nodens id")
    check(board.list.item(1).text().strip() == "Scen 2",
          f"ett kort utan status och synopsis är bara titeln ({board.list.item(1).text()!r})")

    # markering två vägar
    seen = []
    board.scene_selected.connect(seen.append)
    check(board.select_node(andra.id) and board.current_node_id() == andra.id,
          "en scen kan markeras från kortvyn")
    board._on_clicked(board.list.item(1))
    check(seen == [andra.id], f"klick ger rätt nod-id ({seen})")

    # en ny scen skall synas efter refresh
    tredje = book.add_node(SCENE, "Scen 3", parent=kapitel.id)
    board.refresh()
    check(board.list.count() == 3, f"refresh plockar upp en ny scen ({board.list.count()})")
    check(board.list.item(2).data(Qt.ItemDataRole.UserRole) == tredje.id,
          "korten följer manusets ordning")

    # tomt projekt
    tomt = Project.create(Path(tmp) / "tom", "Tom")
    tomt.delete_node(tomt.children(tomt.children(None)[0].id)[0].id)
    board.set_project(tomt)
    check(board.list.count() == 1, "ett projekt utan scener visar förklaringen")

    print(f"corkboard: {checks - len(failures)} av {checks} kontroller gröna")
    for failure in failures:
        print(f"  ✗ {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
