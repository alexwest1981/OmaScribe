from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QFrame, QListWidget, QListWidgetItem,
    QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from core.i18n import _, i18n
from core.document_stats import DocumentStats

class SidebarInspector(QWidget):
    apply_suggestion_requested = pyqtSignal(str, str) # (original, replacement)
    outline_item_clicked = pyqtSignal(int) # cursor position

    def __init__(self, ai_client, theme_mgr, parent=None):
        super().__init__(parent)
        self.ai = ai_client
        self.theme_mgr = theme_mgr
        self.setFixedWidth(320)

        self.init_ui()
        self.apply_theme()
        self.theme_mgr.theme_changed.connect(self.apply_theme)
        i18n.language_changed.connect(self.retranslate_ui)

        self.ai.review_completed.connect(self._on_review_received)
        if hasattr(self.ai, "review_error"):
            self.ai.review_error.connect(self._on_review_error)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self.tabs = QTabWidget()
        self.tab_review = QWidget()
        self.tab_outline = QWidget()
        self.tab_metrics = QWidget()

        self._init_review_tab()
        self._init_outline_tab()
        self._init_metrics_tab()

        self.tabs.addTab(self.tab_review, _("sidebar_tab_review"))
        self.tabs.addTab(self.tab_outline, _("sidebar_tab_outline"))
        self.tabs.addTab(self.tab_metrics, _("sidebar_tab_metrics"))

        layout.addWidget(self.tabs)

    def _init_review_tab(self):
        layout = QVBoxLayout(self.tab_review)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Header with score + refresh button
        top = QHBoxLayout()
        self.lbl_tone = QLabel("Tone: Neutral")
        self.lbl_tone.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        top.addWidget(self.lbl_tone)
        top.addStretch()

        self.btn_refresh = QPushButton("⟳ " + _("ai_review_btn_refresh"))
        self.btn_refresh.setFixedHeight(24)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        # Indeterminate progress bar for loading state
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Suggestions Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(6)
        self.cards_layout.addStretch()

        self.scroll.setWidget(self.cards_container)
        layout.addWidget(self.scroll)

    def _init_outline_tab(self):
        layout = QVBoxLayout(self.tab_outline)
        layout.setContentsMargins(6, 6, 6, 6)

        self.list_outline = QListWidget()
        self.list_outline.itemClicked.connect(self._on_outline_clicked)
        layout.addWidget(self.list_outline)

    def _init_metrics_tab(self):
        layout = QVBoxLayout(self.tab_metrics)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.lbl_words = QLabel("0 words")
        self.lbl_chars = QLabel("0 characters")
        self.lbl_read_time = QLabel("0 min read")
        self.lbl_lix = QLabel("LIX Readability: -")

        for lbl in [self.lbl_words, self.lbl_chars, self.lbl_read_time, self.lbl_lix]:
            lbl.setFont(QFont("Segoe UI", 10))
            layout.addWidget(lbl)

        layout.addStretch()

    def set_loading(self, is_loading=True):
        if is_loading:
            self.btn_refresh.setEnabled(False)
            self.btn_refresh.setText("⏳ " + _("ai_review_refreshing"))
            self.progress_bar.setVisible(True)

            # Clear cards and show a loading placeholder
            self._clear_cards()
            c = self.theme_mgr.current
            loading_card = QFrame()
            loading_card.setStyleSheet(f"""
                QFrame {{
                    background-color: {c["sidebar_card"]};
                    border: 1px dashed {c["accent"]};
                    border-radius: 6px;
                    padding: 12px;
                }}
            """)
            card_layout = QVBoxLayout(loading_card)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(6)

            lbl_spinner = QLabel("✨ " + _("ai_review_loading_text"))
            lbl_spinner.setWordWrap(True)
            lbl_spinner.setStyleSheet(f"color: {c['accent']}; font-size: 11px; font-weight: bold;")
            card_layout.addWidget(lbl_spinner)
            self.cards_layout.insertWidget(0, loading_card)
        else:
            self.progress_bar.setVisible(False)
            self._reset_refresh_button()

    def _reset_refresh_button(self):
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("⟳ " + _("ai_review_btn_refresh"))

    def show_short_message(self):
        self.progress_bar.setVisible(False)
        self._reset_refresh_button()
        self._clear_cards()
        c = self.theme_mgr.current
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c["sidebar_card"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        l = QVBoxLayout(card)
        lbl = QLabel("ℹ️ " + _("ai_review_short_text"))
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {c['text_muted']}; font-size: 11px;")
        l.addWidget(lbl)
        self.cards_layout.insertWidget(0, card)

    def _clear_cards(self):
        while self.cards_layout.count() > 1:
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update_metrics_and_outline(self, text_document):
        stats = DocumentStats.analyze(text_document)

        self.lbl_words.setText(f"📝 {stats['word_count']} { _('status_words')}")
        self.lbl_chars.setText(f"🔤 {stats['char_count']} { _('status_chars')}")
        self.lbl_read_time.setText(f"⏱️ ~{stats['reading_time_min']} { _('status_reading_time')}")
        read_lbl = _(stats.get("readability_key", "lix_medium"))
        self.lbl_lix.setText(f"📊 LIX: {stats['lix_score']} ({read_lbl})")

        # Update Outline
        self.list_outline.clear()
        for item in stats["outline"]:
            indent = "  " * (item["level"] - 1)
            icon = "📌" if item["level"] == 1 else "▪"
            list_item = QListWidgetItem(f"{indent}{icon} {item['text']}")
            list_item.setData(Qt.ItemDataRole.UserRole, item["position"])
            self.list_outline.addItem(list_item)

    def _on_outline_clicked(self, item):
        pos = item.data(Qt.ItemDataRole.UserRole)
        if pos is not None:
            self.outline_item_clicked.emit(pos)

    def _on_review_received(self, data):
        self.progress_bar.setVisible(False)
        self.btn_refresh.setEnabled(True)
        self.btn_refresh.setText("✓ " + _("ai_review_done"))
        QTimer.singleShot(2000, self._reset_refresh_button)

        self._clear_cards()

        tone = data.get("tone", "Professional")
        self.lbl_tone.setText(f"Tone: {tone}")

        suggestions = data.get("suggestions", [])
        if not suggestions:
            c = self.theme_mgr.current
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {c["sidebar_card"]};
                    border: 1px solid {c["canvas_border"]};
                    border-radius: 6px;
                    padding: 10px;
                }}
            """)
            l = QVBoxLayout(card)
            lbl_empty = QLabel("✓ " + _("ai_review_no_issues"))
            lbl_empty.setWordWrap(True)
            lbl_empty.setStyleSheet(f"color: {c['accent']}; font-size: 11px;")
            l.addWidget(lbl_empty)
            self.cards_layout.insertWidget(0, card)
            return

        c = self.theme_mgr.current
        for sug in suggestions:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {c["sidebar_card"]};
                    border: 1px solid {c["canvas_border"]};
                    border-radius: 6px;
                    padding: 6px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(6, 6, 6, 6)
            card_layout.setSpacing(4)

            # Type badge
            stype = sug.get("type", "style").upper()
            lbl_badge = QLabel(f"<b>[{stype}]</b>")
            lbl_badge.setStyleSheet(f"color: {c['accent']}; font-size: 10px;")
            card_layout.addWidget(lbl_badge)

            # Text
            orig = sug.get("original", "")
            repl = sug.get("replacement", "")
            expl = sug.get("explanation", "")

            lbl_txt = QLabel(f"<s>{orig}</s> → <b>{repl}</b>")
            lbl_txt.setWordWrap(True)
            card_layout.addWidget(lbl_txt)

            if expl:
                lbl_expl = QLabel(f"<i>{expl}</i>")
                lbl_expl.setStyleSheet(f"color: {c['status_text']}; font-size: 10px;")
                lbl_expl.setWordWrap(True)
                card_layout.addWidget(lbl_expl)

            btn_row = QHBoxLayout()
            btn_apply = QPushButton(_("ai_card_btn_apply"))
            btn_apply.setFixedHeight(20)
            btn_apply.clicked.connect(lambda ch, o=orig, r=repl: self.apply_suggestion_requested.emit(o, r))

            btn_dismiss = QPushButton(_("ai_card_btn_dismiss"))
            btn_dismiss.setFixedHeight(20)
            btn_dismiss.clicked.connect(lambda ch, w=card: w.deleteLater())

            btn_row.addWidget(btn_apply)
            btn_row.addWidget(btn_dismiss)
            btn_row.addStretch()
            card_layout.addLayout(btn_row)

            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _on_review_error(self, err_msg):
        self.progress_bar.setVisible(False)
        self._reset_refresh_button()
        self._clear_cards()

        c = self.theme_mgr.current
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c["sidebar_card"]};
                border: 1px solid #ef4444;
                border-radius: 6px;
                padding: 10px;
            }}
        """)
        l = QVBoxLayout(card)
        lbl_err_title = QLabel("⚠️ " + _("ai_review_btn_refresh"))
        lbl_err_title.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")
        lbl_err_msg = QLabel(str(err_msg))
        lbl_err_msg.setWordWrap(True)
        lbl_err_msg.setStyleSheet(f"color: {c['text_muted']}; font-size: 10px;")

        l.addWidget(lbl_err_title)
        l.addWidget(lbl_err_msg)
        self.cards_layout.insertWidget(0, card)

    def retranslate_ui(self):
        self.tabs.setTabText(0, _("sidebar_tab_review"))
        self.tabs.setTabText(1, _("sidebar_tab_outline"))
        self.tabs.setTabText(2, _("sidebar_tab_metrics"))
        self._reset_refresh_button()

    def apply_theme(self):
        c = self.theme_mgr.current
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {c["sidebar_bg"]};
                color: {c["text_color"]};
            }}
            QListWidget {{
                background-color: {c["sidebar_card"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                color: {c["text_color"]};
            }}
            QPushButton {{
                background-color: {c["sidebar_card"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {c["btn_hover"]};
                border-color: {c["accent"]};
            }}
            QPushButton:pressed {{
                background-color: {c["btn_active"]};
            }}
            QPushButton:disabled {{
                color: {c["text_muted"]};
                background-color: {c["btn_hover"]};
            }}
            QProgressBar {{
                border: none;
                background-color: {c["canvas_border"]};
                border-radius: 1px;
            }}
            QProgressBar::chunk {{
                background-color: {c["accent"]};
                border-radius: 1px;
            }}
        """)
