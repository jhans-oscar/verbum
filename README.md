# Verbum 0.2.0

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Verbum is a Rich-powered command-line companion for exploring the Bible from your terminal. Version 0.2.0 rebuilds the original 0.1.0 release with a cleaner OOP architecture and improved packaging so it installs as the `verbum` CLI.

## Features

- Instant lookups for single verses, verse ranges, or entire chapters.
- Sequential navigation with `:next` / `:prev`, backed by navigation history.
- Typo-tolerant book resolution (`Genesiss` → `Genesis`).
- Rich-formatted output with clear verse numbering.
- Swappable Bible dataset (defaults to `verbum/data/KJV.json`).

## Installation

Requires Python 3.10 or newer.

```bash
pip install -e .
# Once published to PyPI:
# pip install verbum
```

This exposes the `verbum` command-line entry point.

## Quick Start

Launch the CLI after installing:

```bash
verbum
# or
python -m verbum.cli.main
```

Supported inputs:

- `Book Chapter` → entire chapter (e.g., `Genesis 1`).
- `Book Chapter:Verse` → single verse (e.g., `John 3:16`).
- `Book Chapter:Start-End` → verse range (e.g., `Psalm 23:1-4`).
- `:next` / `:prev` → navigate relative to your last passage.
- `:help` → list available commands.
- `:quit`, `exit`, or `q` → exit the CLI.

Example session:

```text
📜  VERBUM — Scripture at your fingertips.
Type a reference (e.g. 'John 1' or 'Psalm 23:1-4')

📖 John 3
16. For God so loved the world...
17. For God sent not his Son into the world to condemn the world...

Current reference: John 3:16-17
Tips: :next, :prev, :help, :quit
```

## Bible Data & Configuration

- The bundled dataset lives at `verbum/data/KJV.json`.
- To use another translation, point `BIBLE_PATH` to a compatible JSON file:

  ```bash
  export BIBLE_PATH=/path/to/another_bible.json
  verbum
  ```

## Project Structure

- `verbum/domain/reference.py` — reference parsing & formatting.
- `verbum/core/normalizer.py` — user input normalization helpers.
- `verbum/core/bible_service.py` — navigation orchestration.
- `verbum/infrastructure/repositories/json_bible_repository.py` — JSON-backed repository.
- `verbum/cli/main.py` — Rich-powered CLI loop.

## Development

```bash
pytest
```

Pull requests are welcome. Please include tests for new features or fixes.

## License

MIT
