"""Churchley operator/control window."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .data import Hymn, HymnRepository, Verse
from .display import DisplayWindow
from .library import AddHymnDialog, choose_import_file

_RETARGET_DEBOUNCE_MS = 500


class ControlWindow(QMainWindow):
    """Operator-only window for search, selection, library, and navigation."""

    def __init__(self, repository: HymnRepository, display: DisplayWindow) -> None:
        super().__init__()
        self.repository = repository
        self.display = display
        self.current_hymn: Hymn | None = None
        self.current_verse_number: int | None = None

        self.setWindowTitle("Churchley · Operator")
        self.resize(1120, 720)
        self.setMinimumSize(850, 560)
        self._build_ui()
        self._apply_style()
        self._refresh_results()

        panic_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        panic_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        panic_shortcut.activated.connect(self._panic_clear)

        self._retarget_timer = QTimer(self)
        self._retarget_timer.setSingleShot(True)
        self._retarget_timer.setInterval(_RETARGET_DEBOUNCE_MS)
        self._retarget_timer.timeout.connect(self.display.show_on_projector)
        application = QGuiApplication.instance()
        if application is not None:
            application.screenAdded.connect(self._on_screens_changed)
            application.screenRemoved.connect(self._on_screens_changed)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(36, 30, 36, 30)
        root_layout.setSpacing(20)

        header = QHBoxLayout()
        brand = QLabel("CHURCHLEY")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        self.connection_label = QLabel("LOCAL LIBRARY")
        self.connection_label.setObjectName("mutedLabel")
        header.addWidget(self.connection_label)
        root_layout.addLayout(header)

        intro = QLabel("Search the hymn library")
        intro.setObjectName("pageTitle")
        root_layout.addWidget(intro)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Search by hymn title or number…")
        self.search_input.textChanged.connect(self._refresh_results)
        root_layout.addWidget(self.search_input)

        body = QHBoxLayout()
        body.setSpacing(22)
        left = QVBoxLayout()
        left.addWidget(QLabel("RESULTS"), alignment=Qt.AlignmentFlag.AlignLeft)
        self.results_list = QListWidget()
        self.results_list.setObjectName("resultsList")
        self.results_list.itemSelectionChanged.connect(self._selection_changed)
        left.addWidget(self.results_list)
        self.result_count = QLabel()
        self.result_count.setObjectName("mutedLabel")
        left.addWidget(self.result_count)
        body.addLayout(left, stretch=3)

        right = QVBoxLayout()
        right.addWidget(QLabel("CURRENT HYMN"), alignment=Qt.AlignmentFlag.AlignLeft)
        self.selected_label = QLabel("Select a hymn to send it to the display.")
        self.selected_label.setObjectName("selectedHymn")
        self.selected_label.setWordWrap(True)
        right.addWidget(self.selected_label)
        self.verse_status = QLabel("No verse on display")
        self.verse_status.setObjectName("mutedLabel")
        right.addWidget(self.verse_status)
        right.addStretch()

        navigation = QHBoxLayout()
        self.previous_button = QPushButton("← Previous")
        self.previous_button.clicked.connect(self._previous_verse)
        self.next_button = QPushButton("Next →")
        self.next_button.setObjectName("primaryButton")
        self.next_button.clicked.connect(self._next_verse)
        navigation.addWidget(self.previous_button)
        navigation.addWidget(self.next_button)
        right.addLayout(navigation)

        self.panic_button = QPushButton("PANIC CLEAR  ·  ESC")
        self.panic_button.setObjectName("panicButton")
        self.panic_button.clicked.connect(self._panic_clear)
        right.addWidget(self.panic_button)
        body.addLayout(right, stretch=2)
        root_layout.addLayout(body, stretch=1)

        library_controls = QHBoxLayout()
        self.add_hymn_button = QPushButton("+ Add hymn")
        self.add_hymn_button.clicked.connect(self._add_hymn)
        self.import_button = QPushButton("Import text file")
        self.import_button.clicked.connect(self._import_hymns)
        library_controls.addWidget(self.add_hymn_button)
        library_controls.addWidget(self.import_button)
        library_controls.addStretch()
        self.retarget_button = QPushButton("Send to projector")
        self.retarget_button.setObjectName("retargetButton")
        self.retarget_button.clicked.connect(self.display.show_on_projector)
        library_controls.addWidget(self.retarget_button)
        root_layout.addLayout(library_controls)
        self.setCentralWidget(root)

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #0b0e12; color: #f1f4f8; }
            QLabel { color: #dbe4ee; }
            #brand { color: #4aa3ff; font-size: 18px; font-weight: 800; letter-spacing: 2px; }
            #pageTitle { color: #ffffff; font-size: 30px; font-weight: 700; }
            #mutedLabel { color: #78899b; font-size: 12px; letter-spacing: 1px; }
            QLineEdit, QTextEdit { background: #131922; border: 1px solid #273342;
                border-radius: 7px; padding: 12px; color: #ffffff; font-size: 16px; }
            QLineEdit:focus, QTextEdit:focus { border: 1px solid #4aa3ff; }
            #searchInput { font-size: 19px; padding: 15px; }
            QListWidget { background: #11161d; border: 1px solid #273342; border-radius: 7px;
                padding: 7px; font-size: 16px; }
            QListWidget::item { padding: 13px; border-radius: 5px; }
            QListWidget::item:selected { background: #163c61; color: #ffffff; }
            #selectedHymn { color: #ffffff; font-size: 25px; font-weight: 700; padding-top: 12px; }
            QPushButton { background: #18222d; border: 1px solid #304052; border-radius: 6px;
                padding: 11px 16px; color: #eaf2fb; font-weight: 600; }
            QPushButton:hover { border-color: #4aa3ff; background: #1d2b3a; }
            #primaryButton { background: #1976d2; border-color: #4aa3ff; }
            #primaryButton:hover { background: #2588e7; }
            #panicButton { background: #521d2a; border-color: #a43b51; color: #ffb8c5; }
            #panicButton:hover { background: #702337; }
            #retargetButton { background: #1a3328; border-color: #3d8b63; color: #a8e6c3; }
            #retargetButton:hover { background: #244836; }
            """
        )

    def _refresh_results(self) -> None:
        results = self.repository.search_hymns(self.search_input.text())
        self.results_list.blockSignals(True)
        self.results_list.clear()
        for result in results:
            item = QListWidgetItem(f"{result.number}   {result.title}")
            item.setData(Qt.ItemDataRole.UserRole, result.id)
            if result.tune_name:
                item.setToolTip(f"Tune: {result.tune_name}")
            self.results_list.addItem(item)
        self.results_list.blockSignals(False)
        self.result_count.setText(f"{len(results)} result{'s' if len(results) != 1 else ''}")

    def _selection_changed(self) -> None:
        selected_items = self.results_list.selectedItems()
        if not selected_items:
            return
        hymn_id = int(selected_items[0].data(Qt.ItemDataRole.UserRole))
        hymn = self.repository.get_hymn(hymn_id)
        if hymn is None or not hymn.verses:
            QMessageBox.warning(self, "Hymn unavailable", "The selected hymn has no verses.")
            return
        self.current_hymn = hymn
        self.current_verse_number = hymn.verses[0].number
        self._show_current_verse()

    def _show_current_verse(self) -> None:
        if self.current_hymn is None or self.current_verse_number is None:
            return
        verse = self.repository.get_verse(self.current_hymn.id, self.current_verse_number)
        if verse is None:
            return
        self.display.show_hymn_verse(self.current_hymn, verse)
        self.selected_label.setText(f"{self.current_hymn.number}  ·  {self.current_hymn.title}")
        self.verse_status.setText(
            f"Verse {verse.number} of {len(self.current_hymn.verses)} on display"
        )
        self.previous_button.setEnabled(verse.number > 1)
        self.next_button.setEnabled(verse.number < len(self.current_hymn.verses))

    def _next_verse(self) -> None:
        if self.current_hymn is None or self.current_verse_number is None:
            return
        verse = self.repository.get_next_verse(self.current_hymn.id, self.current_verse_number)
        if verse is not None:
            self.current_verse_number = verse.number
            self._show_current_verse()

    def _previous_verse(self) -> None:
        if self.current_hymn is None or self.current_verse_number is None:
            return
        verse = self.repository.get_previous_verse(
            self.current_hymn.id, self.current_verse_number
        )
        if verse is not None:
            self.current_verse_number = verse.number
            self._show_current_verse()

    def _panic_clear(self) -> None:
        self.current_hymn = None
        self.current_verse_number = None
        self.display.clear_display()
        self.selected_label.setText("Select a hymn to send it to the display.")
        self.verse_status.setText("DISPLAY CLEARED")

    def _on_screens_changed(self) -> None:
        """Debounced handler for monitor hotplug — retarget display after settling."""
        self._retarget_timer.start()

    def _add_hymn(self) -> None:
        dialog = AddHymnDialog(self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        try:
            self.repository.add_hymn(**dialog.hymn_data())
        except ValueError as error:
            QMessageBox.critical(self, "Could not add hymn", str(error))
            return
        self._refresh_results()
        self.search_input.setText(str(dialog.hymn_data()["number"]))

    def _import_hymns(self) -> None:
        records = choose_import_file(self)
        if records is None:
            return
        imported_count = 0
        try:
            for record in records:
                self.repository.add_hymn(**record)
                imported_count += 1
        except (TypeError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Import failed",
                f"Failed on hymn {imported_count + 1} of {len(records)}:\n\n"
                f"{error}\n\n"
                f"{imported_count} hymn(s) were imported before the error.",
            )
            self._refresh_results()
            return
        self._refresh_results()
        QMessageBox.information(self, "Import complete", f"Imported {len(records)} hymn(s).")
