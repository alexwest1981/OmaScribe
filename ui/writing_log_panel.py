"""
ui/writing_log_panel.py — författarlagret: dagens skrivande.

Fas 2.1–2.5 i planen: mål för dagen och projektet, deadline och dagskvot,
historik med svit och snitt, sessionsrader i skrivloggen (`core.writing_log`)
samt skrivsprintar. Panelen äger loggen och får antalet ord efter varje
ändring: `track()` räknar skillnaden mot förra mätningen och bokför den. Ett
ändrat ord är inte ett skrivet ord — det är skillnaden mellan två mätningar.

Siffrorna i panelen räknas om sällan (vid byte, var 20:e sekund, när fliken
öppnas); mellan dess följer etiketterna det som ligger i minnet. Att summera
30 dagar i SQLite per tangenttryckning vore slöseri.

Loggen ligger i projektet när ett projekt är öppet (då hör dagarna till boken),
annars i användarens data-mapp så att även ett löst dokument loggas.
"""

import os
from pathlib import Path

from PyQt6.QtCore import QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel, QProgressBar, QPushButton,
    QVBoxLayout, QWidget,
)

from core.i18n import _, i18n
from core.writing_log import WritingLog

LOG_DB = "writing_log.sqlite"
DATA_DIR = Path.home() / ".local" / "share" / "omascribe"
SPRINT_MINUTES = (15, 25, 45, 60)
FLUSH_MS = 20_000


def default_log_path() -> Path:
    """Loggen för ett löst dokument (ingen projektmapp).

    `OMASCRIBE_DATA_DIR` pekar ut en annan mapp — grinden och rökprovet använder
    det så att deras skrivande inte hamnar i den riktiga loggen.
    """
    mapp = Path(os.environ.get("OMASCRIBE_DATA_DIR") or DATA_DIR)
    mapp.mkdir(parents=True, exist_ok=True)
    return mapp / LOG_DB


def log_path_for(project) -> Path:
    """Projektets egen logg, så att bokens dagar hör till boken."""
    root = Path(getattr(project, "root", DATA_DIR))
    root.mkdir(parents=True, exist_ok=True)
    return root / LOG_DB


class DayChart(QWidget):
    """En stapel per dag: netto ord. Dagens siffra är den man jämför med."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogChart")
        self.days = []              # [(dag, netto)]
        self.colors = {"bar": "#3366ff", "empty": "#e7e9ed", "text": "#87909b"}

    def set_days(self, days) -> None:
        self.days = list(days)
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(280, 96)

    def minimumSizeHint(self) -> QSize:
        return QSize(180, 78)

    def paintEvent(self, e) -> None:
        if not self.days:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setFont(QFont("sans-serif", 7))

        vänster, topp = 4.0, 4.0
        bredd = max(40.0, self.width() - 2 * vänster)
        höjd = max(20.0, self.height() - 20.0)
        bas = topp + höjd
        stapel = bredd / len(self.days)
        högsta = max((abs(netto) for _, netto in self.days), default=0) or 1

        for i, (dag, netto) in enumerate(self.days):
            x = vänster + i * stapel
            h = (abs(netto) / högsta) * (höjd - 4.0)
            painter.fillRect(QRectF(x + 1.0, bas - h, max(2.0, stapel - 3.0), h),
                             QColor(self.colors["bar"] if netto else self.colors["empty"]))
            if i in (0, len(self.days) - 1):
                painter.setPen(QColor(self.colors["text"]))
                painter.drawText(QRectF(x - 8.0, bas + 2.0, stapel + 16.0, 14.0),
                                 Qt.AlignmentFlag.AlignCenter, f"{dag[8:10]}/{dag[5:7]}")

        painter.setPen(QPen(QColor(self.colors["empty"]), 1.0))
        painter.drawLine(int(vänster), int(bas), int(vänster + bredd), int(bas))


class WritingLogPanel(QWidget):
    """Skrivloggen i sidopanelen, plus etiketten till statusfältet."""

    status_message = pyqtSignal(str)
    sprint_finished = pyqtSignal(int, int)      # (minuter, ord under sprinten)

    def __init__(self, config, theme_mgr, parent=None):
        super().__init__(parent)
        self.setObjectName("WritingLogPanel")
        self.config = config
        self.theme_mgr = theme_mgr

        self.project = None
        self.log = WritingLog(str(default_log_path()))

        self._progress = {"words": 0, "target": 0, "percent": 0, "daily_quota": 0}
        self._today = 0                  # dagens netto enligt senaste omläsning
        self._streak = (0, 0)
        self._average = 0.0

        self._doc_key = None
        self._last_words = 0
        self._added = 0
        self._removed = 0
        self._session_open = False
        self._session_seconds = 0
        self._sprint_left = 0
        self._sprint_words = 0

        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(FLUSH_MS)
        self._flush_timer.timeout.connect(self.flush)
        self._flush_timer.start()

        self._tick = QTimer(self)
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self._on_tick)

        self._build_ui()
        self.refresh()
        self.retranslate_ui()
        if theme_mgr is not None:
            theme_mgr.theme_changed.connect(self.apply_theme)
        i18n.language_changed.connect(self.retranslate_ui)
        self.apply_theme()

    # ------------------------------------------------------------- gränssnitt

    def _build_ui(self) -> None:
        kolumn = QVBoxLayout(self)
        kolumn.setContentsMargins(14, 12, 14, 12)
        kolumn.setSpacing(8)

        self.lbl_head = QLabel()
        self.lbl_head.setObjectName("InspectorEyebrow")
        kolumn.addWidget(self.lbl_head)

        rad = QHBoxLayout()
        rad.setSpacing(8)
        self.lbl_today = QLabel()
        self.lbl_today.setObjectName("InspectorTitle")
        rad.addWidget(self.lbl_today)
        rad.addStretch(1)
        self.chip_quota = QLabel()
        self.chip_quota.setObjectName("Chip")
        rad.addWidget(self.chip_quota)
        kolumn.addLayout(rad)

        self.lbl_quota = QLabel()
        kolumn.addWidget(self.lbl_quota)
        self.bar_quota = QProgressBar()
        self.bar_quota.setTextVisible(False)
        self.bar_quota.setFixedHeight(6)
        self.bar_quota.setRange(0, 100)
        kolumn.addWidget(self.bar_quota)

        self.lbl_days = QLabel()
        kolumn.addWidget(self.lbl_days)
        self.chart = DayChart()
        kolumn.addWidget(self.chart)

        self.lbl_numbers = QLabel()
        self.lbl_numbers.setWordWrap(True)
        kolumn.addWidget(self.lbl_numbers)

        self.lbl_sprint_head = QLabel()
        self.lbl_sprint_head.setObjectName("InspectorEyebrow")
        kolumn.addWidget(self.lbl_sprint_head)

        sprint = QHBoxLayout()
        sprint.setSpacing(6)
        self.combo_sprint = QComboBox()
        for minuter in SPRINT_MINUTES:
            self.combo_sprint.addItem(str(minuter), minuter)
        sprint.addWidget(self.combo_sprint)
        self.btn_sprint = QPushButton()
        self.btn_sprint.clicked.connect(self.toggle_sprint)
        sprint.addWidget(self.btn_sprint, 1)
        self.lbl_sprint = QLabel("--:--")
        self.lbl_sprint.setObjectName("Chip")
        sprint.addWidget(self.lbl_sprint)
        kolumn.addLayout(sprint)

        kolumn.addStretch(1)

        self.btn_csv = QPushButton()
        self.btn_csv.clicked.connect(self.export_csv)
        kolumn.addWidget(self.btn_csv)

        self.lbl_status = QLabel()          # statusfältets etikett
        self.lbl_status.setObjectName("StageMeta")

    def status_widget(self) -> QWidget:
        return self.lbl_status

    def showEvent(self, e) -> None:
        super().showEvent(e)
        self.refresh()

    # ---------------------------------------------------------------- projektet

    def set_project(self, project) -> None:
        """Byter logg när projektet byts: bokens dagar hör till boken."""
        self.flush()
        self.project = project
        self.log = WritingLog(str(log_path_for(project) if project is not None
                                  else default_log_path()))
        self._doc_key = None            # ny bok: ny baslinje, ingen skillnad att bokföra
        self.refresh()

    def _read_progress(self) -> dict:
        if self.project is None:
            return {"words": 0, "target": 0, "percent": 0, "daily_quota": 0}
        try:
            return dict(self.project.progress())
        except Exception:
            return {"words": 0, "target": 0, "percent": 0, "daily_quota": 0}

    # ---------------------------------------------------------------- räkningen

    def track(self, words_now: int, doc_key: str) -> None:
        """Antal ord efter en ändring. Skillnaden mot förra mätningen bokförs."""
        if doc_key != self._doc_key:
            if self._doc_key is not None:
                self.flush()            # annat dokument: skriv klart det förra först
            self._doc_key = doc_key
            self._last_words = int(words_now)
            return
        skillnad = int(words_now) - self._last_words
        if skillnad == 0:
            return
        if skillnad > 0:
            self._added += skillnad
            if self._sprint_left > 0:
                self._sprint_words += skillnad
        else:
            self._removed += -skillnad
        self._last_words = int(words_now)
        if not self._session_open:
            self.log.start_session()
            self._session_open = True
        self._refresh_cheap()           # siffrorna ska följa medan man skriver

    def today_net(self) -> int:
        """Dagens netto inklusive det som ännu inte skrivits till loggen."""
        return self._today + self._added - self._removed

    def flush(self) -> None:
        """Skriver det som ligger i minnet till loggen och stänger sessionen."""
        if self._added or self._removed:
            self.log.record(self._added, self._removed)
            self._added = self._removed = 0
            self._today = self.log.day().net
        if self._session_open and self._session_seconds >= 30:
            try:
                self.log.end_session()
            except ValueError:
                pass
            self._session_open = False
            self._session_seconds = 0
        self._refresh_cheap()

    def close_log(self) -> None:
        self.flush()
        if self._session_open:
            try:
                self.log.end_session()
            except ValueError:
                pass
            self._session_open = False

    # ------------------------------------------------------------------ sprint

    def toggle_sprint(self) -> None:
        if self._sprint_left > 0:
            self._sprint_left = 0                 # avbryt
            self._tick.stop()
        else:
            self._sprint_left = int(self.combo_sprint.currentData() or 25) * 60
            self._sprint_words = 0
            self._tick.start()
        self._update_sprint_labels()

    def _on_tick(self) -> None:
        if self._sprint_left > 0:
            self._sprint_left -= 1
            self._session_seconds += 1
        if self._sprint_left <= 0:
            self._tick.stop()
            minuter = int(self.combo_sprint.currentData() or 25)
            skrivna = self._sprint_words
            self.flush()
            self._sprint_left = 0
            self._update_sprint_labels()
            self.sprint_finished.emit(minuter, skrivna)
            return
        self._update_sprint_labels()

    def _update_sprint_labels(self) -> None:
        if self._sprint_left > 0:
            self.lbl_sprint.setText(f"{self._sprint_left // 60}:{self._sprint_left % 60:02d}")
            self.btn_sprint.setText(_("log_sprint_stop"))
        else:
            self.lbl_sprint.setText("--:--")
            self.btn_sprint.setText(_("log_sprint_start"))

    # ------------------------------------------------------------------ visning

    def refresh(self) -> None:
        """Läser om loggen och projektet — tungt, så det görs sällan."""
        dag = self.log.day()
        self._today = dag.net
        self._streak = self.log.streak()
        self._average = self.log.average(30)
        self._progress = self._read_progress()

        dagar = self.log.history(14)
        self.chart.set_days([(d.day, d.net) for d in dagar])
        self.lbl_days.setText(_("log_last_days", days=len(dagar)))
        self.lbl_numbers.setText(_("log_numbers", streak=self._streak[0],
                                   longest=self._streak[1], avg=round(self._average)))
        self._refresh_cheap()

    def _refresh_cheap(self) -> None:
        """Bara etiketter, inga databasfrågor. Kallas vid varje ändring."""
        dagens = self.today_net()
        kvot = int(self._progress.get("daily_quota") or 0)
        mål = int(self._progress.get("target") or 0)

        self.lbl_today.setText(_("log_today", n=dagens))
        if kvot > 0:
            klar = dagens >= kvot
            self.chip_quota.setObjectName("ChipOk" if klar else "Chip")
            self.chip_quota.setText(_("log_quota_done") if klar
                                    else _("log_quota_left", n=max(0, kvot - dagens)))
            self.lbl_quota.setText(_("log_quota_line", n=dagens, quota=kvot))
            self.bar_quota.setVisible(True)
            self.bar_quota.setValue(min(100, int(dagens / kvot * 100)))
        elif mål:
            ord_totalt = int(self._progress.get("words") or 0)
            self.chip_quota.setObjectName("Chip")
            self.chip_quota.setText(_("log_goal_chip", percent=int(self._progress.get("percent") or 0)))
            self.lbl_quota.setText(_("log_goal_line", total=ord_totalt, goal=mål))
            self.bar_quota.setVisible(True)
            self.bar_quota.setValue(min(100, int(self._progress.get("percent") or 0)))
        else:
            self.chip_quota.setObjectName("Chip")
            self.chip_quota.setText(_("log_quota_none"))
            self.lbl_quota.setText("")
            self.bar_quota.setVisible(False)
        # Objektnamnet styr stilen (chip med och utan bock), så den måste målas om
        self.chip_quota.style().unpolish(self.chip_quota)
        self.chip_quota.style().polish(self.chip_quota)

        if self.project is not None:
            self.lbl_status.setText(_("log_status", n=dagens, streak=self._streak[0]))
        else:
            self.lbl_status.setText(_("log_status_solo", n=dagens))
        self._update_sprint_labels()

    def export_csv(self) -> None:
        self.flush()
        start = str(Path.home() / "skrivlogg.csv")
        path, _valt = QFileDialog.getSaveFileName(self, _("log_csv_title"), start, "CSV (*.csv)")
        if not path:
            return
        try:
            self.log.export_csv(path)
        except OSError as exc:
            self.status_message.emit(_("log_csv_failed", error=exc))
            return
        self.status_message.emit(_("log_csv_saved", path=path))

    # -------------------------------------------------------------- tema/språk

    def apply_theme(self) -> None:
        if self.theme_mgr is None:
            return
        c = self.theme_mgr.tokens()
        self.chart.colors = {"bar": c["accent"], "empty": c["canvas_border"],
                             "text": c["text_muted"]}
        self.chart.update()
        self.bar_quota.setStyleSheet(f"""
            QProgressBar {{ background-color: {c['canvas_border']}; border: 0; border-radius: 3px; }}
            QProgressBar::chunk {{ background-color: {c['accent']}; border-radius: 3px; }}
        """)
        self.lbl_status.setStyleSheet(f"color: {c['status_text']};")
        self.lbl_numbers.setStyleSheet(f"color: {c['text_muted']};")
        for lbl in (self.lbl_days, self.lbl_quota):
            lbl.setStyleSheet(f"color: {c['text_muted']};")

    def retranslate_ui(self) -> None:
        self.lbl_head.setText(_("sidebar_tab_log").upper())
        self.lbl_sprint_head.setText(_("log_sprint").upper())
        self.btn_csv.setText(_("log_csv"))
        self.combo_sprint.setToolTip(_("log_sprint_minutes"))
        if int(self._progress.get("daily_quota") or 0):
            self.lbl_quota.setToolTip(_("log_deadline_tip", deadline=self._deadline_text()))
        self.refresh()

    def _deadline_text(self) -> str:
        if self.project is None:
            return ""
        return str(getattr(self.project, "settings", {}).get("deadline") or "")
