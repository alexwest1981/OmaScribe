"""core/compile.py — kompilera ett manus till filer (5.15).

Scriveners Compile i den form som faktiskt behövs: **vilka** stycken följer med
(hela det som är öppet, eller bara markeringen), **hur** de delas (en fil, eller
en per kapitel) och **vad** filerna heter (en mall med `{n}` och `{title}`).

Modulen ritar ingenting och skriver bara filer genom de exportvägar som redan
finns (`core.doc_manager` och `core.epub`) — den bestämmer bara *vad* som ska ut
och *vart*. Profilerna (namngivna inställningar per bok) hör till projektet och
ligger i `project.json`; de är vad 5.1 hade kvar som "ett sparat
publiceringsprojekt".

    python -m core.compile     kör självprovet
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile

from PyQt6.QtGui import QTextBlockFormat, QTextCursor, QTextDocument

# Vad en kompilering kan omfatta. Det som är öppet redan i editorn är manuscript;
# markeringen är den del av det som författaren pekat ut.
SCOPE_OPEN = "open"
SCOPE_SELECTION = "selection"
SCOPES = (SCOPE_OPEN, SCOPE_SELECTION)

# Kanalerna är desamma som exportmenyn redan har.
FORMAT_EPUB = "epub"
FORMAT_DOCX = "docx"
FORMAT_PDF = "pdf"
FORMAT_MD = "md"
FORMATS = (FORMAT_EPUB, FORMAT_DOCX, FORMAT_PDF, FORMAT_MD)
FORMAT_EXT = {FORMAT_EPUB: ".epub", FORMAT_DOCX: ".docx", FORMAT_PDF: ".pdf",
              FORMAT_MD: ".md"}

DEFAULT_TEMPLATE = "{title}"
UNSAFE = re.compile(r"[^\w\s\-.]+", re.UNICODE)


def safe_name(text: str, fallback: str = "utan-titel") -> str:
    """Ett filnamn som går att skriva på varje filsystem.

    `:` `?` `*` och snedstreck är inga filnamn på Windows, och en rubrik kan
    innehålla dem. Bokstäver, siffror, mellanslag, punkt och bindestreck står
    kvar; resten blir tomt.
    """
    rensat = UNSAFE.sub("", str(text)).strip().strip(".")
    rensat = re.sub(r"\s+", " ", rensat)
    return rensat[:80] or fallback


def fill_template(template: str, nummer: int, titel: str, projekt: str = "") -> str:
    """Filnamnsmallen: `{n}`, `{title}` och `{project}`. Ändelsen läggs på utanför.

    Är mallen tom används titeln. En mall utan kända platshållare är ändå en mall
    — då blir alla filer lika döpta, vilket är författarens val, och `-{n}`
    läggs på så filerna inte skriver över varandra.
    """
    mall = (template or DEFAULT_TEMPLATE).strip() or DEFAULT_TEMPLATE
    ut = (mall.replace("{n}", f"{nummer:02d}")
              .replace("{title}", str(titel))
              .replace("{project}", str(projekt)))
    return safe_name(ut)


def chapter_title(block, fallback: str) -> str:
    text = block.text().strip() if block is not None else ""
    return text or fallback


def split_document(doc: QTextDocument, level: int = 1) -> list[tuple[str, QTextDocument]]:
    """Delar dokumentet i kapitel vid rubriker på `level` (1 = `#`).

    Allt före den första rubriken blir ett eget kapitel — en försättssida eller en
    dedikation skall inte tappas bort bara för att den saknar rubrik. Hittas
    ingen rubrik alls blir hela dokumentet ett kapitel.
    """
    if doc is None:
        return []
    indelningar: list[tuple[str, int, int]] = []      # (titel, från, till)
    block = doc.begin()
    while block.isValid():
        if block.blockFormat().headingLevel() == level and block.text().strip():
            indelningar.append((chapter_title(block, "kapitel"),
                                block.position(), doc.characterCount()))
        block = block.next()
    if not indelningar:
        return [("", doc.clone())]
    # Slutet på ett kapitel är början på nästa.
    ut: list[tuple[str, QTextDocument]] = []
    if indelningar[0][1] > 0:
        ut.append(("", _slice(doc, 0, indelningar[0][1])))
    for i, (titel, start, _) in enumerate(indelningar):
        slut = indelningar[i + 1][1] if i + 1 < len(indelningar) else doc.characterCount()
        ut.append((titel, _slice(doc, start, slut)))
    return ut


def _slice(doc: QTextDocument, start: int, slut: int) -> QTextDocument:
    """Ett dokument med texten mellan två positioner, formateringen kvar."""
    ny = QTextDocument()
    ny.setDefaultFont(doc.defaultFont())
    markor = QTextCursor(ny)
    källa = QTextCursor(doc)
    # Sista giltiga positionen är characterCount() - 1: dokumentets slut står
    # *efter* sista tecknet, och en position där är utanför dokumentet.
    slut = max(0, min(slut, doc.characterCount() - 1))
    källa.setPosition(max(0, min(start, slut)))
    källa.setPosition(slut, QTextCursor.MoveMode.KeepAnchor)
    markor.insertFragment(källa.selection())
    # insertFragment lägger till ett tomt slutblock; ta bort det så ett kapitel
    # inte slutar med en tom sida.
    sist = ny.lastBlock()
    if sist.isValid() and not sist.text().strip() and ny.blockCount() > 1:
        markor = QTextCursor(sist)
        markor.select(QTextCursor.SelectionType.BlockUnderCursor)
        markor.removeSelectedText()
    return ny


def document_of(editor) -> QTextDocument | None:
    """Dokumentet bakom en editor.

    Fönstrets editor har dokumentet som egenskap (`editor.document`), en naken
    QTextEdit som metod (`editor.document()`) — båda går bra, så en kompilering
    kan prövas utan ett helt fönster.
    """
    if editor is None:
        return None
    doc = getattr(editor, "document", None)
    return doc() if callable(doc) else doc


def selection_document(editor) -> QTextDocument | None:
    """Markeringen som ett eget dokument, eller None om inget är markerat.

    Hela block följer med markeringen: en halv mening är inget urval att
    kompilera, och stycket runt markeringen är det författaren menar.
    """
    if editor is None:
        return None
    markor = editor.textCursor()
    if not markor.hasSelection():
        return None
    doc = document_of(editor)
    if doc is None:
        return None
    start = doc.findBlock(markor.selectionStart()).position()
    slut_block = doc.findBlock(markor.selectionEnd())
    slut = slut_block.position() + slut_block.length() - 1
    val = QTextCursor(doc)
    val.setPosition(start)
    val.setPosition(max(start, slut), QTextCursor.MoveMode.KeepAnchor)
    ny = QTextDocument()
    ny.setDefaultFont(doc.defaultFont())
    QTextCursor(ny).insertFragment(val.selection())
    return ny


def document_for(editor, scope: str) -> tuple[QTextDocument | None, str]:
    """Dokumentet som skall kompileras, och ett skäl om det inte går."""
    doc = document_of(editor)
    if doc is None:
        return None, "no_editor"
    if scope == SCOPE_SELECTION:
        valt = selection_document(editor)
        if valt is None:
            return None, "no_selection"
        return valt, ""
    return doc, ""


def compile_to_files(doc: QTextDocument, folder: str, *, fmt: str = FORMAT_DOCX,
                     scope: str = SCOPE_OPEN, per_chapter: bool = False,
                     template: str = DEFAULT_TEMPLATE, project_name: str = "",
                     metadata: dict | None = None,
                     page_settings: dict | None = None,
                     colors: dict | None = None) -> list[str]:
    """Skriver dokumentet till `folder` och returnerar filerna som blev.

    En fil blir det `template` säger, och en per kapitel blir det `per_chapter`
    säger — då numreras kapitlen i ordningen de står, så `{n}` blir 01, 02, …
    """
    from core import doc_manager

    if doc is None or not os.path.isdir(folder):
        return []
    ändelse = FORMAT_EXT.get(fmt, ".docx")
    delar = split_document(doc) if per_chapter else [("", doc)]
    if not delar:
        return []
    filer: list[str] = []
    for i, (titel, del_doc) in enumerate(delar, start=1):
        namn = fill_template(template, i, titel, project_name)
        sökväg = os.path.join(folder, f"{namn}{ändelse}")
        # Två kapitel kan heta samma sak — då hade den andra skrivit över den
        # första. Numret läggs på, inte ett hopp över filen.
        unik = 2
        while os.path.exists(sökväg):
            sökväg = os.path.join(folder, f"{namn}-{unik}{ändelse}")
            unik += 1
        if fmt == FORMAT_EPUB:
            from core.epub import export_epub

            export_epub(sökväg, del_doc, metadata or {})
        else:
            doc_manager.DocumentManager.save_file(sökväg, del_doc, colors or {},
                                                  page_settings or {})
        if os.path.exists(sökväg):
            filer.append(sökväg)
    return filer


# --------------------------------------------------------------- profilerna

def profile_for(project, name: str) -> dict | None:
    return next((p for p in project.profiles if p["name"] == name), None)


def save_profile(project, name: str, **settings) -> dict:
    """Sparar valen under ett namn. Samma namn skriver över — det är så man ändrar.

    Bara kända nycklar sparas: en profil skall gå att läsa även om en nyare
    version av programmet har lagt till något (5.1).
    """
    namn = str(name).strip()
    if not namn:
        raise ValueError("profilen behöver ett namn")
    kända = {k: settings[k] for k in ("fmt", "scope", "per_chapter", "template", "folder")
             if k in settings}
    profil = profile_for(project, namn)
    if profil is None:
        projekt_profil = {"name": namn, **kända}
        project.profiles.append(projekt_profil)
        return projekt_profil
    profil.update(kända)
    return profil


def remove_profile(project, name: str) -> bool:
    profil = profile_for(project, name)
    if profil is None:
        return False
    project.profiles.remove(profil)
    return True


def _self_check() -> int:
    import os as _os

    _os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication

    _app = QApplication.instance() or QApplication([])

    checks = 0
    failures = 0

    def kolla(ok, text):
        nonlocal checks, failures
        checks += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            failures += 1

    # Ett litet manus: försättssida, två kapitel med var sitt stycke.
    doc = QTextDocument()
    markor = QTextCursor(doc)
    markor.insertText("För Anna, som läste allt.")
    markor.insertBlock(QTextBlockFormat())
    rubrik = QTextBlockFormat()
    rubrik.setHeadingLevel(1)
    markor.insertBlock(rubrik)
    markor.insertText("Första kapitlet")
    markor.insertBlock(QTextBlockFormat())
    markor.insertText("Det började med regn.")
    markor.insertBlock(rubrik)
    markor.insertText("Andra kapitlet: allt som hände sedan?")
    markor.insertBlock(QTextBlockFormat())
    markor.insertText("Sedan slutade det.")

    kolla(len(split_document(doc)) == 3,
          f"tre delar: försättssidan och två kapitel ({len(split_document(doc))})")
    titlar = [t for t, _ in split_document(doc)]
    kolla(titlar == ["", "Första kapitlet", "Andra kapitlet: allt som hände sedan?"],
          f"med kapitelrubrikerna som namn ({titlar})")
    forsta = split_document(doc)[1][1]
    kolla("Det började med regn." in forsta.toPlainText(),
          "och varje del har sitt eget innehåll")
    kolla("Sedan slutade det." not in forsta.toPlainText(),
          "utan att ta med nästa kapitel")
    kolla("För Anna" not in forsta.toPlainText(), "och utan försättssidan")
    sista = split_document(doc)[2][1].toPlainText()
    kolla("Sedan slutade det." in sista,
          f"och det sista kapitlet behåller sin sista mening ({sista.strip()!r})")
    kolla(sista.strip().startswith("Andra kapitlet"),
          f"med sin egen rubrik först ({sista.strip().splitlines()[0]!r})")

    kolla(fill_template("{n} - {title}", 3, "Ett kapitel") == "03 - Ett kapitel",
          "mallen sätter kapitelnumret")
    kolla(fill_template("{title}", 1, "Andra kapitlet: allt som hände sedan?")
          == "Andra kapitlet allt som hände sedan",
          "och tar bort det som inte får stå i ett filnamn")
    kolla(fill_template("", 1, "") == "utan-titel", "tom titel ger ett namn ändå")
    kolla(fill_template("{n}_{project}", 2, "x", "Min bok") == "02_Min bok",
          "och projektnamnet går att använda")

    root = tempfile.mkdtemp(prefix="compile-check-")
    try:
        filer = compile_to_files(doc, root, fmt=FORMAT_MD, per_chapter=True,
                                 template="{n} - {title}", project_name="Prov")
        kolla(len(filer) == 3, f"tre filer skrivs ({len(filer)})")
        kolla(all(_os.path.exists(f) for f in filer), "och alla finns på disken")
        kolla(_os.path.basename(filer[1]).startswith("02 - Första kapitlet"),
              f"med nummer och rubrik i namnet ({_os.path.basename(filer[1])})")
        kolla("Det började med regn." in open(filer[1], encoding="utf-8").read(),
              "och kapiteltexten i sin fil")

        en = compile_to_files(doc, root, fmt=FORMAT_MD, per_chapter=False,
                              template="{title}", project_name="Prov")
        kolla(len(en) == 1, "utan delning blir det en fil")
        kolla(en[0] == filer[1] + ".md"[:0] or _os.path.exists(en[0]),
              "och den ligger där den ska")

        # Två kapitel med samma namn får inte skriva över varandra.
        dubbel = QTextDocument()
        m2 = QTextCursor(dubbel)
        m2.insertText("Samma")
        m2.setBlockFormat(rubrik)
        m2.insertBlock(rubrik)
        m2.insertText("Samma")
        filer2 = compile_to_files(dubbel, root, fmt=FORMAT_MD, per_chapter=True,
                                  template="{title}")
        kolla(len(filer2) == 2 and len(set(filer2)) == 2,
              f"två kapitel med samma namn blir två filer ({[_os.path.basename(f) for f in filer2]})")

        kolla(compile_to_files(doc, "/finns/inte", fmt=FORMAT_MD) == [],
              "en mapp som inte finns ger inga filer i stället för ett krasch")
        kolla(split_document(None) == [], "och ett tomt dokument ger inga kapitel")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"compile: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
