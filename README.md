# Verbum Bible Reader

Verbum is a Rich-powered command-line companion for exploring the King James Version (KJV) Bible from your terminal. It supports quick lookups of chapters, single verses, and verse ranges while keeping track of where you left off.

## Features
- Instant lookups for single verses, verse ranges, or entire chapters
- Sequential navigation with `:next` and `:prev`, backed by a persistent navigation state
- Typo-tolerant book resolution that suggests the closest canonical name
- Rich-formatted output with superscript verse numbers for easy reading
- Swappable Bible dataset via the `BIBLE_PATH` environment variable

## Installation
Verbum targets Python 3.9 or newer.

```bash
git clone https://github.com/<your-account>/verbum-project.git
cd verbum-project
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
pip install -e .
```

To install the development-only dependencies (pytest for the test suite), either rely on the editable install above or run:

```bash
pip install -r requirements.txt
```

## Quick Start
Launch the CLI after installation:

```bash
verbum
# or
python -m verbum.cli.main
```

You will be greeted with the interactive prompt. Enter any of the supported inputs:

- `Book Chapter` &rarr; load an entire chapter (for example, `Genesis 1`)
- `Book Chapter:Verse` &rarr; load a single verse (for example, `John 3:16`)
- `Book Chapter:Start-End` &rarr; load a continuous range (for example, `Psalm 23:1-4`)
- `:next` / `:prev` &rarr; revisit the passage immediately after or before the last reference
- `:help` &rarr; display a summary of supported commands
- `:quit`, `exit`, or `q` &rarr; leave the application

Example session:

```text
$ verbum
Verbum CLI — type a reference (e.g., 'Genesis 1' or 'Exodus 2:1-10'). Type ':help' or ':quit'.

📖 Genesis 1:1
--------------------------------
[01] In the beginning God created the heaven and the earth.
<- :prev     :next ->
```

The CLI remembers the last verse or chapter you opened. You can continue navigating with `:next` and `:prev` without re-entering the original reference.

## Bible Data and Configuration
- The default dataset ships with the project at `verbum/data/KJV.json`.
- Set the `BIBLE_PATH` environment variable to point to a different JSON file that follows the same nested structure (`Book -> Chapter -> [Verses]`). For example:

  ```bash
  export BIBLE_PATH=/path/to/another_bible.json
  verbum
  ```

- The loader validates that the file exists and raises a clear error when it cannot be found.

## Project Structure
- `verbum/cli/main.py` — CLI entry point that manages the interaction loop and navigation state
- `verbum/core/reference.py` — Parsers and helpers for canonicalizing free-form references
- `verbum/core/bible_io.py` — Dataset loader plus navigation helpers for chapters, verses, and neighboring books
- `verbum/core/reader.py` — Validates references, fetches verses, and orchestrates formatted console output
- `verbum/core/formatting.py` — Shared utilities for superscript numbering and display strings
- `docs/overview.md` — Technical overview of the architecture, data flow, and extension points
- `tests/` — Pytest suite covering data access, parsing, rendering, navigation, and CLI behavior

## Development Guide
Start with [`docs/overview.md`](docs/overview.md) for a system-level tour and extension tips.

Run the automated tests before contributing changes:

```bash
pytest
```

To iterate quickly on the CLI, you can load the module directly:

```bash
python -m verbum.cli.main
```

Pull requests are welcome! If you add new features, include tests that capture their expected behavior to keep the CLI experience reliable.
