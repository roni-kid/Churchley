# Churchley

Churchley is an offline Windows hymn-library and projector display app for
church media operators. It uses Python, PySide6, and one local SQLite file.

## Run from source

```powershell
python -m pip install -r requirements.txt
python main.py
```

The operator window and projector-facing display are separate windows. If a
second monitor is connected, the display opens fullscreen on that monitor.
The operator window remains separate and controls the displayed verse.

Press `Esc` or use **PANIC CLEAR** to blank the display immediately.

## Bulk import format

Bulk imports are UTF-8 plain-text files. A block starts with `[number] Title`,
may contain `Tune:` and `Tags:` metadata, and then contains sequential verses.
Separate hymn blocks with a line containing `---`:

```text
[101] Amazing Grace
Tune: NEW BRITAIN
Tags: grace, opening
Verse 1:
Amazing grace, how sweet the sound
That saved a wretch like me.

Verse 2:
"Twas grace that taught my heart to fear
And grace my fears relieved.
---
[102] Another Hymn
Verse 1:
First verse text.
```

Manual entry uses the same data model; separate verses with a blank line.

## Tests and packaging

The Stage 1 data layer regression check is a standalone script:

```powershell
python tests/test_data_layer.py
```

Run the complete regression suite, including headless PySide6 GUI flows, with:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
python -m unittest discover -s tests -v
```

The GUI suite covers live search, selection, verse navigation, button states,
panic clear, ESC handling, manual entry, projector retargeting, monitor-change
debounce, and single-monitor display behavior.

Build the Windows executable on Windows with:

```powershell
pyinstaller --noconfirm --clean --windowed --name Churchley main.py
```

The executable will be in `dist/Churchley/`.
