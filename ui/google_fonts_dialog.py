from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QScrollArea, QWidget, QFrame, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from core.i18n import _, i18n
from core.google_fonts_data import GOOGLE_FONTS_CATALOG
from core.google_fonts_manager import GoogleFontsManager

class GoogleFontsDialog(QDialog):
    font_list_changed = pyqtSignal()

    def __init__(self, theme_mgr, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        self.gfonts = GoogleFontsManager()
        self.current_category = "all"
        self.search_query = ""

        self.setWindowTitle(_("gfonts_title"))
        self.resize(740, 600)
        self.setMinimumSize(600, 480)

        self.init_ui()
        self.apply_theme()
        self.gfonts.font_installed.connect(self._on_font_installed)
        self.gfonts.font_error.connect(self._on_font_error)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Header Title
        lbl_title = QLabel("🌐 " + _("gfonts_title"))
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_title)

        # Search Bar
        search_row = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText(_("gfonts_search_placeholder"))
        self.input_search.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self.input_search)
        layout.addLayout(search_row)

        # Category Filter Pills
        cat_row = QHBoxLayout()
        self.cat_group = QButtonGroup(self)
        
        categories = [
            ("all", _("gfonts_filter_all")),
            ("sans-serif", _("gfonts_filter_sans")),
            ("serif", _("gfonts_filter_serif")),
            ("monospace", _("gfonts_filter_mono")),
            ("display", _("gfonts_filter_display")),
            ("handwriting", _("gfonts_filter_hand"))
        ]

        for idx, (cid, cname) in enumerate(categories):
            btn = QPushButton(cname)
            btn.setCheckable(True)
            if idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda ch, c=cid: self._on_category_changed(c))
            self.cat_group.addButton(btn, idx)
            cat_row.addWidget(btn)

        cat_row.addStretch()
        layout.addLayout(cat_row)

        # Scroll Area for Font Cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.container = QWidget()
        self.cards_layout = QVBoxLayout(self.container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        # Populate Initial List
        self.populate_cards()

    def populate_cards(self):
        # Clear existing
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        c = self.theme_mgr.current

        for info in GOOGLE_FONTS_CATALOG:
            family = info["family"]
            cat = info["category"]
            desc = info["description"]
            author = info["author"]

            # Filter category
            if self.current_category != "all" and cat != self.current_category:
                continue

            # Filter search query
            if self.search_query and self.search_query not in family.lower() and self.search_query not in desc.lower():
                continue

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {c["sidebar_card"]};
                    border: 1px solid {c["canvas_border"]};
                    border-radius: 6px;
                    padding: 8px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 8, 10, 8)
            card_layout.setSpacing(4)

            # Top Row: Family name + Author + Category Badge + Install Button
            top_row = QHBoxLayout()
            lbl_name = QLabel(f"<b>{family}</b> <span style='color: {c['status_text']}; font-size: 11px;'>by {author}</span>")
            lbl_name.setFont(QFont("Segoe UI", 11))
            top_row.addWidget(lbl_name)

            lbl_cat = QLabel(f"[{cat.upper()}]")
            lbl_cat.setStyleSheet(f"color: {c['accent']}; font-size: 10px; font-weight: bold;")
            top_row.addWidget(lbl_cat)
            top_row.addStretch()

            is_inst = self.gfonts.is_installed(family)
            btn_inst = QPushButton("✓ " + _("gfonts_btn_installed") if is_inst else "⬇ " + _("gfonts_btn_install"))
            btn_inst.setEnabled(not is_inst)
            btn_inst.setFixedHeight(26)
            if is_inst:
                btn_inst.setStyleSheet("background-color: #16a34a; color: #ffffff; font-weight: bold;")
            else:
                btn_inst.clicked.connect(lambda ch, f=info, b=btn_inst: self._start_install(f, b))

            top_row.addWidget(btn_inst)
            card_layout.addLayout(top_row)

            # Description
            lbl_desc = QLabel(desc)
            lbl_desc.setStyleSheet(f"color: {c['status_text']}; font-size: 11px;")
            lbl_desc.setWordWrap(True)
            card_layout.addWidget(lbl_desc)

            # Live Preview text
            lbl_prev = QLabel(_("gfonts_preview_text"))
            if is_inst:
                prev_font = QFont(family, 13)
                lbl_prev.setFont(prev_font)
            else:
                lbl_prev.setFont(QFont("Segoe UI", 12))
            lbl_prev.setStyleSheet(f"margin-top: 4px; padding: 4px 0; color: {c['text_color']};")
            card_layout.addWidget(lbl_prev)

            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _on_search_changed(self, text):
        self.search_query = text.strip().lower()
        self.populate_cards()

    def _on_category_changed(self, cat):
        self.current_category = cat
        self.populate_cards()

    def _start_install(self, font_info, button):
        button.setEnabled(False)
        button.setText("⏳ " + _("gfonts_downloading"))
        self.gfonts.install_font(font_info)

    def _on_font_installed(self, family):
        self.populate_cards()
        self.font_list_changed.emit()

    def _on_font_error(self, family, err):
        self.populate_cards()

    def apply_theme(self):
        c = self.theme_mgr.current
        self.setStyleSheet(self.theme_mgr.get_stylesheet() + f"""
            #FontCard {{
                background-color: {c["sidebar_card"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 8px;
            }}
            #FontCard:hover {{
                border-color: {c["accent"]};
            }}
        """)
