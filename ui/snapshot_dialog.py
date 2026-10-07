"""Versionshistorik för en scen: punkterna, skillnaden och vägen tillbaka (R01.6, R02.4).

Ändringarna visas som en unified diff — plus och minus i texten, samma tecken
som i en patch, med en svag ton bakom som förstärkning. Tecknet bär betydelsen,
färgen bär den inte ensam.

Rutan tar en ögonblicksbild av texten som ligger på disk just nu, så "spara en
punkt" kostar inget extra steg: skriv klart, öppna historiken, spara punkten.
"""
from __future__ import annotations

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QPlainTextEdit, QPushButton, QSplitter,
    QTextEdit, QVBoxLayout, QWidget,
)

from core.i18n import _


class HistoryDialog(QDialog):
    """Punkterna för en scen, skillnaden mot texten nu, och återställning."""

    restore_requested = pyqtSignal(str)          # ögonblicksbildens id
    review_requested = pyqtSignal(str)           # granska punkten mot texten nu

    def __init__(self, store, source: str, parent=None):
        super().__init__(parent)
        self.store = store
        self.source = source
        self.setWindowTitle(_("history_title"))
        self.setModal(True)
        self.resize(880, 520)

        layout = QVBoxLayout(self)
        delad = QSplitter(Qt.Orientation.Horizontal)

        vanster = QWidget()
        v_layout = QVBoxLayout(vanster)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.addWidget(QLabel(_("history_points")))
        self.lst_points = QListWidget()
        self.lst_points.currentRowChanged.connect(lambda *_: self._visa_diff())
        v_layout.addWidget(self.lst_points, 1)
        delad.addWidget(vanster)

        hoger = QWidget()
        h_layout = QVBoxLayout(hoger)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addWidget(QLabel(_("history_diff")))
        self.visning = QPlainTextEdit()
        self.visning.setReadOnly(True)
        self.visning.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        typsnitt = self.visning.font()
        typsnitt.setFamilies(["monospace", "DejaVu Sans Mono", "Courier New"])
        self.visning.setFont(typsnitt)
        h_layout.addWidget(self.visning, 1)
        delad.addWidget(hoger)
        delad.setSizes([340, 540])
        layout.addWidget(delad, 1)

        self.lbl_status = QLabel("")
        layout.addWidget(self.lbl_status)

        knappar = QHBoxLayout()
        self.btn_new = QPushButton(_("history_new"))
        self.btn_new.clicked.connect(self._ny_punkt)
        knappar.addWidget(self.btn_new)
        self.btn_review = QPushButton(_("history_review"))
        self.btn_review.setToolTip(_("history_review_tip"))
        self.btn_review.clicked.connect(self._review_selected)
        self.btn_review.setEnabled(False)
        knappar.addWidget(self.btn_review)
        knappar.addStretch(1)
        self.btn_restore = QPushButton(_("history_restore"))
        self.btn_restore.clicked.connect(self._atervand)
        self.btn_restore.setEnabled(False)
        knappar.addWidget(self.btn_restore)
        self.btn_close = QPushButton(_("exercise_close"))
        self.btn_close.clicked.connect(self.reject)
        knappar.addWidget(self.btn_close)
        layout.addLayout(knappar)

        self.refresh()

    # ------------------------------------------------------------------ data
    def refresh(self) -> None:
        valt = self.selected_id()
        self.lst_points.blockSignals(True)
        self.lst_points.clear()
        for punkt in self.store.list(self.source):
            etikett = punkt.label or _("history_automatic")
            self.lst_points.addItem(f"{self._lokal_tid(punkt.created)} · {etikett}")
            self.lst_points.item(self.lst_points.count() - 1).setData(Qt.ItemDataRole.UserRole, punkt.id)
        self.lst_points.blockSignals(False)
        rader = self.lst_points.count()
        if rader:
            index = 0
            if valt:
                for i in range(rader):
                    if self.lst_points.item(i).data(Qt.ItemDataRole.UserRole) == valt:
                        index = i
            self.lst_points.setCurrentRow(index)
        else:
            self.visning.setPlainText(_("history_empty"))
        self.btn_restore.setEnabled(bool(rader))
        self.btn_review.setEnabled(bool(rader))
        self.lbl_status.setText(_("history_count", n=rader))

    @staticmethod
    def _lokal_tid(stamp: str) -> str:
        """ISO-tid med tidszon blir lokal tid, utan sekunder."""
        try:
            from datetime import datetime
            return datetime.fromisoformat(stamp).astimezone().strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return stamp[:16].replace("T", " ")

    def selected_id(self) -> str:
        rad = self.lst_points.currentItem()
        return rad.data(Qt.ItemDataRole.UserRole) if rad is not None else ""

    # ---------------------------------------------------------------- visning
    def _visa_diff(self) -> None:
        punkt_id = self.selected_id()
        if not punkt_id:
            return
        # Rubriken läses av en människa: punktens etikett och scenens filnamn i
        # stället för id och full sökväg. Jämförelsen är fortfarande fil mot fil.
        punkt = self.store._find(punkt_id)
        etikett = punkt.label or _("history_automatic")
        text = self.store.diff(punkt_id,
                               fromfile=f"{self._lokal_tid(punkt.created)} · {etikett}",
                               tofile=os.path.basename(self.source))
        self.visning.setPlainText(text or _("history_no_diff"))
        self._tona_rader()

    def _tona_rader(self) -> None:
        """Svag ton bakom tillagda och borttagna rader — tecknet står kvar."""
        tillagg = QTextCharFormat()
        tillagg.setBackground(QColor(46, 160, 67, 46))
        borttag = QTextCharFormat()
        borttag.setBackground(QColor(248, 81, 73, 46))
        markeringar = []
        block = self.visning.document().begin()
        while block.isValid():
            text = block.text()
            if text.startswith("+") and not text.startswith("+++"):
                markeringar.append((block, tillagg))
            elif text.startswith("-") and not text.startswith("---"):
                markeringar.append((block, borttag))
            block = block.next()
        val = []
        for block, fmt in markeringar:
            mark = QTextEdit.ExtraSelection()     # klassen hör till QTextEdit, inte till widgeten
            mark.format = fmt
            markursor = QTextCursor(block)
            markursor.select(QTextCursor.SelectionType.LineUnderCursor)
            mark.cursor = markursor
            val.append(mark)
        self.visning.setExtraSelections(val)

    # ------------------------------------------------------------------ knappar
    def _ny_punkt(self) -> None:
        punkt = self.store.create(self.source, label=_("history_manual"))
        if punkt is not None:
            self.lbl_status.setText(_("history_saved_point"))
            self.refresh()

    def _review_selected(self) -> None:
        """Ber fönstret granska den valda punkten mot texten som är nu (R02.3)."""
        punkt_id = self.selected_id()
        if punkt_id:
            self.review_requested.emit(punkt_id)

    def _atervand(self) -> None:
        punkt_id = self.selected_id()
        if punkt_id:
            self.restore_requested.emit(punkt_id)
            self.refresh()
