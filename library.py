"""Operator dialogs for adding and importing hymns."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from .importer import parse_bulk_hymns


class AddHymnDialog(QDialog):
    """Manual hymn entry dialog."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add hymn")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("e.g. 101")
        form.addRow("Number", self.number_input)
        self.title_input = QLineEdit()
        form.addRow("Title", self.title_input)
        self.tune_input = QLineEdit()
        form.addRow("Tune", self.tune_input)
        self.tags_input = QLineEdit()
        form.addRow("Tags", self.tags_input)
        layout.addLayout(form)

        layout.addWidget(QLabel("Verses (separate verses with a blank line)"))
        self.verses_input = QTextEdit()
        self.verses_input.setMinimumHeight(230)
        self.verses_input.setPlaceholderText("First verse...\n\nSecond verse...")
        layout.addWidget(self.verses_input)

        buttons = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        save_button = QPushButton("Add hymn")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self._validate_and_accept)
        buttons.addStretch()
        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)
        layout.addLayout(buttons)

    def _validate_and_accept(self) -> None:
        if not self.number_input.text().strip():
            QMessageBox.warning(self, "Missing number", "Enter a hymn number.")
            return
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Missing title", "Enter a hymn title.")
            return
        verses = tuple(
            verse.strip()
            for verse in self.verses_input.toPlainText().split("\n\n")
            if verse.strip()
        )
        if not verses:
            QMessageBox.warning(self, "Missing verses", "Enter at least one verse.")
            return
        self.accept()

    def hymn_data(self) -> dict[str, object]:
        verses = tuple(
            verse.strip()
            for verse in self.verses_input.toPlainText().split("\n\n")
            if verse.strip()
        )
        return {
            "number": self.number_input.text().strip(),
            "title": self.title_input.text().strip(),
            "tune_name": self.tune_input.text().strip(),
            "tags": self.tags_input.text().strip() or None,
            "verses": verses,
        }


def choose_import_file(parent=None) -> list[dict[str, object]] | None:
    """Select and parse one bulk import file, showing errors in the UI."""

    file_name, _ = QFileDialog.getOpenFileName(
        parent,
        "Import hymns",
        "",
        "Text files (*.txt);;All files (*.*)",
    )
    if not file_name:
        return None
    try:
        records = parse_bulk_hymns(Path(file_name).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        QMessageBox.critical(parent, "Import failed", str(error))
        return None
    return [asdict(record) for record in records]
