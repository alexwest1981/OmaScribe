import os
import json
from PyQt6.QtCore import QObject, pyqtSignal

from core.languages import native

LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locales")

class LocalizationManager(QObject):
    language_changed = pyqtSignal(str)

    def __init__(self, default_lang="en"):
        super().__init__()
        self.current_lang = default_lang
        self.translations = {}
        self.fallback_translations = {}
        self._load_fallback()
        self.set_language(default_lang)

    def _load_fallback(self):
        en_path = os.path.join(LOCALES_DIR, "en.json")
        if os.path.exists(en_path):
            try:
                with open(en_path, "r", encoding="utf-8") as f:
                    self.fallback_translations = json.load(f)
            except Exception as e:
                print(f"[i18n] Error loading fallback en.json: {e}")

    def set_language(self, lang_code):
        lang_path = os.path.join(LOCALES_DIR, f"{lang_code}.json")
        if os.path.exists(lang_path):
            try:
                with open(lang_path, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
                self.current_lang = lang_code
                self.language_changed.emit(lang_code)
                return True
            except Exception as e:
                print(f"[i18n] Error loading {lang_code}.json: {e}")
        
        # Fallback to English
        self.translations = self.fallback_translations.copy()
        self.current_lang = "en"
        self.language_changed.emit("en")
        return False

    def t(self, key, **kwargs):
        """Translate a string key with optional formatting variables.

        Flertal: en nyckel kan bära 'singular|plural' — 'en anteckning|{n} anteckningar'.
        Formen väljs efter antalet i kwargs (count, n, num, antal, items, total).
        Texten är orörd när nyckeln inte har något '|'.

        ponytail: två former räcker för alla elva språken i tabellen. Polska och
        ryska behöver tre (1 / 2-4 / 5+) — bygg ut _plural med en regel per språk
        när de språken kommer in, inte förr.
        """
        val = self.translations.get(key, self.fallback_translations.get(key, key))
        if not isinstance(val, str):
            return val
        if "|" in val:
            val = self._plural(val, kwargs)
        if kwargs:
            try:
                return val.format(**kwargs)
            except Exception:
                pass
        return val

    @staticmethod
    def _plural(val, kwargs):
        """Rätt form av 'singular|plural' för antalet i kwargs."""
        former = val.split("|")
        if len(former) == 1:
            return val
        for namn in ("count", "n", "num", "antal", "items", "total"):
            if namn in kwargs:
                try:
                    return former[0] if float(kwargs[namn]) == 1 else former[1]
                except (TypeError, ValueError):
                    return former[1]
        return former[1]

    def n(self, key, count, **kwargs):
        """Flertalsform av en nyckel: n_('notes_stat_notes', 3)."""
        return self.t(key, count=count, **kwargs)

    def get_language(self):
        return self.current_lang

    def get_available_languages(self):
        """(kod, namn på språket självt) för varje språkfil som finns."""
        langs = []
        if os.path.exists(LOCALES_DIR):
            for fname in os.listdir(LOCALES_DIR):
                if fname.endswith(".json"):
                    code = os.path.splitext(fname)[0]
                    langs.append((code, native(code)))
        return sorted(langs)

# Global singleton instance
i18n = LocalizationManager("en")
_ = i18n.t
