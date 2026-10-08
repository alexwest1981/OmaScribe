"""
ui/chrome.py — appskalet enligt v0-referensen.

Referensen (docs/design/scribentia-ui-spec.md) har tre delar runt dokumentet:
en topbar (64px), en vänsterrail (66px) och en statusbar. Här bor de två första
som egna widgets; färger och mått kommer från temats tokens och den globala
stilfilen (`ui/theme_manager.py`), inte från hårdkodade värden här.

    TopBar    — brand, menyraden, dokumentet, sparat-läget, Ångra/Gör om/Hjälp
    LeftRail  — ikoner: aktuellt dokument, öppna filer, mallar, inställningar

Ikonerna är Lucide-linjeikoner (ui/icons.py) i temats färg, som i referensen.
Saknas en ikonfil faller knappen tillbaka på sin text, så inget blir tomt.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QMenu, QToolButton, QVBoxLayout,
    QWidget,
)

from core.i18n import _, i18n
from ui import icons


def set_tracking(widget, px: float) -> None:
    """Spärrning i pixlar. Stilfilen kan inte sätta letter-spacing, så
    referensens -.02em/.12em/.15em måste sättas på widgetens font."""
    font = widget.font()
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, px)
    widget.setFont(font)


def chip(text: str, ok: bool = False) -> QLabel:
    """Liten rund etikett (referensens tonchip)."""
    lbl = QLabel(text)
    lbl.setObjectName("ChipOk" if ok else "Chip")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


def kbd(text: str) -> QLabel:
    """Tangenthänvisning (referensens <kbd>)."""
    lbl = QLabel(text)
    lbl.setObjectName("Kbd")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


def icon_button(icon_name: str, tooltip: str = "", fallback: str = "") -> QToolButton:
    """Ikonknapp. Texten är reserv om ikonfilen inte finns."""
    btn = QToolButton()
    btn.setObjectName("IconButton")
    btn.setProperty("icon_name", icon_name)
    if fallback:
        btn.setText(fallback)
    if tooltip:
        btn.setToolTip(tooltip)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def _apply_icon(button, name: str, color: str, size: int) -> None:
    """Sätter ikonen om den finns, annars behålls knappens text."""
    ic = icons.icon(name, color, size)
    if ic.isNull():
        return
    button.setIcon(ic)
    button.setIconSize(ic.pixmap(size, size).size() if not ic.isNull() else button.iconSize())
    button.setText("")


class TopBar(QWidget):
    """Referensens topbar. Menyraden bor inuti den — appens alla kommandon
    finns kvar, de är bara formgivna som referensens rad i stället för som en
    egen list mellan fönsterkanten och innehållet."""

    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    help_requested = pyqtSignal()

    def __init__(self, theme_mgr=None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        self.setObjectName("TopBar")
        self.setFixedHeight(64)          # referensen: 64

        row = QHBoxLayout(self)
        row.setContentsMargins(20, 8, 22, 8)     # referensen: 0 22px 0 20px
        row.setSpacing(12)

        self.brand_mark = QLabel("O")
        self.brand_mark.setObjectName("BrandMark")
        self.brand_mark.setFixedSize(31, 31)     # referensen: 31x31, radie 10
        self.brand_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.brand_mark)

        self.brand_name = QLabel("Scribentia")
        self.brand_name.setObjectName("BrandName")
        set_tracking(self.brand_name, -0.3)      # referensen: letter-spacing -.02em
        row.addWidget(self.brand_name)

        self.divider = QFrame()
        self.divider.setObjectName("BrandDivider")
        self.divider.setFixedSize(1, 22)         # referensen: 22x1, marginal 0 8
        row.addSpacing(8)
        row.addWidget(self.divider)
        row.addSpacing(8)

        self.menu_row = QHBoxLayout()            # menyraden hamnar här
        self.menu_row.setContentsMargins(0, 0, 0, 0)
        self.menu_row.setSpacing(8)
        row.addLayout(self.menu_row)

        self.btn_file = QToolButton()
        self.btn_file.setObjectName("FileButton")
        self.btn_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_file.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.btn_file.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        row.addWidget(self.btn_file)

        row.addStretch(1)

        self.save_dot = QLabel()
        self.save_dot.setObjectName("SaveDot")
        self.save_dot.setFixedSize(6, 6)         # referensen: 6x6 rund
        row.addWidget(self.save_dot)

        self.lbl_save = QLabel()
        self.lbl_save.setObjectName("SaveState")
        row.addWidget(self.lbl_save)

        self.btn_undo = icon_button("undo-2", fallback="↶")
        self.btn_redo = icon_button("redo-2", fallback="↷")
        self.btn_help = icon_button("circle-help", fallback="?")
        row.addSpacing(2)
        for btn in (self.btn_undo, self.btn_redo, self.btn_help):
            row.addWidget(btn)

        self.btn_undo.clicked.connect(self.undo_requested)
        self.btn_redo.clicked.connect(self.redo_requested)
        self.btn_help.clicked.connect(self.help_requested)

        self.set_modified(False)
        self.retranslate_ui()
        self.apply_theme()
        i18n.language_changed.connect(self.retranslate_ui)
        if self.theme_mgr is not None:
            self.theme_mgr.theme_changed.connect(self.apply_theme)

    # ------------------------------------------------------------------- API

    def set_menu_bar(self, menu_bar) -> None:
        """Sätter in appens menyrad i raden. Den får sin egen höjd (34px) så
        att layouten centrerar den i topbaren — annars ligger menyorden längst
        upp i raden och ser ut att klistra vid fönsterkanten."""
        menu_bar.setFixedHeight(34)
        self.menu_row.addWidget(menu_bar)

    def set_file_menu(self, menu: QMenu) -> None:
        self.btn_file.setMenu(menu)

    def set_document_name(self, name: str) -> None:
        # Meny-pilen ritar Qt själv när knappen har en meny.
        text = name or _("untitled_document")
        self.btn_file.setText(text)
        self.btn_file.setToolTip(text)      # hela namnet syns även när raden är smal

    def set_modified(self, modified: bool) -> None:
        """Sparat-läget: punkten och ordet följs åt, så läget syns även utan färg."""
        self.lbl_save.setText(_("topbar_unsaved") if modified else _("topbar_saved"))
        self.save_dot.setToolTip(self.lbl_save.text())

    def apply_theme(self) -> None:
        if self.theme_mgr is None:
            return
        c = self.theme_mgr.tokens()
        for btn, namn in ((self.btn_undo, "undo-2"), (self.btn_redo, "redo-2"),
                          (self.btn_help, "circle-help"), (self.btn_file, "file-text")):
            _apply_icon(btn, namn, c["text_muted"], 16)

    def retranslate_ui(self) -> None:
        self.btn_undo.setToolTip(_("menu_edit_undo"))
        self.btn_redo.setToolTip(_("menu_edit_redo"))
        self.btn_help.setToolTip(_("topbar_help"))
        self.set_modified(self.lbl_save.text() == _("topbar_unsaved"))
        if self.btn_file.text() == "":
            self.set_document_name("")


class LeftRail(QWidget):
    """Referensens vänsterrail: 66px, 40x40-knappar.

    Raden byter vy — den äger ingen data. Det som är markerat är den vy som
    visas, och markeringen syns både som färg och som ifylld yta.
    """

    view_requested = pyqtSignal(str)      # "document" | "files" | "templates"
    settings_requested = pyqtSignal()

    VIEWS = (
        ("document", "file-text", "rail_document"),
        ("files", "folder-open", "rail_files"),
        ("templates", "layout-list", "rail_templates"),
    )

    def __init__(self, theme_mgr=None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        self.setObjectName("LeftRail")
        self.setFixedWidth(66)               # referensen: 66
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        kolumn = QVBoxLayout(self)
        kolumn.setContentsMargins(12, 18, 12, 18)   # referensen: padding 18px 12px
        kolumn.setSpacing(10)                       # referensen: gap 10
        kolumn.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self._buttons = {}

        for key, icon_name, tip_key in self.VIEWS:
            btn = self._make_button(icon_name, tip_key)
            btn.setCheckable(True)
            btn.toggled.connect(lambda _checked, b=btn: self._sync_icon(b))
            btn.clicked.connect(lambda _checked, k=key: self.view_requested.emit(k))
            self.group.addButton(btn)
            self._buttons[key] = btn
            kolumn.addWidget(btn, 0, Qt.AlignmentFlag.AlignHCenter)

        kolumn.addStretch(1)

        self.btn_settings = self._make_button("settings-2", "rail_settings")
        self.btn_settings.clicked.connect(self.settings_requested)
        kolumn.addWidget(self.btn_settings, 0, Qt.AlignmentFlag.AlignHCenter)

        self.set_active("document")
        self.retranslate_ui()
        self.apply_theme()
        i18n.language_changed.connect(self.retranslate_ui)
        if self.theme_mgr is not None:
            self.theme_mgr.theme_changed.connect(self.apply_theme)

    def _make_button(self, icon_name: str, tip_key: str) -> QToolButton:
        btn = QToolButton()
        btn.setObjectName("RailButton")
        btn.setProperty("icon_name", icon_name)
        btn.setFixedSize(40, 40)             # referensen: 40x40, radie 11
        btn.setProperty("tip_key", tip_key)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _sync_icon(self, btn: QToolButton) -> None:
        """Ikonen färgas efter läget: markerad knapp bär accentfärgen."""
        if self.theme_mgr is None:
            return
        c = self.theme_mgr.tokens()
        färg = c["rail_active_text"] if btn.isChecked() else c["rail_text"]
        _apply_icon(btn, btn.property("icon_name"), färg, 20)

    def apply_theme(self) -> None:
        if self.theme_mgr is None:
            return
        for btn in list(self._buttons.values()) + [self.btn_settings]:
            self._sync_icon(btn)

    def set_active(self, key: str) -> None:
        btn = self._buttons.get(key)
        if btn is not None:
            btn.setChecked(True)
        elif key == "settings":
            self.btn_settings.setChecked(True)

    def retranslate_ui(self) -> None:
        for key, _icon, tip_key in self.VIEWS:
            self._buttons[key].setToolTip(_(tip_key))
        self.btn_settings.setToolTip(_("rail_settings"))
