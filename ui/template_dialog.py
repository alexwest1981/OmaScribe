"""
ui/template_dialog.py — Mallväljare för OmaScribe.

Visar ett modernt galleri med fördefinierade mallar (Rapport, Avhandling,
Mötesanteckningar, Projektplan, Promemoria) med beskrivningar, ikoner och
förhandsgranskning.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QSizePolicy, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

from core.i18n import _, i18n
from core.templates import TEMPLATES, get_template_html
from ui.widgets import ClickableCard


class TemplateDialog(QDialog):
    template_selected = pyqtSignal(str)  # template_id

    def __init__(self, theme_mgr, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        self.selected_id = None

        self.setWindowTitle(_("templates_dialog_title"))
        self.resize(760, 520)
        self.setModal(True)

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(16)

        # Header
        lbl_title = QLabel("🎨 " + _("templates_dialog_title"))
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        root_layout.addWidget(lbl_title)

        lbl_sub = QLabel(_("templates_dialog_sub"))
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {self.theme_mgr.current['text_muted']};")
        root_layout.addWidget(lbl_sub)

        # Scroll Area with Template Cards Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        lang = i18n.get_language()

        for idx, t in enumerate(TEMPLATES):
            t_id = t["id"]
            icon = t.get("icon", "📄")
            title = t.get(f"title_{lang}") or t.get("title_sv", "")
            desc = t.get(f"desc_{lang}") or t.get("desc_sv", "")

            card_btn = ClickableCard(object_name="TemplateCard")
            card_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            card_btn.setMinimumHeight(120)
            card_btn.clicked.connect(lambda tid=t_id: self._select_template(tid))

            card_layout = card_btn.body
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(6)

            row_top = QHBoxLayout()
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet("font-size: 24px;")
            lbl_card_title = QLabel(title)
            lbl_card_title.setObjectName("TemplateCardTitle")
            lbl_card_title.setWordWrap(True)
            row_top.addWidget(lbl_icon, 0, Qt.AlignmentFlag.AlignTop)
            row_top.addWidget(lbl_card_title, 1)
            card_layout.addLayout(row_top)

            lbl_desc = QLabel(desc)
            lbl_desc.setObjectName("TemplateCardDesc")
            lbl_desc.setWordWrap(True)
            lbl_desc.setAlignment(Qt.AlignmentFlag.AlignTop)
            card_layout.addWidget(lbl_desc)
            card_layout.addStretch()

            # Ingen etikett får tryckas ihop under sin egen textrad
            for lbl in (lbl_card_title, lbl_desc):
                lbl.setMinimumHeight(lbl.fontMetrics().height())

            row = idx // 2
            col = idx % 2
            grid.addWidget(card_btn, row, col)

        scroll.setWidget(container)
        root_layout.addWidget(scroll, 1)

        # Bottom Buttons
        btn_bar = QHBoxLayout()
        self.btn_cancel = QPushButton(_("dlg_cancel"))
        self.btn_cancel.clicked.connect(self.reject)

        btn_bar.addStretch()
        btn_bar.addWidget(self.btn_cancel)
        root_layout.addLayout(btn_bar)

    def _select_template(self, template_id: str):
        self.selected_id = template_id
        self.template_selected.emit(template_id)
        self.accept()

    def get_selected_template_id(self) -> str | None:
        return self.selected_id

    def apply_theme(self):
        c = self.theme_mgr.current
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c["window_bg"]};
                color: {c["text_color"]};
            }}
            #TemplateCard {{
                background-color: {c["sidebar_card"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 8px;
                text-align: left;
            }}
            #TemplateCard:hover {{
                border-color: {c["accent"]};
                background-color: {c["btn_hover"]};
            }}
            #TemplateCardTitle {{
                font-size: 14px;
                font-weight: bold;
                color: {c["text_color"]};
            }}
            #TemplateCardDesc {{
                font-size: 11px;
                color: {c["text_muted"]};
            }}
            QPushButton {{
                background-color: {c["sidebar_card"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 6px 16px;
                color: {c["text_color"]};
            }}
            QPushButton:hover {{
                background-color: {c["btn_hover"]};
                border-color: {c["accent"]};
            }}
        """)
