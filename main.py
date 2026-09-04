#!/usr/bin/env python3
import sys
import os

# Ensure project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from core.config import ConfigManager
from core.i18n import i18n
from core.font_manager import FontManager
from core.ai_client import AIClient
from core.dictation_engine import DictationEngine
from core.doc_manager import DocumentManager
from ui.theme_manager import ThemeManager
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("OmaScribe")
    app.setOrganizationName("OmaScribe")

    # Load custom TTF/OTF fonts from resources & user dir
    FontManager.load_custom_fonts()

    config_mgr = ConfigManager()
    theme_mgr = ThemeManager(config_mgr)
    theme_mgr.apply_theme_to_app(app)
    
    # Initialize language from config
    saved_lang = config_mgr.get("language", "en")
    i18n.set_language(saved_lang)

    ai_client = AIClient(config_mgr)
    dictation_engine = DictationEngine(config_mgr)

    window = MainWindow(ai_client, dictation_engine, theme_mgr, config_mgr)

    # Open file if passed via CLI argument
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        try:
            window.open_recent_file(os.path.abspath(sys.argv[1]))
        except Exception as e:
            print(f"Error loading {sys.argv[1]}: {e}")

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
