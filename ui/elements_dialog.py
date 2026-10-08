"""ui/elements_dialog.py — scenens story-element (2.19).

Fictionary ställer frågor per scen och författaren svarar i några ord. Dialogen
är därför tjugo korta fält i tre grupper (karaktär, handling, miljö), inte en
blankett: ett tomt fält är ett svar som inte givits, och den räknaren står längst
ned så författaren ser hur många luckor som är kvar.

Dialogen äger ingen data. Den får scenen, lämnar sina värden ifrån sig, och
sceninspektören skriver dem vidare — samma väg som all annan scenmetadata.

    python -m ui.elements_dialog      kör självprovet (offscreen)
"""

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QGroupBox, QLabel, QLineEdit, QFormLayout,
    QScrollArea, QVBoxLayout, QWidget,
)

from core import story_elements
from core.i18n import _, i18n


class ElementsDialog(QDialog):
    """Ett fält per story-element, grupperat i sina tre familjer."""

    def __init__(self, node, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("elements_title"))
        self.setModal(True)
        self.resize(420, 560)
        self.fields: dict[str, QLineEdit] = {}

        svar = getattr(node, "elements", None) or {}
        layout = QVBoxLayout(self)

        rubrik = QLabel(_("elements_hint"))
        rubrik.setWordWrap(True)
        layout.addWidget(rubrik)

        inre = QWidget()
        inre_layout = QVBoxLayout(inre)
        inre_layout.setContentsMargins(0, 0, 0, 0)
        for familj in story_elements.FAMILIES:
            grupp = QGroupBox(_(f"element_family_{familj}"))
            form = QFormLayout(grupp)
            for key in story_elements.of_family(familj):
                fält = QLineEdit(str(svar.get(key, "")))
                fält.setPlaceholderText(_("elements_placeholder"))
                fält.textChanged.connect(self._update_count)
                form.addRow(_(f"element_{key}"), fält)
                self.fields[key] = fält
            inre_layout.addWidget(grupp)
        inre_layout.addStretch(1)

        ruta = QScrollArea()
        ruta.setWidgetResizable(True)
        ruta.setWidget(inre)
        layout.addWidget(ruta, 1)

        self.label_count = QLabel("")
        layout.addWidget(self.label_count)

        knappar = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                                   | QDialogButtonBox.StandardButton.Cancel)
        knappar.accepted.connect(self.accept)
        knappar.rejected.connect(self.reject)
        layout.addWidget(knappar)

        self.retranslate_ui()
        i18n.language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self) -> None:
        self._update_count()

    def _update_count(self) -> None:
        self.label_count.setText(_("elements_filled", filled=self.filled(),
                                   total=story_elements.TOTAL))

    def filled(self) -> int:
        return sum(story_elements.is_filled(f.text()) for f in self.fields.values())

    def values(self) -> dict:
        """Bara de element som faktiskt besvarats — tomma svar sparas inte."""
        return {key: fält.text().strip() for key, fält in self.fields.items()
                if story_elements.is_filled(fält.text())}


def _self_check() -> int:
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from types import SimpleNamespace
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])   # noqa: F841
    checks = 0
    failures = 0

    def kolla(ok, text):
        nonlocal checks, failures
        checks += 1
        print(f"  {'OK  ' if ok else 'FEL '} {text}")
        if not ok:
            failures += 1

    nod = SimpleNamespace(elements={"pov_character": "Anna"})
    dialog = ElementsDialog(nod)
    kolla(len(dialog.fields) == story_elements.TOTAL,
          f"ett fält per element ({len(dialog.fields)} av {story_elements.TOTAL})")
    kolla(dialog.fields["pov_character"].text() == "Anna",
          "scenens svar står i fältet")
    kolla(dialog.values() == {"pov_character": "Anna"},
          f"och bara besvarade element lämnas ifrån sig ({dialog.values()})")
    kolla(str(story_elements.TOTAL) in dialog.label_count.text(),
          f"räknaren visar av hur många ({dialog.label_count.text()})")

    dialog.fields["weather"].setText("  regn  ")
    kolla(dialog.values().get("weather") == "regn", "ett svar trimmas")
    kolla(dialog.filled() == 2, f"och räknaren följer med ({dialog.filled()})")
    dialog.fields["pov_character"].clear()
    kolla(dialog.values() == {"weather": "regn"},
          f"ett tömt fält blir inget svar ({dialog.values()})")

    print(f"elements_dialog: {checks - failures} av {checks} kontroller gröna")
    return failures


if __name__ == "__main__":
    raise SystemExit(_self_check())
