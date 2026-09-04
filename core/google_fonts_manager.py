import os
import threading
import httpx
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QFontDatabase
from core.google_fonts_data import GOOGLE_FONTS_CATALOG

USER_FONTS_DIR = os.path.expanduser("~/.config/omascribe/fonts")

class GoogleFontsManager(QObject):
    font_installed = pyqtSignal(str) # family name
    font_error = pyqtSignal(str, str) # (family, error)

    def __init__(self):
        super().__init__()
        os.makedirs(USER_FONTS_DIR, exist_ok=True)

    def is_installed(self, family_name):
        return family_name in QFontDatabase.families()

    def install_font(self, font_info):
        family = font_info["family"]
        url = font_info["url"]
        
        def worker():
            try:
                fname = f"{family.replace(' ', '')}-Regular.ttf"
                target_path = os.path.join(USER_FONTS_DIR, fname)
                
                with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                    resp = client.get(url)
                    if resp.status_code == 200:
                        with open(target_path, "wb") as f:
                            f.write(resp.content)
                        
                        font_id = QFontDatabase.addApplicationFont(target_path)
                        if font_id != -1:
                            self.font_installed.emit(family)
                        else:
                            self.font_error.emit(family, "Failed to register font with Qt")
                    else:
                        self.font_error.emit(family, f"HTTP Error {resp.status_code}")
            except Exception as e:
                self.font_error.emit(family, str(e))

        threading.Thread(target=worker, daemon=True).start()

    def uninstall_font(self, family_name):
        fname = f"{family_name.replace(' ', '')}-Regular.ttf"
        target_path = os.path.join(USER_FONTS_DIR, fname)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
                return True
            except Exception as e:
                print(f"Error removing font: {e}")
        return False
