"""ui/compile_dialog.py — kompilera manuset (5.15).

Fönstret som gör Scriveners Compile till en knapp: **vad** som ska ut (allt som
är öppet, eller markeringen), **i vilket format**, **hur det delas** (en fil
eller en per kapitel), **vad filerna heter** och **vart de hamnar**. Valen går
att spara som en profil på boken, så en tryckfärdig inställning inte behöver
sättas om varje gång (5.1).

Själva arbetet ligger i `core/compile.py`; den här filen frågar och visar.

    python -m ui.compile_dialog      kör självprovet (offscreen)
"""

import os

from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QInputDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout,
)

from core import compile as compile_mod
from core.i18n import _, i18n


class CompileDialog(QDialog):
    """Kompilerar det som är öppet, eller markeringen, till filer i en mapp."""

    def __init__(self, project, editor, parent=None):
        super().__init__(parent)
        self.project = project
        self.editor = editor
        self.files: list[str] = []
        self.setWindowTitle(_("compile_title"))
        self.setModal(True)
        self.resize(560, 380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        rad_mapp = QHBoxLayout()
        self.edit_folder = QLineEdit(self._standard_folder())
        rad_mapp.addWidget(self.edit_folder, 1)
        self.btn_folder = QPushButton("…")
        self.btn_folder.clicked.connect(self.choose_folder)
        rad_mapp.addWidget(self.btn_folder)
        self.lbl_folder = QLabel()
        form.addRow(self.lbl_folder, rad_mapp)

        self.combo_format = QComboBox()
        for fmt in compile_mod.FORMATS:
            self.combo_format.addItem(fmt.upper(), fmt)
        self.lbl_format = QLabel()
        form.addRow(self.lbl_format, self.combo_format)

        self.combo_scope = QComboBox()
        self.combo_scope.addItem("", compile_mod.SCOPE_OPEN)
        self.combo_scope.addItem("", compile_mod.SCOPE_SELECTION)
        self.lbl_scope = QLabel()
        form.addRow(self.lbl_scope, self.combo_scope)

        self.edit_template = QLineEdit(compile_mod.DEFAULT_TEMPLATE)
        self.edit_template.textChanged.connect(self._update_preview)
        self.lbl_template = QLabel()
        form.addRow(self.lbl_template, self.edit_template)
        self.lbl_preview = QLabel()
        self.lbl_preview.setObjectName("CompilePreview")
        form.addRow("", self.lbl_preview)

        self.chk_chapter = QCheckBox()
        form.addRow("", self.chk_chapter)

        rad_profil = QHBoxLayout()
        self.combo_profile = QComboBox()
        self.combo_profile.currentIndexChanged.connect(self.apply_profile)
        rad_profil.addWidget(self.combo_profile, 1)
        self.btn_save_profile = QPushButton()
        self.btn_save_profile.clicked.connect(self.save_profile_as)
        rad_profil.addWidget(self.btn_save_profile)
        self.btn_drop_profile = QPushButton("−")
        self.btn_drop_profile.clicked.connect(self.drop_profile)
        rad_profil.addWidget(self.btn_drop_profile)
        self.lbl_profile = QLabel()
        form.addRow(self.lbl_profile, rad_profil)

        layout.addLayout(form)
        self.lbl_result = QLabel()
        self.lbl_result.setWordWrap(True)
        layout.addWidget(self.lbl_result)
        layout.addStretch(1)

        self.knappar = QDialogButtonBox()
        self.btn_go = self.knappar.addButton("", QDialogButtonBox.ButtonRole.AcceptRole)
        self.knappar.addButton(QDialogButtonBox.StandardButton.Close)
        self.btn_go.clicked.connect(self.run_compile)
        self.knappar.rejected.connect(self.reject)
        layout.addWidget(self.knappar)

        i18n.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()
        self.reload_profiles()

    # ------------------------------------------------------------------ valen

    def _standard_folder(self) -> str:
        """Bokens egen mapp om inget annat sagts — där ligger manuset redan."""
        if self.project is not None and getattr(self.project, "root", None):
            return str(self.project.root)
        return os.path.expanduser("~")

    def choose_folder(self) -> str:
        vald = QFileDialog.getExistingDirectory(self, _("compile_choose_folder"),
                                               self.edit_folder.text())
        if vald:
            self.edit_folder.setText(vald)
        return vald

    def settings(self) -> dict:
        return {
            "folder": self.edit_folder.text().strip(),
            "fmt": self.combo_format.currentData(),
            "scope": self.combo_scope.currentData(),
            "per_chapter": self.chk_chapter.isChecked(),
            "template": self.edit_template.text(),
        }

    def apply(self, val: dict) -> None:
        if val.get("folder"):
            self.edit_folder.setText(str(val["folder"]))
        if val.get("fmt") in compile_mod.FORMATS:
            self.combo_format.setCurrentIndex(compile_mod.FORMATS.index(val["fmt"]))
        if val.get("scope") in compile_mod.SCOPES:
            self.combo_scope.setCurrentIndex(compile_mod.SCOPES.index(val["scope"]))
        if "per_chapter" in val:
            self.chk_chapter.setChecked(bool(val["per_chapter"]))
        if "template" in val:
            self.edit_template.setText(str(val["template"]))
        self._update_preview()

    # --------------------------------------------------------------- profilerna

    def reload_profiles(self, välj: str = "") -> None:
        self.combo_profile.blockSignals(True)
        self.combo_profile.clear()
        self.combo_profile.addItem(_("compile_profile_none"), "")
        for profil in self.project.profiles if self.project is not None else []:
            self.combo_profile.addItem(profil["name"], profil["name"])
        if välj:
            i = self.combo_profile.findData(välj)
            if i >= 0:
                self.combo_profile.setCurrentIndex(i)
        self.combo_profile.blockSignals(False)

    def apply_profile(self) -> None:
        namn = self.combo_profile.currentData()
        if not namn:
            return
        val = compile_mod.profile_for(self.project, namn)
        if val:
            self.apply(val)

    def save_profile_as(self) -> str:
        namn, ok = QInputDialog.getText(self, _("compile_profile_save"),
                                        _("compile_profile_name"),
                                        text=self.combo_profile.currentData() or "")
        if not ok or not str(namn).strip():
            return ""
        compile_mod.save_profile(self.project, namn, **self.settings())
        self.reload_profiles(välj=str(namn).strip())
        self.lbl_result.setText(_("compile_profile_saved", name=str(namn).strip()))
        return str(namn).strip()

    def drop_profile(self) -> bool:
        namn = self.combo_profile.currentData()
        if not namn or not compile_mod.remove_profile(self.project, namn):
            return False
        self.reload_profiles()
        self.lbl_result.setText(_("compile_profile_dropped", name=namn))
        return True

    # -------------------------------------------------------------- arbetet

    def _update_preview(self) -> None:
        """Visar ett riktigt filnamn i stället för att beskriva mallen."""
        doc, skal = compile_mod.document_for(self.editor, self.combo_scope.currentData())
        titel = "Första kapitlet"
        if doc is not None:
            for namn, _del in compile_mod.split_document(doc):
                if namn:
                    titel = namn
                    break
            else:
                titel = self.project.title if self.project is not None else titel
        namn = compile_mod.fill_template(self.edit_template.text(), 2, titel,
                                         self.project.title if self.project else "")
        ändelse = compile_mod.FORMAT_EXT.get(self.combo_format.currentData(), "")
        self.lbl_preview.setText(_("compile_preview", name=namn + ändelse))
        if self.combo_scope.currentData() == compile_mod.SCOPE_SELECTION and doc is None:
            self.lbl_result.setText(_("compile_no_selection"))

    def run_compile(self) -> list[str]:
        doc, skal = compile_mod.document_for(self.editor, self.combo_scope.currentData())
        if doc is None:
            self.lbl_result.setText(_("compile_no_selection"))
            return []
        mapp = self.edit_folder.text().strip()
        if not os.path.isdir(mapp):
            self.lbl_result.setText(_("compile_no_folder", folder=mapp))
            return []
        val = self.settings()
        self.files = compile_mod.compile_to_files(
            doc, mapp, fmt=val["fmt"], scope=val["scope"],
            per_chapter=val["per_chapter"], template=val["template"],
            project_name=self.project.title if self.project is not None else "",
            metadata=self._metadata(), page_settings=self._page_settings(),
        )
        if not self.files:
            self.lbl_result.setText(_("compile_nothing"))
            return []
        self.lbl_result.setText(_("compile_done", count=str(len(self.files)), folder=mapp))
        return self.files

    def _metadata(self) -> dict:
        parent = self.parent()
        if parent is not None and hasattr(parent, "book_metadata"):
            try:
                return parent.book_metadata()
            except Exception:
                return {}
        return {}

    def _page_settings(self) -> dict:
        parent = self.parent()
        return dict(getattr(parent, "page_settings", {}) or {})

    # ------------------------------------------------------------------ texten

    def retranslate_ui(self) -> None:
        self.setWindowTitle(_("compile_title"))
        self.lbl_folder.setText(_("compile_folder"))
        self.btn_folder.setToolTip(_("compile_choose_folder"))
        self.lbl_format.setText(_("compile_format"))
        self.lbl_scope.setText(_("compile_scope"))
        self.combo_scope.setItemText(0, _("compile_scope_open"))
        self.combo_scope.setItemText(1, _("compile_scope_selection"))
        self.lbl_template.setText(_("compile_template"))
        self.edit_template.setToolTip(_("compile_template_hint"))
        self.chk_chapter.setText(_("compile_per_chapter"))
        self.lbl_profile.setText(_("compile_profile"))
        self.btn_save_profile.setText(_("compile_profile_save"))
        self.btn_drop_profile.setToolTip(_("compile_profile_remove"))
        self.btn_go.setText(_("compile_go"))
        if self.combo_profile.count():
            self.combo_profile.setItemText(0, _("compile_profile_none"))
        self._update_preview()


def _self_check() -> int:
    import shutil
    import tempfile

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtGui import QTextBlockFormat, QTextCursor, QTextDocument
    from PyQt6.QtWidgets import QApplication
    from core.project import Project

    app = QApplication.instance() or QApplication([])   # noqa: F841
    checks = 0
    failures = 0

    def kolla(ok, text):
        nonlocal checks, failures
        checks += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            failures += 1

    class Editor:
        """Det enda fönstret behöver av en editor: dokumentet och markören.

        Dokumentet ligger som egenskap, precis som i fönstrets editor
        (`@property document`), inte som metod.
        """

        def __init__(self, doc):
            self.document = doc
            self._cursor = QTextCursor(doc)

        def textCursor(self):
            return self._cursor

    doc = QTextDocument()
    markor = QTextCursor(doc)
    rubrik = QTextBlockFormat()
    rubrik.setHeadingLevel(1)
    markor.insertText("Första kapitlet")
    markor.setBlockFormat(rubrik)
    markor.insertBlock(QTextBlockFormat())
    markor.insertText("Det började med regn.")
    markor.insertBlock(rubrik)
    markor.insertText("Andra kapitlet")
    markor.insertBlock(QTextBlockFormat())
    markor.insertText("Och slutade med sol.")

    root = tempfile.mkdtemp(prefix="compile-dialog-")
    ut = os.path.join(root, "ut")
    os.makedirs(ut, exist_ok=True)
    try:
        project = Project.create(os.path.join(root, "bok"), "Provboken", template="enkel")
        editor = Editor(doc)
        dialog = CompileDialog(project, editor)
        dialog.edit_folder.setText(ut)
        dialog.combo_format.setCurrentIndex(compile_mod.FORMATS.index(compile_mod.FORMAT_MD))
        dialog.edit_template.setText("{n} - {title}")
        kolla(".md" in dialog.lbl_preview.text() and "02 - Första kapitlet" in dialog.lbl_preview.text(),
              f"förhandsvisningen visar ett riktigt filnamn ({dialog.lbl_preview.text()})")

        filer = dialog.run_compile()
        kolla(len(filer) == 1, "utan delning blir det en fil")
        kolla(os.path.exists(filer[0]), "och den finns på disken")
        kolla("Det började med regn." in open(filer[0], encoding="utf-8").read(),
              "med hela manuset i")

        dialog.chk_chapter.setChecked(True)
        filer2 = dialog.run_compile()
        kolla(len(filer2) == 2, f"med delning blir det en per kapitel ({len(filer2)})")
        kolla(all(os.path.exists(f) for f in filer2), "och alla skrivs")
        kolla("Och slutade med sol." in open(filer2[1], encoding="utf-8").read(),
              "med rätt text i den andra")

        # Markeringen: inget markerat skall säga det, inte skriva en tom fil.
        dialog.combo_scope.setCurrentIndex(compile_mod.SCOPES.index(compile_mod.SCOPE_SELECTION))
        kolla(dialog.run_compile() == [], "utan markering kompileras ingenting")
        kolla(dialog.lbl_result.text() != "", f"och fönstret säger varför ({dialog.lbl_result.text()!r})")

        markor = editor.textCursor()
        markor.setPosition(0)
        markor.setPosition(18, QTextCursor.MoveMode.KeepAnchor)
        editor._cursor = markor
        filer3 = dialog.run_compile()
        kolla(len(filer3) == 1, "men med markeringen blir det en fil")
        text3 = open(filer3[0], encoding="utf-8").read()
        kolla("Första kapitlet" in text3 and "Och slutade med sol." not in text3,
              f"med bara det markerade kapitlet ({text3.strip()[:40]!r})")

        # Profilen: spara, läs tillbaka, ta bort.
        compile_mod.save_profile(project, "Pocket", fmt=compile_mod.FORMAT_MD,
                                 scope=compile_mod.SCOPE_OPEN, per_chapter=True,
                                 template="{n} - {title}", folder=ut)
        dialog.edit_template.setText("{title}")
        dialog.chk_chapter.setChecked(False)
        dialog.combo_scope.setCurrentIndex(compile_mod.SCOPES.index(compile_mod.SCOPE_OPEN))
        dialog.reload_profiles(välj="Pocket")
        dialog.apply_profile()
        kolla(dialog.edit_template.text() == "{n} - {title}" and dialog.chk_chapter.isChecked(),
              "profilen sätter tillbaka mall och delning")
        kolla(dialog.edit_folder.text() == ut, "och mappen")
        project.save()
        omlast = Project.load(project.root)
        kolla(compile_mod.profile_for(omlast, "Pocket") is not None,
              "och profilen följer med i projektfilen")
        kolla(project.profiles[0].get("fmt") == compile_mod.FORMAT_MD,
              f"med sitt format ({project.profiles[0]})")
        kolla(dialog.drop_profile() is True, "en profil kan tas bort")
        kolla(Project.load(project.root) is not None and compile_mod.remove_profile(project, "Pocket") is False,
              "och att ta bort den två gånger gör inget")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"compile_dialog: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
