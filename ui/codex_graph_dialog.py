"""ui/codex_graph_dialog.py — relationsgraf över codexet (2.22).

Samma rityta som valvets graf (`ui/graph_dialog.py`): entiteterna läggs på en
cirkel med radien efter hur många relationer de har, och relationerna ritas som
kanter. Ett klick på en nod väljer posten i codexpanelen, så grafen är en väg
tillbaka till karaktärsbladet och inte en bild vid sidan av.

Varför en tunn underklass i stället för en egen rityta: matematiken, ritningen,
hover och klickträffen ligger redan i `GraphCanvas` och `circle_layout`. Det som
skiljer är varifrån noderna kommer, och det är den enda biten som skrivs här.

    python -m ui.codex_graph_dialog      kör självprovet (offscreen)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from core.i18n import _, i18n
from ui.graph_dialog import GraphCanvas, circle_layout


class CodexGraphCanvas(GraphCanvas):
    """Relationsgrafen: entiteter som noder, relationer som kanter."""

    def __init__(self, codex, theme_mgr, parent=None):
        self.codex = codex
        # vault=None: underklassen fyller ytan själv, basklassen rör den inte.
        super().__init__(None, theme_mgr, parent)

    def rebuild(self) -> None:
        self.relayout()
        self.update()

    def relayout(self) -> None:
        self.nodes = []
        self.edges = []
        if self.codex is None:
            return
        entities = list(self.codex.entities())
        namn = {e.id: e.name for e in entities}
        kanter = set()
        for entity in entities:
            for rel in self.codex.relations(entity.id):
                if rel.to_id in namn and rel.from_id in namn:
                    kanter.add((namn[rel.from_id], namn[rel.to_id]))
        self.nodes, self.edges = circle_layout([e.name for e in entities],
                                               sorted(kanter), self.width(), self.height())
        for node, entity in zip(self.nodes, entities):
            # Klicket bär entitetens id — grafen är en väg tillbaka till bladet.
            node["path"] = entity.id


class CodexGraphDialog(QDialog):
    """Visar codexets entiteter och relationer."""

    entity_activated = pyqtSignal(str)     # klick på en nod: entitetens id

    def __init__(self, codex, theme_mgr, parent=None):
        super().__init__(parent)
        self.codex = codex
        self.theme_mgr = theme_mgr
        self.setWindowTitle(_("codex_graph_title"))
        self.setMinimumSize(720, 580)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        head = QHBoxLayout()
        self.lbl_heading = QLabel("🕸 " + _("codex_graph_title"))
        self.lbl_heading.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        head.addWidget(self.lbl_heading)
        head.addStretch()
        self.btn_refresh = QPushButton("⟳ " + _("graph_btn_refresh"))
        self.btn_refresh.clicked.connect(self._refresh)
        head.addWidget(self.btn_refresh)
        layout.addLayout(head)

        self.lbl_hint = QLabel(_("codex_graph_hint"))
        self.lbl_hint.setWordWrap(True)
        layout.addWidget(self.lbl_hint)

        self.canvas = CodexGraphCanvas(codex, theme_mgr, self)
        self.canvas.node_activated.connect(self._on_node)
        layout.addWidget(self.canvas, 1)

        self.lbl_count = QLabel("")
        layout.addWidget(self.lbl_count)

        self._update_count()
        i18n.language_changed.connect(self.retranslate_ui)

    def _on_node(self, entity_id: str) -> None:
        """Ett klick på en nod väljer posten i panelen och stänger grafen."""
        self.entity_activated.emit(entity_id)
        self.accept()

    def _refresh(self) -> None:
        self.canvas.rebuild()
        self._update_count()

    def _update_count(self) -> None:
        antal = len(self.canvas.nodes) if self.canvas.nodes else 0
        self.lbl_count.setText(_("codex_graph_count", nodes=antal,
                                 edges=len(self.canvas.edges)))

    def retranslate_ui(self) -> None:
        self.setWindowTitle(_("codex_graph_title"))
        self.lbl_heading.setText("🕸 " + _("codex_graph_title"))
        self.lbl_hint.setText(_("codex_graph_hint"))
        self.btn_refresh.setText("⟳ " + _("graph_btn_refresh"))
        self._update_count()


def _self_check() -> int:
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import tempfile
    import shutil
    from PyQt6.QtCore import QEvent, QPointF
    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtWidgets import QApplication
    from core.storybible import StoryBible

    app = QApplication.instance() or QApplication([])   # noqa: F841
    checks = 0
    failures = 0

    def kolla(ok, text):
        nonlocal checks, failures
        checks += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            failures += 1

    root = tempfile.mkdtemp(prefix="codex-graph-")
    try:
        with StoryBible(os.path.join(root, "codex.sqlite")) as codex:
            anna = codex.add_entity("Anna")
            bo = codex.add_entity("Bo")
            staden = codex.add_entity("Hamnstaden", type="place")
            codex.add_relation(anna.id, bo.id, "syster till")
            codex.add_relation(anna.id, staden.id, "kommer från")

            dialog = CodexGraphDialog(codex, _ThemeStub())
            canv = dialog.canvas
            kolla(len(canv.nodes) == 3, f"en nod per entitet ({len(canv.nodes)})")
            kolla(len(canv.edges) == 2, f"en kant per relation ({len(canv.edges)})")
            kolla(all(n["resolved"] for n in canv.nodes), "och alla noder är kända poster")
            kolla(sorted(n["title"] for n in canv.nodes)
                  == ["Anna", "Bo", "Hamnstaden"], "med entiteternas namn")
            kolla(canv.nodes[0]["path"] == anna.id,
                  "och noden bär entitetens id, inte en filmsökväg")
            kolla("2" in dialog.lbl_count.text() or "3" in dialog.lbl_count.text(),
                  f"räknaren visar grafen ({dialog.lbl_count.text()})")

            # Klicket: en nod mitt på sin egen punkt väljer posten.
            träff = []
            dialog.entity_activated.connect(lambda eid: träff.append(eid))
            pos = canv.nodes[0]["pos"]
            canv.mousePressEvent(QMouseEvent(
                QEvent.Type.MouseButtonPress, QPointF(pos.x(), pos.y()),
                Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier))
            kolla(träff == [anna.id], f"klicket på noden väljer posten ({träff})")

            # En relation till en borttagen post får inte bli en kant till ingenting.
            codex.remove_relation(anna.id, bo.id, "syster till")
            canv.rebuild()
            kolla(len(canv.edges) == 1, f"och en borttagen relation försvinner ({len(canv.edges)})")

            tom = StoryBible(os.path.join(root, "tom.sqlite"))
            tom_dialog = CodexGraphDialog(tom, _ThemeStub())
            kolla(tom_dialog.canvas.nodes == [], "ett tomt codex ger en tom graf")
            tom.close()
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"codex_graph_dialog: {checks - failures} av {checks} kontroller gröna")
    return failures


class _ThemeStub:
    """Tema-stubbe: provet ritar inte på en skärm utan prövar datan och klicket."""

    def __init__(self):
        from PyQt6.QtCore import QObject, pyqtSignal

        class _Signal(QObject):
            theme_changed = pyqtSignal()

        self._signal = _Signal()
        self.theme_changed = self._signal.theme_changed
        self.current = {"canvas_bg": "#000000", "canvas_border": "#333333",
                        "text_color": "#ffffff", "text_muted": "#888888",
                        "accent": "#ff8800"}

    def __getattr__(self, namn):
        raise AttributeError(namn)


if __name__ == "__main__":
    raise SystemExit(_self_check())
