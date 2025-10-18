# Verbum 0.3.0

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Verbum is a Rich-powered Bible companion that now ships with both a colorful terminal experience and a lightweight JSON API. Version 0.3.0 introduces full-text search, consistent pagination, and a shared service layer between the CLI and FastAPI app.

## Features
- Instant lookups for single verses, verse ranges, or entire chapters.
- Keyword search via the `:search` CLI command and the `/lookup` API endpoint.
- Sequential navigation with `:next` / `:prev`, backed by navigation history.
- Typo-tolerant book resolution (`Genesiss` → `Genesis`).
- JSON responses modeled with Pydantic, including pagination metadata and optional book filtering.
- Swappable Bible dataset (defaults to `verbum/data/KJV.json`).

## Installation

Requires Python 3.10 or newer.

```bash
pip install -e .
# Once published to PyPI:
# pip install verbum
```

### Run the CLI

```bash
verbum
# or
python -m verbum.cli.main
```

### Run the API

```bash
uvicorn api.main:app --reload
```

The server starts at `http://127.0.0.1:8000` by default.

## Quick Start (CLI)

Supported inputs:

- `Book Chapter` → entire chapter (e.g., `Genesis 1`).
- `Book Chapter:Verse` → single verse (e.g., `John 3:16`).
- `Book Chapter:Start-End` → verse range (e.g., `Psalm 23:1-4`).
- `:search grace` → keyword search across the dataset.
- `:next` / `:prev` → navigate relative to your last passage.
- `:help` → list available commands.
- `:quit`, `exit`, or `q` → exit the CLI.

## Using the API

`GET /lookup` accepts a free-form query and optional pagination parameters:

- `GET /lookup?q=grace`
- `GET /lookup?q=faith&book=Romans`
- `GET /lookup?q=love&page_size=10&page=2`

Passing `page_size=0` disables pagination and streams the full result set in a single response. When `book` is provided, results are restricted to that book and `total_results` reflects the filtered count.

### Example Output

#### CLI (`:search grace`)

```text
🔍 Search results for 'grace'
Romans 3:24 - Being justified freely by his grace through the redemption that is in Christ Jesus:
Romans 4:4 - Now to him that worketh is the reward not reckoned of grace, but of debt.
...
```

![CLI search screenshot](docs/images/cli-search.png)

#### API (`GET /lookup?q=faith&book=Romans&page_size=5`)

```json
{
  "query": "faith",
  "page": 1,
  "page_size": 5,
  "total_pages": 10,
  "total_results": 50,
  "results": [
    {
      "book": "Romans",
      "chapter": 1,
      "verse": 8,
      "text": "First, I thank my God through Jesus Christ for you all, that your faith is spoken of throughout the whole world."
    }
  ]
}
```

![API lookup screenshot](docs/images/api-lookup.png)

The FastAPI startup banner can be captured for documentation at `docs/images/api-startup.png`.

## Bible Data & Configuration

- The bundled dataset lives at `verbum/data/KJV.json`.
- To use another translation, point `BIBLE_PATH` to a compatible JSON file:

  ```bash
  export BIBLE_PATH=/path/to/another_bible.json
  verbum
  ```

## Development

```bash
pytest -v
uvicorn api.main:app --reload
```

Pull requests are welcome. Please include tests for new features or fixes.

## License

MIT
