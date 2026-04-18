# file-organizer-cli

A Python CLI tool that automatically organizes files by type, date, or extension — with dry-run preview, undo, watch mode, duplicate detection, and rich terminal output.

---

## Features

- **Organize by type** — Images, Videos, Documents, Audio, Code, Archives, and more
- **Organize by date** — Groups files into `YYYY/MM` folders by last modified date
- **Organize by extension** — Groups files into `JPG/`, `PDF/`, `MP4/` folders
- **Dry-run mode** — Preview exactly what will move before touching anything
- **Undo** — Reverse the last organize operation, file by file
- **Watch mode** — Auto-organize new files the moment they land in a folder
- **Duplicate detection** — SHA-256 content hashing finds identical files regardless of name
- **Config file** — Customize rules, folder names, and ignored files via `.organizer.json`
- **Conflict resolution** — Never overwrites; renames to `file (1).jpg`, `file (2).jpg` automatically
- **Rich terminal UI** — Colored output, progress bars, and preview tables

---

## Installation

```bash
git clone https://github.com/your-username/file-organizer-cli.git
cd file-organizer-cli
pip install -r requirements.txt
```

Or install as a command:

```bash
pip install -e .
```

---

## Usage

```bash
python main.py [directory] [options]
```

If no directory is given, the current directory is used.

### Examples

```bash
# Organize ~/Downloads by file type (default)
python main.py ~/Downloads

# Organize by date modified (creates 2024/03/ folders)
python main.py ~/Downloads --by date

# Organize by file extension (creates JPG/, PDF/ folders)
python main.py ~/Downloads --by extension

# Preview changes without moving anything
python main.py ~/Downloads --dry-run

# Detect duplicate files before organizing
python main.py ~/Downloads --duplicates

# Undo the last organize operation
python main.py ~/Downloads --undo

# Watch folder and auto-organize new files in real time
python main.py ~/Downloads --watch

# Generate a editable config file in the target directory
python main.py ~/Downloads --init-config

# Use a custom config file
python main.py ~/Downloads --config ~/my-rules.json
```

---

## Output Structure

### By type (default)

```
Downloads/
├── Images/
│   ├── photo.jpg
│   └── screenshot.png
├── Videos/
│   └── clip.mp4
├── Documents/
│   ├── report.pdf
│   └── notes.txt
├── Audio/
│   └── song.mp3
├── Archives/
│   └── backup.zip
├── Code/
│   └── script.py
└── Others/
    └── mystery.xyz
```

### By date

```
Downloads/
└── 2024/
    ├── 01/
    │   └── january-file.pdf
    └── 03/
        └── march-photo.jpg
```

### By extension

```
Downloads/
├── JPG/
├── PDF/
├── MP4/
└── Others/
```

---

## Configuration

Run `--init-config` to generate a `.organizer.json` in your target directory, then edit it:

```json
{
  "type_rules": {
    "Images": [".jpg", ".jpeg", ".png", ".gif"],
    "Videos": [".mp4", ".avi", ".mov"],
    "Documents": [".pdf", ".docx", ".txt"],
    "MyCustomFolder": [".sketch", ".fig"]
  },
  "ignored_files": [".ds_store", "thumbs.db"],
  "duplicate_action": "report",
  "others_folder": "Others",
  "date_format": "%Y/%m"
}
```

The config file is discovered automatically — it searches from the target directory upward, then checks `~/.organizer.json`.

---

## Tech Stack

| Component | Library |
|---|---|
| CLI | `argparse` |
| Terminal UI | `rich` |
| File watching | `watchdog` |
| Hashing | `hashlib` (stdlib) |
| File ops | `shutil`, `os`, `pathlib` (stdlib) |

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

28 tests covering all modules: rules, config, duplicates, undo, and core organize logic.

---

## Project Structure

```
file-organizer/
├── main.py                  # CLI entry point
├── organizer/
│   ├── rules.py             # Default extension → folder mappings
│   ├── config.py            # Config loader (.organizer.json)
│   ├── core.py              # Core organize engine
│   ├── duplicates.py        # SHA-256 duplicate detection
│   ├── undo.py              # Undo log and restore
│   └── watcher.py           # Real-time watch mode
├── tests/
│   └── test_organizer.py    # Full test suite (28 tests)
├── requirements.txt
└── setup.py
```

---

## License

MIT
