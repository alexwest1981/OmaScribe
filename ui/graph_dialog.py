"""
ui/graph_dialog.py — grafvy över hur anteckningarna länkar till varandra.

Noderna läggs ut på en cirkel (stabil och läsbar för valv upp till några
hundra anteckningar) med radien efter hur många kopplingar de har. Länkar
till anteckningar som inte finns ännu ritas som streckade noder, så att det
går att se var valvet har hål.
"""

import math
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics, QBrush

from core.i18n import _, i18n


class GraphCanvas(QWidget):
    """Ritar noder och kanter. Klick på en nod öppnar anteckningen."""

    node_activated = pyqtSignal(str)      # filsökväg
    unresolved_activated = pyqtSignal(str)  # länkmål utan anteckning

    def __init__(self, vault, theme_mgr, parent=None):
        super().__init__(parent)
        self.vault = vault
        self.theme_mgr = theme_mgr
        self.nodes = []        # {title, path, pos, radius, resolved}
        self.edges = []        # (index, index)
        self.hover = -1
        self.setMouseTracking(True)
        self.setMinimumSize(560, 420)
        self.relayout()

    def rebuild(self):
        self.vault.scan()
        self.relayout()
        self.update()

    def relayout(self):
        """Beräknar nodpositioner på en cirkel, med hänsyn till kopplingar."""
        self.nodes = []
        self.edges = []

        notes = self.vault.notes
        titles, raw_edges = self.vault.graph()

        # Grad per titel (in + ut), för att styra nodstorlek
        degree = {t: 0 for t in titles}
        for src, dst in raw_edges:
            degree[src] = degree.get(src, 0) + 1
            degree[dst] = degree.get(dst, 0) + 1

        unresolved = self.vault.unresolved_targets()

        cx, cy = self.width() / 2.0, self.height() / 2.0
        radius = max(90.0, min(self.width(), self.height()) / 2.0 - 74.0)

        total = len(notes)
        index_of = {}
        for i, note in enumerate(notes):
            angle = (2 * math.pi * i / max(1, total)) - math.pi / 2
            deg = degree.get(note.title, 0)
            r = 6.0 + min(deg, 8) * 1.9
            self.nodes.append({
                "title": note.title,
                "path": note.path,
                "pos": QPointF(cx + radius * math.cos(angle), cy + radius * math.sin(angle)),
                "radius": r,
                "resolved": True,
                "degree": deg,
            })
            index_of[note.title] = i

        for src, dst in raw_edges:
            if src in index_of and dst in index_of:
                self.edges.append((index_of[src], index_of[dst]))

        # Olösta länkmål: yttre ring
        outer = radius + 46.0
        for j, target in enumerate(unresolved[:24]):
            angle = (2 * math.pi * j / max(1, min(len(unresolved), 24))) + math.pi / 8
            self.nodes.append({
                "title": target,
                "path": "",
                "pos": QPointF(cx + outer * math.cos(angle), cy + outer * math.sin(angle)),
                "radius": 4.5,
                "resolved": False,
                "degree": 0,
            })

    # ------------------------------------------------------------------ ritning

    def paintEvent(self, _event):
        c = self.theme_mgr.current
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.fillRect(self.rect(), QColor(c["canvas_bg"]))

        edge_color = QColor(c["text_muted"])
        edge_color.setAlpha(70)

        # Kanter
        p.setPen(QPen(edge_color, 1))
        for a, b in self.edges:
            if a < len(self.nodes) and b < len(self.nodes):
                p.drawLine(self.nodes[a]["pos"], self.nodes[b]["pos"])

        # Noder
        accent = QColor(c["accent"])
        muted = QColor(c["text_muted"])
        text_col = QColor(c["text_color"])

        font = QFont("Segoe UI", 8)
        p.setFont(font)
        metrics = QFontMetrics(font)

        for i, node in enumerate(self.nodes):
            pos = node["pos"]
            r = node["radius"]
            is_hover = (i == self.hover)

            if not node["resolved"]:
                pen = QPen(muted, 1.2, Qt.PenStyle.DashLine)
                p.setPen(pen)
                p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            else:
                fill = QColor(accent)
                fill.setAlpha(210 if is_hover else 150)
                p.setPen(QPen(accent if is_hover else QColor(c["canvas_border"]), 1.6 if is_hover else 1.0))
                p.setBrush(QBrush(fill))

            p.drawEllipse(pos, r + (2 if is_hover else 0), r + (2 if is_hover else 0))

            # Etikett
            label = metrics.elidedText(node["title"], Qt.TextElideMode.ElideRight, 110)
            p.setPen(text_col if node["resolved"] else muted)
            p.drawText(
                QRectF(pos.x() - 60, pos.y() + r + 3, 120, 14),
                int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop),
                label
            )

        p.end()

    # ------------------------------------------------------------------ interaktion

    def _node_at(self, point) -> int:
        for i in range(len(self.nodes) - 1, -1, -1):
            pos = self.nodes[i]["pos"]
            r = self.nodes[i]["radius"] + 4
            dx, dy = point.x() - pos.x(), point.y() - pos.y()
            if dx * dx + dy * dy <= r * r:
                return i
        return -1

    def mouseMoveEvent(self, event):
        idx = self._node_at(event.position())
        if idx != self.hover:
            self.hover = idx
            if idx >= 0:
                n = self.nodes[idx]
                extra = _("graph_node_links", n=n["degree"]) if n["resolved"] else _("graph_node_missing")
                self.setToolTip(f"{n['title']}\n{extra}")
            else:
                self.setToolTip("")
            self.update()

    def mousePressEvent(self, event):
        idx = self._node_at(event.position())
        if idx < 0:
            return
        node = self.nodes[idx]
        if node["resolved"] and node["path"]:
            self.node_activated.emit(node["path"])
        elif not node["resolved"]:
            self.unresolved_activated.emit(node["title"])

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.relayout()


class GraphDialog(QDialog):
    """Visar valvets länkgraf."""

    open_file_requested = pyqtSignal(str)
    create_note_requested = pyqtSignal(str)

    def __init__(self, vault, theme_mgr, parent=None):
        super().__init__(parent)
        self.vault = vault
        self.theme_mgr = theme_mgr

        self.setWindowTitle(_("graph_title"))
        self.setMinimumSize(760, 620)
        self.init_ui()
        self.apply_theme()
        self.theme_mgr.theme_changed.connect(self.apply_theme)
        i18n.language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        head = QHBoxLayout()
        self.lbl_heading = QLabel("🕸 " + _("graph_title"))
        self.lbl_heading.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        head.addWidget(self.lbl_heading)
        head.addStretch()
        self.btn_refresh = QPushButton("⟳ " + _("graph_btn_refresh"))
        self.btn_refresh.clicked.connect(self._refresh)
        head.addWidget(self.btn_refresh)
        layout.addLayout(head)

        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.lbl_stats)

        self.canvas = GraphCanvas(self.vault, self.theme_mgr, self)
        self.canvas.node_activated.connect(self._on_node)
        self.canvas.unresolved_activated.connect(self._on_unresolved)
        layout.addWidget(self.canvas, 1)

        self.lbl_hint = QLabel(_("graph_hint"))
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.lbl_hint)

        foot = QHBoxLayout()
        foot.addStretch()
        self.btn_close = QPushButton(_("graph_btn_close"))
        self.btn_close.clicked.connect(self.reject)
        foot.addWidget(self.btn_close)
        layout.addLayout(foot)

        self._refresh()

    def _refresh(self):
        self.canvas.rebuild()
        s = self.vault.stats()
        parts = [
            _("graph_stat_nodes", n=s.get("notes", 0)),
            _("graph_stat_links", n=s.get("links", 0)),
        ]
        if s.get("unresolved"):
            parts.append(_("graph_stat_missing", n=s["unresolved"]))
        self.lbl_stats.setText(" · ".join(parts))

    def _on_node(self, path):
        self.open_file_requested.emit(path)

    def _on_unresolved(self, target):
        self.create_note_requested.emit(target)

    def retranslate_ui(self):
        self.setWindowTitle(_("graph_title"))
        self.lbl_heading.setText("🕸 " + _("graph_title"))
        self.btn_refresh.setText("⟳ " + _("graph_btn_refresh"))
        self.btn_close.setText(_("graph_btn_close"))
        self.lbl_hint.setText(_("graph_hint"))
        self._refresh()

    def apply_theme(self):
        c = self.theme_mgr.current
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c["dialog_bg"]}; color: {c["text_color"]}; }}
            QLabel {{ color: {c["text_color"]}; background: transparent; }}
            QPushButton {{
                background-color: {c["btn_bg"]};
                color: {c["btn_text"]};
                border: 1px solid {c["btn_border"]};
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {c["btn_hover"]}; border-color: {c["accent"]}; }}
        """)
