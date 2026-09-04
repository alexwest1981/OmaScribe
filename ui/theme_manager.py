from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor

THEMES = {
    "paper": {
        "id": "paper",
        "name": "Classic Paper (Light)",
        "window_bg": "#f0f2f5",
        "canvas_bg": "#ffffff",
        "canvas_border": "#d0d4dc",
        "text_color": "#1a1d24",
        "toolbar_bg": "#ffffff",
        "toolbar_border": "#e1e4ea",
        "btn_hover": "#eef1f6",
        "btn_active": "#dbe3f0",
        "accent": "#2563eb",
        "sidebar_bg": "#f8f9fb",
        "sidebar_card": "#ffffff",
        "status_bg": "#f8f9fb",
        "status_text": "#555d6e"
    },
    "dark": {
        "id": "dark",
        "name": "Modern Obsidian (Dark)",
        "window_bg": "#121316",
        "canvas_bg": "#1e2025",
        "canvas_border": "#2e323b",
        "text_color": "#e2e6ed",
        "toolbar_bg": "#181a1f",
        "toolbar_border": "#282c34",
        "btn_hover": "#2c303a",
        "btn_active": "#3d4351",
        "accent": "#3b82f6",
        "sidebar_bg": "#16181d",
        "sidebar_card": "#21242b",
        "status_bg": "#16181d",
        "status_text": "#8c94a4"
    },
    "nord": {
        "id": "nord",
        "name": "Nord Arctic",
        "window_bg": "#2e3440",
        "canvas_bg": "#3b4252",
        "canvas_border": "#4c566a",
        "text_color": "#eceff4",
        "toolbar_bg": "#2e3440",
        "toolbar_border": "#434c5e",
        "btn_hover": "#434c5e",
        "btn_active": "#4c566a",
        "accent": "#88c0d0",
        "sidebar_bg": "#2e3440",
        "sidebar_card": "#3b4252",
        "status_bg": "#2e3440",
        "status_text": "#d8dee9"
    },
    "amber": {
        "id": "amber",
        "name": "Retro Amber CRT",
        "window_bg": "#0a0700",
        "canvas_bg": "#140e00",
        "canvas_border": "#3d2b00",
        "text_color": "#ffb000",
        "toolbar_bg": "#140e00",
        "toolbar_border": "#3d2b00",
        "btn_hover": "#261a00",
        "btn_active": "#473000",
        "accent": "#ffaa00",
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
        self.current_theme_id = self.config.get("theme", "paper")
        if self.current_theme_id not in THEMES:
            self.current_theme_id = "paper"

    def set_theme(self, theme_id):
        if theme_id in THEMES:
            self.current_theme_id = theme_id
            self.config.set("theme", theme_id)
            self.theme_changed.emit()

    @property
    def current(self):
        return THEMES[self.current_theme_id]

    def get_color(self, key, fallback="#000000"):
        return self.current.get(key, fallback)

    def get_stylesheet(self):
        c = self.current
        return f"""
        QMainWindow, QDialog {{
            background-color: {c["window_bg"]};
            color: {c["text_color"]};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", Helvetica, Arial, sans-serif;
        }}
        QMenuBar {{
            background-color: {c["toolbar_bg"]};
            color: {c["text_color"]};
            border-bottom: 1px solid {c["toolbar_border"]};
            padding: 3px 6px;
            font-size: 12px;
        }}
        QMenuBar::item {{
            background: transparent;
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
            padding: 6px 24px 6px 12px;
            border-radius: 4px;
            font-size: 12px;
        }}
        QMenu::item:selected {{
            background-color: {c["accent"]};
            color: #ffffff;
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {c["canvas_border"]};
            margin: 4px 6px;
        }}
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
        }}
        QToolButton:checked, QToolButton:pressed {{
            background-color: {c["btn_active"]};
            border-color: {c["accent"]};
            color: {c["accent"]};
            font-weight: bold;
        }}
        /* Quick Style Pill Button specific styling */
        QToolButton[stylePill="true"] {{
            background-color: {c["window_bg"]};
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
            color: #ffffff;
            border-color: {c["accent"]};
        }}
        /* Dropdowns */
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
        QComboBox QAbstractItemView {{
            background-color: {c["toolbar_bg"]};
            color: {c["text_color"]};
            border: 1px solid {c["canvas_border"]};
            border-radius: 6px;
            selection-background-color: {c["accent"]};
            selection-color: #ffffff;
            padding: 4px;
            outline: none;
            max-height: 380px;
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 26px;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {c["btn_hover"]};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {c["accent"]};
            color: #ffffff;
        }}
        QStatusBar {{
            background-color: {c["status_bg"]};
            color: {c["status_text"]};
            border-top: 1px solid {c["toolbar_border"]};
            font-size: 11px;
            padding: 2px 8px;
        }}
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
        QToolTip {{
            background-color: {c["canvas_bg"]};
            color: {c["text_color"]};
            border: 1px solid {c["canvas_border"]};
            padding: 5px 8px;
            border-radius: 4px;
            font-size: 11px;
        }}
        """
