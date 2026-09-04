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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        QToolBar {{
            background-color: {c["toolbar_bg"]};
            border-bottom: 1px solid {c["toolbar_border"]};
            padding: 4px;
            spacing: 4px;
        }}
        QToolButton {{
            background-color: transparent;
            color: {c["text_color"]};
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 4px 6px;
            font-size: 11px;
            font-weight: 500;
        }}
        QToolButton:hover {{
            background-color: {c["btn_hover"]};
            border-color: {c["canvas_border"]};
        }}
        QToolButton:checked, QToolButton:pressed {{
            background-color: {c["btn_active"]};
            border-color: {c["accent"]};
        }}
        QComboBox, QFontComboBox {{
            background-color: {c["canvas_bg"]};
            color: {c["text_color"]};
            border: 1px solid {c["canvas_border"]};
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 11px;
            min-height: 20px;
        }}
        QComboBox::drop-down, QFontComboBox::drop-down {{
            border: none;
        }}
        QStatusBar {{
            background-color: {c["status_bg"]};
            color: {c["status_text"]};
            border-top: 1px solid {c["toolbar_border"]};
            font-size: 11px;
        }}
        QScrollBar:vertical {{
            background: {c["window_bg"]};
            width: 10px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {c["canvas_border"]};
            min-height: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c["accent"]};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QTabWidget::pane {{
            border: 1px solid {c["canvas_border"]};
            background: {c["sidebar_bg"]};
        }}
        QTabBar::tab {{
            background: {c["window_bg"]};
            color: {c["status_text"]};
            border: 1px solid {c["canvas_border"]};
            padding: 6px 12px;
            font-size: 11px;
            font-weight: 600;
        }}
        QTabBar::tab:selected {{
            background: {c["sidebar_bg"]};
            color: {c["accent"]};
            border-bottom-color: {c["sidebar_bg"]};
        }}
        """
