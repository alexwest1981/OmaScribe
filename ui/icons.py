"""
ui/icons.py — linjeikoner (Lucide, ISC) som QIcon i temats färg.

Referensen ritar ikoner i samma färg som texten (`stroke="currentColor"`).
Här byts `currentColor` mot den färg som efterfrågas innan SVG:n renderas, så
samma fil kan vara grå i en rad och accentfärgad i en annan — och varje tema
får sina egna ikoner utan att några filer behöver bytas.

    icon("file-text", "#87909b", 18)

Saknas filen returneras en tom QIcon, och anroparen behåller sin text i stället.
"""

from pathlib import Path

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap

ICON_DIR = Path(__file__).resolve().parent.parent / "resources" / "icons"

_cache: dict[tuple[str, str, int], QIcon] = {}


def icon(name: str, color: str = "#000000", size: int = 16) -> QIcon:
    """Ikonen `name` i färgen `color`, ritad i `size` px (2x för HiDPI)."""
    key = (name, color, size)
    if key in _cache:
        return _cache[key]

    path = ICON_DIR / f"{name}.svg"
    if not path.exists():
        _cache[key] = QIcon()
        return _cache[key]

    if not _has_painter():
        _cache[key] = QIcon(str(path))
        return _cache[key]

    from PyQt6.QtSvg import QSvgRenderer

    svg = path.read_text(encoding="utf-8").replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pm = QPixmap(size * 2, size * 2)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    renderer.render(painter)
    painter.end()
    pm.setDevicePixelRatio(2.0)
    _cache[key] = QIcon(pm)
    return _cache[key]


def has(name: str) -> bool:
    return (ICON_DIR / f"{name}.svg").exists()


def _has_painter() -> bool:
    """QSvgRenderer finns bara om QtSvg är installerat; annars får Qt:s egen
    SVG-läsare sköta det (färgen blir då svart)."""
    from PyQt6.QtWidgets import QApplication
    if QApplication.instance() is None:
        return False
    try:
        from PyQt6.QtSvg import QSvgRenderer  # noqa: F401
        return True
    except ImportError:
        return False
