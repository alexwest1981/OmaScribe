"""
ui/image_dialog.py — Dialog för att importera och anpassa bilder i OmaScribe.

Låter användaren välja en bildfil (eller använda urklippt bild), ställa in
skalning/bredd, justering (vänster, centrerad, höger) och bildtext.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QComboBox, QLineEdit, QGroupBox, QSpinBox,
    QRadioButton, QButtonGroup, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QColor

from core.i18n import _


class ImageDialog(QDialog):
    image_ready = pyqtSignal(str, int, str, str)  # (image_path, width_px, alignment, caption)

    def __init__(self, theme_mgr, initial_path: str = "", parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        self.image_path = initial_path
        self.original_pixmap = None

        self.setWindowTitle(_("img_dialog_title"))
        self.resize(600, 520)
        self.setModal(True)

        self.init_ui()
        self.apply_theme()

        if self.image_path and os.path.exists(self.image_path):
            self._load_image_file(self.image_path)

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(14)

        # Header
        lbl_header = QLabel("🖼️ " + _("img_dialog_title"))
        lbl_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        root_layout.addWidget(lbl_header)

        # 1. Filval
        row_file = QHBoxLayout()
        self.input_path = QLineEdit()
        self.input_path.setPlaceholderText(_("img_choose_placeholder"))
        self.input_path.textChanged.connect(self._on_path_changed)

        btn_browse = QPushButton("📂 " + _("img_btn_browse"))
        btn_browse.clicked.connect(self._browse_file)

        row_file.addWidget(self.input_path, 1)
        row_file.addWidget(btn_browse)
        root_layout.addLayout(row_file)

        # 2. Förhandsgranskningsruta
        grp_preview = QGroupBox(_("img_preview"))
        preview_layout = QVBoxLayout(grp_preview)
        preview_layout.setContentsMargins(12, 12, 12, 12)

        self.scroll_preview = QScrollArea()
        self.scroll_preview.setWidgetResizable(True)
        self.scroll_preview.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_preview.setFixedHeight(180)
        self.scroll_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_preview = QLabel(_("img_no_image_selected"))
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_preview.setWidget(self.lbl_preview)
        preview_layout.addWidget(self.scroll_preview)

        self.lbl_dim_info = QLabel("")
        self.lbl_dim_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_dim_info.setStyleSheet("font-size: 11px; color: #64748b;")
        preview_layout.addWidget(self.lbl_dim_info)

        root_layout.addWidget(grp_preview)

        # 3. Storlek & Skalning
        grp_size = QGroupBox(_("img_size_and_placement"))
        size_layout = QVBoxLayout(grp_size)
        size_layout.setSpacing(10)

        # Storlekspreset
        row_size = QHBoxLayout()
        lbl_size = QLabel(_("img_scale") + ":")
        lbl_size.setFixedWidth(80)

        self.combo_size = QComboBox()
        self.combo_size.addItem(_("img_size_small") + " (25%)", 0.25)
        self.combo_size.addItem(_("img_size_medium") + " (50%)", 0.50)
        self.combo_size.addItem(_("img_size_large") + " (75%)", 0.75)
        self.combo_size.addItem(_("img_size_full") + " (100%)", 1.0)
        self.combo_size.addItem(_("img_size_custom"), "custom")
        self.combo_size.setCurrentIndex(1)  # 50% som standard
        self.combo_size.currentIndexChanged.connect(self._on_size_preset_changed)

        self.spin_width = QSpinBox()
        self.spin_width.setRange(50, 1600)
        self.spin_width.setValue(400)
        self.spin_width.setSuffix(" px")
        self.spin_width.setEnabled(False)

        row_size.addWidget(lbl_size)
        row_size.addWidget(self.combo_size)
        row_size.addWidget(self.spin_width)
        size_layout.addLayout(row_size)

        # Justering (Vänster, Centrerad, Höger)
        row_align = QHBoxLayout()
        lbl_align = QLabel(_("img_alignment") + ":")
        lbl_align.setFixedWidth(80)

        self.combo_align = QComboBox()
        self.combo_align.addItem("⯮ " + _("align_left"), "left")
        self.combo_align.addItem("⯭ " + _("align_center"), "center")
        self.combo_align.addItem("⯬ " + _("align_right"), "right")
        self.combo_align.setCurrentIndex(1)  # Centrerad som standard

        row_align.addWidget(lbl_align)
        row_align.addWidget(self.combo_align)
        size_layout.addLayout(row_align)

        # Bildtext (valfritt)
        row_caption = QHBoxLayout()
        lbl_caption = QLabel(_("img_caption") + ":")
        lbl_caption.setFixedWidth(80)
        self.input_caption = QLineEdit()
        self.input_caption.setPlaceholderText(_("img_caption_placeholder"))
        row_caption.addWidget(lbl_caption)
        row_caption.addWidget(self.input_caption)
        size_layout.addLayout(row_caption)

        root_layout.addWidget(grp_size)

        # 4. Knappar
        btn_bar = QHBoxLayout()
        self.btn_cancel = QPushButton(_("dlg_cancel"))
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_insert = QPushButton("🖼️ " + _("img_btn_insert"))
        self.btn_insert.setDefault(True)
        self.btn_insert.setEnabled(False)
        self.btn_insert.clicked.connect(self._on_insert)

        btn_bar.addStretch()
        btn_bar.addWidget(self.btn_cancel)
        btn_bar.addWidget(self.btn_insert)
        root_layout.addLayout(btn_bar)

    def _browse_file(self):
        fpath, _flt = QFileDialog.getOpenFileName(
            self,
            _("img_dialog_title"),
            "",
            "Bilder (*.png *.jpg *.jpeg *.webp *.svg *.gif *.bmp);;Alla filer (*.*)"
        )
        if fpath:
            self.input_path.setText(fpath)

    def _on_path_changed(self, path):
        if path and os.path.exists(path):
            self._load_image_file(path)
        else:
            self.lbl_preview.setText(_("img_no_image_selected"))
            self.lbl_preview.setPixmap(QPixmap())
            self.lbl_dim_info.setText("")
            self.btn_insert.setEnabled(False)
            self.original_pixmap = None

    def _load_image_file(self, path):
        self.image_path = path
        pix = QPixmap(path)
        if not pix.isNull():
            self.original_pixmap = pix
            scaled = pix.scaled(
                260, 160,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_preview.setPixmap(scaled)
            self.lbl_dim_info.setText(f"{pix.width()} × {pix.height()} px")
            self.btn_insert.setEnabled(True)
            self._on_size_preset_changed()

    def _on_size_preset_changed(self):
        val = self.combo_size.currentData()
        if val == "custom":
            self.spin_width.setEnabled(True)
        else:
            self.spin_width.setEnabled(False)
            if self.original_pixmap:
                base_page_width = 720  # Standard A4 sidbredd i editorn
                target_w = int(base_page_width * float(val))
                self.spin_width.setValue(min(self.original_pixmap.width(), target_w))

    def _on_insert(self):
        if not self.image_path or not os.path.exists(self.image_path):
            return
        width_px = self.spin_width.value()
        align = self.combo_align.currentData() or "center"
        caption = self.input_caption.text().strip()
        self.image_ready.emit(self.image_path, width_px, align, caption)
        self.accept()

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
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {c["canvas_bg"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 5px 8px;
                color: {c["text_color"]};
            }}
            QPushButton {{
                background-color: {c["sidebar_card"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 5px 14px;
                color: {c["text_color"]};
            }}
            QPushButton:hover {{
                background-color: {c["btn_hover"]};
                border-color: {c["accent"]};
            }}
        """)
