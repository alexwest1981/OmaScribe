import os
import json
from core.i18n import i18n

CONFIG_PATH = os.path.expanduser("~/.config/omascribe/config.json")

DEFAULT_CONFIG = {
    "language": "en",
    "theme": "paper",  # "paper", "dark", "nord", "amber"
    "autosave": True,
    "autosave_interval_sec": 30,
    "default_font_family": "DejaVu Serif",
    "default_font_size": 12,
    "zoom_level": 100,
    "show_ai_sidebar": True,
    "sidebar_active_tab": 0,
    "ai_endpoint": "http://127.0.0.1:20128/v1",
    "ai_key": "",
    "ai_model": "OmniRoute",
    "dictation_model": "base",
    "dictation_lang": "auto",
    "dictation_auto_punctuate": True,
    "recent_files": [],
    "has_run_before": False
}

class ConfigManager:
    def __init__(self):
        self.data = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.data.update(saved)
                    if "has_run_before" not in saved:
                        self.data["has_run_before"] = True
                    if "language" in saved:
                        i18n.set_language(saved["language"])
            except Exception as e:
                print(f"[Config] Error loading config: {e}")

    def save(self):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"[Config] Error saving config: {e}")

    def get(self, key, fallback=None):
        return self.data.get(key, fallback)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def add_recent_file(self, filepath):
        if not filepath:
            return
        recents = self.data.get("recent_files", [])
        if filepath in recents:
            recents.remove(filepath)
        recents.insert(0, filepath)
        self.data["recent_files"] = recents[:10]
        self.save()

    def remove_recent_file(self, filepath):
        recents = self.data.get("recent_files", [])
        if filepath in recents:
            recents.remove(filepath)
            self.data["recent_files"] = recents
            self.save()

    def clear_recent_files(self):
        self.data["recent_files"] = []
        self.save()
