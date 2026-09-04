from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QCheckBox, QPushButton, QTabWidget, QWidget,
    QFormLayout
)
from PyQt6.QtCore import Qt
from core.i18n import _, i18n
from ui.theme_manager import THEMES

class SettingsDialog(QDialog):
    def __init__(self, config_mgr, theme_mgr, parent=None):
        super().__init__(parent)
        self.config = config_mgr
        self.theme_mgr = theme_mgr

        self.setWindowTitle(_("settings_title"))
        self.resize(500, 360)
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()

        # Tab 1: General
        tab_gen = QWidget()
        form_gen = QFormLayout(tab_gen)

        self.combo_lang = QComboBox()
        for code, name in i18n.get_available_languages():
            self.combo_lang.addItem(name, code)
        # Select current
        idx = self.combo_lang.findData(i18n.get_language())
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)
        form_gen.addRow(_("settings_language"), self.combo_lang)

        self.combo_theme = QComboBox()
        for tid, tinfo in THEMES.items():
            self.combo_theme.addItem(tinfo["name"], tid)
        idx_t = self.combo_theme.findData(self.theme_mgr.current_theme_id)
        if idx_t >= 0:
            self.combo_theme.setCurrentIndex(idx_t)
        form_gen.addRow(_("settings_theme"), self.combo_theme)

        self.chk_autosave = QCheckBox(_("settings_autosave"))
        self.chk_autosave.setChecked(self.config.get("autosave", True))
        form_gen.addRow("", self.chk_autosave)

        self.tabs.addTab(tab_gen, _("settings_tab_general"))

        # Tab 2: AI Provider
        tab_ai = QWidget()
        form_ai = QFormLayout(tab_ai)

        self.combo_provider = QComboBox()
        self.providers = [
            ("omniroute", "OmniRoute (Local Proxy)", "http://127.0.0.1:20128/v1", "OmniRoute"),
            ("ollama", "Ollama (100% Free & Offline Local AI)", "http://localhost:11434/v1", "llama3.2"),
            ("openai", "OpenAI (GPT-4o / GPT-4o-mini)", "https://api.openai.com/v1", "gpt-4o-mini"),
            ("openrouter", "OpenRouter (Claude 3.5 Sonnet / Llama)", "https://openrouter.ai/api/v1", "anthropic/claude-3.5-sonnet"),
            ("gemini", "Google Gemini (Direct OpenAI-API)", "https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-1.5-flash"),
            ("lmstudio", "LM Studio / LocalAI (Local server)", "http://localhost:1234/v1", "local-model"),
            ("custom", "Custom / Self-Hosted Endpoint", "", "")
        ]

        curr_url = self.config.get("ai_endpoint", "http://127.0.0.1:20128/v1")
        matched_idx = len(self.providers) - 1 # default custom
        for i, (pid, pname, purl, pmodel) in enumerate(self.providers):
            self.combo_provider.addItem(pname, pid)
            if purl and purl.rstrip("/") == curr_url.rstrip("/"):
                matched_idx = i

        self.combo_provider.setCurrentIndex(matched_idx)
        self.combo_provider.currentIndexChanged.connect(self._on_provider_preset_changed)
        form_ai.addRow(_("settings_ai_provider"), self.combo_provider)

        self.input_ai_url = QLineEdit(curr_url)
        form_ai.addRow(_("settings_ai_endpoint"), self.input_ai_url)

        self.input_ai_key = QLineEdit(self.config.get("ai_key", ""))
        self.input_ai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_ai_key.setPlaceholderText("sk-... (leave empty if not required, e.g. Ollama)")
        form_ai.addRow(_("settings_ai_key"), self.input_ai_key)

        self.input_ai_model = QLineEdit(self.config.get("ai_model", "OmniRoute"))
        form_ai.addRow(_("settings_ai_model"), self.input_ai_model)

        # Test connection button & status label
        test_row = QHBoxLayout()
        self.btn_test = QPushButton(_("settings_btn_test_ai"))
        self.btn_test.clicked.connect(self._test_ai_connection)
        self.lbl_test_status = QLabel("")
        self.lbl_test_status.setWordWrap(True)
        test_row.addWidget(self.btn_test)
        test_row.addWidget(self.lbl_test_status)
        test_row.addStretch()
        form_ai.addRow("", test_row)

        self.tabs.addTab(tab_ai, _("settings_tab_ai"))

        # Tab 3: Dictation
        tab_dict = QWidget()
        form_dict = QFormLayout(tab_dict)

        self.combo_dict_lang = QComboBox()
        self.combo_dict_lang.addItem("Auto Detect (SV/EN/...)", "auto")
        self.combo_dict_lang.addItem("Swedish (sv)", "sv")
        self.combo_dict_lang.addItem("English (en)", "en")
        idx_d = self.combo_dict_lang.findData(self.config.get("dictation_lang", "auto"))
        if idx_d >= 0:
            self.combo_dict_lang.setCurrentIndex(idx_d)
        form_dict.addRow(_("dictation_language"), self.combo_dict_lang)

        self.chk_punct = QCheckBox(_("dictation_auto_punctuate"))
        self.chk_punct.setChecked(self.config.get("dictation_auto_punctuate", True))
        form_dict.addRow("", self.chk_punct)

        self.tabs.addTab(tab_dict, _("settings_tab_dictation"))

        layout.addWidget(self.tabs)

        # Buttons
        btn_row = QHBoxLayout()
        btn_save = QPushButton(_("settings_btn_save"))
        btn_save.clicked.connect(self._save_and_close)
        btn_cancel = QPushButton(_("settings_btn_cancel"))
        btn_cancel.clicked.connect(self.reject)

        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_cancel)
        layout.addLayout(btn_row)

    def _on_provider_preset_changed(self, idx):
        if 0 <= idx < len(self.providers):
            pid, pname, purl, pmodel = self.providers[idx]
            if purl:
                self.input_ai_url.setText(purl)
            if pmodel:
                self.input_ai_model.setText(pmodel)

    def _test_ai_connection(self):
        url = self.input_ai_url.text().strip().rstrip("/") + "/chat/completions"
        key = self.input_ai_key.text().strip()
        model = self.input_ai_model.text().strip()

        self.lbl_test_status.setText("⏳ Testing connection...")
        self.lbl_test_status.setStyleSheet("color: #3b82f6; font-size: 11px;")
        self.btn_test.setEnabled(False)

        import threading, httpx
        def worker():
            headers = {"Content-Type": "application/json"}
            if key:
                headers["Authorization"] = f"Bearer {key}"
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Respond with the word OK."}],
                "max_tokens": 10
            }
            try:
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        msg = _("settings_test_success", model=model)
                        self.lbl_test_status.setText(f"✓ {msg}")
                        self.lbl_test_status.setStyleSheet("color: #16a34a; font-size: 11px;")
                    else:
                        err_txt = resp.text[:80]
                        self.lbl_test_status.setText(f"✕ HTTP {resp.status_code}: {err_txt}")
                        self.lbl_test_status.setStyleSheet("color: #dc2626; font-size: 11px;")
            except Exception as e:
                self.lbl_test_status.setText(f"✕ {_('settings_test_failed', error=str(e)[:60])}")
                self.lbl_test_status.setStyleSheet("color: #dc2626; font-size: 11px;")
            finally:
                self.btn_test.setEnabled(True)

        threading.Thread(target=worker, daemon=True).start()

    def _save_and_close(self):
        # Apply language
        new_lang = self.combo_lang.currentData()
        if new_lang != i18n.get_language():
            i18n.set_language(new_lang)
            self.config.set("language", new_lang)

        # Apply theme
        new_theme = self.combo_theme.currentData()
        self.theme_mgr.set_theme(new_theme)

        # Apply config
        self.config.set("autosave", self.chk_autosave.isChecked())
        self.config.set("ai_endpoint", self.input_ai_url.text().strip())
        self.config.set("ai_key", self.input_ai_key.text().strip())
        self.config.set("ai_model", self.input_ai_model.text().strip())
        self.config.set("dictation_lang", self.combo_dict_lang.currentData())
        self.config.set("dictation_auto_punctuate", self.chk_punct.isChecked())
        self.config.save()

        self.accept()

    def apply_theme(self):
        self.setStyleSheet(self.theme_mgr.get_stylesheet())
