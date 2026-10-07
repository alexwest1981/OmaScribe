"""ui/scrivenings.py — läsvyn: flera scener som ett sammanhängande manus.

Scenerna läggs efter varandra i EN text med en rubrikrad per scen, så ett
kapitel (eller hela manuset) kan läsas i ett svep. Rubrikraden bär scenens namn
och ordantal, och ett klick på den öppnar scenen i den vanliga editorn.

Vyn går att skriva i. Varje stycke märks med vilken scen det hör till
(_BlockInfo), så texten kan skrivas tillbaka till rätt fil — rubrikraderna
hoppas över, och ett nytt stycke (Enter) hör till samma scen som stycket före.
Ett klick i prosan sätter markören; ett klick på en rubrikrad öppnar scenen.

    python -m ui.scrivenings      kör självprovet (offscreen)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QPalette, QTextBlockFormat, QTextBlockUserData, QTextCharFormat, QTextCursor,
    QTextDocumentFragment,
)
from PyQt6.QtWidgets import (
    QLabel, QTextEdit, QVBoxLayout, QWidget,
)

from core.i18n import _, i18n

CARD_LIMIT = 120          # scener i en och samma läsvy innan vyn kapar


class _BlockInfo(QTextBlockUserData):
    """Vilken scen ett stycke hör till — och om det är läsvyns rubrikrad."""

    def __init__(self, node_id: str, heading: bool = False):
        super().__init__()
        self.node_id = node_id
        self.heading = heading


class _ReadingPane(QTextEdit):
    """Skrivytan. Klick och Escape översätts till signaler i stället för länkar."""

    scene_clicked = pyqtSignal(str)
    escape_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAcceptRichText(True)
        self.setTabChangesFocus(False)      # tab i texten skall bli tab, inte fokusbyte

    # ------------------------------------------------------------- märkningen

    def info_at(self, position: int):
        """(scen-id, är rubrik) för textpositionen, eller (None, False).

        Ett stycke utan märkning (nytt, efter Enter) ärver stycket före — det är
        samma sak som att skriva vidare i samma scen.
        """
        block = self.document().findBlock(position)
        while block.isValid():
            info = block.userData()
            if isinstance(info, _BlockInfo):
                return info.node_id, info.heading
            block = block.previous()
        return None, False

    def node_at(self, position: int):
        """Scenen som innehåller textpositionen, annars None."""
        return self.info_at(position)[0]

    def heading_at(self, position: int) -> bool:
        return self.info_at(position)[1]

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.position().toPoint())
            node_id, heading = self.info_at(cursor.position())
            if node_id and heading:                 # rubriken är en rad, inte prosa
                self.scene_clicked.emit(node_id)
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.escape_pressed.emit()
            return
        super().keyPressEvent(event)


class ScriveningsView(QWidget):
    """Flera scener som en text. Ett klick på en scenrubrik öppnar scenen."""

    scene_activated = pyqtSignal(str)      # node_id
    closed = pyqtSignal()

    def __init__(self, parent=None, limit: int = CARD_LIMIT):
        super().__init__(parent)
        self.limit = limit
        self.project = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.lbl_info = QLabel()
        self.lbl_info.setContentsMargins(12, 8, 12, 8)
        self.lbl_info.setWordWrap(True)
        layout.addWidget(self.lbl_info)

        self.pane = _ReadingPane()
        self.pane.scene_clicked.connect(self.scene_activated)
        self.pane.escape_pressed.connect(self.closed)
        self.pane.document().contentsChange.connect(self._on_contents_change)
        layout.addWidget(self.pane, 1)

        i18n.language_changed.connect(self.retranslate_ui)
        self._shown: list = []
        self._original: dict = {}
        self.cut = 0
        self.heading = ""

    # ------------------------------------------------------------------ bygget

    def set_content(self, project, nodes, heading: str = "") -> int:
        """Bygger läsvyn av noderna (i den ordning de skall läsas). Antal visade."""
        self.project = project
        self._shown = list(nodes)[: self.limit]
        self.cut = len(nodes) - len(self._shown)

        muted = self.palette().color(QPalette.ColorRole.PlaceholderText)
        doc = self.pane.document()
        doc.clear()
        cursor = QTextCursor(doc)
        self._original: dict[str, str] = {}

        heading_block = QTextBlockFormat()
        heading_block.setTopMargin(16)
        heading_block.setBottomMargin(2)
        heading_char = QTextCharFormat()
        heading_char.setForeground(muted)
        heading_char.setFontPointSize(9)

        first = True
        for node in self._shown:
            if not first:
                cursor.insertBlock()
            first = False
            cursor.setBlockFormat(heading_block)
            cursor.insertText(
                f"{node.title} — {_('scene_words', words=project.words(node.id))}", heading_char)
            cursor.block().setUserData(_BlockInfo(node.id, heading=True))
            cursor.insertBlock()
            # insertHtml lägger texten i samma stycke som rubriken; insertFragment
            # behåller styckesindelningen från scenens fil. Char-formatet nollställs
            # så scenens text inte ärver rubrikens gråa nio punkter.
            cursor.setCharFormat(QTextCharFormat())
            forste = doc.findBlock(cursor.position())
            cursor.insertFragment(QTextDocumentFragment.fromHtml(project.read(node.id)))
            siste = doc.findBlock(cursor.position())
            block = forste
            while block.isValid():
                block.setUserData(_BlockInfo(node.id))
                if block == siste:
                    break
                block = block.next()
            self._original[node.id] = self._html_for(node.id)
        self.pane.moveCursor(QTextCursor.MoveOperation.Start)
        self.heading = heading or (project.title if project else "")
        self._refresh_info()
        return len(self._shown)

    # -------------------------------------------------------- tillbaka till fil

    def _iter_marked(self, node_id: str):
        """Styckena som hör till scenen, i ordning. Rubrikraden är inte med."""
        doc = self.pane.document()
        block = doc.begin()
        while block.isValid():
            info = block.userData()
            if (isinstance(info, _BlockInfo) and info.node_id == node_id
                    and not info.heading):
                yield block
            block = block.next()

    def _runs(self, node_id: str) -> list[tuple]:
        """Scenens stycken som sammanhängande stycken — oftast ett enda."""
        runs: list[list] = []
        for block in self._iter_marked(node_id):
            if runs and runs[-1][-1].next() == block:
                runs[-1].append(block)
            else:
                runs.append([block])
        return [(run[0], run[-1]) for run in runs]

    def _html_for(self, node_id: str) -> str:
        """Scenens text som HTML, byggd ur styckena i vyn."""
        delar = []
        for forst, sist in self._runs(node_id):
            cursor = QTextCursor(self.pane.document())
            cursor.setPosition(forst.position())
            cursor.setPosition(sist.position() + sist.length() - 1,
                               QTextCursor.MoveMode.KeepAnchor)
            delar.append(QTextDocumentFragment(cursor).toHtml())
        return "".join(delar)

    def content_by_node(self) -> dict:
        """Vyens text per scen, nycklad på nod-id."""
        return {node.id: self._html_for(node.id) for node in self._shown}

    def changed_content(self) -> dict:
        """Bara de scener vars text ändrats sedan vyn byggdes (eller sparades).

        Jämförelsen är mot vyens eget utgångsläge, inte mot filen: vyn bygger om
        formateringen när texten läses in, och det skall inte räknas som en ändring.
        """
        return {node_id: html for node_id, html in self.content_by_node().items()
                if html != self._original.get(node_id)}

    def mark_saved(self) -> None:
        """Efter skrivning: vyn är sitt eget utgångsläge igen."""
        self._original = self.content_by_node()

    def _on_contents_change(self, position: int, removed: int, added: int) -> None:
        """Nya stycken ärver scenen från stycket före.

        Enter mitt i en scen betyder 'samma scen', inte 'okänd' — ett omärkt
        stycke annars skulle tappas tyst när texten skrivs tillbaka.
        """
        doc = self.pane.document()
        block = doc.findBlock(position)
        while block.isValid() and block.position() <= position + added:
            if not isinstance(block.userData(), _BlockInfo):
                node_id, _ = self.pane.info_at(max(0, block.position() - 1))
                if node_id:
                    block.setUserData(_BlockInfo(node_id))
            block = block.next()

    def _refresh_info(self) -> None:
        words = sum(self.project.words(n.id) for n in self._shown) if self.project else 0
        text = _("scrivenings_info", heading=self.heading,
                 scenes=len(self._shown), words=words)
        if self.cut:
            text += " " + _("scrivenings_cut", cut=self.cut, limit=self.limit)
        self.lbl_info.setText(text)

    def shown_nodes(self) -> list:
        return list(self._shown)

    def retranslate_ui(self) -> None:
        self._refresh_info()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.closed.emit()
            return
        super().keyPressEvent(event)


def _self_check() -> int:
    import os
    import tempfile
    from pathlib import Path

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from core.project import Project, SCENE

    checks = 0
    failures: list[str] = []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    tmp = Path(tempfile.mkdtemp())
    book = Project.create(tmp / "bok", "Boken")
    kapitel = book.children(None)[0]
    ett = book.children(kapitel.id)[0]
    book.write(ett.id, "<p>Alfa beta.</p>")
    tva = book.add_node(SCENE, "Scen två", parent=kapitel.id)
    book.write(tva.id, "<p>Gamma <b>delta</b> epsilon.</p>")
    tre = book.add_node(SCENE, "Scen tre", parent=kapitel.id)
    book.write(tre.id, "<p>Zeta eta.</p>")

    view = ScriveningsView(limit=2)
    klick: list[str] = []
    stangd: list[int] = []
    view.scene_activated.connect(klick.append)
    view.closed.connect(lambda: stangd.append(1))

    antal = view.set_content(book, book.manuscript(), heading="Kapitel 1")
    check(antal == 2, f"vyn kapar vid gränsen ({antal} av 3)")
    check(view.cut == 1, f"vyn vet hur många den kapade ({view.cut})")
    check("Kapitel 1" in view.lbl_info.text(), f"rubriken syns i informationsraden ({view.lbl_info.text()!r})")
    check(str(antal) in view.lbl_info.text() and "2" in view.lbl_info.text(),
          f"informationsraden räknar scenerna ({view.lbl_info.text()!r})")

    text = view.pane.toPlainText()
    check("Alfa beta." in text and "Gamma" in text and "delta" in text,
          f"scenernas text finns med ({text[:60]!r})")
    check("Zeta eta." not in text, "den kapade scenen visas inte")
    check(text.index("Alfa") < text.index("Gamma"), "texterna kommer i läsordning")
    check("Scen två" in text, "scenrubriken står i texten")
    check(view.pane.document().blockCount() > 3, "texten byggdes som egna stycken")

    # riksdokumentet: feta ordet skall överleva in i läsvyn
    doc = view.pane.document()
    found_bold = False
    for nummer in range(doc.blockCount()):
        it = doc.findBlockByNumber(nummer).begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid() and "delta" in frag.text() and frag.charFormat().fontWeight() > 500:
                found_bold = True
            it += 1
    check(found_bold, "fetstilen överlever in i läsvyn")

    # scenens text skall inte ärva rubrikens gråa nio punkter
    vanlig = None
    for nummer in range(doc.blockCount()):
        it = doc.findBlockByNumber(nummer).begin()
        while not it.atEnd():
            frag = it.fragment()
            if frag.isValid() and "Alfa" in frag.text():
                vanlig = frag.charFormat()
            it += 1
    check(vanlig is not None and (vanlig.foreground().style() == Qt.BrushStyle.NoBrush
          or vanlig.foreground().color() != view.palette().color(QPalette.ColorRole.PlaceholderText)),
          f"scenens text ärver inte rubrikens gråa ({vanlig.foreground().color().name() if vanlig else None})")

    # klick inuti en scen pekar på rätt scen
    forsta_scen_block = next(
        n for n in range(doc.blockCount()) if "Alfa" in doc.findBlockByNumber(n).text())
    forsta_pos = doc.findBlockByNumber(forsta_scen_block).position()
    check(view.pane.node_at(forsta_pos) == ett.id,
          f"en position i scen ett pekar på scen ett ({view.pane.node_at(forsta_pos)})")
    siste_pos = doc.findBlockByNumber(doc.blockCount() - 1).position()
    check(view.pane.node_at(siste_pos) == tva.id,
          f"en position i sista scenen pekar rätt ({view.pane.node_at(siste_pos)} mot {tva.id})")
    rubrik_pos = doc.findBlockByNumber(0).position()
    check(view.pane.node_at(rubrik_pos) == ett.id, "även scenrubriken pekar på sin scen")

    view.pane.scene_clicked.emit(ett.id)
    check(klick == [ett.id], f"klicket når vidare ({klick})")
    view.pane.escape_pressed.emit()
    check(stangd == [1], "Escape stänger läsvyn")

    # ------------------------------------------------ att skriva i vyn (R01.9)

    check(view.changed_content() == {},
          f"en orörd vy har inget att skriva ({list(view.changed_content())})")

    def skriv_efter(scen_id, text):
        """Sätter markören sist i scenens sista stycke och skriver vidare där."""
        sista = None
        for block in view._iter_marked(scen_id):
            sista = block
        cursor = QTextCursor(sista)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        cursor.insertText(text)

    skriv_efter(ett.id, " Och lite till.")
    andrat = view.changed_content()
    check(set(andrat) == {ett.id}, f"bara scenen jag skrev i ändras ({list(andrat)})")
    check("Och lite till." in andrat[ett.id], "och texten hänger med")
    check("Gamma" not in andrat[ett.id], "aldrig grannscenens text")
    check("Scen ett —" not in andrat[ett.id],
          f"rubrikraden skrivs inte in i scenen ({andrat[ett.id][:60]!r})")
    check("Alfa beta." in andrat[ett.id], "och det som stod där är kvar")

    # Enter sist i en scen: det nya stycket hör till samma scen
    sista = None
    for block in view._iter_marked(ett.id):
        sista = block
    cursor = QTextCursor(sista)
    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
    cursor.insertBlock()
    cursor.insertText("Nytt stycke.")
    andrat = view.changed_content()
    check("Nytt stycke." in andrat[ett.id], "ett nytt stycke hör till scenen jag stod i")
    check(tva.id not in andrat, "och grannscenen är fortfarande orörd")

    # tillbaka till fil, samma väg som fönstret tar
    for node_id, html in view.changed_content().items():
        book.write(node_id, html)
    view.mark_saved()
    check(view.changed_content() == {}, "efter skrivningen är vyn sitt utgångsläge")
    check("Och lite till." in book.read(ett.id), "texten ligger i scenens fil")
    check("Nytt stycke." in book.read(ett.id), "med det nya stycket")
    check("Gamma" in book.read(tva.id) and "Och lite till." not in book.read(tva.id),
          "och grannscenens fil är orörd")

    # en scen som fått text mitt i skrivs tillbaka utan att tappa stycken
    book.write(tre.id, "<p>Första.</p><p>Andra.</p>")
    view.set_content(book, [tre], heading="En scen")
    forsta_block = next(iter(view._iter_marked(tre.id)))
    cursor = QTextCursor(forsta_block)
    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
    cursor.insertText(" Mer.")
    ett_stycke = view.changed_content()[tre.id]
    check(ett_stycke.count("<p") == 2, f"båda styckena är med ({ett_stycke.count('<p')})")
    check("Mer." in ett_stycke and "Andra." in ett_stycke, "med ändringen i det första")

    # ett tomt projekt skall inte krascha
    tom = Project.create(tmp / "tom", "Tom")
    check(view.set_content(tom, [], heading="Tomt") == 0, "en tom läsvy går att bygga")

    print(f"scrivenings: {checks - len(failures)} av {checks} kontroller gröna")
    for failure in failures:
        print(f"  ✗ {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
