import html

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QFrame, QListWidget, QListWidgetItem,
    QProgressBar, QApplication, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from core.i18n import _, i18n
from core.document_stats import DocumentStats
from ui.chrome import chip, kbd, set_tracking

class SidebarInspector(QWidget):
    apply_suggestion_requested = pyqtSignal(str, str) # (original, replacement)
    outline_item_clicked = pyqtSignal(int) # cursor position
    close_requested = pyqtSignal()         # stängknappen i huvudet
    rewrite_requested = pyqtSignal()       # "Förbättra markeringen"

    def __init__(self, ai_client, theme_mgr, parent=None):
        super().__init__(parent)
        self.ai = ai_client
        self.theme_mgr = theme_mgr
        self.setObjectName("InspectorRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(312)            # referensen: 312

        self.init_ui()
        self.retranslate_ui()
        self.apply_theme()
        self.theme_mgr.theme_changed.connect(self.apply_theme)
        i18n.language_changed.connect(self.retranslate_ui)

        self.ai.review_completed.connect(self._on_review_received)
        if hasattr(self.ai, "review_error"):
            self.ai.review_error.connect(self._on_review_error)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Panelens huvud: eyebrow, rubrik och stängknapp (referensens
        # inspector-header). Rubriken säger vad panelen gör, inte vad den lovar.
        head = QWidget()
        head.setObjectName("InspectorHead")
        head.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        head_row = QHBoxLayout(head)
        head_row.setContentsMargins(22, 26, 18, 14)   # referensen: 28px 22px 21px
        head_row.setSpacing(8)
        head_text = QVBoxLayout()
        head_text.setContentsMargins(0, 0, 0, 0)
        head_text.setSpacing(5)
        self.lbl_eyebrow = QLabel()
        self.lbl_eyebrow.setObjectName("InspectorEyebrow")
        set_tracking(self.lbl_eyebrow, 1.5)           # referensen: .15em
        self.lbl_title = QLabel()
        self.lbl_title.setObjectName("InspectorTitle")
        set_tracking(self.lbl_title, -0.8)            # referensen: -.04em
        head_text.addWidget(self.lbl_eyebrow)
        head_text.addWidget(self.lbl_title)
        head_row.addLayout(head_text)
        head_row.addStretch(1)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("InspectorClose")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.close_requested)
        head_row.addWidget(self.btn_close, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(head)

        self._extra_tabs = []
        self.tabs = QTabWidget()
        self.tabs.setObjectName("InspectorTabs")
        # Panelen är 312px som referensen, men appen har fler flikar än
        # referensens tre — de får full text och raden får skrolla i stället
        # för att klippas ("Anteckninga...").
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabBar().setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)   # annars kläms flikarna i stället för att skrolla
        self.tabs.tabBar().setElideMode(Qt.TextElideMode.ElideNone)
        self.tab_review = QWidget()
        self.tab_outline = QWidget()
        self.tab_metrics = QWidget()

        self._init_review_tab()
        self._init_outline_tab()
        self._init_metrics_tab()

        self.tabs.addTab(self.tab_review, _("sidebar_tab_review"))
        self.tabs.addTab(self.tab_outline, _("sidebar_tab_outline"))
        self.tabs.addTab(self.tab_metrics, _("sidebar_tab_metrics"))

        layout.addWidget(self.tabs, 1)

    def _init_review_tab(self):
        layout = QVBoxLayout(self.tab_review)
        layout.setContentsMargins(22, 16, 22, 18)     # referensen: 20px 22px
        layout.setSpacing(12)

        # Raden ovanför förslagen: vad texten låter som och hur många förslag
        # som väntar. Referensen har samma rad — siffrorna är appens egna.
        self.row_tone = QHBoxLayout()
        self.row_tone.setContentsMargins(0, 0, 0, 0)
        self.row_tone.setSpacing(6)
        self.lbl_tone = QLabel()
        self.lbl_tone.setObjectName("CardText")
        self.chip_tone = chip("")
        self.chip_count = chip("", ok=True)
        self.chip_tone.setVisible(False)
        self.chip_count.setVisible(False)
        self.row_tone.addWidget(self.lbl_tone)
        self.row_tone.addWidget(self.chip_tone)
        self.row_tone.addWidget(self.chip_count)
        self.row_tone.addStretch(1)

        self.btn_refresh = QPushButton("⟳")
        self.btn_refresh.setObjectName("RefreshButton")
        self.btn_refresh.setFixedSize(26, 26)
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.row_tone.addWidget(self.btn_refresh)
        layout.addLayout(self.row_tone)

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
        self.cards_layout.setSpacing(9)               # referensen: gap 9

        self.cards_layout.addStretch()
        self.scroll.setWidget(self.cards_container)
        layout.addWidget(self.scroll, 1)

        # "Förbättra markeringen" — referensens mörka knapp längst ned. Gör
        # samma sak som AI-knappen i verktygsraden: förbättrar markeringen.
        self.btn_rewrite = QPushButton()
        self.btn_rewrite.setObjectName("RewriteButton")
        self.btn_rewrite.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rewrite.setMinimumHeight(38)         # referensen: padding 11px
        self.btn_rewrite.clicked.connect(self.rewrite_requested)
        layout.addWidget(self.btn_rewrite)

    def _init_outline_tab(self):
        layout = QVBoxLayout(self.tab_outline)
        layout.setContentsMargins(12, 12, 12, 12)

        self.list_outline = QListWidget()
        self.list_outline.setObjectName("OutlineList")
        self.list_outline.itemClicked.connect(self._on_outline_clicked)
        layout.addWidget(self.list_outline)

    def _init_metrics_tab(self):
        layout = QVBoxLayout(self.tab_metrics)
        layout.setContentsMargins(22, 16, 22, 18)     # referensen: 20px 22px
        layout.setSpacing(10)

        # Referensens 2x2-rutnät: stort tal, liten etikett under.
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)                            # referensen: gap 10

        self._metric_labels = {}
        for index, (key, attr) in enumerate(
                (("words", "lbl_words"), ("chars", "lbl_chars"),
                 ("read_time", "lbl_read_time"), ("lix", "lbl_lix"))):
            card = QFrame()
            card.setObjectName("MetricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 14, 12, 14)   # referensen: 16px 12px
            card_layout.setSpacing(4)

            value = QLabel("0")
            value.setObjectName("MetricValue")
            set_tracking(value, -1.0)                  # referensen: -.05em
            caption = QLabel()
            caption.setObjectName("MetricLabel")

            card_layout.addWidget(value)
            card_layout.addWidget(caption)
            setattr(self, attr, value)                 # samma namn som förut
            self._metric_labels[key] = caption
            grid.addWidget(card, index // 2, index % 2)

        layout.addLayout(grid)
        layout.addStretch(1)

        self._words = 0
        self._chars = 0

    @property
    def words(self) -> int:
        """Antalet ord panelen visar — skrivloggen bokför samma siffra."""
        return int(getattr(self, "_words", 0))

    def status_text(self) -> str:
        """Statusbarens sammanfattning — samma siffror som panelen visar."""
        return f"{self._words} {_('status_words')} | {self._chars} {_('status_chars')}"

    def set_loading(self, is_loading=True):
        if is_loading:
            self.btn_refresh.setEnabled(False)
            self.btn_refresh.setText("⏳")
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
        self.btn_refresh.setText("⟳")
        self.btn_refresh.setToolTip(_("ai_review_btn_refresh"))

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

    def _show_idle_hint(self):
        """Vad panelen väntar på. Referensen har färdiga kort; appen visar
        i stället vad som faktiskt ska göras för att få dem."""
        self._clear_cards()
        card = QFrame()
        card.setObjectName("SuggestionCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(11, 11, 11, 11)
        lbl = QLabel(_("inspector_idle"))
        lbl.setObjectName("CardText")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        self.cards_layout.insertWidget(0, card)

    def _clear_cards(self):
        while self.cards_layout.count() > 1:
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update_metrics_and_outline(self, text_document):
        stats = DocumentStats.analyze(text_document)

        self._words = stats["word_count"]
        self._chars = stats["char_count"]
        # Siffrorna är desamma som förut — de står bara i referensens rutnät
        # i stället för i en lista med emoji framför.
        self.lbl_words.setText(f"{self._words:,}".replace(",", " "))
        self.lbl_chars.setText(f"{self._chars:,}".replace(",", " "))
        self.lbl_read_time.setText(_("metric_minutes", n=stats["reading_time_min"]))
        self.lbl_lix.setText(str(stats["lix_score"]))
        self._metric_labels["lix"].setText(
            f"LIX · {_(stats.get('readability_key', 'lix_medium'))}")
        self._metric_labels["words"].setText(_("status_words"))
        self._metric_labels["chars"].setText(_("status_chars"))
        self._metric_labels["read_time"].setText(_("status_reading_time"))

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
        self.btn_refresh.setText("✓")
        QTimer.singleShot(2000, self._reset_refresh_button)

        self._clear_cards()

        tone = data.get("tone", "")
        self.lbl_tone.setText(_("inspector_tone"))
        self.chip_tone.setText(tone.capitalize() if tone else "")
        self.chip_tone.setVisible(bool(tone))

        suggestions = data.get("suggestions", [])
        antal = len([s for s in suggestions if s.get("original")])
        self.chip_count.setText(_("inspector_to_review", count=antal))
        self.chip_count.setVisible(antal > 0)
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

        for sug in suggestions:
            card = QFrame()
            card.setObjectName("SuggestionCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(11, 11, 11, 11)      # referensen: padding 11
            card_layout.setSpacing(9)                            # referensen: margin 9

            orig = sug.get("original", "")
            repl = sug.get("replacement", "")
            expl = sug.get("explanation", "")

            # Översta raden: slag, och de två åtgärderna. Färgen bär inget
            # besked — ordet till vänster säger vilket slags förslag det är.
            top = QHBoxLayout()
            top.setSpacing(7)
            stype = sug.get("type", "style")
            icon = QLabel("✦")
            icon.setObjectName("SuggestionIcon")
            icon.setFixedSize(21, 21)                            # referensen: 21x21
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            top.addWidget(icon)
            kind = QLabel(str(stype).capitalize())
            kind.setObjectName("SuggestionKind")
            top.addWidget(kind)
            top.addStretch(1)

            btn_apply = QPushButton("+")
            btn_apply.setObjectName("CardAction")
            btn_apply.setFixedSize(21, 21)
            btn_apply.setToolTip(_("ai_card_btn_apply"))
            btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_apply.clicked.connect(
                lambda ch, o=orig, r=repl: self.apply_suggestion_requested.emit(o, r))
            top.addWidget(btn_apply)

            btn_dismiss = QPushButton("✕")
            btn_dismiss.setObjectName("CardAction")
            btn_dismiss.setFixedSize(21, 21)
            btn_dismiss.setToolTip(_("ai_card_btn_dismiss"))
            btn_dismiss.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_dismiss.clicked.connect(lambda ch, w=card: w.deleteLater())
            top.addWidget(btn_dismiss)
            card_layout.addLayout(top)

            # Texten från AI-tjänsten är data, inte markup — den escapas.
            body = QLabel(f"<s>{html.escape(str(orig))}</s> → <b>{html.escape(str(repl))}</b>")
            body.setObjectName("SuggestionBody")
            body.setWordWrap(True)
            card_layout.addWidget(body)

            if expl:
                lbl_expl = QLabel(html.escape(str(expl)))
                lbl_expl.setObjectName("CardText")
                lbl_expl.setWordWrap(True)
                card_layout.addWidget(lbl_expl)

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

    def add_tab(self, widget, title_key: str):
        """Lägger till en flik utifrån och kommer ihåg nyckeln för översättning."""
        self._extra_tabs.append((widget, title_key))
        self.tabs.addTab(widget, _(title_key))
        return widget

    def retranslate_ui(self):
        self.tabs.setTabText(0, _("sidebar_tab_review"))
        self.tabs.setTabText(1, _("sidebar_tab_outline"))
        self.tabs.setTabText(2, _("sidebar_tab_metrics"))
        for widget, key in self._extra_tabs:
            idx = self.tabs.indexOf(widget)
            if idx >= 0:
                self.tabs.setTabText(idx, _(key))
        self.lbl_eyebrow.setText(_("inspector_eyebrow"))
        self.lbl_title.setText(_("inspector_title"))
        self.btn_close.setToolTip(_("inspector_close"))
        self.lbl_tone.setText(_("inspector_tone"))
        self.btn_rewrite.setText(_("inspector_rewrite"))
        for key, i18n_key in (("words", "status_words"), ("chars", "status_chars"),
                              ("read_time", "status_reading_time")):
            self._metric_labels[key].setText(_(i18n_key))
        self._metric_labels["lix"].setText("LIX")
        self._reset_refresh_button()
        if not self.cards_layout.count() > 1:
            self._show_idle_hint()

    def apply_theme(self):
        c = self.theme_mgr.tokens()
        self.setStyleSheet(f"""
            #InspectorRoot {{
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

            /* Referensens anatomi inuti panelen (specen, avsnitt 4). */
            #OutlineList {{
                background-color: transparent;
                border: 0;
            }}
            #OutlineList::item {{
                padding: 13px 6px;
                border-bottom: 1px solid {c["card_border"]};
                color: {c["text_muted"]};
            }}
            #OutlineList::item:selected {{
                background-color: {c["rail_active_bg"]};
                color: {c["accent"]};
                border-radius: 8px;
            }}
            #RefreshButton {{
                background: transparent;
                border: 0;
                border-radius: 7px;
                color: {c["text_muted"]};
                font-size: 13px;
                padding: 0;
            }}
            #RefreshButton:hover {{
                background-color: {c["btn_hover"]};
                color: {c["text_color"]};
            }}
            #CardAction {{
                background-color: {c["btn_hover"]};
                border: 0;
                border-radius: 5px;
                color: {c["text_muted"]};
                font-size: 11px;
                padding: 0;
            }}
            #CardAction:hover {{
                color: {c["text_color"]};
            }}
            #RewriteButton {{
                background-color: {c["text_color"]};
                color: {c["canvas_bg"]};
                border: 0;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 9px 12px;
            }}
            #RewriteButton:hover {{
                background-color: {c["accent"]};
                color: {c["accent_text"]};
                border: 0;
            }}
            #RewriteButton:disabled {{
                background-color: {c["btn_hover"]};
                color: {c["text_muted"]};
            }}
        """)
