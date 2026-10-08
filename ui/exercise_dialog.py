"""Fastnat? — en fråga, tre förslag, och en väg tillbaka till skrivandet (R03.16).

Förslagen är inte text att klistra in i manuset; de är vägar in. Därför hamnar
det valda förslaget i scenens egen anteckning, där författaren ser det nästa
gång och där AI:n läser det som sammanhang. Anropet görs av den befintliga
AI-klienten — den här rutan vet inget om vare sig modellen eller editorn, den
ber sin förälder om sammanhanget och lämnar tillbaka ett valt förslag.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout,
)

from core import exercises
from core.i18n import _


class ExerciseDialog(QDialog):
    ask_requested = pyqtSignal(str)          # kategori — föräldern har texten
    insert_requested = pyqtSignal(str)       # det valda förslaget

    def __init__(self, ai, parent=None):
        super().__init__(parent)
        self.ai = ai
        self.setWindowTitle(_("exercise_title"))
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(_("exercise_intro")))

        rad = QHBoxLayout()
        self.combo_category = QComboBox()
        for kategori in exercises.CATEGORIES:
            self.combo_category.addItem(kategori[1], kategori[0])
        rad.addWidget(self.combo_category, 1)
        self.btn_ask = QPushButton(_("exercise_ask"))
        self.btn_ask.clicked.connect(self._ask)
        rad.addWidget(self.btn_ask)
        layout.addLayout(rad)

        self.lst_suggestions = QListWidget()
        self.lst_suggestions.itemDoubleClicked.connect(lambda *_: self._insert())
        layout.addWidget(self.lst_suggestions, 1)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        knappar = QHBoxLayout()
        knappar.addStretch(1)
        self.btn_insert = QPushButton(_("exercise_insert"))
        self.btn_insert.clicked.connect(self._insert)
        self.btn_insert.setEnabled(False)
        knappar.addWidget(self.btn_insert)
        self.btn_close = QPushButton(_("exercise_close"))
        self.btn_close.clicked.connect(self.reject)
        knappar.addWidget(self.btn_close)
        layout.addLayout(knappar)

        self.ask_requested.connect(lambda *_: self._visa_vantar())
        self.ai.suggestions_ready.connect(self.set_suggestions)
        self.ai.suggestions_error.connect(self.set_error)

    # ------------------------------------------------------------------ in
    def selected_category(self) -> str:
        return self.combo_category.currentData() or exercises.CATEGORIES[0][0]

    def selected_suggestion(self) -> str:
        rad = self.lst_suggestions.currentItem()
        return rad.text() if rad is not None else ""

    def set_suggestions(self, suggestions: list) -> None:
        """Fyller listan. Egen metod så att rutan går att prova utan nät."""
        self.lst_suggestions.clear()
        for förslag in suggestions or []:
            self.lst_suggestions.addItem(förslag)
        if self.lst_suggestions.count():
            self.lst_suggestions.setCurrentRow(0)
        else:
            self.lbl_status.setText(_("exercise_empty"))
        self.btn_insert.setEnabled(self.lst_suggestions.count() > 0)

    def set_error(self, message: str) -> None:
        self.lbl_status.setText(f"{_('exercise_failed')}: {message}")

    # ----------------------------------------------------------------- ut
    def _visa_vantar(self) -> None:
        self.lbl_status.setText(_("exercise_waiting"))
        self.btn_insert.setEnabled(False)

    def _ask(self) -> None:
        self.lst_suggestions.clear()
        self.ask_requested.emit(self.selected_category())

    def _insert(self) -> None:
        förslag = self.selected_suggestion()
        if förslag:
            self.insert_requested.emit(förslag)
            self.lbl_status.setText(_("exercise_inserted"))
