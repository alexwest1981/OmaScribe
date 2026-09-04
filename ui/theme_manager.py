from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

THEMES = {
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
            self.apply_theme_to_app()
            self.theme_changed.emit()

    @property
    def current(self):
        return THEMES[self.current_theme_id]

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
        c = self.current
        return f"""
        /* Global Base */
        QWidget {{
            color: {c["text_color"]};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", Helvetica, Arial, sans-serif;
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
        QComboBox QAbstractItemView {{
            background-color: {c["toolbar_bg"]};
            color: {c["text_color"]};
            border: 1px solid {c["canvas_border"]};
            border-radius: 6px;
            selection-background-color: {c["accent"]};
            selection-color: {c["accent_text"]};
            padding: 4px;
            outline: none;
            max-height: 380px;
        }}
        QComboBox QAbstractItemView::item {{
            color: {c["text_color"]};
            min-height: 26px;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {c["btn_hover"]};
            color: {c["text_color"]};
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {c["accent"]};
            color: {c["accent_text"]};
        }}

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
        """
