"""Granska ändringar: behåll eller ångra, stycke för stycke (R02.1).

Ändringarna kommer från `core/revisions.py` och är operationer, inte färg. Raden
säger vad som hände — `+` tillagt, `−` borttaget, `~` omskrivet — med tecknet
först, så betydelsen syns även utan färg. Kryssad rad betyder behåll.

Förhandsvisningen längst ner är exakt den text som skrivs om man trycker
Verkställ: den räknas om för varje kryss, ur samma funktion som skriver den.
Det ska inte gå att bli överraskad av vad knappen gjorde.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPlainTextEdit,
    QPushButton, QSplitter, QVBoxLayout, QWidget,
)

from core.i18n import _
from core.revisions import (apply_changes, blocks, changes, formatting_changes,
                            plain, word_diff)

MARK = {"added": "+", "removed": "−", "changed": "~"}
KEPT = "✓"          # behålls
REVERTED = "↩"      # ångras — tecknet står i raden, så beslutet syns även om
                    # kryssrutan ritas svagt (den är formen, inte betydelsen)


def _kort(text: str, längd: int = 84) -> str:
    en_rad = " ".join((text or "").split())
    return en_rad if len(en_rad) <= längd else en_rad[:längd - 1] + "…"


def _preview(before_html: str, after_html: str, decisions) -> str:
    """Texten som den blir — läsbar, stycke för stycke."""
    resultat = apply_changes(before_html, after_html, decisions)
    return "\n\n".join(plain(block) for block in blocks(resultat) if plain(block))


class ReviewDialog(QDialog):
    """Ändringarna sedan en punkt, med ett beslut per stycke."""

    apply_requested = pyqtSignal(list)          # ["keep" | "revert", ...]

    def __init__(self, before_html: str, after_html: str, label: str = "", parent=None):
        super().__init__(parent)
        self.before = before_html
        self.after = after_html
        self.changes = changes(before_html, after_html)
        self.setWindowTitle(_("review_title"))
        self.setModal(True)
        self.resize(880, 460)

        layout = QVBoxLayout(self)
        if label:
            rubrik = QLabel(_("review_since", label=label))
            rubrik.setStyleSheet("color: palette(mid);")
            layout.addWidget(rubrik)

        # Formateringen hålls åtskild från textändringarna (R02.15): den sägs i
        # en rad, och läggs inte in som ändringar att ta ställning till.
        formatering = formatting_changes(before_html, after_html)
        if formatering:
            lbl_format = QLabel(_("review_formatting", n=len(formatering)))
            lbl_format.setStyleSheet("color: palette(mid);")
            layout.addWidget(lbl_format)

        delad = QSplitter(Qt.Orientation.Vertical)

        övre = QWidget()
        övre_layout = QVBoxLayout(övre)
        övre_layout.setContentsMargins(0, 0, 0, 0)
        övre_layout.addWidget(QLabel(_("review_changes")))
        self.lst_changes = QListWidget()
        for change in self.changes:
            item = QListWidgetItem(self._rad(change))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)      # kryssad = behåll
            # Raden visar hela stycket; verktygstipset har detaljnivån — orden som
            # gick och kom — först, sedan före/efter och ankaret.
            rader = [_("review_row_tooltip",
                       before=_kort(change.before_text, 160) or _("review_empty"),
                       after=_kort(change.after_text, 160) or _("review_empty"),
                       anchor=_kort(change.anchor, 80))]
            if change.kind == "changed":
                rader.insert(0, word_diff(change.before_text, change.after_text))
            item.setToolTip("\n".join(rader))
            self.lst_changes.addItem(item)
        self.lst_changes.itemChanged.connect(lambda *_: self._uppdatera())
        övre_layout.addWidget(self.lst_changes, 1)
        delad.addWidget(övre)

        undre = QWidget()
        undre_layout = QVBoxLayout(undre)
        undre_layout.setContentsMargins(0, 0, 0, 0)
        undre_layout.addWidget(QLabel(_("review_preview")))
        self.visning = QPlainTextEdit()
        self.visning.setReadOnly(True)
        undre_layout.addWidget(self.visning, 1)
        delad.addWidget(undre)
        delad.setSizes([280, 300])
        layout.addWidget(delad, 1)

        knappar = QHBoxLayout()
        self.btn_keep_all = QPushButton(_("review_keep_all"))
        self.btn_keep_all.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
        knappar.addWidget(self.btn_keep_all)
        self.btn_revert_all = QPushButton(_("review_revert_all"))
        self.btn_revert_all.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))
        knappar.addWidget(self.btn_revert_all)
        knappar.addStretch(1)
        self.btn_apply = QPushButton(_("review_apply"))
        self.btn_apply.clicked.connect(self._apply)
        knappar.addWidget(self.btn_apply)
        self.btn_close = QPushButton(_("exercise_close"))
        self.btn_close.clicked.connect(self.reject)
        knappar.addWidget(self.btn_close)
        layout.addLayout(knappar)

        self.lbl_status = QLabel("")
        layout.addWidget(self.lbl_status)
        self._uppdatera()

    def _rad(self, change) -> str:
        """Radens text: beslutet först, sedan vad som hände."""
        i = self.changes.index(change)
        beslutad = (self.lst_changes.item(i).checkState() == Qt.CheckState.Checked
                    if self.lst_changes.count() > i else True)
        text = change.after_text or change.before_text
        return f"{KEPT if beslutad else REVERTED} {MARK.get(change.kind, '~')} {_kort(text)}"

    # ------------------------------------------------------------------ beslut
    def decisions(self) -> list:
        return ["keep" if self.lst_changes.item(i).checkState() == Qt.CheckState.Checked
                else "revert" for i in range(self.lst_changes.count())]

    def preview_text(self) -> str:
        return _preview(self.before, self.after, self.decisions())

    def _set_all(self, läge) -> None:
        self.lst_changes.blockSignals(True)
        for i in range(self.lst_changes.count()):
            self.lst_changes.item(i).setCheckState(läge)
        self.lst_changes.blockSignals(False)
        self._uppdatera()

    def _uppdatera(self) -> None:
        self.visning.setPlainText(self.preview_text())
        # radens tecken följer beslutet — kryssrutan får inte vara enda beviset
        self.lst_changes.blockSignals(True)
        for i, change in enumerate(self.changes):
            self.lst_changes.item(i).setText(self._rad(change))
        self.lst_changes.blockSignals(False)
        behåll = sum(1 for d in self.decisions() if d == "keep")
        self.lbl_status.setText(_("review_status", kept=behåll, total=len(self.changes)))

    def _apply(self) -> None:
        """Verkställer granskningen.

        Metodnamnet är medvetet utan prickar över bokstäverna: PyQt6 kraschar
        (signal 11) när en signal kopplas till en bunden metod med icke-ASCII i
        namnet. Mätt i ett minimalt prov — en lambda och ett ASCII-namn går bra,
        `self._verkställ` tar ner processen vid kopplingen.
        """
        self.apply_requested.emit(self.decisions())
        self.accept()
