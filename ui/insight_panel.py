"""ui/insight_panel.py — analysen i sidopanelen: upprepningar, namn och siffror.

Fynden kommer ur `core.analysis` (upprepade ord och fraser, namnvarianter,
versaler/gemener, codexnamn som aldrig nämns) och siffrorna ur
`core.story_stats`. Panelen äger ingen data: den får projektet och codexet, och
ett klick på en rad ber fönstret öppna scenen och markera textstället — så är
rapporten en väg in i texten i stället för en siffra vid sidan av den.

Analysen kostar tid (mätt: 1,8 s på en bok på 120 000 ord), så den körs när
författaren ber om den och inte vid varje tangenttryckning.

    python -m ui.insight_panel      kör självprovet (offscreen)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from core import analysis, story_stats
from core.i18n import _, i18n

NODE_ROLE = Qt.ItemDataRole.UserRole
QUOTE_ROLE = Qt.ItemDataRole.UserRole + 1
OCCURRENCE_ROLE = Qt.ItemDataRole.UserRole + 2

# Ordningen är rapportens: upprepningarna först, de är det läsaren åtgärdar.
KINDS = ("repeat", "phrase", "name_variant", "capitalisation", "unused")


class InsightPanel(QWidget):
    """Rapporten över manuset — och vägen tillbaka in i texten."""

    scene_requested = pyqtSignal(str, str, int)   # node_id, quote, förekomst
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.bible = None
        self.report = None
        self.stats = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        row = QHBoxLayout()
        self.btn_run = QPushButton(_("insight_run"))
        self.btn_run.clicked.connect(self.refresh)
        row.addWidget(self.btn_run)
        self.combo_kind = QComboBox()
        self.combo_kind.addItem(_("insight_kind_all"), "")
        for kind in KINDS:
            self.combo_kind.addItem(_(f"insight_kind_{kind}"), kind)
        self.combo_kind.currentIndexChanged.connect(self._fill)
        row.addWidget(self.combo_kind, 1)
        layout.addLayout(row)

        self.label_summary = QLabel(_("insight_empty"))
        self.label_summary.setWordWrap(True)
        layout.addWidget(self.label_summary)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels([_("insight_col_finding"), _("insight_col_count"),
                                   _("insight_col_scene")])
        self.tree.setRootIsDecorated(False)
        self.tree.itemClicked.connect(self._activate)
        layout.addWidget(self.tree, 1)
        i18n.language_changed.connect(self.retranslate_ui)

    # ------------------------------------------------------------- projektet

    def set_project(self, project, bible=None) -> None:
        """Ta emot projektet. Rapporten körs först när någon ber om den."""
        self.project = project
        self.bible = bible
        self.report = None
        self.stats = None
        self.tree.clear()
        self.label_summary.setText(_("insight_empty"))

    def retranslate_ui(self) -> None:
        """Språkbytet: rubriker och värden är i18n-nycklar, som i de andra panelerna."""
        self.btn_run.setText(_("insight_run"))
        for index in range(self.combo_kind.count()):
            self.combo_kind.setItemText(
                index, _(f"insight_kind_{self.combo_kind.itemData(index) or 'all'}"))
        self.tree.setHeaderLabels([_("insight_col_finding"), _("insight_col_count"),
                                   _("insight_col_scene")])
        self._fill()
        if self.report is None:
            self.label_summary.setText(_("insight_empty"))

    def _entities(self):
        if self.bible is None:
            return None
        try:
            return self.bible.entities()
        except Exception:          # noqa: BLE001 — ett stängt codex får inte stoppa analysen
            return None

    def refresh(self) -> dict:
        """Kör analysen över hela manuset och fyller listan."""
        if self.project is None:
            self.report = None
            self.label_summary.setText(_("insight_empty"))
            self._fill()
            return {}
        self.report = analysis.report(self.project, self._entities())
        try:
            self.stats = story_stats.report(self.project, self.bible)
        except Exception:          # noqa: BLE001 — siffrorna är ett tillägg, inte kravet
            self.stats = None
        self._fill()
        return self.report

    # --------------------------------------------------------------- listan

    def _fill(self) -> None:
        self.tree.clear()
        if self.report is None:
            return
        valt = self.combo_kind.currentData() or ""
        fynd = [f for f in self.report["findings"] if not valt or f.kind == valt]
        for f in fynd:
            item = QTreeWidgetItem([f.quote or f.label, f.note, f.node_title])
            item.setData(0, NODE_ROLE, f.node_id)
            item.setData(0, QUOTE_ROLE, f.quote)
            item.setData(0, OCCURRENCE_ROLE, int(f.occurrence))
            item.setToolTip(0, f.quote or f.label)
            self.tree.addTopLevelItem(item)
        self.label_summary.setText(self._summary_text(len(fynd)))

    def _summary_text(self, visade: int) -> str:
        r = self.report or {}
        text = _("insight_summary").format(scenes=r.get("scenes", 0),
                                           words=r.get("words", 0),
                                           findings=visade)
        pov = (self.stats or {}).get("pov") or {}
        if pov:
            topp = ", ".join(f"{namn} {antal}" for namn, antal in list(pov.items())[:3])
            text += " · " + _("insight_pov").format(pov=topp)
        return text

    def _activate(self, item: QTreeWidgetItem, _column: int = 0) -> None:
        """Ett klick: be fönstret öppna scenen vid textstället."""
        node_id = item.data(0, NODE_ROLE) or ""
        quote = item.data(0, QUOTE_ROLE) or ""
        if not node_id or not quote:
            self.status_message.emit(_("insight_no_place"))
            return
        self.scene_requested.emit(node_id, quote, int(item.data(0, OCCURRENCE_ROLE) or 0))


def _self_check() -> int:
    """Panelen mot ett riktigt projekt: rader, filter, siffror och signalen."""
    import os
    import shutil
    import tempfile
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    from core.project import Project
    from core.storybible import StoryBible

    app = QApplication.instance() or QApplication([])   # noqa: F841
    fel = 0
    antal = 0

    def kolla(ok, text):
        nonlocal fel, antal
        antal += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            fel += 1

    root = tempfile.mkdtemp(prefix="insight-check-")
    try:
        project = Project.create(root + "/bok", "Analysprov", template="enkel")
        sida = project.manuscript()[0]
        project.write(sida.id, "<p>tyst tyst tyst blorpt blorpt blorpt "
                              "han sade han sade han sade.</p>")
        andra = project.add_node("scene", "Andra")
        project.write(andra.id, "<p>blorpt igen</p>")

        panel = InsightPanel()
        kolla(panel.report is None, "ingen rapport innan någon bett om den")
        panel.set_project(project)
        r = panel.refresh()
        kolla(r["scenes"] == 2, f"båda scenerna räknas ({r['scenes']})")
        kolla(r["words"] == project.total_words(), "ordtalet är projektets eget")
        kolla(any(f.label == "tyst" for f in r["findings"]), "upprepningen hittas")
        kolla(panel.tree.topLevelItemCount() == len(r["findings"]),
              f"listan visar alla fynd ({panel.tree.topLevelItemCount()} av {len(r['findings'])})")
        kolla("ord" in panel.label_summary.text(), "sammanfattningen skrivs")

        # Filtret: bara fraser
        panel.combo_kind.setCurrentIndex(panel.combo_kind.findData("phrase"))
        fraser = [f for f in r["findings"] if f.kind == "phrase"]
        kolla(panel.tree.topLevelItemCount() == len(fraser),
              f"filtret visar bara fraser ({panel.tree.topLevelItemCount()} av {len(fraser)})")
        panel.combo_kind.setCurrentIndex(0)

        # Klicket: signalen bär scen, citat och förekomst — och citatet finns i texten
        tagen = {}
        panel.scene_requested.connect(lambda nid, q, occ: tagen.update(node=nid, quote=q, occ=occ))
        rader = [panel.tree.topLevelItem(i) for i in range(panel.tree.topLevelItemCount())]
        rad = next(r for r in rader if r.data(0, QUOTE_ROLE) == "tyst")
        panel._activate(rad)
        kolla(tagen.get("node") == sida.id and tagen.get("quote") == "tyst" and tagen.get("occ") == 0,
              f"klicket bär scen, citat och förekomst ({tagen})")

        # Codexet: en post som aldrig nämns skall ge ett fynd, inte en krasch
        with StoryBible(root + "/bok/codex.sqlite") as bible:
            bible.add_entity("AldrigNämnd")
            panel.set_project(project, bible)
            r2 = panel.refresh()
            kolla(any(f.kind == "unused" for f in r2["findings"]),
                  "ett codexnamn som inte nämns blir ett fynd")
            kolla(panel.stats and panel.stats["scene_count"] == 2, "siffrorna följer med")

        panel.set_project(None, None)
        kolla(panel.tree.topLevelItemCount() == 0, "stängt projekt tömmer listan")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(f"insight_panel: {antal - fel} av {antal} kontroller gröna")
    return fel


if __name__ == "__main__":
    raise SystemExit(_self_check())
