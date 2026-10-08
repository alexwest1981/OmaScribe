"""ui/events_dialog.py — händelsetabellen (2.23).

En rad per händelse: tid, vad som händer och vilka scener den spelas i. Tid och
beskrivning skrivs direkt i tabellen; scenkopplingen görs med knapparna, som
kopplar **scenen som är öppen** till den valda händelsen — samma händelse kan
alltså höra till flera scener, och en scen kan ha flera händelser.

Ändringarna går rakt in i projektet (som med all annan metadata) och `changed`
säger till när något skrivits, så tavlan och manifestet kan sparas.

    python -m ui.events_dialog      kör självprovet (offscreen)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from core import events as events_mod
from core.i18n import _, i18n

COL_WHEN, COL_TEXT, COL_SCENES = 0, 1, 2


class EventsDialog(QDialog):
    """Händelserna i projektet, i tidsordning."""

    changed = pyqtSignal()

    def __init__(self, project, current_scene_id: str = "", parent=None):
        super().__init__(parent)
        self.project = project
        self.current_scene_id = current_scene_id
        self._loading = False
        self.setWindowTitle(_("events_title"))
        self.setModal(True)
        self.resize(620, 420)

        layout = QVBoxLayout(self)
        self.lbl_hint = QLabel(_("events_hint"))
        self.lbl_hint.setWordWrap(True)
        layout.addWidget(self.lbl_hint)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            [_("events_col_when"), _("events_col_text"), _("events_col_scenes")])
        self.table.horizontalHeader().setSectionResizeMode(
            COL_TEXT, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemChanged.connect(self._on_item_changed)
        layout.addWidget(self.table, 1)

        rad = QHBoxLayout()
        self.btn_add = QPushButton("+")
        self.btn_add.clicked.connect(self.add_event)
        rad.addWidget(self.btn_add)
        self.btn_remove = QPushButton("−")
        self.btn_remove.clicked.connect(self.remove_event)
        rad.addWidget(self.btn_remove)
        self.btn_attach = QPushButton()
        self.btn_attach.clicked.connect(self.attach_current_scene)
        rad.addWidget(self.btn_attach)
        self.btn_detach = QPushButton()
        self.btn_detach.clicked.connect(self.detach_current_scene)
        rad.addWidget(self.btn_detach)
        rad.addStretch(1)
        layout.addLayout(rad)

        knappar = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        knappar.rejected.connect(self.reject)
        knappar.accepted.connect(self.accept)
        layout.addWidget(knappar)

        self.retranslate_ui()
        self._fill()
        i18n.language_changed.connect(self.retranslate_ui)

    # -------------------------------------------------------------- listan

    def _fill(self, keep: str = "") -> None:
        self._loading = True
        try:
            self.table.setRowCount(0)
            for event in events_mod.ordered(self.project):
                rad = self.table.rowCount()
                self.table.insertRow(rad)
                when = QTableWidgetItem(str(event["when"]))
                when.setData(Qt.ItemDataRole.UserRole, event["id"])
                self.table.setItem(rad, COL_WHEN, when)
                self.table.setItem(rad, COL_TEXT, QTableWidgetItem(str(event["text"])))
                scener = QTableWidgetItem(", ".join(events_mod.scene_titles(self.project, event)))
                scener.setFlags(scener.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(rad, COL_SCENES, scener)
        finally:
            self._loading = False
        if keep:
            self.select(keep)

    def select(self, event_id: str) -> None:
        for rad in range(self.table.rowCount()):
            if self.table.item(rad, COL_WHEN).data(Qt.ItemDataRole.UserRole) == event_id:
                self.table.selectRow(rad)
                return

    def selected_id(self) -> str:
        rad = self.table.currentRow()
        if rad < 0:
            return ""
        objekt = self.table.item(rad, COL_WHEN)
        return objekt.data(Qt.ItemDataRole.UserRole) if objekt else ""

    # -------------------------------------------------------------- skrivandet

    def add_event(self) -> str:
        event = events_mod.add_event(self.project, text="",
                                     scene_ids=[self.current_scene_id] if self.current_scene_id else [])
        self._fill(keep=event["id"])
        self.changed.emit()
        return event["id"]

    def remove_event(self) -> bool:
        event_id = self.selected_id()
        if not event_id or not events_mod.remove_event(self.project, event_id):
            return False
        self._fill()
        self.changed.emit()
        return True

    def attach_current_scene(self) -> bool:
        if not events_mod.attach(self.project, self.selected_id(), self.current_scene_id):
            return False
        self._fill(keep=self.selected_id())
        self.changed.emit()
        return True

    def detach_current_scene(self) -> bool:
        if not events_mod.detach(self.project, self.selected_id(), self.current_scene_id):
            return False
        self._fill(keep=self.selected_id())
        self.changed.emit()
        return True

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._loading:
            return
        rad = item.row()
        ankare = self.table.item(rad, COL_WHEN)
        event_id = ankare.data(Qt.ItemDataRole.UserRole) if ankare else ""
        if not event_id:
            return
        if item.column() == COL_WHEN:
            events_mod.update_event(self.project, event_id, when=item.text())
        elif item.column() == COL_TEXT:
            events_mod.update_event(self.project, event_id, text=item.text())
        else:
            return
        self.changed.emit()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(_("events_title"))
        self.lbl_hint.setText(_("events_hint"))
        self.table.setHorizontalHeaderLabels(
            [_("events_col_when"), _("events_col_text"), _("events_col_scenes")])
        self.btn_add.setToolTip(_("events_add"))
        self.btn_remove.setToolTip(_("events_remove"))
        self.btn_attach.setText(_("events_attach"))
        self.btn_detach.setText(_("events_detach"))


def _self_check() -> int:
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import shutil
    import tempfile
    from PyQt6.QtWidgets import QApplication
    from core.project import Project

    app = QApplication.instance() or QApplication([])   # noqa: F841
    checks = 0
    failures = 0

    def kolla(ok, text):
        nonlocal checks, failures
        checks += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            failures += 1

    root = tempfile.mkdtemp(prefix="events-dialog-")
    try:
        project = Project.create(root, "Händelsedialog", template="enkel")
        scen = project.manuscript()[0]

        def händelse(eid):
            e = events_mod.by_id(project, eid)
            if e is None:
                raise AssertionError(f"händelsen {eid} finns inte")
            return e

        dialog = EventsDialog(project, current_scene_id=scen.id)
        kolla(dialog.table.rowCount() == 0, "en tom tabell utan händelser")

        eid = dialog.add_event()
        kolla(dialog.table.rowCount() == 1, "en händelse läggs till")
        kolla(dialog.selected_id() == eid, f"och raden blir markerad ({dialog.selected_id()})")
        kolla(händelse(eid)["scenes"] == [scen.id],
              "med den öppna scenen kopplad")

        dialog.table.item(0, COL_WHEN).setText("dag 3")
        dialog.table.item(0, COL_TEXT).setText("Anna hittar nyckeln")
        kolla(händelse(eid)["when"] == "dag 3",
              "tid skrivs till projektet")
        kolla(händelse(eid)["text"] == "Anna hittar nyckeln",
              "och beskrivningen med den")
        kolla(dialog.table.item(0, COL_SCENES).text() == scen.title,
              f"scenkolumnen visar rubriken ({dialog.table.item(0, COL_SCENES).text()!r})")

        andra = project.add_node("scene", "Andra")
        dialog.current_scene_id = andra.id
        kolla(dialog.detach_current_scene() is False, "en oscen kan inte lossas")
        dialog.current_scene_id = scen.id
        kolla(dialog.detach_current_scene() is True, "men den kopplade kan")
        kolla(händelse(eid)["scenes"] == [], "och kopplingen försvinner")
        kolla(dialog.attach_current_scene() is True, "och kan sättas tillbaka")

        tagen = []
        dialog.changed.connect(lambda: tagen.append(1))
        kolla(dialog.remove_event() is True, "en händelse kan tas bort")
        kolla(dialog.table.rowCount() == 0, "och raden försvinner")
        kolla(tagen != [], "och ändringen sägs till om")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"events_dialog: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
