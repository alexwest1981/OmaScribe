"""
ui/widgets.py — delade gränssnittsbyggstenar för OmaScribe.

ClickableCard finns här av ett skäl: ett klickbart kort får inte vara en
QPushButton.

En QPushButton räknar sin storlek ur sin egen text och ikon och struntar helt i
en layout som ligger inuti den. Sätter stilmallen (global eller lokal) en box på
knappen — appens globala regel ger `min-height: 22px` + `padding: 6px 16px` +
1 px ram = 36 px — så blir knappen 36 px hög, medan etiketterna inuti får dela
på de pixlarna och kläms ihop till en enda pixel per rad. Kortet ser tomt ut och
texten går inte att läsa.

En QFrame räknar in sin layout i både storlek och minimum, så kortet blir så
högt som innehållet kräver och växer när teckensnittet blir större (till exempel
med GDK_SCALE=2, som ger Qt dubbelt så stora teckensnitt via GTK-temat).
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QBoxLayout, QFrame


class ClickableCard(QFrame):
    """Ett klickbart kort som växer med sitt innehåll.

    Använd ``card.body`` som layout för innehållet (``orientation`` avgör om den
    är lodrät eller vågrät). Stilmallen når kortet via dess ``objectName``
    (t.ex. ``#ActionCard``), precis som förut — men regeln gäller nu en ram som
    respekterar sina barn.
    """

    clicked = pyqtSignal()

    def __init__(self, parent=None, object_name: str = "ClickableCard",
                 orientation: Qt.Orientation = Qt.Orientation.Vertical):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        direction = (QBoxLayout.Direction.LeftToRight
                     if orientation == Qt.Orientation.Horizontal
                     else QBoxLayout.Direction.TopToBottom)
        self.body = QBoxLayout(direction, self)

    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton
                and self.rect().contains(event.position().toPoint())):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)
