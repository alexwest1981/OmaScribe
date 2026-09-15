#!/usr/bin/env python3
"""tools/ui_smoke.py — rökprov på att appen och de nya funktionerna fungerar ihop.

Startar MainWindow offscreen (inget fönster visas) och kör igenom de vägar som
sidlayouten, mallarna, bilder, diagram och export hänger på. Fönstret visas
aldrig, så provet kan köras utan skärm.

Kör:  QT_QPA_PLATFORM=offscreen .venv/bin/python tools/ui_smoke.py
"""

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import cast  # noqa: E402

from PyQt6.QtWidgets import QApplication  # noqa: E402
from PyQt6.QtGui import QImage, QColor, QTextDocument  # noqa: E402

from core import templates, print_style  # noqa: E402
from core.charts import ChartRenderer, PALETTES  # noqa: E402
from core.doc_manager import DocumentManager, DEFAULT_PAGE_SETTINGS  # noqa: E402

failures: list[str] = []
checks = 0


def check(ok: bool, label: str):
    global checks
    checks += 1
    if not ok:
        failures.append(label)
    print(f"  {'✓' if ok else '✗'} {label}")


def main() -> int:
    app = cast(QApplication, QApplication.instance() or QApplication(sys.argv[:1]))
    out = Path(tempfile.mkdtemp(prefix="omascribe-smoke-"))

    print("1. Huvudfönstret")
    from core.config import ConfigManager
    from core.ai_client import AIClient
    from core.dictation_engine import DictationEngine
    from ui.theme_manager import ThemeManager
    from ui.main_window import MainWindow

    config_mgr = ConfigManager()
    theme_mgr = ThemeManager(config_mgr)
    win = MainWindow(AIClient(config_mgr), DictationEngine(config_mgr), theme_mgr, config_mgr)
    check(win is not None, "MainWindow skapas")
    check(win.editor is not None, "editorn finns")
    check(win.page_settings.get("clean_print") is True, "ren export är på som standard")
    check(win.toolbar is not None, "verktygsraden finns")

    print("\n2. Sidlayout och sidnummer")
    win.editor.set_page_settings({
        "page_numbering": True,
        "page_number_pos": "bottom-alternating",
        "page_number_format": "slash",
        "header_text": "Testhuvud",
    })
    canvas = win.editor.canvas
    check(canvas.page_settings.get("page_number_pos") == "bottom-alternating",
          "växlande sidnummer når arbetsytan")
    check(canvas.page_settings.get("header_text") == "Testhuvud", "sidhuvudet når arbetsytan")

    print("\n3. Mallbiblioteket")
    for t in templates.TEMPLATES:
        html = templates.get_template_html(t["id"], lang="sv")
        doc = QTextDocument()
        doc.setHtml(html)
        check(len(doc.toPlainText().strip()) > 100 and doc.blockCount() > 3,
              f"mallen {t['id']} ger ett dokument med innehåll")

    print("\n4. Infogning i editorn (bild, diagram, tabell, sidbrytning)")
    canvas.document().clear()  # type: ignore[union-attr]
    cursor = canvas.textCursor()
    cursor.insertText("Rubrik\n")
    cursor.insertText("Ett stycke text som ska följa med i varje exportformat, "
                      "långt nog att både PDF, DOCX, HTML, Markdown och ren text "
                      "får ett innehåll som går att mäta.\n")
    canvas.insert_page_break()
    img = QImage(60, 40, QImage.Format.Format_RGB32)
    img.fill(QColor("#cc3366"))
    canvas.insert_image(img, width_px=200, align="center", caption="Bildtext")
    chart = ChartRenderer.render("bar", "T", ["A", "B"], [{"name": "S", "values": [1, 2]}],
                                 palette="mono", width=400, height=240)
    canvas.insert_chart(chart, align="center")
    check(canvas._try_insert_tsv_table(["A\tB", "1\t2"]), "klistrad TSV blir en tabell")
    check(len(canvas.toPlainText()) > 0, "dokumentet har innehåll efter infogningarna")

    print("\n5. Diagrampaletter")
    for name in PALETTES:
        im = ChartRenderer.render("line", "T", ["A", "B"], [{"name": "S", "values": [1, 2]}],
                                  palette=name, width=300, height=200)
        check(not im.isNull(), f"paletten {name} renderar")
    check("mono" in PALETTES, "gråskalepaletten finns")

    print("\n6. Export av det redigerade dokumentet")
    doc = canvas.document() or QTextDocument()
    for ext in (".pdf", ".docx", ".html", ".md", ".txt"):
        path = out / f"export{ext}"
        try:
            DocumentManager.save_file(str(path), doc, page_settings=win.page_settings)
            # Markdown och ren text bär bara texten (inga bilder), så de blir
            # med nödvändighet små — kravet är att filen har innehåll.
            ok = path.exists() and path.stat().st_size > 50
        except Exception as exc:          # noqa: BLE001
            print(f"      {ext}: {exc}")
            ok = False
        check(ok, f"export {ext} skrivs ({path.stat().st_size if path.exists() else 0} byte)")

    check((out / "export.md").read_text(encoding="utf-8").strip().startswith("#")
          or "Rubrik" in (out / "export.md").read_text(encoding="utf-8"),
          "markdown-exporten innehåller dokumentets text")
    check("Rubrik" in (out / "export.txt").read_text(encoding="utf-8"),
          "text-exporten innehåller dokumentets text")

    print("\n7. Ingen text kläms ihop")
    # Fällan: en QPushButton räknar sin storlek ur sin egen text och struntar i
    # en layout inuti. Appens globala stilmall ger knappen min-height 22px +
    # padding 6px 16px + 1px ram = 36px, så etiketterna inuti fick dela på 36
    # pixlar och klämdes ihop till en pixel per rad — korten såg tomma ut och
    # texten gick inte att läsa. Provet kör därför med den globala stilmallen
    # satt (som main.py) och med dubbelt så stort teckensnitt (som GDK_SCALE=2
    # ger via GTK-temat), alltså värsta fallet.
    from PyQt6.QtWidgets import QLabel, QPushButton
    from PyQt6.QtGui import QFont
    from ui.widgets import ClickableCard

    app.setStyleSheet(theme_mgr.get_stylesheet())
    big = QFont(app.font())
    big.setPointSizeF(app.font().pointSizeF() * 2.0)
    app.setFont(big)

    def squeezed(widget, label):
        bad = []
        for lbl in widget.findChildren(QLabel):
            if not lbl.isVisible() or not lbl.text().strip():
                continue
            if lbl.height() < lbl.fontMetrics().height() * 0.8:
                bad.append(f"{lbl.objectName() or 'label'} '{lbl.text()[:24]}' "
                           f"({lbl.height()} av {lbl.fontMetrics().height()} px)")
        check(not bad, f"{label}: ingen etikett är lägre än sin textrad"
              + ("" if not bad else f" — {len(bad)} klämda: {bad[:3]}"))
        return len(bad)

    # Regeln bakom felet: en knapp får aldrig bära en layout
    knappar_med_layout = [b.objectName() or b.text() for b in win.findChildren(QPushButton)
                          if b.layout() is not None]
    check(not knappar_med_layout,
          "ingen QPushButton bär en layout (det var felet)"
          + ("" if not knappar_med_layout else f" — {knappar_med_layout}"))

    from ui.start_screen import StartScreen
    start = StartScreen(config_mgr, theme_mgr)
    start.resize(1100, 800)
    start.show()
    app.processEvents()
    kort = [c for c in start.findChildren(ClickableCard) if c.objectName() == "ActionCard"]
    check(len(kort) == 3 and all(c.height() >= 90 for c in kort),
          f"startskärmens tre kort är fullhöga ({[c.height() for c in kort]} px)")
    squeezed(start, "Startskärmen")
    start.close()

    from ui.template_dialog import TemplateDialog
    dlg = TemplateDialog(theme_mgr)
    dlg.show()
    app.processEvents()
    mallkort = dlg.findChildren(ClickableCard)
    check(len(mallkort) == len(templates.TEMPLATES)
          and all(c.height() >= 120 for c in mallkort),
          f"alla {len(mallkort)} mallkort är fullhöga "
          f"({mallkort[0].height() if mallkort else 0} px i stället för 36)")
    squeezed(dlg, "Mallväljaren")
    dlg.close()

    from ui.chart_dialog import ChartDialog
    from ui.image_dialog import ImageDialog
    from ui.page_setup_dialog import PageSetupDialog
    from ui.table_dialog import TableDialog
    for factory, namn in ((lambda: ChartDialog(theme_mgr), "Diagramdialogen"),
                          (lambda: ImageDialog(theme_mgr), "Bilddialogen"),
                          (lambda: PageSetupDialog(dict(win.page_settings), theme_mgr),
                           "Sidinställningar"),
                          (lambda: TableDialog(theme_mgr), "Tabell dialogen")):
        try:
            d = factory()
            d.show()
            app.processEvents()
            squeezed(d, namn)
            d.close()
        except Exception as exc:          # noqa: BLE001
            check(False, f"{namn} kunde inte kontrolleras: {exc}")

    # Tillbaka till appens eget typsnitt för resten av provet
    app.setFont(QFont())

    print("\n8. Papperets färger")
    check(print_style.PAPER_WHITE == "#ffffff", "papperet är vitt")
    check(print_style.PAPER_TEXT == "#000000", "texten är svart")
    pal = print_style.paper_palette()
    check(pal.color(pal.ColorRole.Text).name() == "#000000", "papperspaletten ger svart text")

    print("\n" + "=" * 66)
    if failures:
        print(f"RESULTAT: {len(failures)} av {checks} kontroller föll")
        for f in failures:
            print(f"  ✗ {f}")
    else:
        print(f"RESULTAT: alla {checks} kontroller gröna")
    print(f"Exporter i: {out}")
    print("=" * 66)
    win.close()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
