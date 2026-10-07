"""Projektöversikt — var boken står, på ett ställe (R03.18).

Fyra frågor en författare ställer mitt i en bok: Hur långt har jag kommit? Vad
är ogjort? Vilka trådar hänger löst? Vad står i mina anteckningar? Allt räknas
ur projektet och valvet som redan finns — inget nytt lager, ingen ny modell, och
inga filer flyttas. Anteckningarna blir en del av projektvyn utan att valvet
delas: en enda samling anteckningar, samma länkar mellan dem som förut.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from core.i18n import _


def overview_rows(project, vault=None) -> list:
    """Översiktens rader som (etikett, värde) — ren, så den går att prova."""
    if project is None:
        return []

    rader = []
    framsteg = project.progress()
    mal = int(framsteg.get("target") or 0)
    if mal:
        rader.append((_("overview_words"),
                      f'{framsteg["words"]:,} / {mal:,} ({framsteg["percent"]} %)'.replace(",", " ")))
    else:
        rader.append((_("overview_words"), f'{framsteg["words"]:,}'.replace(",", " ")))

    kvot = int(framsteg.get("daily_quota") or 0)
    if kvot:
        deadline = (project.settings.get("deadline") or "").strip()
        rader.append((_("overview_quota"),
                      f'{kvot:,}'.replace(",", " ") + f' {_("overview_per_day")}' +
                      (f' · {deadline}' if deadline else "")))

    scener = list(project.manuscript())
    rader.append((_("overview_scenes"), str(len(scener))))

    # status: räknas ur scenerna, inte ur inställningarna — det som är skrivet
    statusar = {}
    for node in scener:
        nyckel = (node.status or "").strip() or _("overview_no_status")
        statusar[nyckel] = statusar.get(nyckel, 0) + 1
    rader.append((_("overview_status"),
                  " · ".join(f"{namn} ({antal})" for namn, antal in sorted(statusar.items()))
                  or _("overview_none")))

    # utkast: hur långt revisionen har kommit, samma siffror som plot-tavlan
    utkast = {}
    for node in scener:
        nummer = int(node.revision or 1)
        utkast[nummer] = utkast.get(nummer, 0) + 1
    rader.append((_("overview_drafts"),
                  " · ".join(_("overview_draft", n=nummer) + f" ({antal})"
                             for nummer, antal in sorted(utkast.items()))
                  or _("overview_none")))

    # trådar: etiketterna som faktiskt används på scenerna
    tradar = {}
    for node in scener:
        for etikett in (node.labels or []):
            tradar[etikett] = tradar.get(etikett, 0) + 1
    rader.append((_("overview_threads"),
                  " · ".join(f"{namn} ({antal})" for namn, antal in sorted(tradar.items()))
                  or _("overview_none")))

    # anteckningarna: valvet som projektlager, utan att flytta en enda fil
    if vault is not None:
        rader.append((_("overview_notes"), str(len(vault.notes))))
        saknade = list(vault.unresolved_targets())
        rader.append((_("overview_links"),
                      " · ".join(saknade[:6]) + (f' (+{len(saknade) - 6})' if len(saknade) > 6 else "")
                      if saknade else _("overview_links_ok")))

    instruktioner = (project.settings.get("ai_instructions") or "").strip()
    rader.append((_("overview_instructions"),
                  instruktioner.splitlines()[0][:60] if instruktioner else _("overview_none")))
    return rader


class OverviewDialog(QDialog):
    """Översikten som en ruta: något man tittar på, inte ett läge man står i."""

    def __init__(self, project, vault=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("overview_title"))
        self.setModal(True)
        self.setMinimumWidth(560)
        self.adjustSize()          # rutan är så hög som innehållet, inte mer

        layout = QVBoxLayout(self)
        rubrik = QLabel(project.title if project is not None else _("overview_no_project"))
        rubrik.setStyleSheet("font-size: 15px; font-weight: 600;")
        layout.addWidget(rubrik)

        inre = QWidget()
        form = QFormLayout(inre)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        for etikett, varde in overview_rows(project, vault):
            nyckel = QLabel(etikett)
            nyckel.setStyleSheet("color: palette(mid);")
            form.addRow(nyckel, QLabel(str(varde)))
        ruta = QScrollArea()
        ruta.setWidgetResizable(True)
        ruta.setWidget(inre)
        ruta.setFrameShape(QScrollArea.Shape.Box)
        layout.addWidget(ruta)          # utan stretch: rutan krymper till innehållet

        knappar = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        knappar.rejected.connect(self.reject)
        knappar.accepted.connect(self.accept)
        layout.addWidget(knappar)
