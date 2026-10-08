"""
ui/plot_grid.py — scenöversikt, plot-tavla och tidslinje (fas 2.9).

En rad per scen ur manuset, med det som går att jämföra: tråd (etiketter), POV,
status, när i berättelsen den händer, ord och ordmål. Tabellen är projektets
tredje vy över samma sak — korktavlan visar korten, trädet strukturen, och
den här visar *mönstret*: vilka trådar som löper genom boken och hur scenerna
ligger i tidsordning i stället för i lässtordning.

Sorteringen är hela poängen. Dabbles plot-tavla visar huvudtråd och sidotrådar
sida vid sida; här är det samma tabell sorterad efter tråd, POV eller status.
"Tidslinje" sorterar på scenens egen tid (`when`) med lässtordningen som
ordningsföljd när tiden är tom eller lika — en grafisk tidslinje är en egen vy
och byggs den dagen någon saknar den.

Ett klick på scenens titel öppnar scenen; dubbelklick i de andra kolumnerna
ändrar dem. Titeln är därför inte redigerbar: ett klick skall inte kunna bli
både "öppna" och "ändra".
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QStyledItemDelegate, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from core import story_elements
from core.i18n import _, i18n

# (nyckel, fält på noden, redigerbar, bredd)
COLUMNS = (
    ("grid_col_scene", None, False, 0),          # 0 = töjbar
    ("grid_col_part", None, False, 120),
    ("grid_col_thread", "labels", True, 170),
    ("grid_col_pov", "pov", True, 96),
    ("grid_col_status", "status", True, 110),
    ("grid_col_when", "when", True, 110),
    ("grid_col_elements", None, False, 60),
    ("grid_col_words", None, False, 62),
    ("grid_col_target", "target_words", True, 62),
    ("grid_col_revision", "revision", True, 70),
)
(COL_TITLE, COL_PART, COL_THREAD, COL_POV, COL_STATUS, COL_WHEN, COL_ELEMENTS, COL_WORDS,
 COL_TARGET, COL_REVISION) = range(len(COLUMNS))

SORTS = ("manuscript", "timeline", "pov", "status", "elements")
DRAFTS = (1, 2, 3, 4, 5, 6, 7, 8, 9)             # utkast 1–9, som i sceninspektören
RANGE_DRAFTS = (0,) + DRAFTS                     # 0 = alla utkast


class _StatusDelegate(QStyledItemDelegate):
    """Status är en av projektets statusar, inte vad som helst man råkar skriva."""

    def __init__(self, statuses, parent=None):
        super().__init__(parent)
        self.statuses = statuses

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItem("")
        editor.addItems(self.statuses)
        return editor

    def setEditorData(self, editor, index):
        editor.setCurrentText(str(index.data(Qt.ItemDataRole.EditRole) or ""))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)


class PlotGrid(QWidget):
    """Tabellen över manuset: en rad per scen, sorterbar som tidslinje eller tråd."""

    scene_selected = pyqtSignal(str)         # node_id
    structure_changed = pyqtSignal()         # metadata ändrad → spara manifestet
    events_requested = pyqtSignal()          # händelsetabellen (2.23) begärs

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PlotGrid")
        self.project = None
        self._rows = []                      # [(node, parentatitel)]
        self._loading = False

        rad = QHBoxLayout()
        rad.setContentsMargins(10, 8, 10, 4)
        rad.setSpacing(8)
        self.lbl_sort = QLabel()
        rad.addWidget(self.lbl_sort)
        self.combo_sort = QComboBox()
        for key in SORTS:
            self.combo_sort.addItem(_(f"grid_sort_{key}"), key)
        self.combo_sort.currentIndexChanged.connect(lambda *_: self.refresh())
        rad.addWidget(self.combo_sort)
        self.lbl_draft = QLabel()
        rad.addWidget(self.lbl_draft)
        self.combo_draft = QComboBox()
        for utkast in RANGE_DRAFTS:
            self.combo_draft.addItem(str(utkast), utkast)
        self.combo_draft.currentIndexChanged.connect(lambda *_: self.refresh())
        rad.addWidget(self.combo_draft)
        # Händelsetabellen (2.23): tidslinjens datahalva, i samma vy som sorterar
        # på tid — fönstret äger scenen som är öppen och öppnar den.
        self.btn_events = QPushButton("📅")
        self.btn_events.clicked.connect(self.events_requested.emit)
        rad.addWidget(self.btn_events)
        rad.addStretch(1)
        self.lbl_count = QLabel()
        rad.addWidget(self.lbl_count)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked
                                   | QTableWidget.EditTrigger.EditKeyPressed)
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.cellClicked.connect(self._on_cell_clicked)

        kolumn = QVBoxLayout(self)
        kolumn.setContentsMargins(0, 0, 0, 0)
        kolumn.setSpacing(0)
        kolumn.addLayout(rad)
        kolumn.addWidget(self.table, 1)

        i18n.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    # --------------------------------------------------------------- projektet

    def showEvent(self, e) -> None:
        """Fliken visas: läs om modellen — någon annan kan ha ändrat sedan sist."""
        super().showEvent(e)
        self.refresh()

    def set_project(self, project) -> None:
        self.project = project
        self.refresh()

    def set_statuses(self, statuses) -> None:
        """Projektets statusar till statuskolumnens meny."""
        self.table.setItemDelegateForColumn(COL_STATUS, _StatusDelegate(list(statuses or []), self))

    def refresh(self) -> None:
        """Bygger om raderna ur modellen, i den ordning som valts."""
        self._loading = True
        self.table.setRowCount(0)
        self._rows = []
        if self.project is not None:
            self._rows = self._ordered_scenes()
        self.table.setRowCount(len(self._rows))
        for rad, (node, del_titel) in enumerate(self._rows):
            self._fill_row(rad, node, del_titel)
        self._loading = False
        valt_utkast = int(self.combo_draft.currentData() or 0)
        if valt_utkast:
            totalt = len(self.project.manuscript()) if self.project is not None else 0
            self.lbl_count.setText(_("grid_count_draft", n=len(self._rows), total=totalt,
                                     draft=valt_utkast))
        else:
            self.lbl_count.setText(_("grid_count", n=len(self._rows)))

    def _fill_row(self, rad: int, node, del_titel: str) -> None:
        varden = {
            COL_TITLE: node.title,
            COL_PART: del_titel,
            COL_THREAD: ", ".join(node.labels),
            COL_POV: node.pov,
            COL_STATUS: node.status,
            COL_WHEN: node.when,
            COL_ELEMENTS: "%d/%d" % (story_elements.scene_row(node)["filled"],
                                     story_elements.TOTAL),
            COL_WORDS: str(self.project.words(node.id) if self.project else 0),
            COL_TARGET: str(node.target_words or ""),
            COL_REVISION: str(node.revision or 1),
        }
        for kol, värde in varden.items():
            item = QTableWidgetItem(värde)
            _, fält, redigerbar, _bredd = COLUMNS[kol]
            if not redigerbar:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if kol == COL_TITLE:
                item.setData(Qt.ItemDataRole.UserRole, node.id)
                if node.synopsis:
                    item.setToolTip(node.synopsis)
            if kol in (COL_ELEMENTS, COL_WORDS, COL_TARGET, COL_REVISION):
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                      | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(rad, kol, item)

    def _ordered_scenes(self) -> list:
        """Scenerna i vald ordning, med sin närmaste del/kapitel-rubrik.

        Utkastfiltret är revisionsläget: välj utkast 2 och tabellen visar bara
        de scener som nått dit — arbetet blir en lista i stället för ett helt
        manus.
        """
        valt_utkast = int(self.combo_draft.currentData() or 0)
        manus = [n for n in self.project.manuscript()
                 if valt_utkast == 0 or int(n.revision or 1) == valt_utkast]
        scener = [(n, self._part_title(n)) for n in manus]
        nyckel = self.combo_sort.currentData() or "manuscript"
        if nyckel == "timeline":
            # Tom tid sist: en scen utan tid i berättelsen hör inte först.
            scener.sort(key=lambda p: (not p[0].when, p[0].when))
        elif nyckel == "pov":
            scener.sort(key=lambda p: (p[0].pov.casefold(), p[1]))
        elif nyckel == "status":
            scener.sort(key=lambda p: (p[0].status.casefold(), p[1]))
        elif nyckel == "elements":
            # Story Map med luckorna först: den scen som saknar flest svar är
            # den författaren har något att göra i.
            scener.sort(key=lambda p: (story_elements.scene_row(p[0])["filled"], p[1]))
        return scener

    def _part_title(self, node) -> str:
        """Närmaste rubrik ovanför scenen: kapitlet, annars delen."""
        parent = node.parent
        while parent:
            över = self.project.by_id(parent)
            if över is None:
                return ""
            if över.type in ("part", "chapter"):
                return över.title
            parent = över.parent
        return ""

    # -------------------------------------------------------------- ändringar

    def _on_cell_clicked(self, rad: int, kol: int) -> None:
        if kol == COL_TITLE and 0 <= rad < len(self._rows):
            self.scene_selected.emit(self._rows[rad][0].id)

    def _on_item_changed(self, item) -> None:
        if self._loading or self.project is None:
            return
        rad, kol = item.row(), item.column()
        if not (0 <= rad < len(self._rows)):
            return
        _, fält, redigerbar, _bredd = COLUMNS[kol]
        if not redigerbar or fält is None:
            return
        node = self._rows[rad][0]
        text = item.text().strip()
        if fält == "labels":
            värde = [t.strip() for t in text.split(",") if t.strip()]
        elif fält in ("target_words", "revision"):
            try:
                värde = int(text or 0)
            except ValueError:
                värde = int(getattr(node, fält) or 0)
                self._loading = True
                item.setText(str(värde or ""))
                self._loading = False
            if fält == "revision":
                värde = max(1, min(9, värde or 1))     # samma gränser som inspektören
                if värde != int(getattr(node, fält) or 1):
                    self._loading = True
                    item.setText(str(värde))
                    self._loading = False
        else:
            värde = text
        if getattr(node, fält) == värde:
            return
        self.project.set_meta(node.id, **{fält: värde})
        self.structure_changed.emit()
        if fält == "labels":              # etiketterna styr samlingarna — bygg om
            self.refresh()

    # -------------------------------------------------------------- tema/språk

    def retranslate_ui(self) -> None:
        for kol, (nyckel, _fält, _red, bredd) in enumerate(COLUMNS):
            self.table.setHorizontalHeaderItem(kol, QTableWidgetItem(_(nyckel)))
            if bredd:
                self.table.setColumnWidth(kol, bredd)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(
            COL_TITLE, self.table.horizontalHeader().ResizeMode.Stretch)
        self.lbl_sort.setText(_("grid_sort"))
        self.lbl_draft.setText(_("grid_draft"))
        self.btn_events.setText(_("grid_btn_events"))
        self.btn_events.setToolTip(_("grid_events_tooltip"))
        valt = self.combo_sort.currentData()
        self.combo_sort.blockSignals(True)
        self.combo_sort.clear()
        for key in SORTS:
            self.combo_sort.addItem(_(f"grid_sort_{key}"), key)
        index = self.combo_sort.findData(valt)
        self.combo_sort.setCurrentIndex(max(0, index))
        self.combo_sort.blockSignals(False)
        valt_utkast = self.combo_draft.currentData()
        self.combo_draft.blockSignals(True)
        self.combo_draft.clear()
        self.combo_draft.addItem(_("grid_draft_all"), 0)
        for utkast in DRAFTS:
            self.combo_draft.addItem(str(utkast), utkast)
        utkast_index = self.combo_draft.findData(valt_utkast)
        self.combo_draft.setCurrentIndex(max(0, utkast_index))
        self.combo_draft.blockSignals(False)
        self.refresh()
