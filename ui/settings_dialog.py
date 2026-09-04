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

        self.input_ai_url = QLineEdit(self.config.get("ai_endpoint", "http://localhost:8000/v1"))
        form_ai.addRow(_("settings_ai_endpoint"), self.input_ai_url)

        self.input_ai_key = QLineEdit(self.config.get("ai_key", ""))
        self.input_ai_key.setEchoMode(QLineEdit.EchoMode.Password)
        form_ai.addRow(_("settings_ai_key"), self.input_ai_key)

        self.input_ai_model = QLineEdit(self.config.get("ai_model", "claude-3-5-sonnet"))
        form_ai.addRow(_("settings_ai_model"), self.input_ai_model)

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
        c = self.theme_mgr.current
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c["window_bg"]};
                color: {c["text_color"]};
            }}
            QLineEdit, QComboBox {{
                background-color: {c["canvas_bg"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton {{
                background-color: {c["sidebar_card"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 6px 12px;
            }}
        """)
