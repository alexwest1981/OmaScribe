from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QCheckBox, QPushButton, QGroupBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from core.i18n import _

class TableDialog(QDialog):
    def __init__(self, theme_mgr, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        self.setWindowTitle(_("dlg_table_title"))
        self.setFixedWidth(320)
        self.setModal(True)
        
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        lbl_title = QLabel("📊 " + _("dlg_table_title"))
        lbl_title.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(lbl_title)

        # Dimensions Group
        group_dims = QGroupBox(_("dlg_table_dimensions"))
        dim_layout = QVBoxLayout(group_dims)
        dim_layout.setSpacing(12)

        # Rows
        row_box = QHBoxLayout()
        lbl_rows = QLabel(_("dlg_table_rows"))
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(1, 50)
        self.spin_rows.setValue(3)
        self.spin_rows.setFixedWidth(80)
        row_box.addWidget(lbl_rows)
        row_box.addStretch()
        row_box.addWidget(self.spin_rows)
        dim_layout.addLayout(row_box)

        # Columns
        col_box = QHBoxLayout()
        lbl_cols = QLabel(_("dlg_table_cols"))
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(1, 20)
        self.spin_cols.setValue(3)
        self.spin_cols.setFixedWidth(80)
        col_box.addWidget(lbl_cols)
        col_box.addStretch()
        col_box.addWidget(self.spin_cols)
        dim_layout.addLayout(col_box)

        # Header Row Checkbox
        self.chk_header = QCheckBox(_("dlg_table_header_row"))
        self.chk_header.setChecked(True)
        dim_layout.addWidget(self.chk_header)

        layout.addWidget(group_dims)

        # Dialog Buttons
        btn_box = QHBoxLayout()
        self.btn_cancel = QPushButton(_("dlg_cancel"))
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_insert = QPushButton("📊 " + _("dlg_table_insert_btn"))
        self.btn_insert.setDefault(True)
        self.btn_insert.clicked.connect(self.accept)
        
        btn_box.addStretch()
        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_insert)
        layout.addLayout(btn_box)

    def apply_theme(self):
        c = self.theme_mgr.current
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c["window_bg"]};
                color: {c["text_color"]};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {c["canvas_border"]};
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 14px;
                background-color: {c["toolbar_bg"]};
                color: {c["text_color"]};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                color: {c["accent"]};
            }}
            QLabel {{
                color: {c["text_color"]};
            }}
            QSpinBox {{
                background-color: {c["canvas_bg"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QCheckBox {{
                color: {c["text_color"]};
                font-weight: normal;
            }}
            QPushButton {{
                background-color: {c["canvas_bg"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {c["btn_hover"]};
                border-color: {c["accent"]};
            }}
            QPushButton[default="true"] {{
                background-color: {c["accent"]};
                color: #ffffff;
                border: none;
            }}
            QPushButton[default="true"]:hover {{
                opacity: 0.9;
            }}
        """)

    def get_table_params(self):
        return {
            "rows": self.spin_rows.value(),
            "cols": self.spin_cols.value(),
            "has_header": self.chk_header.isChecked()
        }
