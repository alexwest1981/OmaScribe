"""Publiceringsprofilen: kanalens siffror, och vad de gör med boken (R05.1, R05.5, R05.6).

Rutan visar **varför** varje tal är vad det är. Väljer man en kanal som inte
publicerar en formel säger den till i stället för att visa ett påhittat mått — en
felaktig ryggbredd syns inte förrän boken är tryckt.

Sidantalet är det som styr mest: gutter-trappan, ryggbredden och omslaget hänger
alla på det, och därför går det att hämta det ur det öppna manuset.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QVBoxLayout,
)

from core.i18n import _, i18n
from core import publishing


def _tal(värde) -> str:
    """Ett mått som en svensk läsare skriver det: 12,7 och inte 12.7."""
    text = f"{float(värde):g}"
    return text.replace(".", ",") if i18n.current_lang == "sv" else text


class PublishDialog(QDialog):
    """Kanal, format, trim, papper och sidantal — och vad de ger."""

    settings_applied = pyqtSignal(dict)

    def __init__(self, page_count: int = 300, settings: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("publish_title"))
        self.setModal(True)
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.combo_channel = QComboBox()
        for nyckel, kanal in publishing.CHANNELS.items():
            self.combo_channel.addItem(kanal["label"], nyckel)
        form.addRow(QLabel(_("publish_channel")), self.combo_channel)

        self.combo_format = QComboBox()
        self.combo_format.addItem(_("publish_print"), "print")
        self.combo_format.addItem(_("publish_ebook"), "ebook")
        form.addRow(QLabel(_("publish_format")), self.combo_format)

        self.combo_trim = QComboBox()
        for nyckel, namn in publishing.TRIM_NAMES.items():
            self.combo_trim.addItem(f"{namn}  ({publishing.TRIMS[nyckel][0]:g} × "
                                    f"{publishing.TRIMS[nyckel][1]:g} mm)", nyckel)
        self.combo_trim.setCurrentIndex(1)                 # 6×9: den vanliga romanen
        # Har boken redan ett trim i sidinställningarna visas det, så att rutan
        # öppnas på det man faktiskt arbetar med.
        if settings:
            for nyckel, (bredd, höjd) in publishing.TRIMS.items():
                if (abs(float(settings.get("custom_width_mm") or 0) - bredd) < 0.5
                        and abs(float(settings.get("custom_height_mm") or 0) - höjd) < 0.5):
                    self.combo_trim.setCurrentIndex(self.combo_trim.findData(nyckel))
        form.addRow(QLabel(_("publish_trim")), self.combo_trim)

        self.combo_paper = QComboBox()
        for nyckel, (koefficient, namn) in publishing.KDP_PAPERS.items():
            self.combo_paper.addItem(namn, nyckel)
        form.addRow(QLabel(_("publish_paper")), self.combo_paper)

        rad_sidor = QHBoxLayout()
        self.spin_pages = QSpinBox()
        self.spin_pages.setRange(1, 2000)
        self.spin_pages.setValue(max(1, int(page_count or 300)))
        rad_sidor.addWidget(self.spin_pages)
        self.btn_from_document = QPushButton(_("publish_from_document"))
        self.btn_from_document.clicked.connect(
            lambda: self.spin_pages.setValue(max(1, int(page_count or 1))))
        rad_sidor.addWidget(self.btn_from_document)
        form.addRow(QLabel(_("publish_pages")), rad_sidor)

        self.chk_bleed = QCheckBox(_("publish_bleed"))
        form.addRow(QLabel(""), self.chk_bleed)
        layout.addLayout(form)

        # Siffrorna, och källan de kommer ifrån
        self.lbl_numbers = QLabel()
        self.lbl_numbers.setWordWrap(True)
        self.lbl_numbers.setObjectName("PublishNumbers")
        self.lbl_numbers.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.lbl_numbers)

        self.lbl_warnings = QLabel()
        self.lbl_warnings.setWordWrap(True)
        self.lbl_warnings.setObjectName("PublishWarnings")
        layout.addWidget(self.lbl_warnings)

        self.btn_apply = QPushButton(_("publish_apply"))
        self.btn_apply.clicked.connect(self._apply)
        knappar = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        knappar.rejected.connect(self.reject)
        knappar.accepted.connect(self.accept)
        rad = QHBoxLayout()
        rad.addWidget(self.btn_apply)
        rad.addStretch(1)
        rad.addWidget(knappar)
        layout.addLayout(rad)

        for widget in (self.combo_channel, self.combo_format, self.combo_trim,
                       self.combo_paper):
            widget.currentIndexChanged.connect(self._update)
        self.spin_pages.valueChanged.connect(self._update)
        self.chk_bleed.stateChanged.connect(self._update)
        self._update()

    # ------------------------------------------------------------------ läget
    def channel(self) -> str:
        return self.combo_channel.currentData()

    def trim(self) -> str:
        return self.combo_trim.currentData()

    def paper(self) -> str:
        return self.combo_paper.currentData()

    def pages(self) -> int:
        return int(self.spin_pages.value())

    def is_print(self) -> bool:
        return self.combo_format.currentData() == "print"

    def _update(self) -> None:
        """Räknar om siffrorna — och säger till när kanalen inte har en formel."""
        kanal = publishing.CHANNELS.get(self.channel()) or {}
        print_ = self.is_print()
        self.combo_paper.setEnabled(print_ and bool(kanal.get("formula")))
        self.chk_bleed.setEnabled(print_)

        if not print_:
            self.lbl_numbers.setText(_("publish_ebook_numbers",
                                       source=publishing.SOURCES.get(kanal.get("source"), "")))
            self.lbl_warnings.setText("")
            self.btn_apply.setEnabled(False)
            return

        gutter = publishing.gutter_mm(self.pages(), self.channel())
        spine = publishing.spine_mm(self.pages(), self.paper(), self.channel())
        cover = publishing.cover_mm(self.trim(), self.pages(), self.paper(),
                                    self.chk_bleed.isChecked(), self.channel())
        rader = []
        if gutter is not None:
            rader.append(_("publish_number_gutter", value=_tal(gutter)))
        else:
            rader.append(_("publish_number_gutter_unknown"))
        if spine is not None:
            rader.append(_("publish_number_spine", value=_tal(spine)))
        else:
            rader.append(_("publish_number_spine_unknown"))
        if cover is not None:
            rader.append(_("publish_number_cover", width=_tal(cover[0]), height=_tal(cover[1])))
        rader.append(_("publish_source",
                       source=publishing.SOURCES.get(kanal.get("source"), "")))
        self.lbl_numbers.setText("<br>".join(rader))

        varningar = [_("warn_" + kod) for kod in
                     publishing.warnings(self.trim(), self.pages(), self.paper(),
                                         self.chk_bleed.isChecked(), self.channel())]
        self.lbl_warnings.setText("<br>".join("⚠ " + rad for rad in varningar) if varningar else "")
        self.btn_apply.setEnabled(publishing.page_settings_for(
            self.trim(), self.pages(), self.paper(), self.chk_bleed.isChecked(),
            self.channel()) is not None)

    def settings(self) -> dict | None:
        """Appens sidinställningar för profilen."""
        return publishing.page_settings_for(self.trim(), self.pages(), self.paper(),
                                            self.chk_bleed.isChecked(), self.channel())

    def _apply(self) -> None:
        ny = self.settings()
        if ny:
            self.settings_applied.emit(ny)
            self.accept()
