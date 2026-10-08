"""ui/ask_panel.py — fråga manuset (6.3, 6.4) och se vad som skickas (6.16, 6.17).

Panelen gör tre saker, och den tredje är den som gör de två första ärliga:

  * frågar manuset och svarar med **källhänvisning** — varje scen som låg till
    grund för svaret står som en länk, och ett klick öppnar scenen;
  * håller en **historik** över frågor och svar, så en följdfråga inte börjar om
    från noll;
  * visar **exakt vilka delar** som skickades, varför var och en togs med och hur
    stora de är (tokenräkning), med en knapp för att se hela urvalet.

Urvalet byggs i `core/context.py`. Ingenting lämnar datorn förrän frågan skickas,
och då är urvalet det som står i rutan.

    python -m ui.ask_panel      kör självprovet (offscreen, utan nätverk)
"""

from __future__ import annotations

import re
import sys

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QTextBrowser, QVBoxLayout, QWidget,
)

from core import context as context_mod
from core.ai_client import AIWorker, DEFAULT_AI_ENDPOINT, DEFAULT_AI_MODEL
from core.i18n import _, i18n

SCOPE_SCENE = "scene"
SCOPE_MANUSCRIPT = "manuscript"

# Slagens färg i kontextvisaren. Den förstärker bara — raden säger sitt slag i
# klartext, så färgen är aldrig den enda bäraren av information.
KIND_COLORS = {
    context_mod.KIND_SCENE: "#1f6f4a",
    context_mod.KIND_CODEX: "#1f4f8f",
    context_mod.KIND_INSTRUCTION: "#8a4b1f",
    context_mod.KIND_NOTE: "#6b4b8a",
}

# Modellen får veta exakt hur den skall hänvisa, annars hittar länkarna inget.
SYSTEM_PROMPT = (
    "You are a story assistant inside a writing tool. Answer only from the "
    "material you are given; if something is not in it, say so in one line "
    "instead of guessing. Cite the part of the material each claim comes from "
    "by writing its label in square brackets, exactly as it stands in the "
    "heading of that part, e.g. [Nyckeln] or [Anna]. Answer in the language the "
    "question is asked in."
)


class AskPanel(QWidget):
    """Fråga manuset, få svar med källor, och se urvalet bakom svaret."""

    scene_requested = pyqtSignal(str)      # node_id
    status_message = pyqtSignal(str)

    def __init__(self, ai_client=None, config_mgr=None, parent=None):
        super().__init__(parent)
        self.ai = ai_client
        self.config = config_mgr
        self.project = None
        self.bible = None
        self.scene_id = ""
        self.items: list = []
        self.history: list[dict] = []
        self._worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        rad = QHBoxLayout()
        self.lbl_scope = QLabel()
        rad.addWidget(self.lbl_scope)
        self.combo_scope = QComboBox()
        self.combo_scope.addItem("", SCOPE_SCENE)
        self.combo_scope.addItem("", SCOPE_MANUSCRIPT)
        rad.addWidget(self.combo_scope, 1)
        layout.addLayout(rad)

        rad2 = QHBoxLayout()
        self.input_question = QLineEdit()
        self.input_question.returnPressed.connect(self.ask)
        rad2.addWidget(self.input_question, 1)
        self.btn_ask = QPushButton()
        self.btn_ask.clicked.connect(self.ask)
        rad2.addWidget(self.btn_ask)
        layout.addLayout(rad2)

        self.lbl_context = QLabel()
        self.lbl_context.setWordWrap(True)
        layout.addWidget(self.lbl_context)
        self.btn_context = QPushButton()
        self.btn_context.clicked.connect(self.show_context)
        layout.addWidget(self.btn_context)

        self.lst_history = QListWidget()
        self.lst_history.setMaximumHeight(120)
        self.lst_history.itemClicked.connect(self._on_history_clicked)
        layout.addWidget(self.lst_history)

        self.view_answer = QTextBrowser()
        self.view_answer.setOpenLinks(False)
        self.view_answer.anchorClicked.connect(self._on_anchor)
        layout.addWidget(self.view_answer, 1)

        i18n.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    # --------------------------------------------------------------- underlaget

    def set_project(self, project, bible=None) -> None:
        """Manuset panelen frågar. Utan projekt finns inget att skicka."""
        self.project = project
        self.bible = bible
        self.history.clear()
        self.items = []
        if self.lst_history is not None:
            self.lst_history.clear()
        if self.view_answer is not None:
            self.view_answer.clear()
        self._update_context_line()

    def set_scene(self, node_id: str) -> None:
        self.scene_id = node_id or ""
        self._update_context_line()

    def build_items(self, question: str) -> list:
        """Urvalet för frågan, utan att skicka något."""
        if self.project is None:
            return []
        scen = self.scene_id if self.combo_scope.currentData() == SCOPE_SCENE else ""
        self.items = context_mod.build(
            self.project, scene_id=scen, question=question, bible=self.bible,
            budget_chars=self._budget())
        self._update_context_line()
        return self.items

    def _budget(self) -> int:
        if self.config is None:
            return context_mod.DEFAULT_BUDGET
        return int(self.config.get("ai_context_budget", context_mod.DEFAULT_BUDGET) or 0)

    def _update_context_line(self) -> None:
        if self.project is None:
            self.lbl_context.setText(_("ask_no_project"))
            return
        if not self.items:
            self.lbl_context.setText(_("ask_context_idle"))
            return
        siffror = context_mod.summary(self.items)
        self.lbl_context.setText(_("ask_context_summary", items=str(siffror["items"]),
                                   tokens=str(siffror["tokens"])))

    # ----------------------------------------------------------------- frågan

    def ask(self) -> str:
        """Bygger urvalet, skickar det och visar svaret med sina källor."""
        fråga = self.input_question.text().strip()
        if self.project is None or not fråga:
            return ""
        if self.ai is None or self.config is None:
            self.status_message.emit(_("ask_no_client"))
            return ""
        endpoint = self.config.get("ai_endpoint", DEFAULT_AI_ENDPOINT)
        if not (endpoint or "").strip():
            # Ingenting skickas, och det sägs i klartext — en tom slutpunkt är
            # inte ett fel, det är ett val ingen har gjort än.
            self.view_answer.setPlainText(_("ask_no_endpoint"))
            self.status_message.emit(_("ask_no_endpoint"))
            return ""

        items = self.build_items(fråga)
        if not items:
            self.view_answer.setPlainText(_("ask_empty_context"))
            return ""
        text = context_mod.render(items)
        self._worker = AIWorker(endpoint, self.config.get("ai_key", ""),
                                self.config.get("ai_model", DEFAULT_AI_MODEL),
                                SYSTEM_PROMPT, text)
        self._worker.finished.connect(self._on_answer)
        self._worker.error.connect(self._on_error)
        self.btn_ask.setEnabled(False)
        self.view_answer.setPlainText(_("ask_thinking"))
        self._worker.start()
        return text

    def _on_answer(self, res: dict) -> None:
        self.btn_ask.setEnabled(True)
        svar = str(res.get("content", ""))
        fråga = self.input_question.text().strip()
        self.history.append({"question": fråga, "answer": svar,
                             "labels": [i.label for i in self.items]})
        post = QListWidgetItem(fråga[:80])
        post.setData(Qt.ItemDataRole.UserRole, len(self.history) - 1)
        self.lst_history.addItem(post)
        self._show_answer(svar)
        self.status_message.emit(_("ask_answered", count=str(len(self.items))))

    def _on_error(self, message: str) -> None:
        self.btn_ask.setEnabled(True)
        self.view_answer.setPlainText(message)
        self.status_message.emit(message)

    def _show_answer(self, svar: str) -> None:
        """Svaret med citaten som länkar till scenerna de kom ifrån."""
        self.view_answer.setHtml(self.answer_html(svar))

    def answer_html(self, svar: str) -> str:
        """Citaten blir klickbara. Etiketten matchas mot urvalets delar."""
        from html import escape

        kända = {i.label: i for i in self.items}

        def _linkify(match):
            etikett = match.group(1).strip()
            del_ = kända.get(etikett)
            if del_ is None:
                return escape(match.group(0))
            if del_.scene_id:
                mål = f"scene:{del_.scene_id}"
            elif del_.entity_id:
                mål = f"codex:{del_.entity_id}"
            else:
                return escape(match.group(0))
            return f'<a href="{mål}">{escape(etikett)}</a>'

        text = escape(svar)
        text = re.sub(r"\[([^\[\]]{1,60})\]", _linkify, text)
        return "<p>" + text.replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"

    def _on_anchor(self, url) -> None:
        text = url.toString()
        if text.startswith("scene:"):
            self.scene_requested.emit(text.split(":", 1)[1])

    def _on_history_clicked(self, post: QListWidgetItem) -> None:
        i = post.data(Qt.ItemDataRole.UserRole)
        if isinstance(i, int) and 0 <= i < len(self.history):
            post_ = self.history[i]
            self.input_question.setText(post_["question"])
            self._show_answer(post_["answer"])

    # ------------------------------------------------------------ vad skickas

    def show_context(self) -> QDialog:
        """Visar urvalet för den skrivna frågan, med skäl och tokenräkning."""
        fråga = self.input_question.text().strip()
        if self.project is not None:
            self.build_items(fråga)
        dialog = ContextView(self.items, self, project=self.project)
        dialog.exec()
        return dialog

    def retranslate_ui(self) -> None:
        self.lbl_scope.setText(_("ask_scope"))
        self.combo_scope.setItemText(0, _("ask_scope_scene"))
        self.combo_scope.setItemText(1, _("ask_scope_manuscript"))
        self.input_question.setPlaceholderText(_("ask_placeholder"))
        self.btn_ask.setText(_("ask_button"))
        self.btn_context.setText(_("ask_show_context"))
        self._update_context_line()


class ContextView(QDialog):
    """Exakt vad ett anrop skulle skicka: del för del, med skäl och storlek.

    NovelAI:s Context Viewer är förebilden: en lista man kan granska *innan*
    något skickas. Codexposterna går att ställa om (alltid / vid omnämning /
    aldrig) — det är användarens hand över urvalet, och valet sparas på boken.
    """

    def __init__(self, items, parent=None, project=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle(_("context_title"))
        self.setMinimumSize(520, 420)
        layout = QVBoxLayout(self)
        self.lbl_hint = QLabel()
        self.lbl_hint.setWordWrap(True)
        layout.addWidget(self.lbl_hint)

        self.lst = QListWidget()
        layout.addWidget(self.lst, 1)
        self.lbl_sum = QLabel()
        layout.addWidget(self.lbl_sum)

        rad = QHBoxLayout()
        self.lbl_policy = QLabel()
        rad.addWidget(self.lbl_policy)
        self.combo_policy = QComboBox()
        self.combo_policy.addItem("", context_mod.POLICY_ALWAYS)
        self.combo_policy.addItem("", context_mod.POLICY_MENTION)
        self.combo_policy.addItem("", context_mod.POLICY_NEVER)
        self.combo_policy.currentIndexChanged.connect(self._on_policy)
        rad.addWidget(self.combo_policy, 1)
        layout.addLayout(rad)

        knappar = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        knappar.rejected.connect(self.reject)
        knappar.accepted.connect(self.accept)
        layout.addWidget(knappar)

        self.lst.currentRowChanged.connect(self._on_row)
        self.set_items(items)
        self.retranslate_ui()

    def set_items(self, items) -> None:
        self.items = list(items or [])
        self.lst.clear()
        for i in self.items:
            post = QListWidgetItem(self.row_text(i))
            post.setData(Qt.ItemDataRole.UserRole, i)
            post.setToolTip(i.text)
            # Färgen *förstärker* slaget, den bär det inte: raden säger sitt slag
            # i klartext, så en läsare som inte ser färg förlorar ingenting.
            färg = KIND_COLORS.get(i.kind)
            if färg:
                post.setForeground(QColor(färg))
            self.lst.addItem(post)
        siffror = context_mod.summary(self.items)
        if hasattr(self, "lbl_sum"):
            self.lbl_sum.setText(_("context_sum", items=str(siffror["items"]),
                                   chars=str(siffror["chars"]), tokens=str(siffror["tokens"])))
        if self.lst.count():
            self.lst.setCurrentRow(0)

    def row_text(self, item) -> str:
        namn = context_mod.KIND_NAMES.get(item.kind, item.kind)
        return f"{namn}: {item.label} — {item.reason} ({item.tokens} tokens)"

    def _on_row(self, rad: int) -> None:
        post = self.lst.item(rad) if rad >= 0 else None
        if post is None:
            self.combo_policy.setEnabled(False)
            return
        it = post.data(Qt.ItemDataRole.UserRole)
        codex = getattr(it, "kind", "") == context_mod.KIND_CODEX and getattr(it, "entity_id", "")
        self.combo_policy.setEnabled(bool(codex) and self.project is not None)
        if codex and self.project is not None:
            vald = context_mod.codex_policies(self.project).get(it.entity_id,
                                                               context_mod.POLICY_ALWAYS)
            i = self.combo_policy.findData(vald)
            self.combo_policy.blockSignals(True)
            self.combo_policy.setCurrentIndex(i if i >= 0 else 0)
            self.combo_policy.blockSignals(False)

    def _on_policy(self) -> None:
        rad = self.lst.currentRow()
        if rad < 0 or self.project is None:
            return
        it = self.lst.item(rad).data(Qt.ItemDataRole.UserRole)
        if getattr(it, "kind", "") != context_mod.KIND_CODEX or not getattr(it, "entity_id", ""):
            return
        context_mod.set_codex_policy(self.project, it.entity_id, self.combo_policy.currentData())
        self.lst.item(rad).setText(self.row_text(it))

    def retranslate_ui(self) -> None:
        self.setWindowTitle(_("context_title"))
        self.lbl_hint.setText(_("context_hint"))
        self.lbl_policy.setText(_("context_policy"))
        self.combo_policy.setItemText(0, _("context_policy_always"))
        self.combo_policy.setItemText(1, _("context_policy_mention"))
        self.combo_policy.setItemText(2, _("context_policy_never"))


def _self_check() -> int:
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import shutil
    import tempfile

    from PyQt6.QtWidgets import QApplication
    from core.project import Project
    from core.storybible import StoryBible

    _app = QApplication.instance() or QApplication([])
    checks = 0
    failures = 0

    def kolla(ok, text):
        nonlocal checks, failures
        checks += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            failures += 1

    class Config:
        def __init__(self, vals=None):
            self.vals = dict(vals or {})

        def get(self, key, default=None):
            return self.vals.get(key, default)

    root = tempfile.mkdtemp(prefix="ask-panel-")
    try:
        projekt = Project.create(root, "Frågeprov", template="enkel")
        kap = projekt.add_node("chapter", "Första kapitlet")
        scen = projekt.add_node("scene", "Nyckeln", parent=kap.id)
        projekt.write(scen.id, "<p>Anna vände nyckeln i handen och lyssnade "
                               "efter trappan.</p>")
        bible = StoryBible(str(projekt.root / "codex.db"))
        bible.add_entity("Anna", "character", summary="Huvudperson.")

        skickat = []
        panel = AskPanel(ai_client=object(), config_mgr=Config())
        panel.set_project(projekt, bible)
        panel.set_scene(scen.id)
        panel.input_question.setText("var är nyckeln?")

        kolla(panel.lbl_context.text() != "", f"panelen säger sitt läge ({panel.lbl_context.text()!r})")
        items = panel.build_items("var är nyckeln?")
        kolla(any(i.kind == context_mod.KIND_SCENE for i in items),
              f"frågan bygger ett urval ({[i.label for i in items]})")
        kolla(panel.lbl_context.text() != "", "och raden uppdateras med siffrorna")

        # Anropet: AIWorker byts ut mot en attrapp, så provet rör inget nätverk.
        # Patchningen sker i *den här* modulens namnrymd: kör man filen med -m
        # importeras den två gånger (__main__ och ui.ask_panel), och att patcha
        # den andra kopian träffar ingenting — anropet gick då ut på nätet.
        mod = sys.modules[__name__]

        klass = mod.AIWorker
        mod.AIWorker = type("TystArbetare", (object,), {
            "finished": type("S", (), {"connect": staticmethod(lambda *_: None)})(),
            "error": type("S", (), {"connect": staticmethod(lambda *_: None)})(),
            "__init__": lambda self, *a: skickat.append(("worker", a)),
            "start": lambda self: None})

        def _run_question():
            panel.ai = object()
            panel.config = Config({"ai_endpoint": "http://127.0.0.1:20129/v1",
                                   "ai_key": "x", "ai_model": "auto/best-coding"})
            return panel.ask()

        try:
            text = _run_question()
        finally:
            mod.AIWorker = klass

        kolla(skickat != [], "frågan skickar ett anrop")
        kolla("## scen: Nyckeln" in text and "## instruktion: fråga" in text,
              f"och anropet bär urvalet med rubriker ({text.splitlines()[0]!r})")
        kolla("Anna vände nyckeln" in text, "med scenens text")
        if skickat:
            anrop = skickat[0][1]
            kolla(anrop[3] == SYSTEM_PROMPT, "och systemprompten är verktygets egen")
            kolla(anrop[0] == "http://127.0.0.1:20129/v1",
                  f"mot den slutpunkt användaren angett ({anrop[0]})")
            kolla(anrop[2] == "auto/best-coding", "med den valda modellen")
            kolla(anrop[4].startswith("## scen:"), "och urvalet som anropets text")

        # Svaret: citaten blir länkar till rätt scen.
        svar = "Nyckeln nämns i [Nyckeln] och Anna bär den [Anna]. Okänt [Ingenting]."
        html = panel.answer_html(svar)
        kolla(f'href="scene:{scen.id}"' in html, "ett citat på en scen blir en länk till scenen")
        kolla("codex:" in html, "och ett citat på en codexpost en länk till posten")
        kolla("[Ingenting]" in html and html.count("<a ") == 2,
              f"medan ett citat utan träff står kvar som text ({html.count('<a ')} länkar)")

        # Historiken
        panel._on_answer({"content": svar})
        kolla(len(panel.history) == 1 and panel.lst_history.count() == 1,
              "svaret hamnar i historiken")
        panel._on_history_clicked(panel.lst_history.item(0))
        kolla(panel.input_question.text() == "var är nyckeln?",
              "och ett klick i historiken tar tillbaka frågan")

        # Kontextvisaren
        visare = ContextView(panel.items, panel, project=projekt)
        kolla(visare.lst.count() == len(panel.items),
              f"visaren listar varje del ({visare.lst.count()} rader)")
        kolla("—" in visare.lst.item(0).text(), "med skälet i raden")
        codex_rad = next((r for r in range(visare.lst.count())
                          if "codex" in visare.lst.item(r).text()), None)
        kolla(codex_rad is not None, "codexposten finns i listan")
        if codex_rad is not None:
            visare.lst.setCurrentRow(codex_rad)
            kolla(visare.combo_policy.isEnabled(), "och en codexpost går att ställa om")
            visare.combo_policy.setCurrentIndex(2)      # aldrig
            ent_id = visare.lst.item(codex_rad).data(Qt.ItemDataRole.UserRole).entity_id
            kolla(context_mod.codex_policies(projekt).get(ent_id) == context_mod.POLICY_NEVER,
                  "och valet sparas på boken")
            projekt.save()
            omlast = Project.load(projekt.root)
            kolla(context_mod.codex_policies(omlast).get(ent_id) == context_mod.POLICY_NEVER,
                  "och följer med i projektfilen")

        # Utan slutpunkt skickas ingenting — och det sägs.
        panel.config = Config()
        panel.view_answer.setPlainText("")
        svar_tom = panel.ask()
        kolla(svar_tom == "" and panel.view_answer.toPlainText() == _("ask_no_endpoint"),
              f"utan slutpunkt skickas inget och det sägs ({panel.view_answer.toPlainText()[:40]!r})")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"ask_panel: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
