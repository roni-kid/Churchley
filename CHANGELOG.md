# 📖 Churcley — Changelog

> All notable changes to this project are documented here.
> Format: `[Date] | File(s) Changed | What Changed | Why | AI(name)`
> Order: **Newest first**

---

## Session Log

### 2026-07-21 | dist_updated/Churchley/Churchley.exe | Rebuilt packaged executable | Rebuilt the Windows package after the GUI hardening changes. The original dist/Churchley output was locked by a running process, so the verified updated package was written to dist_updated/Churchley/Churchley.exe without disturbing the running copy. | AI(Codex)

### 2026-07-21 | churchley/operator.py, tests/test_gui_flows.py, README.md | Projector retargeting and thorough GUI coverage | Added stable operator button references, instance-safe monitor hotplug signal wiring, application-scoped ESC panic handling, and 13 headless QTest flows covering search, selection, navigation, disabled states, panic reset, manual entry, retargeting, debounce, and single-monitor display behavior. The test suite skips GUI tests cleanly when PySide6 is unavailable; all 13 GUI tests pass in the PySide6 environment. | AI(Codex)

### 2026-07-21 | main.py, churchley/data.py, churchley/operator.py, churchley/display.py, churchley/importer.py, churchley/library.py, tests/test_importer.py | Audit and hardening pass | Full audit against GLM_MAINTENANCE_GUIDE.md. Fixed 6 bugs: (1) main.py now catches sqlite3.OperationalError and DatabaseError on startup with clear human-readable messages instead of raw tracebacks. (2) data.py connection now uses explicit timeout=10 and WAL journal mode for better concurrency and reliability. (3) importer.py now detects and rejects duplicate hymn numbers across blocks in a bulk import file. (4) operator.py import failure now reports how many hymns succeeded before the error, and refreshes results so partial imports are visible. (5) operator.py panic clear (ESC/button) now resets current_hymn and current_verse_number to None so pressing Next after a panic clear cannot silently restore the old verse. (6) display.py show_on_projector() no longer goes fullscreen on the primary screen when only one monitor is connected — instead opens as a large window on the right side so the operator window remains accessible. Also replaced record.__dict__ with dataclasses.asdict() in library.py for forward-safety, and added regression test for duplicate hymn numbers. Two-window separation preserved; verse storage unchanged; search isolation unchanged; no new scope added. | AI(GLM)

### 2026-07-21 | main.py, churchley/operator.py, churchley/display.py, dist/Churchley/Churchley.exe | Stage 5 UI polish and packaging completed | Added the dark operator styling, high-contrast projector display styling, requirements, README, and PyInstaller packaging. Verified the Windows executable was generated successfully at dist/Churchley/Churchley.exe. | AI(Codex)

### 2026-07-21 | churchley/library.py, churchley/importer.py, tests/test_importer.py, README.md | Stage 4 library entry and bulk import built | Added manual hymn entry, UTF-8 plain-text bulk import, parser validation, regression tests, and documented the exact import format. No deviations from the plan. | AI(Codex)

### 2026-07-21 | churchley/display.py, churchley/operator.py | Stage 3 separate display and navigation built | Added the separate projector-facing fullscreen window, verse 1 selection behavior, direct next/previous verse navigation, and ESC/PANIC CLEAR blackout. Offscreen UI smoke verification passed. No deviations from the plan. | AI(Codex)

### 2026-07-21 | churchley/operator.py | Stage 2 operator live search built | Added a PySide6 operator window wired to the real SQLite repository, with literal substring search results, selection state, and result ranking from Stage 1. Offscreen UI smoke verification passed. PySide6 was selected consistently as the Qt binding. | AI(Codex)

### 2026-07-21 | churchley/data.py, tests/test_data_layer.py | Stage 1 data layer built | Added the SQLite schema and plain-Python repository with independently addressable verses, ranked substring search, full hymn retrieval, direct next/previous verse lookup, and delete-with-cascade behavior. The standalone regression script passes. No deviations from the build plan. | AI(Codex)

---

## File Index

---

## How to Update This File

Add new entries at the **top** of the Session Log (after the `---` separator), newest first. State which AI you are.

---

*Churchley — Built by RoniKid*
