import os
import json
import locale
from core.i18n import i18n

CONFIG_PATH = os.path.expanduser("~/.config/omascribe/config.json")

def get_system_default_language():
    try:
        lang_env = (os.environ.get("LANG", "") or os.environ.get("LC_ALL", "") or "").lower()
        if lang_env.startswith("sv"):
            return "sv"
        loc = locale.getdefaultlocale()[0]
        if loc and loc.lower().startswith("sv"):
            return "sv"
    except Exception:
        pass
    return "en"

# AI-standarder på ett ställe. Tidigare hade varje modul sin egen reserv
# (api.deepseek.com/v1 i två filer, localhost:8000/v1 i ai_client,
# 127.0.0.1:20128/v1 i tre) och modellreserven var "claude-3-5-sonnet" även mot
# en DeepSeek-endpoint. En ny installation kunde alltså skicka dokumentet till
# en leverantör ingen hade valt. Tom sträng = ingen AI vald, och då görs inget
# anrop alls: chat_completion säger till i klartext i stället.
DEFAULT_AI_ENDPOINT = ""
DEFAULT_AI_MODEL = ""

DEFAULT_CONFIG = {
    "language": get_system_default_language(),
    "theme": "paper",  # "paper", "dark", "nord", "amber"
    "autosave": True,
    "autosave_interval_sec": 30,
    "default_font_family": "DejaVu Serif",
    "default_font_size": 12,
    "zoom_level": 100,
    "show_ai_sidebar": True,
    "sidebar_active_tab": 0,
    # Neutral standard för den som installerar appen. Ingen privat slutpunkt
    # bakas in — användaren anger sin egen leverantör och nyckel i
    # Inställningar. (En sparad config.json vinner alltid över detta.)
    "ai_endpoint": DEFAULT_AI_ENDPOINT,
    "ai_key": "",
    "ai_model": DEFAULT_AI_MODEL,
    "dictation_model": "base",
    "dictation_lang": "auto",
    "dictation_auto_punctuate": True,
    "recent_files": [],
    "has_run_before": False,
    "vault_root": os.path.expanduser("~/Documents/OmaScribe Vault"),
    "research_searxng_url": ""   # egen SearXNG-instans ger nyckelfri webbsökning
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
