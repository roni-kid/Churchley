"""Separate fullscreen lyric display window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from .data import Hymn, Verse


class DisplayWindow(QMainWindow):
    """Projector-facing window containing lyric content only."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Churchley Display")
        self.setStyleSheet("background-color: #05070a; color: #f5f7fa;")

        content = QWidget()
        content.setObjectName("displayContent")
        content.setStyleSheet("#displayContent { background-color: #05070a; }")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(100, 70, 100, 70)
        layout.setSpacing(30)

        self.hymn_label = QLabel()
        self.hymn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hymn_label.setStyleSheet(
            "color: #8fa6bf; font-size: 24px; font-weight: 600;"
        )
        layout.addWidget(self.hymn_label)

        self.lyrics_label = QLabel()
        self.lyrics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyrics_label.setWordWrap(True)
        self.lyrics_label.setStyleSheet(
            "color: #ffffff; font-size: 52px; font-weight: 600;"
        )
        layout.addWidget(self.lyrics_label, stretch=1)

        self.verse_label = QLabel()
        self.verse_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verse_label.setStyleSheet(
            "color: #8fa6bf; font-size: 20px; font-weight: 500;"
        )
        layout.addWidget(self.verse_label)
        self.setCentralWidget(content)
        self.clear_display()

    def show_hymn_verse(self, hymn: Hymn, verse: Verse) -> None:
        """Show one verse and its minimal identifying context."""

        self.hymn_label.setText(f"{hymn.number}  ·  {hymn.title}")
        self.lyrics_label.setText(verse.lyrics)
        self.verse_label.setText(f"Verse {verse.number}")
        self.hymn_label.show()
        self.lyrics_label.show()
        self.verse_label.show()

    def clear_display(self) -> None:
        """Blank the display immediately for the panic-clear action."""

        self.hymn_label.clear()
        self.lyrics_label.clear()
        self.verse_label.clear()

    def show_on_projector(self) -> None:
        """Open fullscreen on the second screen when one is available.

        On a single-monitor setup, the display opens as a large (but not
        fullscreen) window so the operator window remains accessible.
        """

        screens = QGuiApplication.screens()
        if len(screens) > 1:
            target_screen = screens[1]
            self.setGeometry(target_screen.geometry())
            self.showFullScreen()
        else:
            screen = screens[0]
            geometry = screen.availableGeometry()
            display_width = int(geometry.width() * 0.45)
            display_height = int(geometry.height() * 0.85)
            display_x = geometry.right() - display_width
            display_y = geometry.top()
            self.setGeometry(display_x, display_y, display_width, display_height)
            self.show()
