"""
ui/chart_dialog.py — Dialog för att skapa och anpassa diagram i OmaScribe.

Stödjer stapel-, linje-, cirkel-, donut- och områdesdiagram med realtidsförhandsgranskning,
redigerbar datatabell och färgteman.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QPushButton,
    QCheckBox, QGroupBox, QSplitter, QWidget, QHeaderView,
    QScrollArea, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QColor, QCursor

from core.i18n import _
from core.charts import ChartRenderer, PALETTES


class ChartDialog(QDialog):
    chart_ready = pyqtSignal(QImage, str)  # (qimage, alignment)

    def __init__(self, theme_mgr, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_mgr
        self.setWindowTitle(_("chart_dialog_title"))
        self.resize(920, 620)
        self.setModal(True)

        self.generated_image = None

        self.init_ui()
        self.apply_theme()
        self._load_sample_data()
        self._update_preview()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(14)

        # Header Title
        lbl_header = QLabel("📈 " + _("chart_dialog_title"))
        lbl_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        root_layout.addWidget(lbl_header)

        # Splitter: Vänster = Inställningar & Datatabell, Höger = Förhandsgranskning
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # =====================================================================
        # VÄNSTER PANEL (Konfiguration & Data)
        # =====================================================================
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(12)

        # 1. Allmänna inställningar
        grp_settings = QGroupBox(_("chart_grp_settings"))
        set_layout = QVBoxLayout(grp_settings)
        set_layout.setSpacing(8)

        # Typ av diagram
        row_type = QHBoxLayout()
        lbl_type = QLabel(_("chart_type") + ":")
        lbl_type.setFixedWidth(90)
        self.combo_type = QComboBox()
        self.combo_type.addItem("📊 " + _("chart_type_bar"), "bar")
        self.combo_type.addItem("📉 " + _("chart_type_line"), "line")
        self.combo_type.addItem("🌊 " + _("chart_type_area"), "area")
        self.combo_type.addItem("🥧 " + _("chart_type_pie"), "pie")
        self.combo_type.addItem("🍩 " + _("chart_type_donut"), "donut")
        self.combo_type.addItem("📑 " + _("chart_type_hbar"), "horizontal_bar")
        self.combo_type.currentIndexChanged.connect(self._on_type_changed)
        row_type.addWidget(lbl_type)
        row_type.addWidget(self.combo_type)
        set_layout.addLayout(row_type)

        # Titel
        row_title = QHBoxLayout()
        lbl_title = QLabel(_("chart_title") + ":")
        lbl_title.setFixedWidth(90)
        self.input_title = QLineEdit()
        self.input_title.setPlaceholderText(_("chart_title_placeholder"))
        self.input_title.textChanged.connect(self._update_preview)
        row_title.addWidget(lbl_title)
        row_title.addWidget(self.input_title)
        set_layout.addLayout(row_title)

        # Undertitel
        row_sub = QHBoxLayout()
        lbl_sub = QLabel(_("chart_subtitle") + ":")
        lbl_sub.setFixedWidth(90)
        self.input_sub = QLineEdit()
        self.input_sub.setPlaceholderText(_("chart_subtitle_placeholder"))
        self.input_sub.textChanged.connect(self._update_preview)
        row_sub.addWidget(lbl_sub)
        row_sub.addWidget(self.input_sub)
        set_layout.addLayout(row_sub)

        # Färgpalett
        row_pal = QHBoxLayout()
        lbl_pal = QLabel(_("chart_palette") + ":")
        lbl_pal.setFixedWidth(90)
        self.combo_palette = QComboBox()
        self.combo_palette.addItem("🔵 " + _("chart_pal_modern_blue"), "modern_blue")
        self.combo_palette.addItem("🟢 " + _("chart_pal_emerald"), "emerald_teal")
        self.combo_palette.addItem("🌅 " + _("chart_pal_warm"), "warm_sunset")
        self.combo_palette.addItem("🟣 " + _("chart_pal_purple"), "royal_purple")
        self.combo_palette.addItem("⚪ " + _("chart_pal_mono"), "slate_mono")
        self.combo_palette.currentIndexChanged.connect(self._update_preview)
        row_pal.addWidget(lbl_pal)
        row_pal.addWidget(self.combo_palette)
        set_layout.addLayout(row_pal)

        # Flaggor (Värden, Stödlinjer, Förklaring)
        row_flags = QHBoxLayout()
        self.chk_values = QCheckBox(_("chart_chk_values"))
        self.chk_values.setChecked(True)
        self.chk_values.toggled.connect(self._update_preview)
        self.chk_grid = QCheckBox(_("chart_chk_grid"))
        self.chk_grid.setChecked(True)
        self.chk_grid.toggled.connect(self._update_preview)
        self.chk_legend = QCheckBox(_("chart_chk_legend"))
        self.chk_legend.setChecked(True)
        self.chk_legend.toggled.connect(self._update_preview)
        row_flags.addWidget(self.chk_values)
        row_flags.addWidget(self.chk_grid)
        row_flags.addWidget(self.chk_legend)
        set_layout.addLayout(row_flags)

        left_layout.addWidget(grp_settings)

        # 2. Datatabell
        grp_data = QGroupBox(_("chart_grp_data"))
        data_layout = QVBoxLayout(grp_data)
        data_layout.setSpacing(6)

        self.table_data = QTableWidget(4, 2)
        self.table_data.setHorizontalHeaderLabels([_("chart_col_category"), _("chart_col_series1")])
        hdr = self.table_data.horizontalHeader()
        if hdr is not None:
            hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_data.itemChanged.connect(self._update_preview)
        data_layout.addWidget(self.table_data)

        # Knappar för att lägga till/ta bort rader/kolumner
        row_btns = QHBoxLayout()
        btn_add_row = QPushButton("➕ " + _("chart_btn_add_row"))
        btn_add_row.clicked.connect(self._add_row)
        btn_del_row = QPushButton("🗑️ " + _("chart_btn_del_row"))
        btn_del_row.clicked.connect(self._del_row)
        btn_add_col = QPushButton("➕ " + _("chart_btn_add_col"))
        btn_add_col.clicked.connect(self._add_col)
        btn_del_col = QPushButton("🗑️ " + _("chart_btn_del_col"))
        btn_del_col.clicked.connect(self._del_col)

        row_btns.addWidget(btn_add_row)
        row_btns.addWidget(btn_del_row)
        row_btns.addWidget(btn_add_col)
        row_btns.addWidget(btn_del_col)
        data_layout.addLayout(row_btns)

        left_layout.addWidget(grp_data, 1)
        splitter.addWidget(left_widget)

        # =====================================================================
        # HÖGER PANEL (Förhandsgranskning)
        # =====================================================================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(10)

        grp_preview = QGroupBox(_("chart_grp_preview"))
        preview_box_layout = QVBoxLayout(grp_preview)
        preview_box_layout.setContentsMargins(12, 16, 12, 12)

        self.scroll_preview = QScrollArea()
        self.scroll_preview.setWidgetResizable(True)
        self.scroll_preview.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_preview = QLabel()
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_preview.setWidget(self.lbl_preview)
        preview_box_layout.addWidget(self.scroll_preview)

        # Justering vid infogning
        row_align = QHBoxLayout()
        lbl_align = QLabel(_("chart_alignment") + ":")
        self.combo_align = QComboBox()
        self.combo_align.addItem(_("align_center"), "center")
        self.combo_align.addItem(_("align_left"), "left")
        self.combo_align.addItem(_("align_right"), "right")
        row_align.addWidget(lbl_align)
        row_align.addWidget(self.combo_align)
        row_align.addStretch()
        preview_box_layout.addLayout(row_align)

        right_layout.addWidget(grp_preview)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 5)
        root_layout.addWidget(splitter, 1)

        # Dialog-knappar längst ned
        bottom_bar = QHBoxLayout()
        self.btn_cancel = QPushButton(_("dlg_cancel"))
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_insert = QPushButton("📈 " + _("chart_btn_insert"))
        self.btn_insert.setDefault(True)
        self.btn_insert.setStyleSheet("font-weight: bold; padding: 6px 18px;")
        self.btn_insert.clicked.connect(self._on_insert_clicked)

        bottom_bar.addStretch()
        bottom_bar.addWidget(self.btn_cancel)
        bottom_bar.addWidget(self.btn_insert)
        root_layout.addLayout(bottom_bar)

    def _load_sample_data(self):
        self.input_title.setText("Månadsvis Försäljning & Resultat")
        self.input_sub.setText("Jämförelse mellan budget och utfall (tkr)")

        cats = ["Jan", "Feb", "Mar", "Apr", "Maj", "Jun"]
        series1 = ["120", "150", "180", "165", "210", "240"]
        series2 = ["110", "135", "160", "170", "190", "225"]

        self.table_data.blockSignals(True)
        self.table_data.setRowCount(len(cats))
        self.table_data.setColumnCount(3)
        self.table_data.setHorizontalHeaderLabels([_("chart_col_category"), "Utfall", "Budget"])

        for r, cat in enumerate(cats):
            self.table_data.setItem(r, 0, QTableWidgetItem(cat))
            self.table_data.setItem(r, 1, QTableWidgetItem(series1[r]))
            self.table_data.setItem(r, 2, QTableWidgetItem(series2[r]))

        self.table_data.blockSignals(False)

    def _on_type_changed(self):
        c_type = self.combo_type.currentData()
        if c_type in ("pie", "donut"):
            self.chk_grid.setEnabled(False)
            self.chk_values.setText(_("chart_chk_percent"))
        else:
            self.chk_grid.setEnabled(True)
            self.chk_values.setText(_("chart_chk_values"))
        self._update_preview()

    def _add_row(self):
        self.table_data.blockSignals(True)
        r = self.table_data.rowCount()
        self.table_data.insertRow(r)
        self.table_data.setItem(r, 0, QTableWidgetItem(f"Kategori {r + 1}"))
        for c in range(1, self.table_data.columnCount()):
            self.table_data.setItem(r, c, QTableWidgetItem("0"))
        self.table_data.blockSignals(False)
        self._update_preview()

    def _del_row(self):
        if self.table_data.rowCount() > 1:
            self.table_data.removeRow(self.table_data.rowCount() - 1)
            self._update_preview()

    def _add_col(self):
        c_type = self.combo_type.currentData()
        if c_type in ("pie", "donut"):
            QMessageBox.information(self, _("chart_dialog_title"), _("chart_pie_single_series_hint"))
            return
        self.table_data.blockSignals(True)
        c = self.table_data.columnCount()
        self.table_data.insertColumn(c)
        self.table_data.setHorizontalHeaderItem(c, QTableWidgetItem(f"Serie {c}"))
        for r in range(self.table_data.rowCount()):
            self.table_data.setItem(r, c, QTableWidgetItem("0"))
        self.table_data.blockSignals(False)
        self._update_preview()

    def _del_col(self):
        if self.table_data.columnCount() > 2:
            self.table_data.removeColumn(self.table_data.columnCount() - 1)
            self._update_preview()

    def _collect_data(self):
        categories = []
        for r in range(self.table_data.rowCount()):
            it = self.table_data.item(r, 0)
            categories.append(it.text().strip() if it else f"Kategori {r+1}")

        series_data = []
        for c in range(1, self.table_data.columnCount()):
            hdr = self.table_data.horizontalHeaderItem(c)
            s_name = hdr.text() if hdr else f"Serie {c}"
            vals = []
            for r in range(self.table_data.rowCount()):
                it = self.table_data.item(r, c)
                try:
                    vals.append(float(it.text().replace(",", ".")) if it and it.text().strip() else 0.0)
                except ValueError:
                    vals.append(0.0)
            series_data.append({"name": s_name, "values": vals})

        return categories, series_data

    def _update_preview(self):
        categories, series_data = self._collect_data()
        chart_type = self.combo_type.currentData()
        title = self.input_title.text().strip()
        subtitle = self.input_sub.text().strip()
        palette = self.combo_palette.currentData()
        show_values = self.chk_values.isChecked()
        show_grid = self.chk_grid.isChecked()
        show_legend = self.chk_legend.isChecked()

        img = ChartRenderer.render(
            chart_type=chart_type,
            title=title,
            categories=categories,
            series_data=series_data,
            subtitle=subtitle,
            palette=palette,
            width=540,
            height=340,
            show_values=show_values,
            show_grid=show_grid,
            show_legend=show_legend,
            bg_color="#ffffff",
            text_color="#1e293b"
        )
        self.generated_image = img

        pix = QPixmap.fromImage(img).scaled(
            480, 300,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.lbl_preview.setPixmap(pix)

    def _on_insert_clicked(self):
        if not self.generated_image:
            return
        categories, series_data = self._collect_data()
        chart_type = self.combo_type.currentData()
        title = self.input_title.text().strip()
        subtitle = self.input_sub.text().strip()
        palette = self.combo_palette.currentData()
        show_values = self.chk_values.isChecked()
        show_grid = self.chk_grid.isChecked()
        show_legend = self.chk_legend.isChecked()

        # Generera fullskalig högupplöst bild för dokumentet
        high_res_img = ChartRenderer.render(
            chart_type=chart_type,
            title=title,
            categories=categories,
            series_data=series_data,
            subtitle=subtitle,
            palette=palette,
            width=760,
            height=440,
            show_values=show_values,
            show_grid=show_grid,
            show_legend=show_legend,
            bg_color="#ffffff",
            text_color="#1e293b"
        )
        align = self.combo_align.currentData() or "center"
        self.chart_ready.emit(high_res_img, align)
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
            QLineEdit, QComboBox {{
                background-color: {c["canvas_bg"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 5px 8px;
                color: {c["text_color"]};
            }}
            QTableWidget {{
                background-color: {c["canvas_bg"]};
                border: 1px solid {c["canvas_border"]};
                color: {c["text_color"]};
                gridline-color: {c["canvas_border"]};
            }}
            QHeaderView::section {{
                background-color: {c["sidebar_card"]};
                color: {c["text_color"]};
                padding: 4px;
                border: 1px solid {c["canvas_border"]};
                font-weight: bold;
            }}
            QPushButton {{
                background-color: {c["sidebar_card"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 5px 12px;
                color: {c["text_color"]};
            }}
            QPushButton:hover {{
                background-color: {c["btn_hover"]};
                border-color: {c["accent"]};
            }}
        """)
