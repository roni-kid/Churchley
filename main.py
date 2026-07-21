"""Churchley application entry point."""

from __future__ import annotations

from pathlib import Path
import sqlite3
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from churchley.data import HymnRepository
from churchley.display import DisplayWindow
from churchley.operator import ControlWindow


def default_database_path() -> Path:
    """Return a user-writable database location for source and packaged runs."""

    data_directory = Path.home() / "Churchley"
    data_directory.mkdir(parents=True, exist_ok=True)
    return data_directory / "churchley.db"


def _startup_database(database_path: Path) -> HymnRepository:
    """Open or create the hymn database, handling common startup failures."""
    try:
        return HymnRepository(database_path)
    except sqlite3.OperationalError as error:
        message = (
            f"Churchley cannot open its database:\n\n"
            f"{error}\n\n"
            f"Path: {database_path}\n\n"
            f"Check that the file is not locked by another process "
            f"and that the folder is writable."
        )
        raise SystemExit(message) from error
    except sqlite3.DatabaseError as error:
        message = (
            f"Churchley's database appears corrupted:\n\n"
            f"{error}\n\n"
            f"Path: {database_path}\n\n"
            f"To recover, rename or delete this file and restart Churchley. "
            f"A fresh database will be created automatically."
        )
        raise SystemExit(message) from error


def main() -> int:
    application = QApplication(sys.argv)
    repository = _startup_database(default_database_path())
    display = DisplayWindow()
    control = ControlWindow(repository, display)
    display.show_on_projector()
    control.show()
    exit_code = application.exec()
    repository.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
