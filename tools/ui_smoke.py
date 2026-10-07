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

    # kortet visar statusen, och ett klick på kortet öppnar scenen
    check("Bearbetning" in kort.list.item(0).text(),
          f"kortet visar statusen ({kort.list.item(0).text()!r})")
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
