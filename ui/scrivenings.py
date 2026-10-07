"""ui/scrivenings.py — läsvyn: flera scener som ett sammanhängande manus.

Scenerna läggs efter varandra i EN text med en rubrikrad per scen, så ett
kapitel (eller hela manuset) kan läsas i ett svep. Rubrikraden bär scenens namn
och ordantal, och ett klick på den öppnar scenen i den vanliga editorn.

Vyn är läsbar, inte redigerbar: formateringen i verktygsraden pekar på
`MainWindow.editor.canvas`, och att rikta om den mot den scen som råkar ha
fokus är ett eget steg. Ett halvt redigeringsläge som formaterar fel scen vore
värre än inget, så här finns ingen skrivyta att luras av.

    python -m ui.scrivenings      kör självprovet (offscreen)
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QPalette, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocumentFragment,
)
from PyQt6.QtWidgets import (
    QLabel, QTextBrowser, QVBoxLayout, QWidget,
)

from core.i18n import _, i18n

CARD_LIMIT = 120          # scener i en och samma läsvy innan vyn kapar


class _ReadingPane(QTextBrowser):
    """Lästruten. Klick och Escape översätts till signaler i stället för länkar."""

    scene_clicked = pyqtSignal(str)
    escape_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenExternalLinks(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._ranges: list[tuple[int, int, str]] = []

    def set_ranges(self, ranges) -> None:
        self._ranges = ranges

    def node_at(self, position: int):
        """Vilken scen som helst innehåller textpositionen, annars None."""
        block = self.document().findBlock(position).blockNumber()
        for start, end, node_id in self._ranges:
            if start <= block < end:
                return node_id
        return None

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.position().toPoint())
            node_id = self.node_at(cursor.position())
            if node_id:
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
        layout.addWidget(self.pane, 1)

        i18n.language_changed.connect(self.retranslate_ui)
        self._shown: list = []
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
        ranges: list[tuple[int, int, str]] = []

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
            before = cursor.blockNumber()          # rubriken börjar här, och den är klickbar
            cursor.setBlockFormat(heading_block)
            cursor.insertText(
                f"{node.title} — {_('scene_words', words=project.words(node.id))}", heading_char)
            cursor.insertBlock()
            # insertHtml lägger texten i samma stycke som rubriken; insertFragment
            # behåller styckesindelningen från scenens fil. Char-formatet nollställs
            # så scenens text inte ärver rubrikens gråa nio punkter.
            cursor.setCharFormat(QTextCharFormat())
            cursor.insertFragment(QTextDocumentFragment.fromHtml(project.read(node.id)))
            ranges.append((before, doc.blockCount(), node.id))

        self.pane.set_ranges(ranges)
        self.pane.moveCursor(QTextCursor.MoveOperation.Start)
        self.heading = heading or (project.title if project else "")
        self._refresh_info()
        return len(ranges)

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

    # ett tomt projekt skall inte krascha
    tom = Project.create(tmp / "tom", "Tom")
    check(view.set_content(tom, [], heading="Tomt") == 0, "en tom läsvy går att bygga")

    print(f"scrivenings: {checks - len(failures)} av {checks} kontroller gröna")
    for failure in failures:
        print(f"  ✗ {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
