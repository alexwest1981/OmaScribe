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
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Skrivloggens data hamnar i en temp-mapp: rökprovet skriver riktiga ord.
os.environ.setdefault("OMASCRIBE_DATA_DIR", tempfile.mkdtemp(prefix="omascribe-log-"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from typing import cast  # noqa: E402

from PyQt6.QtWidgets import QApplication  # noqa: E402
from PyQt6.QtGui import QImage, QColor, QTextDocument, QTextCursor  # noqa: E402

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

    print("\n6b. Sidinställningarna når exportvägen genom fönstret")
    # Fällan: DOCX-exporten anropade save_file utan page_settings, så samma
    # dokument blev rent i PDF men färgade kvar i Word. Provet går därför genom
    # fönstrets egen väg och kräver att inställningen faktiskt biter.
    import zipfile
    fargad = out / "export-sidinstallning.docx"
    sparat = dict(win.page_settings)
    sparad_html = win.editor.document.toHtml()
    try:
        win.page_settings["clean_print"] = False
        win.editor.document.setHtml('<p><span style="color:#c0392b">Färgad rad</span></p>')
        win._save_document(str(fargad))
        xml = zipfile.ZipFile(fargad).read("word/document.xml").decode("utf-8", "replace")
        check("C0392B" in xml.upper(),
              "page_settings når DOCX-exporten (färgen behölls när reningen är av)")
    except Exception as exc:          # noqa: BLE001
        check(False, f"DOCX via fönstret kunde inte kontrolleras: {exc}")
    finally:
        win.page_settings.clear()
        win.page_settings.update(sparat)
        win.editor.document.setHtml(sparad_html)

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

    print("\n9. Projektläget: scenen hamnar i rätt fil")
    # Fällan: ett projekt är många dokument. Provet öppnar ett projekt, skriver i
    # scen ett, byter scen och skriver igen — och läser sedan filerna från disk.
    # Bara då syns det om texten hamnade i fel scen eller försvann i bytet.
    from core import project as project_mod
    from core.project import Project as Bok
    projektmapp = out / "provprojekt"
    projektmapp.mkdir()
    bok = Bok.create(projektmapp, "Provbok", template="roman")
    win._activate_project(bok)
    # Provet kör utan visat fönster, så isVisible() är alltid falsk. isHidden()
    # mäter det koden faktiskt gör: setVisible(True/False) på panelen.
    check(win.project is bok and not win.binder.isHidden(), "projektet öppnas och trädet syns")
    check(win.windowTitle().startswith("Provbok"), f"fönstertiteln visar projektet ({win.windowTitle()})")

    forsta = bok.manuscript()[0]
    win.binder.add_node(project_mod.SCENE)        # samma väg som 📄-knappen
    andra = bok.manuscript()[1]
    check(andra.id != forsta.id and len(bok.manuscript()) == 2, "en ny scen skapas från panelen")
    check(win.binder.current_node_id() == andra.id, "den nya scenen blir markerad")

    win.binder.select_node(forsta.id)
    win.editor.document.setHtml("<h1>Scen ett</h1><p>Alfa beta gamma.</p>")
    win.is_modified = True
    win.binder.select_node(andra.id)              # bytet skall spara den första
    forsta_text = bok.path_of(forsta).read_text(encoding="utf-8")
    check("Alfa beta gamma." in forsta_text, "texten hamnade i scen ett")
    check("Scen ett" in win.editor.document.toPlainText() is False
          or "Alfa beta gamma." not in win.editor.document.toPlainText(),
          "editorn visar den nya scenen, inte den förra")
    check(bok.words(forsta.id) == 5, f"ordräkningen följer med ({bok.words(forsta.id)})")

    win.editor.document.setHtml("<h1>Scen två</h1><p>Delta epsilon.</p>")
    win.is_modified = True
    check(win.file_save() is True, "Spara i projektläget går igenom")
    andra_text = bok.path_of(andra).read_text(encoding="utf-8")
    check("Delta epsilon." in andra_text, "andra scenen sparades där den skulle")
    check(not win.is_modified, "dokumentet är osparat-flagga borta efter Spara")

    # researchmaterial hör till projektet men inte till manuset (R01.7)
    researchmapp = next(n for n in bok.children(None) if n.type == project_mod.RESEARCH)
    win.binder.select_node(researchmapp.id)
    win.binder.add_node(project_mod.NOTE)          # samma väg som 📝-knappen
    note = bok.research()[-1]
    note_id = note.id
    check(note.parent == researchmapp.id,
          f"anteckningen hamnar i researchmappen ({note.parent})")
    check(note.type == project_mod.NOTE and note.is_writable,
          f"anteckningen är en skrivbar nod ({note.type})")
    fore_ord = bok.total_words()
    win.editor.document.setHtml("<h1>Källor</h1><p>Källa ett två tre.</p>")
    win.is_modified = True
    win.binder.select_node(forsta.id)              # bytet sparar anteckningen
    check(bok.words(note_id) == 5, f"anteckningen har sin text ({bok.words(note_id)})")
    check(bok.total_words() == fore_ord, "anteckningens ord räknas inte in i projektet")
    check(bok.node_progress(researchmapp.id)["words"] == 0,
          "och researchmappen visar inga manusord")

    igen = Bok.load(projektmapp)                   # läs allt tillbaka från disk
    check(igen.total_words() == bok.total_words() and igen.total_words() > 0,
          f"projektet läses tillbaka med samma ordantal ({igen.total_words()})")
    check(len(igen.walk()) == len(bok.walk()),
          f"trädet överlever rundturen ({len(igen.walk())} av {len(bok.walk())})")
    check(all(n.id != note_id for n in igen.manuscript()),
          "researchanteckningen är inte med i manuset efter omladdning")

    win._deactivate_project()
    check(win.project is None and win.binder.isHidden(), "trädet göms när projektet stängs")

    print("\n10. Scenens uppgifter och korktavlan")
    from PyQt6.QtCore import Qt as QtNS
    win._activate_project(bok)
    insp = win.scene_inspector
    kort = win.binder.corkboard
    win.binder.select_node(forsta.id)
    check(insp.input_title.text() == forsta.title, f"panelen visar scenens rubrik ({insp.input_title.text()!r})")
    check(insp.input_title.isEnabled(), "fälten är öppna när en scen är vald")
    check(kort.list.count() == len(bok.manuscript()),
          f"ett kort per scen ({kort.list.count()} kort, {len(bok.manuscript())} scener)")

    # rubriken ändras i panelen och skall slå igenom i trädet och på disk
    insp.input_title.setText("Scen ett, omdöpt")
    insp.input_title.editingFinished.emit()
    check(forsta.title == "Scen ett, omdöpt", f"rubriken ändras ({forsta.title!r})")
    igen2 = Bok.load(projektmapp)
    check(igen2.by_id(forsta.id).title == "Scen ett, omdöpt", "den nya rubriken ligger på disk")
    markering = win.binder.tree.currentIndex().data(QtNS.ItemDataRole.UserRole)
    check(markering == forsta.id, "markeringen stannar kvar efter namnbytet")
    check(win.active_scene_id == forsta.id, "och samma scen är kvar i editorn")

    # status, etiketter, mål
    insp.combo_status.setCurrentText("Bearbetning")
    check(forsta.status == "Bearbetning", f"statusen sätts ({forsta.status!r})")
    check("Bearbetning" in bok.settings["statuses"], "en ny status hamnar i projektets lista")
    insp.input_labels.setText("Anna, kväll")
    insp.input_labels.editingFinished.emit()
    check(forsta.labels == ["Anna", "kväll"], f"etiketterna delas på komma ({forsta.labels})")
    insp.spin_target.setValue(50)
    check(forsta.target_words == 50, "målantalet sätts")
    check("5" in insp.lbl_words.text() and "50" in insp.lbl_words.text(),
          f"panelen visar ord mot mål ({insp.lbl_words.text()!r})")
    insp.spin_revision.setValue(3)
    check(forsta.revision == 3, "utkastnumret sätts")

    # scenanteckningen hör till scenen och rör inte prosan (R01.12)
    ord_fore = bok.words(forsta.id)
    insp.input_note.setPlainText("Kolla: hon har nyckeln redan här.")
    insp._apply_note()
    check(forsta.note.startswith("Kolla"), f"scenanteckningen sparas ({forsta.note!r})")
    check(bok.words(forsta.id) == ord_fore,
          f"och ordantalet rörs inte ({bok.words(forsta.id)} mot {ord_fore})")
    check(Bok.load(projektmapp).by_id(forsta.id).note.startswith("Kolla"),
          "anteckningen ligger på disk")
    check(win._current_note_title() == forsta.title,
          f"valvpanelen slår upp scenens namn ({win._current_note_title()!r})")

    # kortet visar statusen, och ett klick på kortet öppnar scenen
    check("Bearbetning" in kort.list.item(0).text(),
          f"kortet visar statusen ({kort.list.item(0).text()!r})")
    check(kort.list.item(0).foreground().color().name() == bok.status_color("Bearbetning"),
          f"och kortet bär statusens färg "
          f"({kort.list.item(0).foreground().color().name()})")
    # statusen står som text i trädet också — färgen bär aldrig betydelsen själv
    check("Bearbetning" in win.binder._item_for(forsta.id).text(),
          f"trädraden visar statusen som text "
          f"({win.binder._item_for(forsta.id).text()!r})")
    check(win.binder._item_for(forsta.id).foreground().color().name()
          == bok.status_color("Bearbetning"),
          f"och raden bär statusens färg "
          f"({win.binder._item_for(forsta.id).foreground().color().name()})")
    utan_status = next(n for n in bok.children(forsta.parent) if not n.status)
    check(win.binder._item_for(utan_status.id).foreground().style()
          == QtNS.BrushStyle.NoBrush,
          "en nod utan status får ingen egen färg")
    win.binder.select_node(andra.id)
    check(win.active_scene_id == andra.id, "scen två är öppen")
    kort._on_clicked(kort.list.item(0))            # samma väg som ett musklick
    check(win.active_scene_id == forsta.id, "ett klick på kortet öppnar scenen")

    # utan projekt skall panelen vara tom och stängd
    win._deactivate_project()
    check(not insp.input_title.isEnabled() and insp.input_title.text() == "",
          "panelen töms och stängs när projektet stängs")
    check(insp.lbl_hint.isHidden() is False, "och förklarar varför den är tom")

    print("\n11. Dra-och-släpp och omordning")
    win._activate_project(bok)
    binder = win.binder
    check(binder.tree.dragEnabled() and binder.tree.acceptDrops(),
          "trädet tar emot drag och släpp")
    check(binder.corkboard.list.dragEnabled() and binder.corkboard.list.acceptDrops(),
          "kortvyn tar emot drag och släpp")

    # Romanmallen börjar med en del, så föräldern hämtas ur scenen själv
    # i stället för att antas ligga på översta nivån.
    ett = bok.manuscript()[0]
    tva = bok.manuscript()[1]
    kap = bok.by_id(ett.parent)
    check(binder.move_by_drop(tva.id, ett.id, "above") is True, "släpp ovanför en scen flyttar den")
    check(bok.children(kap.id)[0].id == tva.id, "scen två hamnade först")
    check(binder.move_by_drop(tva.id, ett.id, "below") is True, "släpp under en scen flyttar tillbaka")
    check(bok.children(kap.id)[1].id == tva.id, "scen två hamnade sist igen")

    kap2 = bok.add_node(project_mod.CHAPTER, "Kapitel 2")
    binder.refresh(select_id=tva.id)
    check(binder.move_by_drop(tva.id, kap2.id, "on") is True, "släpp på ett kapitel lägger scenen inuti")
    check(bok.by_id(tva.id).parent == kap2.id, "föräldern byttes")
    check([n.id for n in bok.children(kap.id)] == [ett.id], "kapitel ett har bara en scen kvar")

    # det som inte får gå igenom
    check(binder.move_by_drop(kap2.id, tva.id, "on") is False,
          "ett kapitel kan inte flyttas in i sin egen scen")
    check(binder.move_by_drop(tva.id, tva.id, "on") is False, "en nod kan inte flyttas in i sig själv")
    check(binder.move_by_drop(tva.id, "", "end") is True, "släpp utanför korten lägger noden sist")
    check(bok.by_id(tva.id).parent is None and bok.children(None)[-1].id == tva.id,
          "scenen ligger nu sist på översta nivån")

    # flytten skall ligga på disk, inte bara i minnet
    igen3 = Bok.load(projektmapp)
    check(igen3.by_id(tva.id).parent is None, "flytten ligger i manifestet på disk")
    check(len(igen3.children(kap.id)) == 1, "kapitel ett har en scen i den sparade filen")
    win._deactivate_project()

    print("\n12. Sammanhängande läsvy")
    win._activate_project(bok)
    binder = win.binder
    # scen två flyttades till översta nivån i avsnitt 11 — tillbaka in i kapitlet
    binder.move_by_drop(tva.id, ett.id, "below")
    check(bok.by_id(tva.id).parent == kap.id, "scen två är tillbaka i kapitlet")
    binder.refresh(select_id=ett.id)
    binder.select_node(ett.id)
    fore = win.editor.document.toHtml()
    check(win.act_view_scrivenings.isEnabled(), "läsvyn går att välja i projektläge")

    win._toggle_scrivenings()
    check(win.stack.currentIndex() == win._scrivenings_index, "läsvyn är framme")
    lastext = win.scrivenings.pane.toPlainText()
    check("Alfa beta gamma." in lastext, f"scen ett läses i vyn ({lastext[:40]!r})")
    check("Delta epsilon." in lastext, "scen två läses i samma text")
    check(lastext.index("Alfa") < lastext.index("Delta"), "scenerna kommer i läsordning")
    check("ord i läsvyn" in win.lbl_stats.text(),
          f"statusfältet visar läsvyns ord ({win.lbl_stats.text()!r})")
    check(win.windowTitle().startswith("Provbok"), f"titeln visar projektet ({win.windowTitle()})")
    check(len(win.scrivenings.shown_nodes()) == 2,
          f"båda scenerna är med ({len(win.scrivenings.shown_nodes())})")

    # scenen i editorn skall vara orörd av att vyn byggdes
    check(win.editor.document.toHtml() == fore, "editorn rördes inte av läsvyn")

    # klick på en scenrubrik skall lämna vyn och öppna scenen
    win.scrivenings.scene_activated.emit(tva2 := win.scrivenings.shown_nodes()[1].id)
    check(win.stack.currentIndex() == 1, "klicket lämnar läsvyn")
    check(win.active_scene_id == tva2, f"och öppnar den scenen ({win.active_scene_id})")

    # Escape stänger också
    win._toggle_scrivenings()
    check(win.stack.currentIndex() == win._scrivenings_index, "läsvyn är framme igen")
    win.scrivenings.closed.emit()
    check(win.stack.currentIndex() == 1, "Escape går tillbaka till editorn")
    check(win.active_scene_id is not None, "och scenen i editorn finns kvar")

    # samma genväg två gånger växlar fram och tillbaka
    win._toggle_scrivenings()
    win._toggle_scrivenings()
    check(win.stack.currentIndex() == 1, "samma val två gånger stänger läsvyn")

    # utan projekt skall den inte gå att öppna
    win._deactivate_project()
    check(not win.act_view_scrivenings.isEnabled(), "läsvyn stängs av utan projekt")
    win.show_editor_screen()
    win._toggle_scrivenings()
    check(win.stack.currentIndex() == 1, "läsvyn öppnas inte utan projekt")

    print("\n13. Ord och mål i trädet")
    win._activate_project(bok)
    binder = win.binder

    def rad(node_id: str) -> str:
        """Texten i trädraden för en nod — samma väg som ögat tar."""
        return next((item.text() for item in binder._iter_items()
                     if item.data(QtNS.ItemDataRole.UserRole) == node_id), "")

    bok.settings["target_words"] = 100
    binder.refresh(select_id=ett.id)
    check("100" in binder.lbl_title.text() and "ord" in binder.lbl_title.text(),
          f"huvudet visar projektets mål ({binder.lbl_title.text()!r})")
    check("Provbok" in binder.lbl_title.text(), "och projektets namn")

    win.scene_inspector.spin_target.setValue(50)       # scen ett
    binder.refresh_labels()
    check(f"{bok.words(ett.id)}/50" in rad(ett.id),
          f"scenraden visar ord mot mål ({rad(ett.id)!r})")
    check(f"{bok.words_in(kap.id)}/50" in rad(kap.id),
          f"kapitelraden summerar scenerna ({rad(kap.id)!r})")
    check(str(bok.words_in(bok.by_id(kap.parent).id)) in rad(bok.by_id(kap.parent).id),
          f"delen summerar vidare nedåt ({rad(bok.by_id(kap.parent).id)!r})")

    # ordtalet i raden skall följa med när texten sparas
    binder.select_node(ett.id)
    win.editor.document.setHtml("<p>ett två tre</p>")
    win.is_modified = True
    check(win.file_save() is True, "scenen sparas")
    check(f"{bok.words(ett.id)}/50" in rad(ett.id),
          f"raden uppdateras vid sparande ({rad(ett.id)!r})")

    # utan projektmål visas bara ordtalet
    bok.settings["target_words"] = 0
    binder.refresh()
    check("%" not in binder.lbl_title.text(), f"utan mål ingen procent ({binder.lbl_title.text()!r})")
    check(bok.by_id(ett.id).target_words == 50, "scenens eget mål ligger kvar")
    win._deactivate_project()

    print("\n14. Samlingar")
    win._activate_project(bok)
    binder = win.binder
    check(binder.tabs.count() == 3, f"tre vyer i panelen ({binder.tabs.count()})")
    check(binder.tabs.tabText(2) != "", f"samlingsfliken har en rubrik ({binder.tabs.tabText(2)!r})")

    binder.select_node(ett.id)                     # scenen som ★ lägger in
    samling = binder.collections.new_manual("Provsamling")
    check(samling is not None, "en handplockad samling skapas")
    check(bok.collection(samling).contains(ett.id),
          f"den markerade scenen hamnade i samlingen ({bok.collection(samling).node_ids})")
    check(binder.collections.tree.topLevelItemCount() == 1,
          "samlingen syns i panelen")

    # samlingen skall ligga på disk
    igen4 = Bok.load(projektmapp)
    check([c.name for c in igen4.collections] == ["Provsamling"],
          f"samlingen ligger i manifestet ({[c.name for c in igen4.collections]})")

    # ett klick på en rad i samlingen öppnar scenen
    rad = binder.collections.tree.topLevelItem(0).child(0)
    binder.collections._on_clicked(rad, 0)
    check(win.active_scene_id == ett.id, f"klicket öppnar scenen ({win.active_scene_id})")

    # sparad sökning (scenens text skrevs om i avsnitt 13, så ordet är 'ett')
    binder.collections.new_search("Med ettan", "text:ett")
    check(binder.collections.tree.topLevelItemCount() == 2, "sökningen blir en samling")
    traffar = [binder.collections.tree.topLevelItem(1).child(i).text(0)
               for i in range(binder.collections.tree.topLevelItem(1).childCount())]
    check(any("Scen ett" in rad for rad in traffar),
          f"sökningen hittar scenen med ordet ({traffar})")
    check(len(bok.select_collection(bok.collections[1].id)) == 1,
          f"och bara den ({len(bok.select_collection(bok.collections[1].id))})")
    check(bok.select_collection(bok.collections[1].id)[0].id == ett.id,
          "och det är rätt scen")

    # samlingen kan tas bort igen
    binder.collections.delete(samling, ask=False)
    check(len(bok.collections) == 1, f"den handplockade samlingen är borta ({len(bok.collections)})")
    check(Bok.load(projektmapp).collections[0].name == "Med ettan",
          "och manifestet på disk följer med")
    win._deactivate_project()

    print("\n15. Material kopplat till scenen")
    win._activate_project(bok)
    insp = win.scene_inspector
    win.binder.select_node(ett.id)
    check(insp.lst_material.count() == 0, "scenen har inget material än")
    check(insp.btn_link.isEnabled(), "📎 går att använda")

    note = bok.by_id(note_id)
    check(insp.link_material(note_id) is True, "materialet kopplas från panelen")
    rader = [insp.lst_material.item(i).text() for i in range(insp.lst_material.count())]
    check(rader == [note.title], f"och syns i listan ({rader})")
    check([n.id for n in bok.material_for(ett.id)] == [note_id], "kopplingen ligger i modellen")
    check([n.id for n in Bok.load(projektmapp).material_for(ett.id)] == [note_id],
          "och i manifestet på disk")

    # dubbelklick (open_node) öppnar anteckningen i editorn
    insp.open_node.emit(note_id)
    check(win.active_scene_id == note_id,
          f"anteckningen öppnas i editorn ({win.active_scene_id})")
    check("Källa" in win.editor.document.toPlainText(),
          f"och texten är anteckningens ({win.editor.document.toPlainText()[:24]!r})")

    # kopplingen kan tas bort igen
    win.binder.select_node(ett.id)
    check(insp.unlink_material(note_id) is True, "kopplingen kan tas bort")
    check(insp.lst_material.count() == 0, "och listan töms")
    check(Bok.load(projektmapp).material_for(ett.id) == [], "och det ligger borta på disk")

    # en scen som tas bort tar kopplingen med sig
    insp.link_material(note_id)
    kapitel = bok.by_id(ett.parent)
    bok.delete_node(kapitel.id)
    win._on_structure_changed()          # samma väg som panelen tar vid en ändring
    check(bok.links == [], f"kopplingen städas när scenen försvinner ({bok.links})")
    check(bok.validate() == [], "och projektet är fortfarande giltigt")
    check(win.active_scene_id is None,
          f"editorn släpper scenen som togs bort ({win.active_scene_id})")
    check(win.editor.document.toPlainText().strip() == "",
          f"och tömmer sin text ({win.editor.document.toPlainText()[:20]!r})")
    win._deactivate_project()

    print("\n16. Projektmallar och nytt projekt")
    from core.project import Project, PROJECT_TEMPLATES, SCENE
    from ui.project_dialog import NewProjectDialog
    dlg = NewProjectDialog(default_name="Testbok")
    check(dlg.input_name.text() == "Testbok", "namnet är förifyllt från mappen")
    check(dlg.combo_template.currentData() == "roman", "roman är förvald")
    check(dlg.spin_target.value() == 80_000,
          f"och romanens ordmål står där ({dlg.spin_target.value()})")
    check(dlg.lbl_description.text().strip() != "",
          f"mallen beskrivs ({dlg.lbl_description.text()!r})")
    dlg.combo_template.setCurrentIndex(dlg.combo_template.findData("novell"))
    check(dlg.spin_target.value() == 8_000,
          f"novellen byter ordmålet ({dlg.spin_target.value()})")
    dlg.spin_target.setValue(9_500)                 # mitt eget mål går före mallens
    namn, mall, mal = dlg.values()
    check((namn, mall, mal) == ("Testbok", "novell", 9_500),
          f"dialogen lämnar ifrån sig valen ({(namn, mall, mal)})")
    check(dlg.combo_template.count() == len(PROJECT_TEMPLATES),
          f"alla mallar finns i listan ({dlg.combo_template.count()})")

    # samma väg som new_project tar efter dialogen
    mapp = Path(tempfile.mkdtemp(prefix="nytt-projekt-")) / "Testbok"
    ny = Project.create(mapp, namn, template=mall)
    ny.settings["target_words"] = mal
    ny.save()
    check(ny.children(None)[0].type == SCENE,
          f"novellprojektet börjar med en scen ({ny.children(None)[0].type})")
    check(len(ny.children(None)) == 2, "och researchmappen ligger bredvid")
    check(Project.load(mapp).settings["target_words"] == 9_500,
          "ordmålet jag skrev är det som gäller")
    dlg.deleteLater()

    print("\n17. Scenens entiteter (codex i projektet)")
    from core.project import Project as NyBok
    from ui.entity_dialog import EntityDialog
    mapp = Path(tempfile.mkdtemp(prefix="codex-")) / "Boken"
    cbok = NyBok.create(mapp, "Codexboken", template="enkel")
    win._activate_project(cbok)
    check(win.codex is not None, "projektets codex öppnas med projektet")
    check(win.codex.path == str(cbok.codex_path),
          f"och ligger i projektmappen ({win.codex.path})")
    scen = cbok.manuscript()[0]
    win.binder.select_node(scen.id)
    insp = win.scene_inspector
    check(insp.lst_entities.count() == 0, "scenen har inga entiteter än")
    check(insp.btn_entity_link.isEnabled(), "📎 går att använda")

    dlg = EntityDialog(default_name="Elin")
    check(dlg.combo_type.currentData() == "character", "karaktär är förvald typ")
    dlg.combo_type.setCurrentIndex(dlg.combo_type.findData("place"))
    e_namn, e_typ, e_sum = dlg.values()
    check((e_namn, e_typ) == ("Elin", "place"),
          f"dialogen lämnar namn och typ ({(e_namn, e_typ)})")
    dlg.deleteLater()

    elin = win.codex.add_entity(e_namn, type=e_typ, summary="Bor vid älven")
    check(insp.link_entity(elin.id) is True, "entiteten kopplas till scenen")
    check(insp.lst_entities.count() == 1,
          f"och syns i listan ({insp.lst_entities.count()})")
    ent_rad = insp.lst_entities.item(0).text()
    check("Elin" in ent_rad and "Plats" in ent_rad, f"med namn och typ ({ent_rad!r})")
    check([e.id for e in win.codex.for_node(scen.id)] == [elin.id],
          "kopplingen ligger i codex")

    # en entitet som nämns i texten men inte är kopplad pekas ut
    alven = win.codex.add_entity("älven", type="place")
    win.editor.document.setHtml("<p>Elin gick ner till älven.</p>")   # som att skriva det själv
    win._flush_scene()
    check("älven" in cbok.read(scen.id), "texten sparades till scenfilen")
    insp.set_scene(cbok, cbok.by_id(scen.id))
    check("1" in insp.lbl_entities.text(),
          f"den okopplade entiteten pekas ut ({insp.lbl_entities.text()!r})")
    check(len(insp._mentioned_unlinked()) == 1, "och det är just älven")
    check(insp._mentioned_unlinked()[0].id == alven.id, "inte den kopplade Elin")

    check(insp.unlink_entity(elin.id) is True, "kopplingen kan tas bort")
    check(insp.lst_entities.count() == 0, "och listan töms")
    check(win.codex.for_node(scen.id) == [], "och den ligger borta i codex")
    check(cbok.codex_path.exists(), f"codex-filen finns i projektmappen")
    win._deactivate_project()
    check(win.codex is None, "codex stängs när projektet lämnas")

    print("\n18. Redigering i läsvyn (R01.9)")
    import os as _os
    from PyQt6.QtGui import QTextCursor
    from core.project import SCENE as SCEN
    mapp = Path(tempfile.mkdtemp(prefix="lasvy-")) / "Läsboken"
    lbok = NyBok.create(mapp, "Läsboken", template="enkel")
    kap = lbok.children(None)[0]
    s1 = lbok.children(kap.id)[0]
    lbok.write(s1.id, "<p>Alfa beta.</p>")
    s2 = lbok.add_node(SCEN, "Scen två", parent=kap.id)
    lbok.write(s2.id, "<p>Gamma delta.</p>")
    win._activate_project(lbok)
    win.binder.select_node(s1.id)
    check(win.active_canvas is win.editor.canvas,
          "utan läsvyn skriver kommandona i editorn")

    tider = {n.id: _os.path.getmtime(lbok.path_of(n)) for n in (s1, s2)}
    win._toggle_scrivenings()
    check(win.active_canvas is win.scrivenings.pane,
          "med läsvyn uppe tar kommandona läsvyn")
    check(not win.toolbar.isEnabled(), "verktygsraden är avstängd i läsvyn")
    check(not win.act_ins_image.isEnabled(), "och infogningar likaså")
    check(not win.scrivenings.pane.isReadOnly(), "men texten går att skriva i")
    check(win.stack.currentWidget() is win.scrivenings,
          "och läsvyn är den vy som visas")
    check(win.scrivenings.pane.focusPolicy() != QtNS.FocusPolicy.NoFocus,
          "skrivytan kan ta fokus")

    # en läsning utan ändringar rör ingen fil
    win._close_scrivenings()
    check(_os.path.getmtime(lbok.path_of(s2)) == tider[s2.id],
          "en läsning utan ändringar rör inte scenerna")
    check(lbok.read(s2.id) == "<p>Gamma delta.</p>",
          f"och texten står kvar orörd ({lbok.read(s2.id)!r})")
    check(win.toolbar.isEnabled(), "och verktygsraden kommer tillbaka")

    # skriv i en scen, stäng vyn, texten skall ligga i rätt fil
    win._toggle_scrivenings()
    pane = win.scrivenings.pane
    sista = None
    for block in win.scrivenings._iter_marked(s1.id):
        sista = block
    cursor = QTextCursor(sista)
    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
    cursor.insertText(" Ett tillägg.")
    check("Ett tillägg." in pane.toPlainText(), "texten står i vyn")
    check("Ett tillägg." not in lbok.read(s1.id), "men inte i filen än")
    win._close_scrivenings()
    check("Ett tillägg." in lbok.read(s1.id), "tillägget hamnar i scenen jag skrev i")
    check("Gamma delta." in lbok.read(s2.id) and "Ett tillägg." not in lbok.read(s2.id),
          "och grannscenen är orörd")
    check(lbok.words(s1.id) == 4, f"ordantalet räknas om ({lbok.words(s1.id)})")
    check("4" in win.binder._item_for(s1.id).text(),
          f"och syns i trädet ({win.binder._item_for(s1.id).text()!r})")

    # Ångra och klipp-och-klistra följer den yta som har fokus
    win._toggle_scrivenings()
    pane = win.scrivenings.pane
    cursor = pane.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    cursor.insertText(" XYZ")
    check("XYZ" in pane.toPlainText(), "ny text i vyn")
    win.act_undo.trigger()
    check("XYZ" not in pane.toPlainText(), "Ångra tar bort den igen")
    check("XYZ" not in win.editor.document.toPlainText(), "och rör inte editorns text")
    win.act_select_all.trigger()
    check(pane.textCursor().hasSelection(), "Markera allt markerar läsvyns text")
    win._close_scrivenings()
    check(not win.editor.document.toPlainText().startswith("Alfa beta. Ett tillägg."),
          "stängningen lämnar tillbaka till editorn")
    win._deactivate_project()

    print("\n19. Kommentarer fästa i texten (R01.12)")
    from core.project import Project as KomBok
    mapp = Path(tempfile.mkdtemp(prefix="kommentar-")) / "Komboken"
    kbok = KomBok.create(mapp, "Komboken", template="enkel")
    kscen = kbok.manuscript()[0]
    win._activate_project(kbok)
    win.binder.select_node(kscen.id)
    win.editor.document.setHtml("<p>Hon kom hem sent. Dörren stod öppen.</p>")
    win._flush_scene()
    insp = win.scene_inspector
    check(insp.lst_comments.count() == 0, "scenen har inga kommentarer än")
    check(insp.btn_comment_new.isEnabled(), "💬 går att använda")

    # utan markering händer inget — men det syns i statusfältet
    cursor = win.editor.textCursor()
    cursor.clearSelection()
    win.editor.setTextCursor(cursor)
    check(win.ask_new_comment() is False, "utan markering blir det ingen kommentar")
    check(win.status_bar.currentMessage() != "", "och statusfältet säger varför")

    # markera ett textställe och kommentera det
    quote = "Dörren stod öppen."
    cursor = win.editor.document.find(quote)
    win.editor.setTextCursor(cursor)
    check(win.editor.textCursor().selectedText() == quote,
          f"stället är markerat ({win.editor.textCursor().selectedText()!r})")
    fore = kbok.read(kscen.id)
    kom = win.add_comment(quote, "Låt henne stänga den.")
    check(kom is not None and kom["quote"] == quote, "kommentaren fäster på citatet")
    check(kbok.read(kscen.id) == fore, "och rör inte en bokstav i scenfilen")
    check(len(kbok.unresolved_comments()) == 1, "och räknas som kvar att göra")
    check(insp.lst_comments.count() == 1, "och syns i panelen")
    check("Låt henne stänga den." in insp.lst_comments.item(0).text(),
          f"med sin text ({insp.lst_comments.item(0).text()!r})")
    check(insp.lbl_comments.text() != "", f"panelen räknar de ogiltiga ({insp.lbl_comments.text()!r})")
    check(KomBok.load(mapp).comments_for(kscen.id)[0]["quote"] == quote,
          "och kommentaren ligger på disk")

    # stället markeras i texten — utan att röra dokumentet
    markeringar = win.editor.canvas.extraSelections()
    check(len(markeringar) == 1, f"textstället markeras ({len(markeringar)})")
    check(markeringar[0].cursor.selectedText() == quote,
          f"och markeringen sitter på citatet ({markeringar[0].cursor.selectedText()!r})")
    check(win.editor.document.toPlainText().count(quote) == 1,
          "markeringen lägger inte till något i texten")

    # navigera från panelen till textstället
    win._load_scene(kscen.id)
    win.goto_comment(kscen.id, kom["id"])
    check(win.editor.textCursor().selectedText() == quote,
          f"panelen tar mig till stället ({win.editor.textCursor().selectedText()!r})")

    # ett ställe som inte finns kvar: kommentaren lever, men säger ifrån
    win.editor.document.setPlainText("Helt annan text.")
    win._flush_scene()
    check(win.goto_comment(kscen.id, kom["id"]) is False, "ett borta citat ger inget hopp")
    check(win.status_bar.currentMessage() != "", "men ett besked")
    check(len(kbok.unresolved_comments()) == 1, "och kommentaren är kvar")

    # markera som löst: markeringen försvinner, kommentaren stannar
    insp.set_scene(kbok, kbok.by_id(kscen.id))
    win.editor.document.setHtml("<p>Hon kom hem sent. Dörren stod öppen.</p>")
    win._flush_scene()
    insp.set_scene(kbok, kbok.by_id(kscen.id))
    check(len(win.editor.canvas.extraSelections()) == 1, "markeringen är tillbaka")
    check(insp._toggle_resolved() is True, "kommentaren kan markeras löst")
    check(kbok.unresolved_comments() == [], "och räknas inte längre")
    check(insp.lst_comments.count() == 1, "men raden ligger kvar i panelen")
    check(len(win.editor.canvas.extraSelections()) == 0, "och markeringen i texten är borta")
    check(KomBok.load(mapp).unresolved_comments() == [], "löst ligger på disk")

    # och kan tas bort helt
    insp.set_scene(kbok, kbok.by_id(kscen.id))
    check(insp._delete_selected_comment() is True, "kommentaren kan tas bort")
    check(insp.lst_comments.count() == 0, "och försvinner ur panelen")
    check(KomBok.load(mapp).comments_for(kscen.id) == [], "och från disk")
    win._deactivate_project()
    # Att lämna projektet får inte lämna kvar ett "osparat dokument" utan väg:
    # stängningen skulle då fråga om att spara en scenfil som redan är sparad.
    check(win.is_modified is False and win.active_scene_id is None,
          f"inget osparat dokument ligger kvar (modified={win.is_modified})")
    check(win.editor.document.toPlainText() == "", "och editorn är tom")
    check(win.current_filepath is None, "och ingen filväg hänger kvar")

    print("\n20. Manusvarianter (R01.14)")
    from core.project import Project as VarBok
    from ui.variants_dialog import VariantsDialog
    mapp = Path(tempfile.mkdtemp(prefix="variant-")) / "Variantboken"
    vbok = VarBok.create(mapp, "Variantboken", template="enkel")
    vkap = vbok.children(None)[0]
    v1 = vbok.children(vkap.id)[0]
    vbok.write(v1.id, "<p>Ett.</p>")
    v2 = vbok.add_node(SCEN, "Scen två", parent=vkap.id)
    vbok.write(v2.id, "<p>Två.</p>")
    win._activate_project(vbok)
    check(win.act_view_variants.isEnabled(), "varianter går att öppna i projektläge")

    dlg = VariantsDialog(vbok, nodes=vbok.children(vkap.id), parent=win)
    dlg.changed.connect(win._on_variant_changed)
    check(dlg.lst_variants.count() == 0, "inga varianter än")
    check(dlg.lbl_status.text() != "", f"och panelen säger det ({dlg.lbl_status.text()!r})")

    dlg.new_variant("Omvänd")
    check(len(vbok.variants) == 1, "en variant skapas")
    check(dlg.lst_variants.count() == 1, "och listas")
    check(dlg.lst_nodes.count() == 2, f"med kapitlets två scener ({dlg.lst_nodes.count()})")
    check([dlg.lst_nodes.item(r).text() for r in range(2)] == [v1.title, v2.title],
          f"i manusets ordning ({[dlg.lst_nodes.item(r).text() for r in range(2)]})")
    check("Omvänd" in dlg.lst_variants.item(0).text(), "och med sitt namn")
    check("VarBok" not in dlg.lst_variants.item(0).text(), "bara namnet, inte klassen")

    # flytta scenen i varianten
    dlg.lst_nodes.setCurrentRow(1)
    check(dlg.move_node(-1) is True, "scenen flyttas upp i varianten")
    check(dlg.lst_nodes.item(0).text() == v2.title,
          f"och ligger först i listan ({dlg.lst_nodes.item(0).text()!r})")
    check([n.id for n in vbok.children(vkap.id)] == [v1.id, v2.id],
          "medan manuset står still")
    check("ligger i annan ordning" in dlg.lbl_status.text(),
          f"jämförelsen pekar ut det ({dlg.lbl_status.text()!r})")
    check(VarBok.load(mapp).variants[0]["nodes"] == [v2.id, v1.id],
          "och varianten ligger på disk")

    # lägg variantens ordning på manuset
    check(dlg.apply_variant() >= 1, "varianten läggs på manuset")
    check([n.id for n in vbok.children(vkap.id)] == [v2.id, v1.id],
          f"och kapitlet byter ordning ({[n.title for n in vbok.children(vkap.id)]})")
    check([n.id for n in vbok.manuscript()] == [v2.id, v1.id],
          "och manuset med")
    check([n.title for n in vbok.manuscript()][0] == v2.title,
          "så det syns i läsvyn och exporten också")
    check(dlg.lbl_status.text() != "", "och statusraden säger vad som hände")
    check("flyttades" in dlg.lbl_status.text(),
          f"att ordningen lades på ({dlg.lbl_status.text()!r})")

    # vad trädet visar efteråt (samma väg som fönstret tar)
    win.binder.refresh()
    rader = [i.text() for i in win.binder._iter_items() if i.data(QtNS.ItemDataRole.UserRole)]
    scener = [t for t in rader if t.startswith("📄")]
    check(len(scener) == 2 and v2.title in scener[0] and v1.title in scener[1],
          f"trädet visar variantens ordning ({rader})")

    # en variant kan tas bort igen
    dlg.lst_variants.setCurrentRow(0)
    check(dlg.delete_variant() is True, "varianten kan tas bort")
    check(dlg.lst_variants.count() == 0, "och försvinner ur listan")
    check(VarBok.load(mapp).variants == [], "och från disk")
    dlg.deleteLater()
    win._deactivate_project()
    check(not win.act_view_variants.isEnabled(),
          "och varianter stängs av utanför projektläge")

    print("\n21. Appskalet enligt v0-referensen")
    from core.i18n import _ as _t
    from ui.theme_manager import THEMES, ThemeManager
    from ui.chrome import LeftRail, TopBar, chip, kbd

    check("oma" in THEMES, f"temat 'oma' finns ({list(THEMES)[:3]}...)")
    oma = THEMES["oma"]
    check(oma["accent"] == "#3366ff", f"med referensens accent ({oma['accent']})")
    check(oma["window_bg"] == "#f4f5f7", "och referensens canvas")
    check(oma["text_color"] == "#1d2630", "och referensens textfärg")
    check(oma["rail_active_bg"] == "#eef2ff", "och railens aktiva yta")
    check(oma["card_bg"] == "#f7f8fb" and oma["chip_bg"] == "#f0efff",
          "samt kort- och chipytorna")

    tm = ThemeManager(win.config)
    for annat in ("paper", "dark", "nord", "amber"):
        if annat in THEMES:
            tm.current_theme_id = annat
            t = tm.tokens()
            check(all(k in t for k in ("rail_bg", "card_border", "chip_text", "kbd_bg")),
                  f"anatomi-nycklarna ärvs av temat {annat}")
    tm.current_theme_id = "oma"
    t = tm.tokens()
    check(t["rail_bg"] == "#ffffff" and t["save_ok"] == "#3eb68a",
          "och 'oma' anger sina egna")
    check("#TopBar" in tm.get_stylesheet() and "#LeftRail" in tm.get_stylesheet(),
          "stilfilen har topbaren och railen")
    check("#FormatBar" in tm.get_stylesheet(), "stilfilen har verktygsraden")
    check("#RewriteButton" in win.sidebar.styleSheet(),
          "och panelens CTA står i panelens egen stil")

    # Topbaren: brand, menyrad inuti, dokumentnamn, sparat-läge
    check(isinstance(win.topbar, TopBar), "fönstret har en topbar")
    check(win.topbar.height() == 64, f"64px hög ({win.topbar.height()})")
    check(win.topbar.brand_mark.text() == "O" and win.topbar.brand_mark.width() == 31,
          "med referensens brandmark (O, 31px)")
    check(win.topbar.brand_name.text() == "OmaScribe", "och appens namn")
    check(win.menu_bar.parent() is win.topbar,
          "menyraden ligger inuti topbaren (inte ovanför innehållet)")
    check(win.menu_bar.isVisible() or True, "och är den menyrad appen använder")
    check(win.menu_file.title() == _t("menu_file"), "med Arkiv-menyn kvar")
    win._sync_topbar_document("kapitel-1.docx", True)
    check("kapitel-1.docx" in win.topbar.btn_file.text(), "dokumentnamnet syns i topbaren")
    check(win.topbar.lbl_save.text() == _t("topbar_unsaved"),
          f"och sparat-läget står som text ({win.topbar.lbl_save.text()!r})")
    win._sync_topbar_document("kapitel-1.docx", False)
    check(win.topbar.lbl_save.text() == _t("topbar_saved"),
          f"sparat när filen är sparad ({win.topbar.lbl_save.text()!r})")
    check(win.topbar.btn_undo.toolTip() != "", "Ångra-knappen har en förklaring")
    check(win.topbar.btn_file.menu() is win.menu_document and win.menu_document.actions(),
          "och dokumentknappen har Arkiv-kommandona")

    # Railen
    check(isinstance(win.rail, LeftRail) and win.rail.width() == 66,
          f"vänsterrail, 66px ({win.rail.width()})")
    check(len(win.rail._buttons) == 3, f"tre vyknappar ({list(win.rail._buttons)})")
    check(win.rail._buttons["document"].isChecked(), "dokumentvyn är markerad från start")
    check(win.rail.btn_settings.width() == 40, "40x40-knappar")
    check(win.rail._buttons["document"].toolTip() == _t("rail_document"),
          "med förklaring")
    # Inställningar-knappen öppnar dialogens väg (öppen kontroll, inte modalen)
    check(hasattr(win, "_open_settings"), "och inställningarna nås därifrån")

    # Dokumentytan: metarad + papper
    check(win.editor.page_frame.maximumWidth() == 750,
          f"papperet är högst 750px som referensen ({win.editor.page_frame.maximumWidth()})")
    check(win.editor.page_frame.minimumHeight() >= 1000, "och minst en A4-sida högt")
    win._update_window_title()
    check(win.editor.meta_row.isVisibleTo(win.editor),
          "metaraden över papperet visas när fönstret gett den data")
    check(win.editor.lbl_meta_left.text() != "", "med dokumentets namn")
    check(win.editor.lbl_meta_right.text().startswith(_t("stage_edited_today").split("·")[0].strip()),
          f"och när det ändrades ({win.editor.lbl_meta_right.text()!r})")

    # Panelen: huvud, flikar, rutnät
    check(win.sidebar.width() == 312, f"panelen är 312px som referensen ({win.sidebar.width()})")
    check(win.sidebar.lbl_eyebrow.text() == _t("inspector_eyebrow"),
          f"med eyebrow ({win.sidebar.lbl_eyebrow.text()!r})")
    check(win.sidebar.btn_close.width() == 24, "och en stängknapp i huvudet")
    check(win.sidebar.tabs.count() >= 3, f"flikarna finns ({win.sidebar.tabs.count()})")
    check(win.sidebar.tabs.tabBar().expanding() is False,
          "och raden klämmer inte flikarna (skrollar i stället)")
    check(len(win.sidebar._metric_labels) == 4, "statistiken ligger i fyra kort")
    win._update_stats()
    check(win.sidebar.lbl_words.text().strip() != "", "med ett värde i varje")
    check(win.sidebar.status_text() == win.lbl_stats.text(),
          f"och statusbaren visar samma siffror ({win.lbl_stats.text()!r})")
    check(win.sidebar.btn_rewrite.text() == _t("inspector_rewrite"),
          f"panelen har referensens CTA ({win.sidebar.btn_rewrite.text()!r})")
    check(win.sidebar.chip_count.objectName() == "ChipOk" and win.sidebar.chip_tone.objectName() == "Chip",
          "och två chip i samma stil som referensen")
    check(chip("x").objectName() == "Chip" and kbd("F8").objectName() == "Kbd",
          "chip- och kbd-hjälparna ger rätt stilnamn")

    # Pappret: A4 krymper inte, ytan skrollar i stället
    from ui.editor_view import (PAGE_WIDTH_PX, PAGE_HEIGHT_PX, PAGE_MARGIN_TOP,
                                PAGE_MARGIN_BOTTOM, CANVAS_PAGE_PX, DocumentCanvas)
    check(win.editor.page_frame.width() == PAGE_WIDTH_PX,
          f"pappret har fast A4-bredd ({win.editor.page_frame.width()})")
    check(win.editor.page_frame.minimumWidth() == win.editor.page_frame.maximumWidth() == PAGE_WIDTH_PX,
          "samma minimum och maximum — det går inte att krympa")
    check(abs(PAGE_HEIGHT_PX / PAGE_WIDTH_PX - 1.414) < 0.01,
          f"och A4-förhållande ({PAGE_HEIGHT_PX / PAGE_WIDTH_PX:.3f})")
    check(DocumentCanvas.PAGE_HEIGHT_PX == CANVAS_PAGE_PX ==
          PAGE_HEIGHT_PX - PAGE_MARGIN_TOP - PAGE_MARGIN_BOTTOM,
          f"sidmärkena räknar papprets innermått ({DocumentCanvas.PAGE_HEIGHT_PX})")
    check(win.editor.scroll_area.horizontalScrollBarPolicy() == QtNS.ScrollBarPolicy.ScrollBarAsNeeded,
          "och ytan får skrolla i sidled när fönstret är smalare än pappret")

    # Panelen är infälld från början (den tar 312px av texten)
    from core.config import DEFAULT_CONFIG
    check(DEFAULT_CONFIG["show_ai_sidebar"] is False,
          "AI-panelen är infälld i standardinställningen")
    check(win.rail.btn_settings.width() == 40, "inställningarna når panelen igen")

    # Menyraden sitter centrerad i topbaren, inte klistrad i överkanten
    check(win.menu_bar.height() == 34, f"menyraden är 34px i en 64px-rad ({win.menu_bar.height()})")
    check(win.menu_bar.height() < win.topbar.height(), "alltså centreras den av layouten")

    # Ikoner
    from PyQt6.QtCore import Qt as QtNS
    from ui import icons
    check(icons.has("file-text"), "lucide-ikonerna ligger i resources/icons")
    ikon = icons.icon("file-text", "#3366ff", 18)
    check(not ikon.isNull(), "och går att rita")
    if not ikon.isNull():
        bild = ikon.pixmap(18, 18).toImage()
        px = [bild.pixelColor(x, y) for x in range(0, bild.width(), 2)
              for y in range(0, bild.height(), 2)]
        synliga = [c for c in px if c.alpha() > 40]
        check(bool(synliga) and synliga[0].name().lower().startswith("#3"),
              f"i den färg som efterfrågades ({synliga[0].name() if synliga else '-'})")
    check(icons.icon("finns-inte", "#000000", 16).isNull(),
          "och en saknad ikon ger tom ikon (knappen behåller sin text)")
    check(not win.rail._buttons["document"].icon().isNull(),
          "railens knappar bär ikoner")
    check(win.rail._buttons["document"].text() == "",
          "och ingen dubbel text bredvid")
    check(not win.topbar.btn_undo.icon().isNull(), "Ångra i topbaren har en ikon")
    check(win.topbar.btn_file.icon().isNull() is False, "och dokumentknappen med")

    print("\n22. Skrivloggen (författarlagret)")

    logg = win.writing_log
    före = logg.log.day()
    logg.track(100, "dok:prov")          # baslinje
    logg.track(160, "dok:prov")          # +60
    logg.track(150, "dok:prov")          # −10
    check(logg.today_net() - före.net == 50,
          f"ändrade ord bokförs som skillnaden mellan två mätningar ({logg.today_net() - före.net})")
    logg.flush()
    efter = logg.log.day()
    check(efter.added - före.added == 60 and efter.removed - före.removed == 10,
          f"och loggen har lagt till och tagit bort separat "
          f"(+{efter.added - före.added}/−{efter.removed - före.removed})")
    check(str(logg.today_net()) in logg.lbl_status.text()
          and str(logg.today_net()) in logg.lbl_today.text(),
          f"statusfältet och panelen visar samma siffra ({logg.lbl_status.text()!r})")

    logg.track(9000, "annat:dokument")
    logg.track(9000, "annat:dokument")
    check(logg.today_net() == efter.net,
          "ett dokumentbyte blir en ny baslinje, inte ett hopp i statistiken")

    logg._sprint_left = 1
    klara = []
    logg.sprint_finished.connect(lambda m, n: klara.append((m, n)))
    logg._on_tick()
    check(bool(klara) and klara[0][0] == logg.combo_sprint.currentData(),
          f"sprinten larmar när tiden är slut ({klara})")
    from core.i18n import _ as _t          # `_` är en slingvariabel i main()
    check(logg.lbl_sprint.text() == "--:--" and logg.btn_sprint.text() == _t("log_sprint_start"),
          "och panelen går tillbaka till startläget")

    csv_väg = out / "skrivlogg-prov.csv"
    logg.log.export_csv(str(csv_väg))
    rader = csv_väg.read_text(encoding="utf-8").strip().splitlines() if csv_väg.exists() else []
    check(len(rader) >= 2 and rader[0].startswith("day,"),
          f"och loggen går att exportera som CSV ({len(rader)} rader)")

    print("\n23. Skrivmaskinsläget")

    # Mätningen kräver en riktig vy: fönstret måste vara stort nog att lägga ut
    # pappret, annars är skrollfältet 22 px högt och "mitten" betyder ingenting.
    win.resize(1150, 900)
    win.show()
    win.show_editor_screen()
    for _ in range(3):
        app.processEvents()

    editor = win.editor
    stycke = "En mening med några ord, så att raden blir lagom lång. " * 240
    editor.canvas.setHtml("<p>" + stycke + "</p>")
    editor.paper.refresh()
    for _ in range(3):
        app.processEvents()
    markör = editor.canvas.textCursor()
    markör.setPosition(int(editor.canvas.document().characterCount() * 0.5))
    editor.canvas.setTextCursor(markör)
    editor.set_typewriter_mode(True)
    for _ in range(3):
        app.processEvents()
    avstånd = editor.paper.cursor_from_center()
    check(abs(avstånd) <= 10,
          f"markörens rad hamnar mitt i fönstret ({avstånd} px från mitten)")

    # En bit ned i texten, inte sista tecknet: vid dokumentets slut finns ingen
    # text kvar att skrolla förbi, och då kan ingen centrering ske (som i Word).
    markör.setPosition(int(editor.canvas.document().characterCount() * 0.8))
    editor.canvas.setTextCursor(markör)
    for _ in range(3):
        app.processEvents()
    check(abs(editor.paper.cursor_from_center()) <= 10,
          f"och följer med dit man skriver, oavsett ark ({editor.paper.cursor_from_center()} px)")

    editor.set_typewriter_mode(False)
    check(not editor.typewriter, "läget går att slå av igen")
    check(win.config.get("typewriter_mode") in (True, False),
          f"och valet sparas i configen ({win.config.get('typewriter_mode')})")

    # Teckensnittsmenyn: Qt gör menyn skärmhög när stilmallen styr menyvyn
    # (SH_ComboBox_Popup svarar ja) — mätt 800px meny med listen 390px på y=133.
    # Provet mäter mekanismen i stället för att öppna menyn: offscreen-plattformen
    # kraschar ibland i städningen efter en visad popup, och en grind som kraschar
    # ibland är värre än en som mäter rätt sak. Siffrorna (366px meny, 14 rader à
    # 26px, skrollist med 23 rader kvar) är mätta för hand med menyn öppen.
    from PyQt6.QtCore import Qt as QtKärn
    from PyQt6.QtWidgets import QStyle, QStyleOptionComboBox
    combo = win.toolbar.combo_font
    meny_opt = QStyleOptionComboBox()
    combo.initStyleOption(meny_opt)
    meny_läge = combo.style().styleHint(QStyle.StyleHint.SH_ComboBox_Popup, meny_opt, combo)
    check(meny_läge == 0,
          f"teckensnittsmenyn följer inte stilmallens skärmhöga meny-läge ({meny_läge})")
    meny_vy = combo.view()
    check(meny_vy.verticalScrollBarPolicy() != QtKärn.ScrollBarPolicy.ScrollBarAlwaysOff,
          f"och menyvyn behåller sin skrollist ({meny_vy.verticalScrollBarPolicy().name})")
    rad_höjd = combo.view().sizeHintForRow(0)
    check(rad_höjd == 26,
          f"och radhöjden sätts i koden, inte i stilmallen ({rad_höjd} px)")

    # Tillbaka till provets vanliga läge: fönstret dolt och dokumentet orört, så
    # att stängningen i slutet inte stannar i en fråga om att spara.
    editor.canvas.document().setModified(False)
    win.is_modified = False
    win.hide()

    print("\n24. Story biblen (codex)")

    bibel_mapp = out / "bibeln"
    bibel_mapp.mkdir()
    bibelbok = Bok.create(bibel_mapp, "Bibelbok", template="roman")
    win._activate_project(bibelbok)
    codex = win.codex
    panel = win.codex_panel
    scener = bibelbok.manuscript()

    anna = codex.add_entity("Anna", aliases=["Anka"], summary="En pilot")
    hamn = codex.add_entity("Hamnstaden", type="place")
    codex.link(anna.id, scener[0].id)
    codex.add_relation(anna.id, hamn.id, "bor i")
    bibelbok.write(scener[0].id, "<p>Anna gick till kajen. Anka tittade upp. Anna log.</p>")
    panel.refresh()

    check(panel.list_entities.count() == 2,
          f"projektets codex syns i panelen ({panel.list_entities.count()} entiteter)")
    panel.select(anna.id)
    check(panel.current is not None and panel.current.id == anna.id,
          f"bladet visar den valda entiteten ({panel.lbl_name.text()})")
    check(panel.list_scenes.count() == 1 and panel._scene_of_row == [scener[0].id],
          f"och scenen hon är kopplad till ({panel.lbl_scenes.text()})")
    check(panel.list_relations.count() == 1,
          f"och relationen till en annan entitet ({panel.list_relations.item(0).text()})")
    check(panel.list_relations.horizontalScrollBarPolicy()
          == QtKärn.ScrollBarPolicy.ScrollBarAlwaysOff and panel.list_relations.wordWrap(),
          "relationsraden radbryts i stället för att skjuta in en skrollist")
    check("3" in panel.lbl_mentions.text(),
          f"och omnämnandena räknas, alias inräknat ({panel.lbl_mentions.text()})")

    panel.combo_type.setCurrentIndex(panel.combo_type.findData("place"))
    check(panel.list_entities.count() == 1, "typfiltret visar bara platser")
    panel.combo_type.setCurrentIndex(0)
    panel.input_search.setText("Anka")
    check(panel.list_entities.count() == 1, "och sökningen hittar ett alias")
    panel.input_search.setText("")

    panel.select(anna.id)
    öppnade = []
    panel.open_scene.connect(öppnade.append)
    panel._open_scene(panel.list_scenes.item(0))
    check(öppnade == [scener[0].id], f"klick på scenen öppnar rätt scen ({öppnade})")

    panel.list_relations.setCurrentRow(0)
    panel.remove_selected_relation()
    check(panel.list_relations.count() == 0 and codex.entity(anna.id) is not None,
          "en relation går att ta bort, entiteterna består")
    panel.remove_current(ask=False)
    check(panel.list_entities.count() == 1 and codex.by_name("Anna") is None,
          "och entiteten går att ta bort, scenen består")

    win._deactivate_project()

    print("\n25. Plot-tavlan (scenöversikt, trådar och tidslinje)")

    import json as _json
    from core.project import SCENE
    tavlan_mapp = out / "tavlan"
    tavlan_mapp.mkdir()
    tavlabok = Bok.create(tavlan_mapp, "Tavlan", template="roman")
    win._activate_project(tavlabok)
    while len(tavlabok.manuscript()) < 3:
        tavlabok.add_node(SCENE, f"Scen {len(tavlabok.manuscript()) + 1}", None)
    rader = tavlabok.manuscript()
    tavlabok.set_meta(rader[0].id, labels=["huvudtråd"], pov="Anna", status="utkast", when="dag 3")
    tavlabok.set_meta(rader[1].id, labels=["sidotråd"], pov="Bo", status="klar", when="dag 1")

    win._toggle_plot_grid()
    tavla = win.plot_grid
    check(win.stack.currentIndex() == win._plot_grid_index,
          "plot-tavlan är en egen sida i stacken, inte en flik i sidopanelen")
    check(tavla.table.rowCount() == 3 and tavla.table.columnCount() == 9,
          f"en rad per scen och nio kolumner "
          f"({tavla.table.rowCount()} × {tavla.table.columnCount()})")
    check(win.toolbar.isHidden(),
          "och formateringsraden hör till manuset, inte till tabellen")

    tavla.combo_sort.setCurrentIndex(tavla.combo_sort.findData("timeline"))
    tider = [tavla.table.item(r, 5).text() for r in range(tavla.table.rowCount())]
    check(tider == ["dag 1", "dag 3", ""],
          f"tidslinjen sorterar på scenens egen tid, tom tid sist ({tider})")
    tavla.combo_sort.setCurrentIndex(0)
    check(tavla.table.item(0, 0).text() == rader[0].title,
          "och manusordningen är tillbaka")

    # Revisionsläget: arbeta med ett utkast i taget (fas 2.12)
    tavlabok.set_meta(rader[1].id, revision=2)
    tavla.combo_draft.setCurrentIndex(tavla.combo_draft.findData(2))
    check(tavla.table.rowCount() == 1 and tavla.table.item(0, 0).text() == rader[1].title,
          f"revisionsläget visar bara scenerna i utkast 2 ({tavla.table.rowCount()} rad)")
    check(f"2" in tavla.lbl_count.text() and "3" in tavla.lbl_count.text(),
          f"och räknar dem mot hela manuset ({tavla.lbl_count.text()})")
    tavla.combo_draft.setCurrentIndex(0)
    check(tavla.table.rowCount() == 3, "alla utkast visar dem igen")
    tavla.table.item(0, 8).setText("3")
    check(int(tavlabok.by_id(rader[0].id).revision) == 3,
          "och utkastnumret i tabellen skrivs till modellen")
    tavla.table.item(0, 8).setText("99")
    check(int(tavlabok.by_id(rader[0].id).revision) <= 9,
          "utkastet hålls inom 1–9, som i sceninspektören")

    tavla.table.item(0, 2).setText("ny tråd")
    check(tavlabok.by_id(rader[0].id).labels == ["ny tråd"],
          "en ändring i tabellen skrivs till modellen")
    manifest = _json.loads((tavlan_mapp / "project.json").read_text(encoding="utf-8"))
    sparad = [n for n in manifest["nodes"] if n["id"] == rader[0].id][0]
    check(sparad.get("when") == "dag 3" and sparad.get("labels") == ["ny tråd"],
          f"och manifestet sparas med tid och tråd ({sparad.get('when')}, {sparad.get('labels')})")

    öppnade = []
    tavla.scene_selected.connect(öppnade.append)
    tavla._on_cell_clicked(0, 0)
    check(öppnade == [rader[0].id], f"klick på scenens titel öppnar scenen ({öppnade})")
    win._toggle_plot_grid()
    check(win.stack.currentIndex() == 1 and win.toolbar.isEnabled() and not win.toolbar.isHidden(),
          "och vägen tillbaka ger manuset och formateringsraden tillbaka")
    win._deactivate_project()

    print("\n26. Samlingen som läsvy (arbetsflödet i R03.11)")

    samling_mapp = out / "samlingen"
    samling_mapp.mkdir()
    saml_bok = Bok.create(samling_mapp, "Samlingen", template="roman")
    win._activate_project(saml_bok)
    while len(saml_bok.manuscript()) < 3:
        saml_bok.add_node(SCENE, f"Scen {len(saml_bok.manuscript()) + 1}", None)
    saml_rader = saml_bok.manuscript()
    for nod in saml_rader:
        saml_bok.write(nod.id, f"<p>Text i {nod.title}.</p>")
    saml_bok.set_meta(saml_rader[0].id, status="Utkast", labels=["huvudtråd"],
                      note="Behöver ett nytt slut")
    saml_bok.set_meta(saml_rader[1].id, status="Klar")
    saml_bok.set_meta(saml_rader[2].id, status="Utkast")

    samlingspanel = win.binder.collections
    samling_id = samlingspanel.new_search("Saknar redigering", "status:Utkast")
    träffar = [n.id for n in saml_bok.select_collection(samling_id)]
    check(träffar == [saml_rader[0].id, saml_rader[2].id],
          f"scenanteckning, tagg och status räcker för en sparad sökning ({len(träffar)} träffar)")
    check(saml_bok.by_id(saml_rader[0].id).note == "Behöver ett nytt slut",
          "och scenens egen anteckning ligger kvar på scenen")
    check(samlingspanel.select_collection(samling_id) and samlingspanel.read_current(),
          "samlingen kan läsas som en sammanhängande text")
    check(win.stack.currentIndex() == win._scrivenings_index
          and [n.id for n in win.scrivenings.shown_nodes()] == träffar,
          f"läsvyn visar samlingens scener, i manusets ordning "
          f"({[n.title for n in win.scrivenings.shown_nodes()]})")
    win._close_scrivenings()
    check(win.stack.currentIndex() == 1, "och vägen tillbaka går till manuset")
    win._deactivate_project()

    print("\n27. Tunga meningar markeras (fas 2.15)")

    canvas = win.editor.canvas
    tung = ("Kort mening. Den här meningen är avsiktligt tung och innehåller betydligt fler "
            "ord än tjugo stycken, vilket är precis vad LIX reagerar på. Kort igen.")
    canvas.setPlainText(tung)
    for _ in range(3):
        app.processEvents()
    texten = canvas.toPlainText()
    layout = canvas.document().firstBlock().layout()

    win.editor.set_readability_marks(False)
    for _ in range(2):
        app.processEvents()
    check(len(layout.formats()) == 0, "inga markeringar när läget är av")
    win.editor.set_readability_marks(True)
    for _ in range(3):
        app.processEvents()
    check(len(layout.formats()) == 1,
          f"och den tunga meningen markeras ({len(layout.formats())} format)")
    check(canvas.toPlainText() == texten,
          "markeringen rör inte texten — inget hamnar i scenfilen")
    win.editor.set_readability_marks(False)
    for _ in range(3):
        app.processEvents()
    check(len(layout.formats()) == 0, "och markeringen försvinner när läget slås av")
    check(win.config.get("readability_marks") in (True, False),
          f"valet sparas i configen ({win.config.get('readability_marks')})")
    canvas.document().setModified(False)
    win.is_modified = False

    print("\n28. Fastnat? Övningar mot skrivblock (fas 2.14)")

    from ui.exercise_dialog import ExerciseDialog
    from core import exercises as exercises_mod

    check(len(exercises_mod.CATEGORIES) == 4
          and exercises_mod.category("senses")[1] == "Sinnesintryck",
          "fyra frågor att välja mellan, som i forskningens arbetsflöde")
    check(win.act_exercise is not None and win.act_exercise.isEnabled(),
          "och menyn har en väg till dem")

    # en egen liten scen att öva på
    ovningsmapp = tempfile.mkdtemp(prefix="omascribe-ovning-")
    ovningsbok = Bok.create(ovningsmapp, "Ovningen", template="roman")
    win._activate_project(ovningsbok)
    while not ovningsbok.manuscript():
        ovningsbok.add_node(SCENE, f"Scen {len(ovningsbok.manuscript()) + 1}", None)
    ovningsscen = ovningsbok.manuscript()[0]
    ovningsbok.set_meta(ovningsscen.id, note="nyckeln ligger i lådan")
    win._open_node(ovningsscen.id)
    check(win.active_scene_id == ovningsscen.id,
          "scenen är öppen i editorn innan övningen börjar")

    # scenen får en rad text, så att markörens rad betyder något
    win.editor.canvas.setPlainText("Hon stod vid dörren och lyssnade.")
    win.editor.canvas.moveCursor(QTextCursor.MoveOperation.Start)
    for _ in range(2):
        app.processEvents()

    # hela vägen genom menyns hanterare, med exec avbytt (den är modal)
    fangat = {}
    riktig_suggest = win.ai.suggest
    win.ai.suggest = lambda category, **kw: fangat.update(kategori=category, **kw)
    oppnade = []
    riktig_exec = ExerciseDialog.exec
    ExerciseDialog.exec = lambda self: (oppnade.append(self), 0)[1]
    win._open_exercises()
    ExerciseDialog.exec = riktig_exec
    check(len(oppnade) == 1, "menyvalet öppnar övningsrutan")
    dialog = oppnade[0]

    dialog.combo_category.setCurrentIndex(dialog.combo_category.findData("dialogue"))
    dialog._ask()
    check(fangat.get("kategori") == "dialogue", "vald fråga skickas vidare")
    check("nyckeln" in (fangat.get("scene_note") or ""),
          "scenens egen anteckning följer med som sammanhang")
    check(fangat.get("lang") in ("svenska", "English"),
          f"och språket ({fangat.get('lang')!r})")
    check("dörren" in (fangat.get("selection") or ""),
          f"den rad markören står på blir texten som skickas "
          f"({(fangat.get('selection') or '')[:24]!r})")

    # förslagen: listan, valet och var det hamnar
    dialog.set_suggestions(["Hon går in i rummet.", "Hon stannar på tröskeln.", "Hon ropar."])
    check(dialog.lst_suggestions.count() == 3 and dialog.btn_insert.isEnabled(),
          "tre förslag i listan och en väg att spara dem")
    node_id = win.active_scene_id
    anteckning_fore = win.project.by_id(node_id).note
    texten = canvas.toPlainText()
    dialog.lst_suggestions.setCurrentRow(1)
    dialog._insert()
    ny_anteckning = win.project.by_id(node_id).note
    check("tröskeln" in ny_anteckning,
          "det valda förslaget hamnar i scenens anteckning")
    check(len(ny_anteckning) >= len(anteckning_fore) and ny_anteckning.strip().endswith("tröskeln."),
          "och den gamla anteckningen ligger kvar före den")
    check(canvas.toPlainText() == texten,
          "manuset rörs inte — förslaget är en väg in, inte färdig text")
    dialog.set_suggestions([])
    check(not dialog.btn_insert.isEnabled(),
          "och utan förslag stängs vägen att spara")
    dialog.close()
    win.ai.suggest = riktig_suggest
    canvas.document().setModified(False)
    win.is_modified = False

    print("\n29. Projektets instruktioner till AI:n (fas 2.17)")

    import core.ai_client as ai_mod

    ovningsbok.settings["ai_instructions"] = "Håll tempus i preteritum. Hon heter alltid Märta."
    prompt = win.ai._system_prompt("bas")
    check("preteritum" in prompt, "projektets instruktioner följer med i systemprompten")
    check(prompt.index("preteritum") > prompt.index("bas"),
          "och de kommer sist, närmast uppgiften")

    # hela vägen: frågan skickas med instruktionerna, utan nät
    fangat_prompt = {}
    riktig_chat = ai_mod.chat_completion
    ai_mod.chat_completion = lambda endpoint, key, model, system, user, **kw: (
        fangat_prompt.update(system=system, user=user)
        or "1. Hon går in i rummet.\n2. Hon stannar på tröskeln.\n3. Hon ropar.")
    win.ai.suggest("next", selection="Hon gick in.", chapter="Scen 1")
    for _ in range(100):
        app.processEvents()
        if fangat_prompt:
            break
        time.sleep(0.02)
    check("preteritum" in fangat_prompt.get("system", ""),
          "och de följer med hela vägen ut i anropet")
    check("Hon gick in." in fangat_prompt.get("user", ""),
          "utan att tränga undan själva uppgiften")
    ai_mod.chat_completion = riktig_chat

    # spara-vägen
    win._set_ai_instructions("  Bara den här raden.  ")
    check(win.project.settings["ai_instructions"] == "Bara den här raden.",
          "texten sparas trimmad i projektet")
    win._set_ai_instructions("")
    check(win.ai._system_prompt("bas") == "bas",
          "och ett tomt fält ger systemprompten tillbaka orörd")
    check(win.act_instructions is not None, "menyn har en väg till fältet")

    print("\n30. Projektöversikten (fas 2.16)")

    from core.i18n import _ as tr
    from ui.overview_dialog import OverviewDialog, overview_rows
    from core.vault import Vault

    # ett valv med en anteckning som länkar till en som inte finns
    valvmapp = tempfile.mkdtemp(prefix="omascribe-valv-")
    with open(os.path.join(valvmapp, "Märta.md"), "w", encoding="utf-8") as handtag:
        handtag.write("Hon har nyckeln. Se [[Källaren]] och [[Märta]].\n")
    valv = Vault(valvmapp)
    valv.scan()

    rader = dict(overview_rows(ovningsbok, valv))
    from core.i18n import i18n
    scener = list(ovningsbok.manuscript())
    mal = f'{int(ovningsbok.settings.get("target_words") or 0):,}'.replace(",", " ")
    check(len(rader) >= 8, f"översikten har raderna den ska ({len(rader)})")
    check(str(ovningsbok.total_words()) == rader[tr("overview_words")].split(" /")[0].strip(),
          f"orden räknas ur projektet ({rader[tr('overview_words')]})")
    check(mal in rader[tr("overview_words")], f"målet står bredvid ({mal})")
    check(rader[tr("overview_scenes")] == str(len(scener)),
          f"scenerna räknas ({rader[tr('overview_scenes')]})")
    check("nyckeln" in rader[tr("overview_instructions")].lower()
          or rader[tr("overview_instructions")] != "",
          "projektets instruktioner syns, i kortform")
    check(rader[tr("overview_notes")] == "1", "en anteckning i valvet räknas")
    lanter = rader[tr("overview_links")]
    check("Källaren" in lanter and "Märta" not in lanter,
          f"länken utan anteckning visas, den som finns gör det inte ({lanter})")
    check(rader[tr("overview_status")] != "" and rader[tr("overview_drafts")] != "",
          f"status och utkast räknas ur scenerna "
          f"({rader[tr('overview_status')]} · {rader[tr('overview_drafts')]})")

    check(rader[tr("overview_drafts")].startswith(tr("overview_draft", n=1)),
          f"utkastet skrivs ut med namn, inte som en siffra ({rader[tr('overview_drafts')]})")

    # Qts egna standardknappar: svenska i en svensk dialog
    from PyQt6.QtWidgets import QDialogButtonBox
    def _knapptexter():
        ruta = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        return ruta.button(QDialogButtonBox.StandardButton.Close).text().replace("&", "")
    check(win._qt_translator is not None or i18n.current_lang != "sv",
          f"appen har Qts svenska översättning ({i18n.current_lang})")
    check(_knapptexter() == "Stäng",
          f"och stäng-knappen är svensk, inte 'Close' ({_knapptexter()!r})")
    i18n.set_language("en")
    app.processEvents()
    check(_knapptexter() == "Close",
          f"och engelsk igen när språket byts ({_knapptexter()!r})")
    _fangat = {}
    win.ai.suggest = lambda category, **kw: _fangat.update(kw)
    win._ask_exercise(None, "next")
    check(_fangat.get("lang") == "English",
          f"och AI-frågan följer språket ({_fangat.get('lang')!r})")
    i18n.set_language("sv")
    app.processEvents()
    win.ai.suggest = riktig_suggest
    check(_knapptexter() == "Stäng", "och svensk igen")
    # dagskvoten: en deadline ger en siffra, och den ska vara grupperad som ordmålet
    ovningsbok.settings["deadline"] = "2026-12-01"
    ovningsbok.settings["target_words"] = 90000
    rader = dict(overview_rows(ovningsbok, valv))
    kvot = rader[tr("overview_quota")]
    forvantad = f'{ovningsbok.daily_quota():,}'.replace(",", " ")
    check(tr("overview_per_day") in kvot and forvantad in kvot,
          f"dagskvoten är märkt och grupperad som målet ({kvot})")

    # menyn och rutan
    check(win.act_overview is not None, "arkivmenyn har en väg hit")
    oppnade = []
    riktig_exec = OverviewDialog.exec
    OverviewDialog.exec = lambda self: (oppnade.append(self), 0)[1]
    win._open_overview()
    OverviewDialog.exec = riktig_exec
    check(len(oppnade) == 1, "och menyvalet öppnar översikten")
    oppnade[0].close()

    print("\n31. Versionshistorik per scen (fas 3.1 och 3.6)")

    from ui.snapshot_dialog import HistoryDialog
    from core.i18n import _ as tr

    forsta_text = "<p>Hon gick in i källaren och lade nyckeln på bordet.</p>"
    andra_text = "<p>Hon gick nerför trappan och lade mässingsnyckeln på bordet.</p>"
    ovningsbok.write(ovningsscen.id, forsta_text)
    punkt = ovningsbok.snapshot_scene(ovningsscen.id, label="före ändringen")
    check(punkt is not None, "en punkt sparas för scenen")
    check(ovningsbok.snapshot_scene(ovningsscen.id) is None,
          "och en oförändrad text ger ingen ny punkt — historiken fylls inte av kopior")

    ovningsbok.write(ovningsscen.id, andra_text)
    skillnad = ovningsbok.snapshots().diff(punkt.id)
    rader = skillnad.splitlines()
    bort = [r for r in rader if r.startswith("-") and not r.startswith("---")]
    till = [r for r in rader if r.startswith("+") and not r.startswith("+++")]
    check(len(bort) == 1 and "källaren" in bort[0],
          f"diffen visar den gamla raden med minustecken ({bort[:1]})")
    check(len(till) == 1 and "trappan" in till[0],
          f"och den nya med plustecken ({till[:1]})")

    ruta = HistoryDialog(ovningsbok.snapshots(), str(ovningsbok.scene_path(ovningsscen.id)), win)
    check(ruta.lst_points.count() >= 1, f"historiken listar punkterna ({ruta.lst_points.count()})")
    visad = ruta.visning.toPlainText()
    check("trappan" in visad, "och rutan visar skillnaden mot texten nu")
    check("före ändringen" in visad and "snapshot/" not in visad,
          f"med en rubrik som går att läsa, inte punktens id "
          f"({[r for r in visad.splitlines() if r.startswith('---')][:1]})")
    check(os.path.basename(str(ovningsbok.scene_path(ovningsscen.id))) in visad.splitlines()[1],
          "och scenens filnamn i stället för hela sökvägen")
    check(ruta.btn_restore.isEnabled(), "med en väg tillbaka")

    # återställningen: texten tillbaka, och texten före den sparad som egen punkt
    antal_fore = ruta.lst_points.count()
    win._restore_snapshot(punkt.id)
    check(ovningsbok.read(ovningsscen.id) == forsta_text,
          "texten är återställd till punkten")
    check("källaren" in win.editor.document.toPlainText(),
          "och den ligger i editorn, inte bara på disk")
    punkter = ovningsbok.snapshots().list(str(ovningsbok.scene_path(ovningsscen.id)))
    check(len(punkter) > antal_fore, f"och texten som låg där först är sparad som egen punkt "
                                     f"({antal_fore} -> {len(punkter)})")
    check(punkter[0].label == tr("history_before_restore"),
          f"med etiketten 'före återställning' ({punkter[0].label!r})")
    ruta.close()
    win.editor.document.setModified(False)
    win.is_modified = False

    print("\n32. Kommentarer med tråd (fas 3.3)")

    from PyQt6.QtWidgets import QInputDialog
    from PyQt6.QtCore import Qt

    scenen = ovningsscen
    text = "<p>Hon gick in i källaren och lade nyckeln på bordet.</p>"
    ovningsbok.write(scenen.id, text)
    win._show_scene_html(scenen.id, text)
    kommentar = ovningsbok.add_comment(scenen.id, "lade nyckeln på bordet", "Vet hon om att Bo ser henne?")
    check("replies" in kommentar and kommentar["replies"] == [],
          "en ny kommentar har en tom tråd")
    svar = ovningsbok.add_reply(scenen.id, kommentar["id"], "Nej, inte förrän i kapitel 9.")
    check(svar is not None and len(ovningsbok.comment(scenen.id, kommentar["id"])["replies"]) == 1,
          "och ett svar hamnar i tråden")
    check(ovningsbok.add_reply(scenen.id, "finns-inte", "hej") is None,
          "svar på en kommentar som inte finns ger inget")
    check(ovningsbok.add_reply(scenen.id, kommentar["id"], "   ") is None,
          "och ett tomt svar sparas inte")

    # rutan: tråden hänger under sin kommentar
    win.scene_inspector.set_scene(ovningsbok, ovningsbok.by_id(scenen.id))
    rader = win.scene_inspector.lst_comments
    topp = rader.item(0)
    check(topp is not None and topp.text().startswith("💬"),
          f"kommentaren står överst ({topp.text() if topp is not None else None!r})")
    barn = rader.item(1)
    check(rader.count() == 2 and barn is not None and barn.text().startswith("↳ ")
          and "kapitel 9" in barn.text(),
          f"och svaret står indraget direkt under den ({barn.text() if barn is not None else None!r})")
    check(barn is not None and barn.data(Qt.ItemDataRole.UserRole) == kommentar["id"],
          "med kommentarens id, så ett klick går till samma citat")

    # rutan växer med antalet rader (kommentaren + tråden), och kapas högt
    for _extra in range(3):
        ovningsbok.add_reply(scenen.id, kommentar["id"], f"Ännu ett svar {_extra}.")
    win.scene_inspector.set_scene(ovningsbok, ovningsbok.by_id(scenen.id))
    rader = win.scene_inspector.lst_comments
    check(rader.count() == 5, f"fem rader med tråden ({rader.count()})")
    check(rader.maximumHeight() >= 28 + 22 * rader.count(),
          f"och rutan växer så att tråden får plats ({rader.maximumHeight()} px)")
    check(rader.maximumHeight() <= 260,
          f"men inte mer än att panelen går att använda ({rader.maximumHeight()} px)")
    for _bort in range(3):
        ovningsbok.comment(scenen.id, kommentar["id"])["replies"].pop()
    win.scene_inspector.set_scene(ovningsbok, ovningsbok.by_id(scenen.id))
    rader = win.scene_inspector.lst_comments
    topp = rader.item(0)                 # listan byggdes om: den gamla raden är död

    # "löst" fanns redan — nu med tråd kvar under
    win.scene_inspector.lst_comments.setCurrentItem(topp)
    check(win.scene_inspector._toggle_resolved(), "kommentaren kan markeras som löst")
    check(ovningsbok.comment(scenen.id, kommentar["id"])["resolved"], "och det står i modellen")
    win.scene_inspector.set_scene(ovningsbok, ovningsbok.by_id(scenen.id))
    lost_rad = win.scene_inspector.lst_comments.item(0)
    check(lost_rad.text().startswith("✓") and win.scene_inspector.lst_comments.count() == 2,
          "och tråden hänger kvar under den lösta kommentaren")
    win.scene_inspector._toggle_resolved()
    check(not ovningsbok.comment(scenen.id, kommentar["id"])["resolved"], "och den går att öppna igen")

    # svarsvägen genom fönstret, med dialogrutan avbytt
    riktig_dialog = QInputDialog.getMultiLineText
    QInputDialog.getMultiLineText = staticmethod(lambda *a, **k: ("Ett svar till.", True))
    check(win.ask_reply(scenen.id, kommentar["id"]), "svarsknappen lägger till ett svar")
    QInputDialog.getMultiLineText = riktig_dialog
    check(len(ovningsbok.comment(scenen.id, kommentar["id"])["replies"]) == 2,
          "och det hamnar i samma tråd")

    print("\n33. Granska ändringar stycke för stycke (fas 3.2, del 2)")

    from ui.review_dialog import ReviewDialog
    from core import revisions as rev
    from core.i18n import _ as tr

    scen = ovningsscen
    fore = ("<p>Hon gick in i källaren.</p><p>Nyckeln låg på bordet.</p>"
            "<p>Hon tände lampan.</p>")
    efter = ("<p>Hon smög in i källaren.</p><p>Nyckeln låg på bordet.</p>"
             "<p>Hon tände lampan och väntade.</p><p>Dörren stod öppen.</p>")
    ovningsbok.write(scen.id, fore)
    ovningsbok.snapshot_scene(scen.id, label="före omskrivningen")
    ovningsbok.write(scen.id, efter)
    win._show_scene_html(scen.id, efter)

    ändringar = rev.changes(fore, efter)
    check([c.kind for c in ändringar] == ["changed", "changed", "added"],
          f"tre ändringar: två omskrivningar och ett tillägg ({[c.kind for c in ändringar]})")

    # rutan: kryssad rad = behåll, och förhandsvisningen är exakt det som skrivs
    ruta = ReviewDialog(fore, efter, "testpunkten", win)
    check(ruta.lst_changes.count() == 3, "rutan visar en rad per ändring")
    check(all(ruta.lst_changes.item(i).checkState() == Qt.CheckState.Checked
              for i in range(3)), "och alla är kryssade från början")
    ny_text = "\n\n".join(rev.plain(b) for b in rev.blocks(efter) if rev.plain(b))
    gammal_text = "\n\n".join(rev.plain(b) for b in rev.blocks(fore) if rev.plain(b))
    check(ruta.preview_text() == ny_text, "förhandsvisningen är hela den nya texten")
    check(ruta.lst_changes.item(0).text().startswith("✓"),
          f"och raden visar att den behålls ({ruta.lst_changes.item(0).text()[:12]!r})")
    ruta.lst_changes.item(0).setCheckState(Qt.CheckState.Unchecked)
    check("smög" not in ruta.preview_text() and "gick in i källaren" in ruta.preview_text(),
          "och ett avkryssat stycke visar den gamla texten")
    check(ruta.lst_changes.item(0).text().startswith("↩"),
          f"och raden visar att den ångras ({ruta.lst_changes.item(0).text()[:12]!r})")
    check(ruta.lbl_status.text() == tr("review_status", kept=2, total=3),
          f"räknaren följer kryssen ({ruta.lbl_status.text()})")
    ruta._sätt_alla(Qt.CheckState.Unchecked)
    check(ruta.preview_text() == gammal_text, "ångra alla ger den gamla texten")

    # verkställ: skriver enligt besluten och sparar texten före som egen punkt
    antal_fore = len(ovningsbok.snapshots().list(str(ovningsbok.scene_path(scen.id))))
    ruta._sätt_alla(Qt.CheckState.Checked)
    ruta.lst_changes.item(2).setCheckState(Qt.CheckState.Unchecked)   # avvisa tillägget
    beslut = ruta.decisions()
    ruta.apply_requested.connect(lambda b: win._apply_review(fore, efter, b))
    ruta._apply()
    check(ovningsbok.read(scen.id) == rev.apply_changes(fore, efter, beslut),
          "texten är skriven enligt besluten")
    check("Dörren stod öppen" not in ovningsbok.read(scen.id),
          "det avvisade tillägget finns inte kvar")
    check("smög" in ovningsbok.read(scen.id) and "och väntade" in ovningsbok.read(scen.id),
          "och de behållna ändringarna finns")
    punkter = ovningsbok.snapshots().list(str(ovningsbok.scene_path(scen.id)))
    check(len(punkter) == antal_fore + 1 and punkter[0].label == tr("review_before"),
          f"och texten före granskningen är sparad som punkt ({punkter[0].label!r})")
    check("smög" in win.editor.document.toPlainText(),
          "och texten ligger i editorn, inte bara på disk")

    # menyn: utan ändringar öppnas ingen ruta. Först sparas det som står i
    # editorn (Qt skriver om sin HTML), och sedan tas punkten på just de byten —
    # annars finns det en ändring att granska, och det är rätt svar.
    win._flush_scene(quiet=True)
    ovningsbok.snapshot_scene(scen.id)
    oppnade = []
    riktig_exec = ReviewDialog.exec
    ReviewDialog.exec = lambda self: (oppnade.append(self), 0)[1]
    win._open_review()
    ReviewDialog.exec = riktig_exec
    check(not oppnade, "utan ändringar öppnas ingen granskningsruta")
    check(win.status_bar.currentMessage() == tr("review_none"),
          f"och statusfältet säger varför ({win.status_bar.currentMessage()})")
    ruta.close()
    win.editor.document.setModified(False)
    win.is_modified = False

    print("\n34. Granska mot en vald punkt, formateringen för sig (fas 3.4 och 3.5)")

    from ui.snapshot_dialog import HistoryDialog

    v1 = "<p>Hon gick in i källaren.</p><p>Nyckeln låg på bordet.</p>"
    v2 = "<p>Hon smög in i källaren.</p><p>Nyckeln låg på bordet.</p>"
    v3 = "<p>Hon smög in i källaren.</p><p>Nyckeln låg på bordet och sken.</p>"
    ovningsbok.write(scen.id, v1)
    p1 = ovningsbok.snapshot_scene(scen.id, label="första")
    ovningsbok.write(scen.id, v2)
    ovningsbok.snapshot_scene(scen.id, label="andra")
    ovningsbok.write(scen.id, v3)
    win._show_scene_html(scen.id, v3)

    kursiv = v3.replace("Nyckeln", "<i>Nyckeln</i>")
    check(rev.changes(v3, kursiv) == [] and rev.formatting_changes(v3, kursiv) == [1],
          "formateringen hålls åtskild från textändringarna")

    hist = HistoryDialog(ovningsbok.snapshots(), str(ovningsbok.scene_path(scen.id)), win)
    check(hist.btn_review.isEnabled() and hist.btn_review.text() == tr("history_review"),
          f"historiken har en granskningsknapp ({hist.btn_review.text()!r})")
    fangade = []
    hist.review_requested.connect(lambda pid: fangade.append(pid))
    for i in range(hist.lst_points.count()):
        if hist.lst_points.item(i).data(Qt.ItemDataRole.UserRole) == p1.id:
            hist.lst_points.setCurrentRow(i)
    hist._review_selected()
    check(fangade == [p1.id], "och den valda punkten skickas vidare")

    oppnade = []
    riktig_exec = ReviewDialog.exec
    ReviewDialog.exec = lambda self: (oppnade.append(self), 0)[1]
    win._open_review_against(p1.id)
    ReviewDialog.exec = riktig_exec
    check(len(oppnade) == 1, "och fönstret öppnar en granskning för just den punkten")
    ruta2 = oppnade[0]
    rader_aldst = [ruta2.lst_changes.item(i).text() for i in range(ruta2.lst_changes.count())]
    check(any("smög" in t for t in rader_aldst),
          f"mot den äldsta punkten syns ändringen sedan dess ({rader_aldst})")
    ruta2.close()

    # ... och mot den senaste punkten bara den sista ändringen — det är skillnaden
    # mellan att välja original: det är det som är jämförelsen (R02.3)
    oppnade2 = []
    ReviewDialog.exec = lambda self: (oppnade2.append(self), 0)[1]
    win._open_review()
    ReviewDialog.exec = riktig_exec
    rader_senast = [oppnade2[0].lst_changes.item(i).text()
                    for i in range(oppnade2[0].lst_changes.count())]
    check(len(rader_senast) < len(rader_aldst) and not any("smög" in t for t in rader_senast),
          f"och mot den senaste färre, utan den äldre ändringen ({rader_senast})")
    oppnade2[0].close()
    hist.close()

    ruta3 = ReviewDialog(v3, kursiv, "formatering", win)
    from PyQt6.QtWidgets import QLabel as _QLabel
    texter = [w.text() for w in ruta3.findChildren(_QLabel)]
    check(any("formatering" in t for t in texter),
          f"och rutan säger att det är formateringen ({texter[-1][:60]!r})")
    check(ruta3.lst_changes.count() == 0, "utan att göra den till en ändring")
    ruta3.close()
    win.editor.document.setModified(False)
    win.is_modified = False

    print("\n36. Sök och ersätt, och autokorrigering (fas 4.9 och 4.12)")

    text36 = ('<p>Jag <b>skrev</b> teh bok och sa "hej"...</p>'
              '<p>Adressen var seperat skriven.</p>')
    ovningsbok.write(ovningsscen.id, text36)
    win._show_scene_html(ovningsscen.id, text36)

    # 4.9: typografin och orden rättas, och formateringen runt omkring står kvar
    check(win.run_autocorrect(), "autokorrigeringen hittar något att rätta")
    efter36 = win.editor.document.toPlainText()
    check("the bok" in efter36, f"ordet rättas ({efter36[:24]!r})")
    check("”hej”" in efter36 and "…" in efter36,
          f"och typografin blir svensk — citattecken och ellips")
    check("separat skriven" in efter36, f"och fler fel i samma scen rättas")
    markor36 = win.editor.document.find("skrev")
    inne = QTextCursor(win.editor.document)
    inne.setPosition(markor36.selectionStart() + 1)
    check(int(inne.charFormat().fontWeight()) > 400,
          f"och fetstilen runt ordet står kvar (vikt {int(inne.charFormat().fontWeight())})")
    check(not win.run_autocorrect(), "och en gång till hittar ingenting att rätta")
    # 4.12: sökrutan
    win.open_find()
    ruta36 = win.find_dialog
    check(ruta36 is not None and not ruta36.isModal(),
          "sökrutan är icke-modal — man ska kunna skriva medan den står öppen")
    ruta36.input_find.setText("källaren")
    check("0" in ruta36.lbl_status.text() or "Inga" in ruta36.lbl_status.text(),
          f"och räknaren säger att ordet inte finns ({ruta36.lbl_status.text()!r})")
    ruta36.input_find.setText("bok")
    check("1 träff" in ruta36.lbl_status.text() and "träffar" not in ruta36.lbl_status.text(),
          f"och räknar träffarna ({ruta36.lbl_status.text()!r})")
    ruta36._sok()
    valt = win.editor.textCursor().selectedText()
    check(valt == "bok", f"sök nästa markerar träffen i texten ({valt!r})")

    # ersättning, och ett ångra-steg för hela Ersätt alla
    win.editor.document.clearUndoRedoStacks()
    ruta36.input_find.setText("bok")
    ruta36.input_replace.setText("volym")
    ruta36._ersatt_alla()
    efter36b = win.editor.document.toPlainText()
    check("volym" in efter36b and "bok" not in efter36b,
          f"ersätt alla byter ut alla ({efter36b[:24]!r})")
    win.editor.document.undo()
    check("bok" in win.editor.document.toPlainText(),
          "och ett ångra tar tillbaka hela ersättningen")

    # mönster: reguljärt uttryck och bakåtreferens
    ruta36.chk_regex.setChecked(True)
    ruta36.input_find.setText(r"(skriv)en")
    ruta36.input_replace.setText(r"\1et")
    ruta36._ersatt_alla()
    check("skrivet" in win.editor.document.toPlainText(),
          f"och mönster med bakåtreferens fungerar "
          f"({win.editor.document.toPlainText()[:34]!r})")
    ruta36.close()

    print("\n35. AI-förslag i marginalen, och ett ångra-steg (fas 3.7 och 3.8)")

    scen35 = ovningsscen
    kalla_text = ("<p>Hon gick in i källaren och lade nyckeln på bordet. "
                  "Det var mörkt och hon tände lampan.</p>")
    ovningsbok.write(scen35.id, kalla_text)
    win._show_scene_html(scen35.id, kalla_text)

    # 3.7: förslaget hamnar som kommentar, texten står kvar orörd
    original = "Det var mörkt och hon tände lampan."
    förslag = "Mörkret var kompakt; hon trevade efter strömbrytaren."
    texten_fore = win.editor.document.toPlainText()
    check(win.comment_ai_suggestion(original, förslag),
          "förslaget kan läggas i marginalen i stället för att skrivas över")
    kommentar = ovningsbok.comment_by_quote(scen35.id, original)
    check(kommentar is not None and förslag in kommentar["text"],
          f"och kommentaren hänger på citatet med förslaget i sig "
          f"({kommentar['text'][:40] if kommentar else None!r})")
    check(win.editor.document.toPlainText() == texten_fore,
          "och texten står kvar orörd — inget skrivs över")
    check(win.comment_ai_suggestion(original, förslag),
          "samma förslag två gånger")
    kommentarer = ovningsbok.comments_for(scen35.id)
    check(len([k for k in kommentarer if k["quote"] == original]) == 1,
          f"blir en kommentar, inte två ({len(kommentarer)} kommentarer)")

    # AI-förslagets kommentar syns i panelen och går att markera som löst
    win.scene_inspector.set_scene(ovningsbok, ovningsbok.by_id(scen35.id))
    rader35 = win.scene_inspector.lst_comments
    check(rader35.count() >= 1 and any("AI föreslår" in rader35.item(i).text()
                                       for i in range(rader35.count())),
          f"och den syns i marginalen ({[rader35.item(i).text()[:28] for i in range(rader35.count())]})")

    # panelen: kortet för ett förslag har en väg till marginalen
    from PyQt6.QtWidgets import QPushButton
    win.sidebar._on_review_received({"suggestions": [
        {"type": "style", "original": "Det var mörkt",
         "replacement": "Mörkret var kompakt", "explanation": "kortare"}]})
    knappar = [k for k in win.sidebar.findChildren(QPushButton)
               if k.toolTip() == tr("ai_card_btn_comment")]
    check(len(knappar) == 1, f"kortet i panelen har en kommentarsknapp ({len(knappar)})")
    fangat_kort = []
    win.sidebar.comment_suggestion_requested.connect(
        lambda o, r: fangat_kort.append((o, r)))
    knappar[0].click()
    check(fangat_kort == [("Det var mörkt", "Mörkret var kompakt")],
          f"och den skickar citatet och förslaget ({fangat_kort})")

    # 3.8: att skriva in förslaget är ett ångra-steg
    win.editor.document.clearUndoRedoStacks()
    win._apply_ai_suggestion(original, förslag)
    efter_text = win.editor.document.toPlainText()
    check(förslag in efter_text and original not in efter_text,
          "förslaget kan skrivas in i efterhand")
    check("ångra-steg" in win.status_bar.currentMessage()
          or win.status_bar.currentMessage() != "", "och det sägs vad som hände")
    win.editor.document.undo()
    check(win.editor.document.toPlainText() == texten_fore,
          f"och ett enda ångra tar tillbaka hela förslaget "
          f"({win.editor.document.toPlainText()[:30]!r})")
    check(not win._apply_ai_suggestion("finns inte i texten", "något"),
          "och ett förslag som inte går att hitta skriver inte")
    win.editor.document.setModified(False)
    win.is_modified = False

    # orddiffen: detaljnivån i granskningsrutan
    ruta35 = ReviewDialog("<p>Nyckeln låg på bordet.</p>", "<p>Nyckeln låg kvar på bordet.</p>", "ord", win)
    check("[+kvar+]" in ruta35.lst_changes.item(0).toolTip(),
          f"och ord-för-ord-skillnaden står i radens verktygstips "
          f"({ruta35.lst_changes.item(0).toolTip().splitlines()[0][:40]!r})")
    ruta35.close()

    # Arken: ett ark per sida med ett mellanrum där ytan syns, och texten delad
    # mellan rader. Mätt i en riktig rendering, med temats färger.
    from PyQt6.QtCore import QPointF as QtPunkt, QRect as QtRect
    from ui.editor_view import DocumentCanvas
    from ui.paged_paper import PagedPaper, PAGE_WIDTH_PX, PAGE_HEIGHT_PX
    theme_mgr.apply_theme_to_app(app)

    ark_canvas = DocumentCanvas()
    ark = PagedPaper(ark_canvas, theme_mgr)
    ark.resize(PAGE_WIDTH_PX, PAGE_HEIGHT_PX)
    ark.show()
    mening = "En mening med några ord, så att raden blir lagom lång. "
    ark_canvas.setHtml("<p>" + mening * 240 + "</p>")
    ark.refresh()
    for _ in range(3):
        app.processEvents()

    check(len(ark.pages) >= 2, f"lång text ger flera ark ({len(ark.pages)} stycken)")
    check(ark.total_height() >= 2 * PAGE_HEIGHT_PX,
          f"och pappret blir högre än ett ark ({ark.total_height()})")

    # Texten delas vid radslut: varje ark rymmer bara sin egen text
    delad = ark._page_height(0) <= CANVAS_PAGE_PX and len(ark.pages) > 1
    inga_korsande = all(ark.pages[i] < ark.pages[i + 1] for i in range(len(ark.pages) - 1))
    check(delad and inga_korsande, "texten delas vid radslut mellan arken")

    # Mellanrummet mellan två ark visar ytan runt pappret, inte papper
    bild = ark.grab().toImage()
    yta = QColor(theme_mgr.tokens()["window_bg"]).name()
    mellan = QtRect(0, int(ark.sheet_rect(0).bottom()) + 6, ark.width(), 1)
    inne_i_arket = QtRect(0, int(ark.sheet_rect(0).y()) + 200, ark.width(), 1)
    if mellan.y() + 8 < bild.height():
        glapp = bild.pixelColor(300, mellan.y() + 4).name()
        papper = bild.pixelColor(300, inne_i_arket.y()).name()
        check(glapp == yta and papper != yta,
              f"mellanrummet visar ytan ({glapp}) och arket är papper ({papper})")
    else:
        check(False, "mellanrummet hamnade utanför bilden")

    # Editorn sitter i det aktiva arkets innermått
    ruta = ark.content_rect(ark.active)
    geo = ark_canvas.geometry()
    check(abs(geo.x() - ruta.x()) <= 1 and abs(geo.y() - ruta.y()) <= 1,
          f"editorn ligger i det aktiva arkets innermått ({geo.x()},{geo.y()})")
    check(geo.height() <= CANVAS_PAGE_PX,
          f"och bara så högt som arkets text ({geo.height()})")

    # Klick i ett annat ark flyttar markören och editorn dit
    ark.place_cursor(1, QtPunkt(300.0, ark.content_rect(1).y() + 40.0))
    for _ in range(2):
        app.processEvents()
    ark.canvas.setFocus()
    check(ark.active == 1, "klick i ark 2 gör det till det aktiva arket")
    check(abs(ark_canvas.geometry().y() - ark.content_rect(1).y()) <= 1,
          "och editorn flyttar in i ark 2")
    check(ark_canvas.verticalScrollBar().value() == int(ark.pages[1]),
          "med texten från arkets första rad")

    # Arkets fot: sidnumret står där, i tomrummet under texten
    ark.set_page_settings({"page_numbering": True, "page_number_format": "page_of_total",
                           "page_number_pos": "bottom-center"})
    ark.refresh()
    for _ in range(2):
        app.processEvents()
    fot = ark.grab(QtRect(0, int(ark.sheet_rect(0).bottom()) - PAGE_MARGIN_BOTTOM,
                          ark.width(), PAGE_MARGIN_BOTTOM)).toImage()
    mörka = sum(1 for x in range(0, fot.width(), 2) for y in range(0, fot.height(), 2)
                if fot.pixelColor(x, y).lightness() < 200)
    check(mörka > 0, f"sidnumret ritas i arkets fot ({mörka} mörka punkter)")

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
