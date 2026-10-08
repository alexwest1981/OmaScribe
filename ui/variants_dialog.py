"""
ui/variants_dialog.py — manusvarianter: en namngiven ordning av scener (R01.14).

En variant förgrenar bara ORDNINGEN, inte innehållet: scenerna är samma filer
som förut, så en variant kan inte tappa text eller skriva över något annat.
Ett innehållsligt grenat manus kräver snapshots per scen (fas 3.1).

    Ny variant   — av kapitlet/scenen som var markerad, annars hela manuset
    ⬆ / ⬇        — flytta scenen i variantens ordning
    Byt ut…      — lägg en annan scen på platsen
    Jämför       — vad som skiljer varianten från manusets ordning
    Lägg på      — variantens ordning blir manusets (steg 4 i R01.14)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem,
    QMenu, QPushButton, QVBoxLayout, QWidget,
)

from core.i18n import _, i18n


class VariantsDialog(QDialog):
    """Namngivna ordningar av scener, vid sidan av manusets egen."""

    changed = pyqtSignal()          # något ändrades — spara manifestet

    def __init__(self, project, nodes=None, parent=None):
        super().__init__(parent)
        self.project = project
        self._source = list(nodes or project.manuscript())
        self.changed_count = 0

        self.setWindowTitle(_("variants_title"))
        self.resize(720, 460)

        layout = QVBoxLayout(self)
        self.lbl_hint = QLabel(_("variants_hint"))
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setStyleSheet("color: palette(mid);")
        layout.addWidget(self.lbl_hint)

        body = QHBoxLayout()
        self.lst_variants = QListWidget()
        self.lst_variants.currentRowChanged.connect(self._refresh_nodes)
        body.addWidget(self.lst_variants, 1)

        hoger = QVBoxLayout()
        self.lst_nodes = QListWidget()
        self.lst_nodes.currentRowChanged.connect(self._refresh_status)
        hoger.addWidget(self.lst_nodes, 1)
        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        hoger.addWidget(self.lbl_status)
        body.addLayout(hoger, 2)
        layout.addLayout(body, 1)

        knappar = QHBoxLayout()
        self.btn_new = QPushButton(_("variants_new"))
        self.btn_new.clicked.connect(self.new_variant)
        knappar.addWidget(self.btn_new)
        self.btn_delete = QPushButton(_("variants_delete"))
        self.btn_delete.clicked.connect(self.delete_variant)
        knappar.addWidget(self.btn_delete)
        knappar.addStretch(1)
        self.btn_up = QPushButton("⬆")
        self.btn_up.clicked.connect(lambda: self.move_node(-1))
        knappar.addWidget(self.btn_up)
        self.btn_down = QPushButton("⬇")
        self.btn_down.clicked.connect(lambda: self.move_node(1))
        knappar.addWidget(self.btn_down)
        self.btn_replace = QPushButton(_("variants_replace"))
        self.btn_replace.clicked.connect(self.replace_node)
        knappar.addWidget(self.btn_replace)
        self.btn_apply = QPushButton(_("variants_apply"))
        self.btn_apply.clicked.connect(self.apply_variant)
        knappar.addWidget(self.btn_apply)
        layout.addLayout(knappar)

        i18n.language_changed.connect(self.retranslate_ui)
        self.refresh()

    # ------------------------------------------------------------------ listan

    def current_variant(self):
        row = self.lst_variants.currentRow()
        if row < 0 or row >= len(self.project.variants):
            return None
        return self.project.variants[row]

    def refresh(self, keep: str | None = None) -> None:
        """Bygger om variantlistan och markerar en variant (senast rörda)."""
        self.lst_variants.blockSignals(True)
        self.lst_variants.clear()
        for variant in self.project.variants:
            antal = len(self.project.variant_nodes(variant["id"]))
            item = QListWidgetItem(_("variants_row", name=variant["name"], count=antal))
            item.setData(Qt.ItemDataRole.UserRole, variant["id"])
            self.lst_variants.addItem(item)
        self.lst_variants.blockSignals(False)
        rad = 0
        if keep:
            for index, variant in enumerate(self.project.variants):
                if variant["id"] == keep:
                    rad = index
        if self.lst_variants.count():
            self.lst_variants.setCurrentRow(rad)
        self._refresh_nodes()

    def _refresh_nodes(self) -> None:
        """Variantens scener i variantens ordning."""
        self.lst_nodes.blockSignals(True)
        self.lst_nodes.clear()
        variant = self.current_variant()
        if variant is not None:
            borta = set(variant["nodes"]) - {n.id for n in self.project.variant_nodes(variant["id"])}
            for node in self.project.variant_nodes(variant["id"]):
                item = QListWidgetItem(node.title)
                item.setData(Qt.ItemDataRole.UserRole, node.id)
                self.lst_nodes.addItem(item)
            # Slingvariabeln får inte heta `_`: i18n-funktionen `_` används i
            # samma metod, och då blir den ett heltal i stället för en funktion.
            for _borta in borta:
                item = QListWidgetItem(_("variants_gone"))
                # En QListWidgetItem har ingen setEnabled — flaggan är rätt väg.
                # Utan det här kastade raden varje gång en scen tagits bort ur
                # manuset men låg kvar i en variant.
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                self.lst_nodes.addItem(item)
        self.lst_nodes.blockSignals(False)
        self._refresh_status()

    def _refresh_status(self) -> None:
        variant = self.current_variant()
        if variant is None:
            self.lbl_status.setText(_("variants_none"))
        else:
            diff = self.project.variant_diff(variant["id"])
            delar = []
            if diff["moved"]:
                delar.append(_("variants_moved", count=len(diff["moved"])))
            if diff["outside"]:
                delar.append(_("variants_outside", count=len(diff["outside"])))
            if diff["missing"]:
                delar.append(_("variants_missing", count=len(diff["missing"])))
            self.lbl_status.setText(" · ".join(delar) if delar else _("variants_same"))
        for knapp in (self.btn_delete, self.btn_up, self.btn_down, self.btn_replace,
                      self.btn_apply):
            knapp.setEnabled(variant is not None)
        self.btn_up.setEnabled(variant is not None and self.lst_nodes.currentRow() > 0)
        self.btn_down.setEnabled(
            variant is not None and 0 <= self.lst_nodes.currentRow() < self.lst_nodes.count() - 1)

    def _selected_node_id(self):
        item = self.lst_nodes.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item is not None else None

    # ----------------------------------------------------------------- ändringar

    def new_variant(self, name: str | None = None) -> dict:
        """Ny variant av det som var markerat i trädet, annars hela manuset."""
        if name is None:
            name, ok = QInputDialog.getText(self, _("variants_new"),
                                            _("variants_new_label"),
                                            text=_("variants_default_name",
                                                   count=len(self.project.variants) + 1))
            if not ok:
                return None
        variant = self.project.add_variant(name or "", self._source)
        self.changed.emit()
        self.refresh(keep=variant["id"])
        return variant

    def delete_variant(self) -> bool:
        variant = self.current_variant()
        if variant is None:
            return False
        if not self.project.delete_variant(variant["id"]):
            return False
        self.changed.emit()
        self.refresh()
        return True

    def move_node(self, delta: int) -> bool:
        variant = self.current_variant()
        node_id = self._selected_node_id()
        if variant is None or node_id is None:
            return False
        if not self.project.move_in_variant(variant["id"], node_id, delta):
            return False
        self.changed.emit()
        rad = self.lst_nodes.currentRow()
        self.refresh(keep=variant["id"])
        self.lst_nodes.setCurrentRow(max(0, min(rad + delta, self.lst_nodes.count() - 1)))
        return True

    def replace_node(self, node_id: str | None = None):
        """Lägger en annan scen på den markerade platsen."""
        variant = self.current_variant()
        rad = self.lst_nodes.currentRow()
        if variant is None or rad < 0:
            return False
        if node_id is None:
            menu = QMenu(self)
            redan = set(variant["nodes"])
            for node in self.project.manuscript():
                if node.id in redan:
                    continue
                menu.addAction(node.title, lambda nid=node.id: self._do_replace(nid, rad))
            if not menu.actions():
                return False
            menu.exec(self.btn_replace.mapToGlobal(self.btn_replace.rect().bottomLeft()))
            return True
        return self._do_replace(node_id, rad)

    def _do_replace(self, node_id: str, rad: int) -> bool:
        variant = self.current_variant()
        if variant is None or not self.project.replace_in_variant(variant["id"], rad, node_id):
            return False
        self.changed.emit()
        self.refresh(keep=variant["id"])
        self.lst_nodes.setCurrentRow(rad)
        return True

    def apply_variant(self) -> int:
        """Lägger variantens ordning på manuset. Antal flyttade scener."""
        variant = self.current_variant()
        if variant is None:
            return 0
        moved = self.project.apply_variant(variant["id"])
        self.changed_count += 1
        self.changed.emit()
        self.refresh(keep=variant["id"])
        self.lbl_status.setText(_("variants_applied", count=moved))
        return moved

    def retranslate_ui(self) -> None:
        self.setWindowTitle(_("variants_title"))
        self.lbl_hint.setText(_("variants_hint"))
        self.btn_new.setText(_("variants_new"))
        self.btn_delete.setText(_("variants_delete"))
        self.btn_replace.setText(_("variants_replace"))
        self.btn_apply.setText(_("variants_apply"))
        self.refresh(keep=(self.current_variant() or {}).get("id"))
