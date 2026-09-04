import os
import time
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QIcon, QCursor

from core.i18n import _, i18n

class StartScreen(QWidget):
    new_document_requested = pyqtSignal()
    open_document_requested = pyqtSignal()
    open_recent_requested = pyqtSignal(str)

    def __init__(self, config_mgr, theme_mgr, parent=None):
        super().__init__(parent)
        self.config = config_mgr
        self.theme_mgr = theme_mgr

        self.init_ui()
        self.apply_theme()
        self.theme_mgr.theme_changed.connect(self.apply_theme)
        i18n.language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Scroll Area for the Start Screen
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Centered Content Container
        self.container = QFrame()
        self.container.setObjectName("StartContainer")
        self.container.setFixedWidth(780)
        self.container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)

        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(32, 28, 32, 40)
        self.content_layout.setSpacing(20)

        # 0. Top Bar (Language toggle)
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.btn_lang = QPushButton()
        self.btn_lang.setObjectName("StartLangButton")
        self.btn_lang.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_lang.clicked.connect(self._toggle_language)
        self._update_lang_btn()
        top_bar.addWidget(self.btn_lang)
        self.content_layout.addLayout(top_bar)

        # 1. Hero / Header Section
        hero_layout = QVBoxLayout()
        hero_layout.setSpacing(8)
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # App Icon
        self.lbl_icon = QLabel()
        self.lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_icon.setPixmap(pixmap)
        else:
            self.lbl_icon.setText("✍️")
            self.lbl_icon.setStyleSheet("font-size: 48px;")

        hero_layout.addWidget(self.lbl_icon)

        # Title
        self.lbl_title = QLabel("OmaScribe")
        self.lbl_title.setObjectName("StartTitle")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(self.lbl_title)

        # Subtitle
        self.lbl_subtitle = QLabel(_("start_tagline"))
        self.lbl_subtitle.setObjectName("StartSubtitle")
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(self.lbl_subtitle)

        self.content_layout.addLayout(hero_layout)

        # 2. Quick Action Cards (New Blank & Open File)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        # New Document Card Button
        self.btn_new = QPushButton()
        self.btn_new.setObjectName("ActionCard")
        self.btn_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new.clicked.connect(self.new_document_requested.emit)

        card_new_layout = QVBoxLayout(self.btn_new)
        card_new_layout.setContentsMargins(20, 20, 20, 20)
        card_new_layout.setSpacing(6)

        lbl_new_icon = QLabel("📄")
        lbl_new_icon.setStyleSheet("font-size: 26px;")
        self.lbl_new_title = QLabel(_("start_new_doc"))
        self.lbl_new_title.setObjectName("CardTitle")
        self.lbl_new_sub = QLabel(_("start_new_doc_sub"))
        self.lbl_new_sub.setObjectName("CardSubtitle")
        self.lbl_new_sub.setWordWrap(True)

        card_new_layout.addWidget(lbl_new_icon)
        card_new_layout.addWidget(self.lbl_new_title)
        card_new_layout.addWidget(self.lbl_new_sub)
        card_new_layout.addStretch()

        # Browse Files Card Button
        self.btn_open = QPushButton()
        self.btn_open.setObjectName("ActionCard")
        self.btn_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open.clicked.connect(self.open_document_requested.emit)

        card_open_layout = QVBoxLayout(self.btn_open)
        card_open_layout.setContentsMargins(20, 20, 20, 20)
        card_open_layout.setSpacing(6)

        lbl_open_icon = QLabel("📂")
        lbl_open_icon.setStyleSheet("font-size: 26px;")
        self.lbl_open_title = QLabel(_("start_open_doc"))
        self.lbl_open_title.setObjectName("CardTitle")
        self.lbl_open_sub = QLabel(_("start_open_doc_sub"))
        self.lbl_open_sub.setObjectName("CardSubtitle")
        self.lbl_open_sub.setWordWrap(True)

        card_open_layout.addWidget(lbl_open_icon)
        card_open_layout.addWidget(self.lbl_open_title)
        card_open_layout.addWidget(self.lbl_open_sub)
        card_open_layout.addStretch()

        cards_layout.addWidget(self.btn_new)
        cards_layout.addWidget(self.btn_open)
        self.content_layout.addLayout(cards_layout)

        # 3. Recent Documents Section
        recents_header_layout = QHBoxLayout()
        self.lbl_recent_heading = QLabel(_("start_recent_files"))
        self.lbl_recent_heading.setObjectName("SectionHeading")

        self.btn_clear_recents = QPushButton(_("start_clear_recents"))
        self.btn_clear_recents.setObjectName("LinkButton")
        self.btn_clear_recents.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_clear_recents.clicked.connect(self._clear_recents)

        recents_header_layout.addWidget(self.lbl_recent_heading)
        recents_header_layout.addStretch()
        recents_header_layout.addWidget(self.btn_clear_recents)
        self.content_layout.addLayout(recents_header_layout)

        # Recent Files List Container
        self.recents_list_container = QVBoxLayout()
        self.recents_list_container.setSpacing(8)
        self.content_layout.addLayout(self.recents_list_container)

        self.content_layout.addStretch()

        self.scroll_area.setWidget(self.container)
        root_layout.addWidget(self.scroll_area)

        self.refresh_recents()

    def refresh_recents(self):
        # Clear existing items
        while self.recents_list_container.count():
            item = self.recents_list_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        recent_files = self.config.get("recent_files", [])
        
        if not recent_files:
            self.btn_clear_recents.setVisible(False)
            empty_lbl = QLabel(_("start_no_recents"))
            empty_lbl.setObjectName("EmptyRecentsLabel")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setContentsMargins(0, 20, 0, 20)
            self.recents_list_container.addWidget(empty_lbl)
            return

        self.btn_clear_recents.setVisible(True)

        for filepath in recent_files[:10]:
            item_btn = self._create_recent_item_widget(filepath)
            self.recents_list_container.addWidget(item_btn)

    def _get_file_icon(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".docx":
            return "📘"
        elif ext in {".md", ".markdown"}:
            return "📝"
        elif ext in {".html", ".htm"}:
            return "🌐"
        elif ext == ".pdf":
            return "📕"
        return "📄"

    def _create_recent_item_widget(self, filepath):
        btn = QPushButton()
        btn.setObjectName("RecentItemButton")
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setMinimumHeight(68)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.clicked.connect(lambda checked, fp=filepath: self.open_recent_requested.emit(fp))

        layout = QHBoxLayout(btn)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(16)

        # Icon
        icon_str = self._get_file_icon(filepath)
        lbl_icon = QLabel(icon_str)
        lbl_icon.setStyleSheet("font-size: 24px;")
        layout.addWidget(lbl_icon)

        # File details (Name & Dir)
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        filename = os.path.basename(filepath) if filepath else "Untitled"
        lbl_name = QLabel(filename)
        lbl_name.setObjectName("RecentFileName")

        dir_path = os.path.dirname(filepath)
        # Shorten user home directory to ~
        home = os.path.expanduser("~")
        if dir_path.startswith(home):
            dir_display = "~" + dir_path[len(home):]
        else:
            dir_display = dir_path

        lbl_dir = QLabel(dir_display)
        lbl_dir.setObjectName("RecentFileDir")

        text_layout.addWidget(lbl_name)
        text_layout.addWidget(lbl_dir)
        layout.addLayout(text_layout, 1)

        # File status / Date
        date_layout = QVBoxLayout()
        date_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        if os.path.exists(filepath):
            try:
                mtime = os.path.getmtime(filepath)
                dt = datetime.fromtimestamp(mtime)
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                date_str = ""
            lbl_meta = QLabel(date_str)
            lbl_meta.setObjectName("RecentFileMeta")
        else:
            lbl_meta = QLabel(_("start_file_not_found"))
            lbl_meta.setObjectName("RecentFileMissing")

        date_layout.addWidget(lbl_meta)
        layout.addLayout(date_layout)

        return btn

    def _toggle_language(self):
        curr = i18n.get_language()
        new_lang = "sv" if curr == "en" else "en"
        i18n.set_language(new_lang)
        self.config.set("language", new_lang)

    def _update_lang_btn(self):
        curr = i18n.get_language()
        if curr == "sv":
            self.btn_lang.setText("🌐 🇸🇪 Svenska (Byt till EN)")
        else:
            self.btn_lang.setText("🌐 🇬🇧 English (Switch to SV)")

    def _clear_recents(self):
        self.config.clear_recent_files()
        self.refresh_recents()

    def apply_theme(self):
        c = self.theme_mgr.current
        
        self.scroll_area.setStyleSheet(f"background-color: {c['window_bg']};")
        self.container.setStyleSheet(f"background-color: {c['window_bg']};")

        self.setStyleSheet(f"""
            #StartLangButton {{
                background: transparent;
                border: 1px solid {c['canvas_border']};
                border-radius: 12px;
                color: {c['text_muted']};
                font-size: 11px;
                font-weight: 600;
                padding: 4px 10px;
            }}
            #StartLangButton:hover {{
                border-color: {c['accent']};
                color: {c['text_color']};
                background-color: {c['btn_hover']};
            }}
            #StartTitle {{
                font-size: 28px;
                font-weight: 800;
                color: {c['text_color']};
                letter-spacing: -0.5px;
            }}
            #StartSubtitle {{
                font-size: 13px;
                color: {c['text_muted']};
            }}
            #SectionHeading {{
                font-size: 14px;
                font-weight: 700;
                color: {c['text_color']};
                margin-top: 10px;
            }}
            #ActionCard {{
                background-color: {c['sidebar_card']};
                border: 1px solid {c['canvas_border']};
                border-radius: 8px;
                text-align: left;
                min-height: 100px;
            }}
            #ActionCard:hover {{
                border-color: {c['accent']};
                background-color: {c['btn_hover']};
            }}
            #ActionCard:pressed {{
                background-color: {c['btn_active']};
            }}
            #CardTitle {{
                font-size: 14px;
                font-weight: 700;
                color: {c['text_color']};
            }}
            #CardSubtitle {{
                font-size: 11px;
                color: {c['text_muted']};
            }}
            #RecentItemButton {{
                background-color: {c['sidebar_card']};
                border: 1px solid {c['canvas_border']};
                border-radius: 8px;
                text-align: left;
                min-height: 68px;
            }}
            #RecentItemButton:hover {{
                border-color: {c['accent']};
                background-color: {c['btn_hover']};
            }}
            #RecentItemButton:pressed {{
                background-color: {c['btn_active']};
            }}
            #RecentFileName {{
                font-size: 14px;
                font-weight: 600;
                color: {c['text_color']};
            }}
            #RecentFileDir {{
                font-size: 12px;
                color: {c['text_muted']};
            }}
            #RecentFileMeta {{
                font-size: 12px;
                color: {c['text_muted']};
            }}
            #RecentFileMissing {{
                font-size: 11px;
                color: #ef4444;
                font-style: italic;
            }}
            #EmptyRecentsLabel {{
                font-size: 12px;
                color: {c['text_muted']};
                font-style: italic;
            }}
            #LinkButton {{
                background: transparent;
                border: none;
                color: {c['accent']};
                font-size: 12px;
                font-weight: 600;
                padding: 4px 8px;
            }}
            #LinkButton:hover {{
                text-decoration: underline;
            }}
        """)

    def retranslate_ui(self):
        self._update_lang_btn()
        self.lbl_subtitle.setText(_("start_tagline"))
        self.lbl_new_title.setText(_("start_new_doc"))
        self.lbl_new_sub.setText(_("start_new_doc_sub"))
        self.lbl_open_title.setText(_("start_open_doc"))
        self.lbl_open_sub.setText(_("start_open_doc_sub"))
        self.lbl_recent_heading.setText(_("start_recent_files"))
        self.btn_clear_recents.setText(_("start_clear_recents"))
        self.refresh_recents()
