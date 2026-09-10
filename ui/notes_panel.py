"""
ui/notes_panel.py — valvpanelen: anteckningar, länkar och backlinks i sidofältet.

Panelen äger ingen data själv. MainWindow skapar ett Vault, skickar in det med
set_vault() och talar om vilket dokument som är öppet med set_current_document().
Allt som händer utanför panelen sker via signaler:

    open_file_requested(path)   öppna en fil i redigeraren
    insert_text_requested(txt)  sätt in text vid markören
    show_graph_requested()      öppna graftvyn
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QListWidget, QListWidgetItem, QComboBox, QFileDialog, QInputDialog,
    QMessageBox, QMenu, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QAction

from core.i18n import _, i18n
from core.vault import Vault, VAULT_DEFAULT_DIR


class NotesPanel(QWidget):
    open_file_requested = pyqtSignal(str)
    insert_text_requested = pyqtSignal(str)
    show_graph_requested = pyqtSignal()
    vault_changed = pyqtSignal(str)

    def __init__(self, vault: Vault, theme_mgr, parent=None):
        super().__init__(parent)
        self.vault = vault
        self.theme_mgr = theme_mgr
        self.current_title = ""
        self._rows = []          # [(visningstext, payload, typ)]

        self.init_ui()
        self.apply_theme()
        self.theme_mgr.theme_changed.connect(self.apply_theme)
        i18n.language_changed.connect(self.retranslate_ui)
        self.refresh()

    # ------------------------------------------------------------------ uppbyggnad

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Rubrik + verktygsknappar
        top = QHBoxLayout()
        self.lbl_title = QLabel(_("notes_title"))
        self.lbl_title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        top.addWidget(self.lbl_title)
        top.addStretch()

        self.btn_folder = QPushButton("📂")
        self.btn_folder.setFixedWidth(28)
        self.btn_folder.setToolTip(_("notes_choose_folder"))
        self.btn_folder.clicked.connect(self._choose_folder)
        top.addWidget(self.btn_folder)

        self.btn_rescan = QPushButton("⟳")
        self.btn_rescan.setFixedWidth(28)
        self.btn_rescan.setToolTip(_("notes_btn_rescan"))
        self.btn_rescan.clicked.connect(self._rescan)
        top.addWidget(self.btn_rescan)

        self.btn_graph = QPushButton("🕸")
        self.btn_graph.setFixedWidth(28)
        self.btn_graph.setToolTip(_("notes_btn_graph"))
        self.btn_graph.clicked.connect(self.show_graph_requested.emit)
        top.addWidget(self.btn_graph)
        layout.addLayout(top)

        # Valvets sökväg
        self.lbl_root = QLabel("")
        self.lbl_root.setWordWrap(False)
        self.lbl_root.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.lbl_root)

        # Sökfält
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText(_("notes_search_ph"))
        self.input_search.textChanged.connect(lambda _t: self.refresh())
        self.input_search.setClearButtonEnabled(True)
        layout.addWidget(self.input_search)

        # Filter
        self.combo_filter = QComboBox()
        self.combo_filter.addItem(_("notes_filter_all"), "all")
        self.combo_filter.addItem(_("notes_filter_backlinks"), "backlinks")
        self.combo_filter.addItem(_("notes_filter_unresolved"), "unresolved")
        self.combo_filter.addItem(_("notes_filter_tags"), "tags")
        self.combo_filter.currentIndexChanged.connect(lambda _i: self.refresh())
        layout.addWidget(self.combo_filter)

        # Lista
        self.list_notes = QListWidget()
        self.list_notes.setWordWrap(True)
        self.list_notes.itemActivated.connect(self._on_item_activated)
        self.list_notes.itemClicked.connect(self._on_item_activated)
        self.list_notes.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_notes.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.list_notes, 1)

        # Sidfot
        bottom = QHBoxLayout()
        self.btn_new = QPushButton("➕ " + _("notes_btn_new"))
        self.btn_new.clicked.connect(self._create_note)
        bottom.addWidget(self.btn_new)
        bottom.addStretch()
        layout.addLayout(bottom)

        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.lbl_stats)

    # ------------------------------------------------------------------ data

    def set_vault(self, vault: Vault):
        self.vault = vault
        self.refresh()

    def set_current_document(self, title: str):
        """Berättar vilket dokument som är öppet, så backlinks kan visas."""
        self.current_title = title or ""
        if self.combo_filter.currentData() == "backlinks":
            self.refresh()
        else:
            self._update_stats()

    def refresh(self):
        """Bygger om listan utifrån filter och söktext."""
        if self.vault is None:
            return
        self.vault.scan_if_stale(5.0)
        self.lbl_root.setText(self._elide(self.vault.root, 44))

        mode = self.combo_filter.currentData() or "all"
        query = self.input_search.text().strip()

        self.list_notes.clear()
        self._rows = []

        if not self.vault.exists():
            self._add_placeholder(_("notes_no_vault"))
            self._update_stats()
            return

        if mode == "unresolved":
            targets = self.vault.unresolved_targets()
            if not targets:
                self._add_placeholder(_("notes_unresolved_none"))
            for t in targets:
                if query and query.lower() not in t.lower():
                    continue
                self._add_row(f"➕ {t}", _("notes_create_from_link"), "unresolved", t)
            self._update_stats()
            return

        if mode == "tags":
            tags = self.vault.all_tags()
            if not tags:
                self._add_placeholder(_("notes_no_tags"))
            for tag, count in tags:
                if query and query.lower() not in tag.lower():
                    continue
                self._add_row(f"# {tag}", _("notes_tag_count", count=count), "tag", tag)
            self._update_stats()
            return

        if mode == "backlinks":
            note = self.vault.get(self.current_title) if self.current_title else None
            if note is None:
                self._add_placeholder(_("notes_not_in_vault"))
                self._update_stats()
                return
            links = self.vault.backlinks(note)
            if not links:
                self._add_placeholder(_("notes_backlinks_empty"))
            for other, context in links:
                if query and query.lower() not in other.title.lower() and query.lower() not in context.lower():
                    continue
                self._add_row(f"↩ {other.title}", context or other.preview(90), "note", other.path)
            self._update_stats()
            return

        # Standard: sökning eller hela listan
        results = self.vault.search(query) if query else [(n, n.preview(), 0) for n in self.vault.notes]
        if not results:
            self._add_placeholder(_("notes_no_hits"))
        for note, snippet, _score in results:
            link_count = len(set(note.links))
            badge = f"  🔗{link_count}" if link_count else ""
            if note.path == self._current_path():
                badge = "  ●" + badge
            self._add_row(f"{note.title}{badge}", snippet, "note", note.path)

        self._update_stats()

    def _current_path(self):
        return getattr(self, "_current_file", None)

    def set_current_file(self, path):
        """Sökvägen till den fil som är öppen i redigeraren (för ●-markering)."""
        self._current_file = path or None
        self.refresh()

    def _add_row(self, title: str, subtitle: str, kind: str, payload):
        text = f"{title}\n{subtitle}" if subtitle else title
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, (kind, payload))
        item.setToolTip(payload if isinstance(payload, str) else "")
        self.list_notes.addItem(item)
        self._rows.append((title, payload, kind))

    def _add_placeholder(self, text: str):
        item = QListWidgetItem(f"— {text}")
        item.setData(Qt.ItemDataRole.UserRole, ("placeholder", None))
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.list_notes.addItem(item)

    def _update_stats(self):
        s = self.vault.stats() if self.vault else {}
        parts = [
            _("notes_stat_notes", n=s.get("notes", 0)),
            _("notes_stat_links", n=s.get("links", 0)),
        ]
        if s.get("unresolved"):
            parts.append(_("notes_stat_unresolved", n=s["unresolved"]))
        self.lbl_stats.setText(" · ".join(parts))

    @staticmethod
    def _elide(text: str, limit: int) -> str:
        return text if len(text) <= limit else "…" + text[-(limit - 1):]

    # ------------------------------------------------------------------ händelser

    def _on_item_activated(self, item):
        kind, payload = item.data(Qt.ItemDataRole.UserRole) or (None, None)
        if kind == "note":
            self.open_file_requested.emit(payload)
        elif kind == "unresolved":
            self._create_from_link(payload)
        elif kind == "tag":
            self.input_search.setText(payload)

    def _on_context_menu(self, pos):
        item = self.list_notes.itemAt(pos)
        if item is None:
            return
        data = item.data(Qt.ItemDataRole.UserRole) or (None, None)
        kind, payload = data[0], data[1]
        if kind == "placeholder" or not isinstance(payload, str):
            return

        menu = QMenu(self)

        def add(text, slot):
            act = QAction(text, self)
            act.triggered.connect(slot)
            menu.addAction(act)
            return act

        if kind == "note":
            note = self.vault.get_by_path(payload)
            title = note.title if note else os.path.splitext(os.path.basename(payload))[0]
            add("📄 " + _("notes_context_open"), lambda: self.open_file_requested.emit(payload))
            add("🔗 " + _("notes_context_insert_link"), lambda: self.insert_text_requested.emit(f"[[{title}]]"))
            add("📋 " + _("notes_context_copy_link"), lambda: QApplication.clipboard().setText(f"[[{title}]]"))
            menu.addSeparator()
            add("📂 " + _("notes_context_reveal"), lambda: self._reveal(payload))
        elif kind == "unresolved":
            add("➕ " + _("notes_create_from_link"), lambda: self._create_from_link(payload))
            add("🔗 " + _("notes_context_insert_link"), lambda: self.insert_text_requested.emit(f"[[{payload}]]"))
        elif kind == "tag":
            add("🔍 " + _("notes_context_search_tag"), lambda: self.input_search.setText(payload))
        menu.exec(self.list_notes.mapToGlobal(pos))

    def _reveal(self, path):
        folder = os.path.dirname(path)
        import subprocess
        try:
            subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            print(f"[Notes] Kunde inte öppna {folder}: {e}")

    def _rescan(self):
        n = self.vault.scan()
        self.refresh()
        QMessageBox.information(self, _("notes_title"),
                                _("notes_rescan_done", n=n, root=self.vault.root))

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, _("notes_choose_folder"),
                                                  self.vault.root or os.path.expanduser("~"))
        if not folder:
            return
        self.vault = Vault(folder)
        self.vault.scan()
        self.vault_changed.emit(folder)
        self.refresh()

    def _create_note(self):
        title, ok = QInputDialog.getText(self, _("notes_btn_new"), _("notes_new_prompt"))
        if not ok or not title.strip():
            return
        note = self.vault.create_note(title.strip())
        if note is None:
            QMessageBox.warning(self, _("notes_title"), _("notes_create_failed"))
            return
        self.refresh()
        self.open_file_requested.emit(note.path)

    def _create_from_link(self, target: str):
        note = self.vault.create_note(target, content=f"# {target}\n\n")
        if note is None:
            QMessageBox.warning(self, _("notes_title"), _("notes_create_failed"))
            return
        self.refresh()
        self.open_file_requested.emit(note.path)

    # ------------------------------------------------------------------ utseende

    def retranslate_ui(self):
        self.lbl_title.setText(_("notes_title"))
        self.input_search.setPlaceholderText(_("notes_search_ph"))
        self.btn_new.setText("➕ " + _("notes_btn_new"))
        self.btn_folder.setToolTip(_("notes_choose_folder"))
        self.btn_rescan.setToolTip(_("notes_btn_rescan"))
        self.btn_graph.setToolTip(_("notes_btn_graph"))

        current = self.combo_filter.currentData()
        self.combo_filter.blockSignals(True)
        self.combo_filter.clear()
        self.combo_filter.addItem(_("notes_filter_all"), "all")
        self.combo_filter.addItem(_("notes_filter_backlinks"), "backlinks")
        self.combo_filter.addItem(_("notes_filter_unresolved"), "unresolved")
        self.combo_filter.addItem(_("notes_filter_tags"), "tags")
        idx = max(0, [self.combo_filter.itemData(i) for i in range(4)].index(current)
                  if current in [self.combo_filter.itemData(i) for i in range(4)] else 0)
        self.combo_filter.setCurrentIndex(idx)
        self.combo_filter.blockSignals(False)
        self.refresh()

    def apply_theme(self):
        c = self.theme_mgr.current
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {c["sidebar_bg"]};
                color: {c["text_color"]};
            }}
            QLineEdit, QComboBox {{
                background-color: {c["sidebar_card"]};
                color: {c["text_color"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 11px;
            }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
            QListWidget {{
                background-color: {c["sidebar_card"]};
                border: 1px solid {c["canvas_border"]};
                border-radius: 4px;
                color: {c["text_color"]};
                font-size: 11px;
            }}
            QListWidget::item {{ padding: 4px; }}
            QListWidget::item:selected {{
                background-color: {c["accent"]};
                color: #ffffff;
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
            QPushButton:pressed {{ background-color: {c["btn_active"]}; }}
            QLabel {{ background: transparent; }}
        """)
        self.lbl_root.setStyleSheet(f"font-size: 10px; color: {c['text_muted']};")
        self.lbl_stats.setStyleSheet(f"font-size: 10px; color: {c['text_muted']};")
