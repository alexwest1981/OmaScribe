import os
from PyQt6.QtGui import QFontDatabase, QFont, QColor
from PyQt6.QtWidgets import QComboBox, QStyledItemDelegate, QListView
from PyQt6.QtCore import Qt, pyqtSignal

USER_FONTS_DIR = os.path.expanduser("~/.config/omascribe/fonts")
APP_FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "fonts")

# Curated popular writing & document fonts
POPULAR_FONTS = [
    # Clean Modern Sans
    "Inter",
    "Poppins",
    "Montserrat",
    "Adwaita Sans",
    "Liberation Sans",
    "Roboto",
    "Open Sans",
    "Lato",
    "Arial",
    "Helvetica",
    "DejaVu Sans",
    "Carlito",
    "Cantarell",
    "Ubuntu",
    "Noto Sans",
    # Editorial Serif
    "Playfair Display",
    "Merriweather",
    "Lora",
    "Cinzel",
    "Liberation Serif",
    "DejaVu Serif",
    "Times New Roman",
    "Georgia",
    "Noto Serif",
    "Garamond",
    "C059",
    "Nimbus Roman",
    # Monospace & Code
    "JetBrains Mono",
    "JetBrainsMono Nerd Font",
    "Fira Code",
    "Source Code Pro",
    "Liberation Mono",
    "DejaVu Sans Mono",
    "Adwaita Mono",
    "Courier New",
    # Creative & Handwriting
    "Pacifico",
    "Caveat",
    "Dancing Script",
    "Oswald"
]

SKIP_KEYWORDS = {
    "math", "tex", "emoji", "awesome", "brands", "compatibility",
    "rotated", "vertical", "dingbats", "symbol", "music", "braille",
    "phonetic", "icon", "glyph", "legacy", "dummy", "lastresort",
    "rashi", "nastaliq", "kufi", "hieroglyphs", "cuneiform", "linear",
    "inscriptional", "old", "imperial", "warang", "zanabazar", "mro",
    "bhaiksuki", "chorasmian", "elymaic", "hatran", "lycian", "lydian",
    "meroitic", "nabataean", "palmyrene", "parthian", "pau cin hau",
    "phags-pa", "phoenician", "psalter", "samaritan", "saurashtra",
    "sharada", "shavian", "siddham", "signwriting", "sora", "soyombo",
    "tagalog", "tagbanwa", "tangut", "tifinagh", "tirhuta", "ugaritic"
}

ALLOWED_NOTO = {
    "Noto Sans", "Noto Serif", "Noto Sans Mono", "Noto Sans Display",
    "Noto Serif Display", "Noto Color Emoji"
}

class FontItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        font_family = index.data(Qt.ItemDataRole.UserRole)
        is_header = index.data(Qt.ItemDataRole.UserRole + 1) == "header"
        
        opt = option
        self.initStyleOption(opt, index)
        
        if is_header:
            opt.font.setBold(True)
            opt.font.setPointSize(9)
        elif font_family and isinstance(font_family, str):
            opt.font.setFamily(font_family)
            opt.font.setPointSize(11)
            
        super().paint(painter, opt, index)


class FontManager:
    @staticmethod
    def load_custom_fonts():
        """Loads bundled and user TTF/OTF fonts into QFontDatabase."""
        loaded_count = 0
        for directory in [APP_FONTS_DIR, USER_FONTS_DIR]:
            if os.path.exists(directory):
                for fname in os.listdir(directory):
                    if fname.lower().endswith((".ttf", ".otf", ".woff")):
                        fpath = os.path.join(directory, fname)
                        font_id = QFontDatabase.addApplicationFont(fpath)
                        if font_id != -1:
                            loaded_count += 1
        return loaded_count

    @staticmethod
    def get_organized_font_list():
        system_fonts = set(QFontDatabase.families())
        
        # 1. Popular available fonts
        available_popular = [f for f in POPULAR_FONTS if f in system_fonts]
        
        # 2. Filter out non-writing system, ancient scripts, and technical fonts
        filtered_all = []
        for f in sorted(system_fonts):
            f_lower = f.lower()
            if any(k in f_lower for k in SKIP_KEYWORDS):
                continue
            # Filter out hundreds of Noto ancient/foreign script sub-fonts
            if f.startswith("Noto ") and f not in ALLOWED_NOTO:
                continue
            if f not in available_popular:
                filtered_all.append(f)

        return available_popular, filtered_all


class FontSelectorComboBox(QComboBox):
    font_selected = pyqtSignal(QFont)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Use an explicit QListView so Qt creates a solid floating popup with scrollbar
        self.list_view = QListView(self)
        self.list_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_view.setMinimumWidth(220)
        self.setView(self.list_view)
        
        self.setItemDelegate(FontItemDelegate(self))
        self.setFixedWidth(180)
        self.setMaxVisibleItems(14)
        
        self.populate_fonts()
        self.currentIndexChanged.connect(self._on_index_changed)

    def populate_fonts(self):
        self.blockSignals(True)
        self.clear()
        
        popular, all_fonts = FontManager.get_organized_font_list()

        # Popular section
        self.addItem("── ⭐ Popular Writing Fonts ──", None)
        self.setItemData(self.count() - 1, "header", Qt.ItemDataRole.UserRole + 1)
        self.setItemData(self.count() - 1, 0, Qt.ItemDataRole.UserRole - 1)

        for font in popular:
            self.addItem(font, font)
            self.setItemData(self.count() - 1, font, Qt.ItemDataRole.UserRole)

        # All fonts section
        if all_fonts:
            self.addItem("── 🔤 All Fonts (A–Z) ──", None)
            self.setItemData(self.count() - 1, "header", Qt.ItemDataRole.UserRole + 1)

            for font in all_fonts:
                self.addItem(font, font)
                self.setItemData(self.count() - 1, font, Qt.ItemDataRole.UserRole)

        self.blockSignals(False)

    def select_font_family(self, family):
        self.blockSignals(True)
        for i in range(self.count()):
            if self.itemData(i, Qt.ItemDataRole.UserRole) == family:
                self.setCurrentIndex(i)
                break
        self.blockSignals(False)

    def _on_index_changed(self, index):
        family = self.itemData(index, Qt.ItemDataRole.UserRole)
        if family:
            self.font_selected.emit(QFont(family))
        elif self.itemData(index, Qt.ItemDataRole.UserRole + 1) == "header":
            # Jump past header
            if index + 1 < self.count():
                self.setCurrentIndex(index + 1)
