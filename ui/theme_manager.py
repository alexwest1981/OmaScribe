from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

THEMES = {
    # Referensens (v0-exportens) design: docs/design/omascribe-ui-spec.md.
    # Värdena är lästa ur referensens globals.css, inte gissade.
    "oma": {
        "id": "oma",
        "name": "OmaScribe (referens)",
        "window_bg": "#f4f5f7",         # --canvas
        "dialog_bg": "#ffffff",
        "canvas_bg": "#ffffff",
        "canvas_border": "#e7e9ed",     # --line
        "text_color": "#1d2630",        # --ink
        "text_muted": "#87909b",        # --muted-ink
        "toolbar_bg": "#ffffff",
        "toolbar_border": "#e7e9ed",
        "btn_bg": "#ffffff",
        "btn_text": "#1d2630",
        "btn_border": "#e7e9ed",
        "btn_hover": "#f2f4f7",
        "btn_active": "#e7e9ed",
        "accent": "#3366ff",            # --blue
        "accent_text": "#ffffff",
        "link": "#3366ff",
        "link_missing": "#e5a23b",
        "code_bg": "#f7f8fb",
        "code_text": "#29323c",
        "sidebar_bg": "#ffffff",
        "sidebar_card": "#f7f8fb",
        "status_bg": "#ffffff",
        "status_text": "#939ba5",
        "ui_font": "Arial, Helvetica, sans-serif",
        # anatomi-nycklar (se specen, avsnitt 1)
        "brand_bg": "#1e2937",
        "brand_text": "#ffffff",
        "rail_bg": "#ffffff",
        "rail_text": "#9aa2ad",
        "rail_active_bg": "#eef2ff",
        "rail_active_text": "#3366ff",
        "card_bg": "#f7f8fb",
        "card_border": "#eceef2",
        "chip_bg": "#f0efff",
        "chip_text": "#6253db",
        "chip_ok_bg": "#eff8f3",
        "chip_ok_text": "#5b8d79",
        "kbd_bg": "#f2f3f5",
        "kbd_border": "#e2e4e8",
        "kbd_text": "#89919b",
        "save_ok": "#3eb68a",
    },
    "paper": {
        "id": "paper",
        "name": "Classic Paper (Light)",
        "window_bg": "#f1f3f6",
        "dialog_bg": "#ffffff",
        "canvas_bg": "#ffffff",
        "canvas_border": "#cbd5e1",
        "text_color": "#0f172a",       # Deep black/slate for maximum contrast
        "text_muted": "#475569",
        "toolbar_bg": "#ffffff",
        "toolbar_border": "#e2e8f0",
        "btn_bg": "#ffffff",
        "btn_text": "#0f172a",
        "btn_border": "#cbd5e1",
        "btn_hover": "#e2e8f0",
        "btn_active": "#cbd5e1",
        "accent": "#2563eb",
        "accent_text": "#ffffff",
        "link": "#2563eb",              # wikilänk till befintlig anteckning
        "link_missing": "#b45309",      # länk till något som inte finns ännu
        "code_bg": "#eef2f7",
        "code_text": "#0f172a",
        "sidebar_bg": "#f8fafc",
        "sidebar_card": "#ffffff",
        "status_bg": "#f8fafc",
        "status_text": "#334155"
    },
    "dark": {
        "id": "dark",
        "name": "Modern Obsidian (Dark)",
        "window_bg": "#111318",
        "dialog_bg": "#181b22",
        "canvas_bg": "#1e222b",
        "canvas_border": "#333948",
        "text_color": "#f8fafc",       # Crisp white/slate for maximum contrast
        "text_muted": "#94a3b8",
        "toolbar_bg": "#161920",
        "toolbar_border": "#2b303e",
        "btn_bg": "#222733",
        "btn_text": "#f8fafc",
        "btn_border": "#3b4254",
        "btn_hover": "#2f3647",
        "btn_active": "#3d465c",
        "accent": "#3b82f6",
        "accent_text": "#ffffff",
        "link": "#60a5fa",
        "link_missing": "#fbbf24",
        "code_bg": "#12151c",
        "code_text": "#e2e8f0",
        "sidebar_bg": "#161920",
        "sidebar_card": "#212633",
        "status_bg": "#161920",
        "status_text": "#94a3b8"
    },
    "nord": {
        "id": "nord",
        "name": "Nord Arctic",
        "window_bg": "#242933",
        "dialog_bg": "#2e3440",
        "canvas_bg": "#3b4252",
        "canvas_border": "#4c566a",
        "text_color": "#eceff4",
        "text_muted": "#d8dee9",
        "toolbar_bg": "#2e3440",
        "toolbar_border": "#434c5e",
        "btn_bg": "#3b4252",
        "btn_text": "#eceff4",
        "btn_border": "#4c566a",
        "btn_hover": "#434c5e",
        "btn_active": "#4c566a",
        "accent": "#88c0d0",
        "accent_text": "#242933",
        "link": "#88c0d0",
        "link_missing": "#ebcb8b",
        "code_bg": "#2e3440",
        "code_text": "#d8dee9",
        "sidebar_bg": "#2e3440",
        "sidebar_card": "#3b4252",
        "status_bg": "#2e3440",
        "status_text": "#d8dee9"
    },
    "amber": {
        "id": "amber",
        "name": "Retro Amber CRT",
        "window_bg": "#0a0700",
        "dialog_bg": "#140e00",
        "canvas_bg": "#140e00",
        "canvas_border": "#473000",
        "text_color": "#ffb000",
        "text_muted": "#cc8800",
        "toolbar_bg": "#140e00",
        "toolbar_border": "#3d2b00",
        "btn_bg": "#211700",
        "btn_text": "#ffb000",
        "btn_border": "#5c3e00",
        "btn_hover": "#332200",
        "btn_active": "#4d3300",
        "accent": "#ffaa00",
        "accent_text": "#0a0700",
        # På en bärnstens-CRT ligger accenten bara 6 steg från brödtexten.
        # Länkar måste skilja sig i ljusstyrka, inte bara i nyans.
        "link": "#ffe9a8",
        "link_missing": "#ff6b6b",
        "code_bg": "#1c1400",
        "code_text": "#ffe9a8",
        "sidebar_bg": "#0f0a00",
        "sidebar_card": "#1c1400",
        "status_bg": "#0f0a00",
        "status_text": "#cc8800"
    }
}

class ThemeManager(QObject):
    theme_changed = pyqtSignal()

    def __init__(self, config_mgr):
        super().__init__()
        self.config = config_mgr
        self.current_theme_id = self.config.get("theme", "oma")
        if self.current_theme_id not in THEMES:
            self.current_theme_id = "oma"

    def set_theme(self, theme_id):
        if theme_id in THEMES:
            self.current_theme_id = theme_id
            self.config.set("theme", theme_id)
            self.apply_theme_to_app()
            self.theme_changed.emit()

    @property
    def current(self):
        return THEMES[self.current_theme_id]

    def tokens(self) -> dict:
        """Temats färger plus anatomi-nycklarna (topbar, rail, kort, chips, kbd).

        Ett tema som inte anger en anatomi-nyckel ärver den från sina egna
        grundfärger, så alla teman får samma form och bara "oma" behöver
        upprepa referensens värden.
        """
        c = dict(self.current)
        arv = {
            "brand_bg": c["text_color"],
            "brand_text": c["canvas_bg"],
            "rail_bg": c["toolbar_bg"],
            "rail_text": c["text_muted"],
            "rail_active_bg": c["btn_hover"],
            "rail_active_text": c["accent"],
            "card_bg": c["sidebar_card"],
            "card_border": c["canvas_border"],
            "chip_bg": c["btn_hover"],
            "chip_text": c["accent"],
            "chip_ok_bg": c["btn_hover"],
            "chip_ok_text": c.get("link_missing", c["accent"]),
            "kbd_bg": c["btn_hover"],
            "kbd_border": c["canvas_border"],
            "kbd_text": c["text_muted"],
            "save_ok": "#3eb68a",
            "ui_font": "-apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, "
                       "\"Inter\", Helvetica, Arial, sans-serif",
        }
        arv.update({k: v for k, v in c.items() if k in arv and v})   # temat vinner
        return {**c, **arv}

    def get_color(self, key, fallback="#000000"):
        return self.current.get(key, fallback)

    def apply_theme_to_app(self, app=None):
        if app is None:
            app = QApplication.instance()
        if not app:
            return

        c = self.current

        # 1. Synchronize Qt Application Palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(c["window_bg"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(c["text_color"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(c["canvas_bg"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(c["sidebar_bg"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(c["text_color"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(c["btn_bg"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(c["btn_text"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(c["accent"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(c["accent_text"]))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(c["dialog_bg"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(c["text_color"]))
        app.setPalette(palette)

        # 2. Apply Global Stylesheet
        app.setStyleSheet(self.get_stylesheet())

    def get_stylesheet(self):
        c = self.tokens()
        return f"""
        /* Global Base */
        QWidget {{
            color: {c["text_color"]};
            font-family: {c["ui_font"]};
        }}
        QMainWindow, QDialog, QMessageBox {{
            background-color: {c["window_bg"]};
            color: {c["text_color"]};
        }}

        /* Labels & Text */
        QLabel, QMessageBox QLabel, QDialog QLabel {{
            color: {c["text_color"]};
            font-size: 13px;
        }}

        /* Push Buttons (Dialogs, QMessageBox, Forms) */
        QPushButton, QMessageBox QPushButton, QDialog QPushButton {{
            background-color: {c["btn_bg"]};
            color: {c["btn_text"]};
            border: 1px solid {c["btn_border"]};
            border-radius: 6px;
            padding: 6px 16px;
            font-size: 12px;
            font-weight: 600;
            min-height: 22px;
        }}
        QPushButton:hover, QMessageBox QPushButton:hover, QDialog QPushButton:hover {{
            background-color: {c["btn_hover"]};
            border-color: {c["accent"]};
            color: {c["text_color"]};
        }}
        QPushButton:pressed, QMessageBox QPushButton:pressed, QDialog QPushButton:pressed {{
            background-color: {c["btn_active"]};
        }}
        QPushButton:default, QMessageBox QPushButton:default {{
            background-color: {c["accent"]};
            color: {c["accent_text"]};
            border: 1px solid {c["accent"]};
        }}
        QPushButton:default:hover, QMessageBox QPushButton:default:hover {{
            opacity: 0.9;
        }}

        /* Menu Bar & Menus */
        QMenuBar {{
            background-color: {c["toolbar_bg"]};
            color: {c["text_color"]};
            border-bottom: 1px solid {c["toolbar_border"]};
            padding: 3px 6px;
            font-size: 12px;
        }}
        QMenuBar::item {{
            background: transparent;
            color: {c["text_color"]};
            padding: 4px 8px;
            border-radius: 4px;
        }}
        QMenuBar::item:selected {{
            background-color: {c["btn_hover"]};
            color: {c["accent"]};
        }}
        QMenu {{
            background-color: {c["toolbar_bg"]};
            color: {c["text_color"]};
            border: 1px solid {c["canvas_border"]};
            border-radius: 8px;
            padding: 6px;
        }}
        QMenu::item {{
            color: {c["text_color"]};
            padding: 6px 24px 6px 12px;
            border-radius: 4px;
            font-size: 12px;
        }}
        QMenu::item:selected {{
            background-color: {c["accent"]};
            color: {c["accent_text"]};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {c["canvas_border"]};
            margin: 4px 6px;
        }}

        /* Toolbars & Tool Buttons */
        QToolBar {{
            background-color: {c["toolbar_bg"]};
            border-bottom: 1px solid {c["toolbar_border"]};
            padding: 5px 8px;
            spacing: 3px;
        }}
        QToolBar::separator {{
            width: 1px;
            background-color: {c["canvas_border"]};
            margin: 4px 6px;
        }}
        QToolButton {{
            background-color: transparent;
            color: {c["text_color"]};
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 4px 7px;
            font-size: 12px;
            font-weight: 500;
        }}
        QToolButton:hover {{
            background-color: {c["btn_hover"]};
            border-color: {c["canvas_border"]};
            color: {c["text_color"]};
        }}
        QToolButton:checked, QToolButton:pressed {{
            background-color: {c["btn_active"]};
            border-color: {c["accent"]};
            color: {c["accent"]};
            font-weight: bold;
        }}

        /* Quick Style Pill Button specific styling */
        QToolButton[stylePill="true"] {{
            background-color: {c["btn_bg"]};
            color: {c["text_color"]};
            border: 1px solid {c["canvas_border"]};
            border-radius: 5px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 600;
        }}
        QToolButton[stylePill="true"]:hover {{
            background-color: {c["btn_hover"]};
            border-color: {c["accent"]};
        }}
        QToolButton[stylePill="true"]:checked {{
            background-color: {c["accent"]};
            color: {c["accent_text"]};
            border-color: {c["accent"]};
        }}

        /* Dropdown Combo Boxes */
        QComboBox, QFontComboBox {{
            background-color: {c["canvas_bg"]};
            color: {c["text_color"]};
            border: 1px solid {c["canvas_border"]};
            border-radius: 6px;
            padding: 3px 26px 3px 8px;
            font-size: 12px;
            font-weight: 500;
            min-height: 22px;
        }}
        QComboBox:hover, QFontComboBox:hover {{
            border-color: {c["accent"]};
            background-color: {c["btn_hover"]};
        }}
        QComboBox:focus, QFontComboBox:focus {{
            border: 1.5px solid {c["accent"]};
        }}
        QComboBox::drop-down, QFontComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 22px;
            border-left: 1px solid {c["canvas_border"]};
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
            background-color: transparent;
        }}
        QComboBox::down-arrow, QFontComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {c["text_color"]};
            width: 0px;
            height: 0px;
            margin-right: 2px;
        }}
        QComboBox::down-arrow:hover {{
            border-top-color: {c["accent"]};
        }}
        /* Menyns vy (QComboBox QAbstractItemView) stils INTE här med flit: en
           sådan regel får Qt att svara ja på SH_ComboBox_Popup, och då fyller
           menyn hela skärmen med skrollpilar och listan läggs mitt i (mätt:
           800px meny, listen 390px på y=133) — dessutom stängs menyvyns egen
           skrollist av, så bara de första elva typsnitten gick att nå. Färgerna
           kommer i stället från appens palett (se apply_theme_to_app), och
           radhöjden från FontItemDelegate.sizeHint. */
        /* LineEdit & TextInputs */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {{
            background-color: {c["canvas_bg"]};
            color: {c["text_color"]};
            border: 1px solid {c["canvas_border"]};
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 12px;
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {{
            border: 1.5px solid {c["accent"]};
        }}

        /* Status Bar */
        QStatusBar {{
            background-color: {c["status_bg"]};
            color: {c["status_text"]};
            border-top: 1px solid {c["toolbar_border"]};
            font-size: 11px;
            padding: 2px 8px;
        }}
        QStatusBar QLabel {{
            color: {c["status_text"]};
            font-size: 11px;
        }}

        /* Scrollbars */
        QScrollBar:vertical {{
            background: {c["window_bg"]};
            width: 8px;
            margin: 0px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {c["canvas_border"]};
            min-height: 24px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c["accent"]};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: {c["window_bg"]};
            height: 8px;
            margin: 0px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: {c["canvas_border"]};
            min-width: 24px;
            border-radius: 4px;
        }}

        /* Tabs & Groupboxes */
        QTabWidget::pane {{
            border: 1px solid {c["canvas_border"]};
            background: {c["sidebar_bg"]};
            border-radius: 6px;
        }}
        QTabBar::tab {{
            background: {c["window_bg"]};
            color: {c["status_text"]};
            border: 1px solid {c["canvas_border"]};
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 600;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background: {c["sidebar_bg"]};
            color: {c["accent"]};
            border-bottom-color: {c["sidebar_bg"]};
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

        /* Tooltips */
        QToolTip {{
            background-color: {c["dialog_bg"]};
            color: {c["text_color"]};
            border: 1px solid {c["canvas_border"]};
            padding: 5px 8px;
            border-radius: 4px;
            font-size: 11px;
        }}

        /* ---------------------------------------------------------------
           Referensens anatomi (docs/design/omascribe-ui-spec.md).
           Måtten är referensens: topbar 64, rail 66/40x40 radie 11,
           toolbar-knapp 34 radie 7, statusbar 43, inspector 312.
           --------------------------------------------------------------- */

        /* Topbar */
        #TopBar {{
            background-color: {c["toolbar_bg"]};
            border-bottom: 1px solid {c["toolbar_border"]};
        }}
        #InspectorHead {{
            background-color: {c["sidebar_bg"]};
        }}
        #TopBar QMenuBar {{
            background: transparent;
            border-bottom: 0;
            padding: 0;
        }}
        #TopBar QMenuBar::item {{
            padding: 5px 9px;
            border-radius: 7px;
            color: {c["text_color"]};
        }}
        #TopBar QMenuBar::item:selected {{
            background-color: {c["btn_hover"]};
            color: {c["text_color"]};
        }}
        #BrandMark {{
            background-color: {c["brand_bg"]};
            color: {c["brand_text"]};
            border-radius: 10px;
            font-family: Georgia, "Liberation Serif", serif;
            font-size: 19px;
        }}
        #BrandName {{
            font-size: 15px;
            font-weight: 700;
            color: {c["text_color"]};
        }}
        #BrandDivider {{
            background-color: {c["toolbar_border"]};
            border: 0;
        }}
        #FileButton {{
            background: transparent;
            border: 0;
            border-radius: 7px;
            color: {c["text_muted"]};
            font-size: 13px;
            padding: 6px 9px;
        }}
        #FileButton:hover {{
            background-color: {c["btn_hover"]};
            color: {c["text_color"]};
        }}
        #SaveState {{
            color: {c["text_muted"]};
            font-size: 11px;
        }}
        #SaveDot {{
            background-color: {c["save_ok"]};
            border-radius: 3px;
        }}
        #IconButton {{
            background: transparent;
            border: 0;
            border-radius: 8px;
            color: {c["text_muted"]};
            padding: 7px;
        }}
        #IconButton:hover {{
            background-color: {c["btn_hover"]};
            color: {c["text_color"]};
        }}

        /* Vänsterrail: 66px, 40x40-knappar, radie 11 */
        #LeftRail {{
            background-color: {c["rail_bg"]};
            border-right: 1px solid {c["toolbar_border"]};
        }}
        #RailButton {{
            background: transparent;
            border: 0;
            border-radius: 11px;
            color: {c["rail_text"]};
            font-size: 17px;
        }}
        #RailButton:hover {{
            background-color: {c["btn_hover"]};
            color: {c["text_color"]};
        }}
        #RailButton:checked {{
            background-color: {c["rail_active_bg"]};
            color: {c["rail_active_text"]};
        }}

        /* Verktygsraden: 58 hög, knappar 34 med radie 7, avdelare 20 */
        #FormatBar {{
            background-color: {c["toolbar_bg"]};
            border-bottom: 1px solid {c["toolbar_border"]};
            padding: 0 12px;
            min-height: 58px;
        }}
        #FormatBar QToolButton {{
            height: 34px;
            border-radius: 7px;
            color: {c["text_muted"]};
            padding: 0 8px;
            font-size: 12px;
        }}
        #FormatBar QToolButton:hover,
        #FormatBar QToolButton:checked {{
            background-color: {c["btn_hover"]};
            border-color: transparent;
            color: {c["text_color"]};
            font-weight: normal;
        }}
        #FormatBar QToolButton:checked {{
            background-color: {c["rail_active_bg"]};
            color: {c["rail_active_text"]};
        }}
        #FormatBar QToolButton[stylePill="true"] {{
            background-color: transparent;
            border: 1px solid transparent;
            font-size: 11px;
        }}
        #FormatBar QToolButton[stylePill="true"]:hover {{
            background-color: {c["btn_hover"]};
        }}
        #FormatBar QToolButton[stylePill="true"]:checked {{
            background-color: {c["rail_active_bg"]};
            color: {c["rail_active_text"]};
            border-color: transparent;
        }}
        #FormatBar::separator {{
            background-color: {c["toolbar_border"]};
            width: 1px;
            height: 20px;
            margin: 0 6px;
        }}
        #FormatBar QComboBox, #FormatBar QFontComboBox {{
            background: transparent;
            border: 1px solid transparent;
            border-radius: 7px;
            font-size: 12px;
            min-height: 30px;
            padding: 0 18px 0 8px;
        }}
        #FormatBar QComboBox:hover, #FormatBar QFontComboBox:hover {{
            background-color: {c["btn_hover"]};
            border-color: transparent;
        }}
        #FormatBar QComboBox::drop-down, #FormatBar QFontComboBox::drop-down {{
            border-left: 0;
            width: 16px;
        }}
        /* "Inspector"-växlaren längst till höger i verktygsraden */
        #InspectorToggle {{
            background: transparent;
            border: 0;
            border-radius: 7px;
            color: {c["text_muted"]};
            font-size: 12px;
            padding: 7px 10px;
        }}
        #InspectorToggle:hover {{
            background-color: {c["btn_hover"]};
            color: {c["text_color"]};
        }}
        #InspectorToggle:checked {{
            background-color: {c["chip_bg"]};
            color: {c["chip_text"]};
        }}

        /* Statusbar: 43 hög, 11px, dämpad text */
        QStatusBar {{
            min-height: 43px;
            padding: 0 12px;
        }}
        QStatusBar::item {{ border: 0; }}

        /* Inspector: eyebrow, flikar med understrykning, kort, chips, kbd */
        #InspectorRoot {{ background-color: {c["sidebar_bg"]}; border-left: 1px solid {c["toolbar_border"]}; }}
        #InspectorEyebrow {{
            color: {c["text_muted"]};
            font-size: 10px;
        }}
        #InspectorTitle {{
            color: {c["text_color"]};
            font-size: 21px;
            font-weight: 500;
        }}
        #InspectorClose {{
            background: transparent;
            border: 0;
            color: {c["text_muted"]};
            padding: 3px;
        }}
        #InspectorClose:hover {{ color: {c["text_color"]}; }}
        #InspectorTabs::pane {{ border: 0; background: transparent; }}
        QTabWidget#InspectorTabs::tab-bar {{ left: 20px; }}
        #InspectorTabs QTabBar::tab {{
            background: transparent;
            border: 0;
            border-bottom: 2px solid transparent;
            border-radius: 0;
            margin-right: 14px;
            padding: 0 0 11px 0;
            color: {c["text_muted"]};
            font-size: 12px;
            font-weight: normal;
            min-width: 58px;
        }}
        #InspectorTabs QTabBar::tab:selected {{
            background: transparent;
            border-bottom: 2px solid {c["accent"]};
            color: {c["accent"]};
            font-weight: 600;
        }}
        #InspectorTabs QTabBar::tab:hover {{ color: {c["text_color"]}; }}
        #InspectorTabs QTabBar::scroller {{ width: 30px; }}
        #InspectorTabs QTabBar QToolButton {{
            background: transparent;
            border: 0;
        }}
        /* Pilarna ritas som trianglar: stilen tar annars bort plattformens
           egen pil och knapparna blir tomma. */
        #InspectorTabs QTabBar QToolButton::right-arrow {{
            image: none;
            width: 0;
            height: 0;
            border-left: 5px solid {c["text_muted"]};
            border-top: 4px solid transparent;
            border-bottom: 4px solid transparent;
        }}
        #InspectorTabs QTabBar QToolButton::left-arrow {{
            image: none;
            width: 0;
            height: 0;
            border-right: 5px solid {c["text_muted"]};
            border-top: 4px solid transparent;
            border-bottom: 4px solid transparent;
        }}
        #InspectorTabs QTabBar QToolButton:hover::right-arrow {{
            border-left-color: {c["text_color"]};
        }}
        #InspectorTabs QTabBar QToolButton:hover::left-arrow {{
            border-right-color: {c["text_color"]};
        }}

        #SuggestionCard {{
            background-color: transparent;
            border: 1px solid {c["card_border"]};
            border-radius: 10px;
        }}
        #ScoreCard {{
            background-color: {c["card_bg"]};
            border: 0;
            border-radius: 12px;
        }}
        #CardText {{ color: {c["text_muted"]}; font-size: 11px; }}
        #SuggestionKind {{ color: {c["text_muted"]}; font-size: 10px; }}
        #SuggestionBody {{ color: {c["text_color"]}; font-size: 11px; }}
        #SuggestionIcon {{
            border-radius: 6px;
            font-size: 12px;
            color: {c["link_missing"]};
            background-color: {c["btn_hover"]};
        }}
        #MetricCard {{
            background-color: {c["card_bg"]};
            border: 0;
            border-radius: 10px;
        }}
        #MetricValue {{ color: {c["text_color"]}; font-size: 22px; font-weight: 600; }}
        #MetricLabel {{ color: {c["text_muted"]}; font-size: 10px; }}
        #Chip {{
            background-color: {c["chip_bg"]};
            color: {c["chip_text"]};
            border-radius: 99px;
            padding: 5px 9px;
            font-size: 10px;
        }}
        #ChipOk {{
            background-color: {c["chip_ok_bg"]};
            color: {c["chip_ok_text"]};
            border-radius: 99px;
            padding: 5px 9px;
            font-size: 10px;
        }}
        #Kbd {{
            background-color: {c["kbd_bg"]};
            border: 1px solid {c["kbd_border"]};
            border-radius: 4px;
            color: {c["kbd_text"]};
            font-size: 10px;
            padding: 1px 5px;
        }}
        #StageMeta {{
            color: {c["text_muted"]};
            font-size: 10px;
        }}
        """

