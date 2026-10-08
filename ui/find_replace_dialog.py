"""Sök och ersätt i texten (R02.16).

`core/find_replace.py` har kunnat det här hela tiden — den har bara inte nåtts
från gränssnittet. Rutan är tunn: den frågar föräldern om dokumentet, letar med
modulens funktioner, och markerar bara **den aktuella** träffen i stället för
att måla om alla. Kommentarerna och läsbarhetsmarkeringarna äger nämligen sina
egna markeringar i editorn, och en sökning ska inte sudda dem.

Ett ångra-steg per ersättning, och ett för Ersätt alla: `replace_all` gör hela
ändringen inuti ett edit block.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QCheckBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout,
)

from core.find_replace import find_all, replace_all
from core.i18n import _


class FindReplaceDialog(QDialog):
    """Sökrutan. `document_provider` ger dokumentet att söka i, så rutan fungerar
    både i editorn och i läsvyn."""

    def __init__(self, document_provider, parent=None, with_replace: bool = True):
        super().__init__(parent)
        self.document_provider = document_provider
        self.with_replace = with_replace
        self.setWindowTitle(_("find_title_replace") if with_replace else _("find_title"))
        self.setModal(False)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)

        rad_sok = QHBoxLayout()
        rad_sok.addWidget(QLabel(_("find_find")))
        self.input_find = QLineEdit()
        self.input_find.setPlaceholderText(_("find_placeholder"))
        self.input_find.returnPressed.connect(self._sok)
        self.input_find.textChanged.connect(lambda *_: self._rakna())
        rad_sok.addWidget(self.input_find, 1)
        layout.addLayout(rad_sok)

        self.input_replace = QLineEdit()
        if with_replace:
            rad_ers = QHBoxLayout()
            rad_ers.addWidget(QLabel(_("find_replace")))
            self.input_replace.setPlaceholderText(_("find_replace_placeholder"))
            rad_ers.addWidget(self.input_replace, 1)
            layout.addLayout(rad_ers)

        val = QHBoxLayout()
        self.chk_regex = QCheckBox(_("find_regex"))
        self.chk_case = QCheckBox(_("find_case"))
        self.chk_word = QCheckBox(_("find_whole_word"))
        for kryss in (self.chk_regex, self.chk_case, self.chk_word):
            kryss.stateChanged.connect(lambda *_: self._rakna())
            val.addWidget(kryss)
        val.addStretch(1)
        layout.addLayout(val)

        knappar = QHBoxLayout()
        self.btn_find = QPushButton(_("find_next"))
        self.btn_find.clicked.connect(self._sok)
        knappar.addWidget(self.btn_find)
        if with_replace:
            self.btn_replace = QPushButton(_("find_replace_one"))
            self.btn_replace.clicked.connect(self._ersatt)
            knappar.addWidget(self.btn_replace)
            self.btn_replace_all = QPushButton(_("find_replace_all"))
            self.btn_replace_all.clicked.connect(self._ersatt_alla)
            knappar.addWidget(self.btn_replace_all)
        knappar.addStretch(1)
        self.btn_close = QPushButton(_("exercise_close"))
        self.btn_close.clicked.connect(self.close)
        knappar.addWidget(self.btn_close)
        layout.addLayout(knappar)

        self.lbl_status = QLabel("")
        layout.addWidget(self.lbl_status)
        self._rakna()

    # ------------------------------------------------------------------ läge
    def flags(self) -> dict:
        return {
            "regex": self.chk_regex.isChecked(),
            "case_sensitive": self.chk_case.isChecked(),
            "whole_word": self.chk_word.isChecked(),
        }

    def document(self):
        return self.document_provider() if callable(self.document_provider) else None

    def matches(self) -> list:
        document = self.document()
        if document is None or not self.input_find.text():
            return []
        return find_all(document, self.input_find.text(), **self.flags())

    def _rakna(self) -> None:
        """Räknaren säger hur många träffar mönstret har — innan man trycker."""
        antal = len(self.matches())
        if not antal:
            self.lbl_status.setText(_("find_none"))
        elif antal == 1:
            self.lbl_status.setText(_("find_count_one"))
        else:
            self.lbl_status.setText(_("find_count", n=antal))

    # --------------------------------------------------------------- sökandet
    def _sok(self) -> None:
        document = self.document()
        if document is None:
            return
        träffar = self.matches()
        if not träffar:
            self.lbl_status.setText(_("find_none"))
            return
        var = self.input_find.text()
        # Nästa träff efter markören, och runt från början när texten tar slut.
        position = self.cursor_position()
        nästa = next((m for m in träffar if m.start > position), träffar[0])
        self._välj(nästa)
        index = träffar.index(nästa) + 1
        self.lbl_status.setText(_("find_of", n=index, total=len(träffar), text=var))

    def cursor_position(self) -> int:
        dokument = self.document()
        if dokument is None or self.parent() is None:
            return 0
        canvas = getattr(self.parent(), "active_canvas", None)
        if canvas is None:
            return 0
        return canvas.textCursor().position()

    def _välj(self, träff) -> None:
        dokument = self.document()
        markör = QTextCursor(dokument)
        markör.setPosition(träff.start)
        markör.setPosition(träff.start + träff.length, QTextCursor.MoveMode.KeepAnchor)
        canvas = getattr(self.parent(), "active_canvas", None)
        if canvas is not None:
            canvas.setTextCursor(markör)
            canvas.setFocus()

    # ------------------------------------------------------------- ersättandet
    def _ersatt(self) -> None:
        dokument = self.document()
        if dokument is None:
            return
        markör = QTextCursor(dokument)
        canvas = getattr(self.parent(), "active_canvas", None)
        if canvas is not None:
            markör = canvas.textCursor()
        if not markör.hasSelection():
            self._sok()
            return
        from core.find_replace import replace_one

        träffar = self.matches()
        match = next((m for m in träffar if m.start == markör.selectionStart()), None)
        if match is None:
            self._sok()
            return
        replace_one(dokument, match, self.input_replace.text(), **{"regex": self.chk_regex.isChecked()})
        if canvas is not None:
            canvas.setTextCursor(markör)
        self._rakna()
        self._sok()

    def _ersatt_alla(self) -> None:
        dokument = self.document()
        if dokument is None or not self.input_find.text():
            return
        antal = replace_all(dokument, self.input_find.text(), self.input_replace.text(),
                            **self.flags())
        self.lbl_status.setText(_("find_replaced", n=antal))
        self._rakna()
