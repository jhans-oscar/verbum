# Verbum Function Map

## High-Level Flow
- CLI entry `verbum.cli.main.main()` opens the Bible dataset and drives the interactive loop.
- User inputs are parsed by `verbum.core.reference.parse_reference()`; corrections run through CLI `_autocorrect_book()` or the reader’s autosuggest.
- `verbum.core.reader.get_passage()` resolves book/chapter/verse selections, formats verses, and prints via its Rich console.
- Bible data access helpers in `verbum.core.bible_io` load JSON scripture and expose navigation helpers reused by CLI navigation (`:next`, `:prev`) and the reader.
- Formatting helpers render superscript verse numbers, while tests in `tests/test_verbum_app.py` validate CLI flows, parsing, autosuggest, and data integrity.

## Module & Function Map

verbum/__init__.py
└── (empty) → package marker; no runtime behavior.

verbum/cli/__init__.py
└── (empty) → exposes CLI package; no runtime behavior.

verbum/cli/main.py
├── console = Console() → Rich console bound to terminal; monkeypatched in tests for capture.
├── NavigationState dataclass → Tracks last visited book/chapter/verse for CLI navigation.
│   ├── is_ready() → Returns whether book & chapter cached; checked before handling :next/:prev; called only by main().
│   ├── update(book, chapter, verse) → Persists navigation; invoked by _store_navigation().
│   ├── store(state, book, chapter, verse) → Saves navigation context; wraps NavigationState.update
│   └── reset() → Clears navigation state; currently unused (potential cleanup or future feature).
├── print_help() → Prints supported commands via console; triggered by main() when user requests help.
├── friendly_error(message, show_example=True) → Uniform error output; used by main() for invalid input feedback.
├── main() → CLI entry point; orchestrates input loop, parses references, manages navigation, and delegates to reader.get_passage(); called by tests and __main__ guard.
└── if __name__ == "__main__": main() → Script entry for direct execution.

verbum/core/bible_io.py
├── Bible type alias → Dict[str, Dict[str, List[str]]]; used as shared type hint.
├── BIBLE_PATH constant → Resolves JSON source from env or package data; used by open_bible().
├── open_bible() → Loads JSON scripture; raises if missing; called by CLI main(), tests (fixture), and any consumer needing raw data.
├── get_chapter_count(bible, book) → Returns number of chapters; used by reader.get_passage() and CLI navigation helpers.
├── get_verse_count(bible, book, chapter) → Returns verse count; used by reader.get_passage() and CLI navigation helpers.
├── get_next_book(bible, book) → Finds succeeding book; used by pass_next().
├── get_prev_book(bible, book) → Finds preceding book; used by pass_prev().
├── find_text(bible, book, chapter, verse) → Retrieves verse text with cleaning; used exclusively by reader.get_passage
├── pass_prev(bible, book, chapter, verse=None) → Computes previous reference; uses get_verse_count/get_chapter_count/get_prev_book; invoked by main();
└── pass_next(bible, book, chapter, verse=None) → Computes the next reference; uses get_verse_count/get_chapter_count/get_next_book; invoked by main();
().

verbum/core/reader.py
├── console = Console() → Dedicated Rich console for passage output; monkeypatched in tests.
└── get_passage(bible, reference) → Parses reference, validates ranges via bible_io helpers, formats output with formatting.format_verse, autosuggests via suggest_book; returns rendered text while printing; primary consumer is CLI main(), with tests asserting behavior.

verbum/core/reference.py
├── parse_reference(reference) → Normalizes user input into (book, chapter, verse|range|None); used by CLI main(), reader.get_passage(), and tests.
├── build_reference_string(book, chapter, verse) → Normalizes references into strings; used inside main() before calling reader;
├── resolve_book_name(bible, book) → Case-insensitive book resolution with suggest_book fallback; used by main(); duplicates reader autosuggest logic—consider moving to `verbum.core.reference` as `resolve_book_name()`.
└── suggest_book(bible, user_input) → Fuzzy matches book names via difflib; used by CLI `_autocorrect_book()`, reader.get_passage(), and tests.


verbum/core/formatting.py
├── SUPERSCRIPTS → Translation table for superscript numerals; used by format_verse().
└── format_verse(number, text) → Renders verse number with superscript + text; used by reader.get_passage() and verified by tests.

verbum/data/KJV.json
└── JSON scripture source → Loaded by bible_io.open_bible(); contains the verse data consumed application-wide.

tests/test_verbum_app.py
├── bible() fixture → Module-scope loader using bible_io.open_bible(); shared across tests.
├── cli_runner(monkeypatch, bible) fixture → Builds a harness around cli_main.main(), monkeypatching input/open_bible/consoles; returns captured CLI and reader output for assertions.
├── run_session(inputs) inner function → Drives CLI loop with scripted inputs; called inside tests via cli_runner fixture.
├── test_open_bible_contains_expected_books() → Validates Genesis structure from bible fixture.
├── test_get_chapter_count() → Checks get_chapter_count output.
├── test_get_verse_count() → Checks get_verse_count output.
├── test_find_text_returns_expected_verse() → Asserts verse content string prefix.
├── test_find_text_invalid_book_raises() → Ensures ValueError on unknown book.
├── test_format_verse_uses_superscript_numerals() → Confirms superscript formatting.
├── test_parse_reference_single_verse() → Asserts parse_reference returns correct tuple.
├── test_parse_reference_range() → Ensures ranges parsed correctly.
├── test_parse_reference_whole_chapter() → Confirms chapter-only parsing.
├── test_parse_reference_invalid_input() → Expects graceful failure tuple.
├── test_parse_reference_keeps_user_spacing() → Ensures multi-word book names preserved.
├── test_suggest_book_returns_closest_match() → Checks fuzzy match success.
├── test_suggest_book_returns_none_for_unknown() → Ensures no guess when match absent.
├── test_get_passage_single_verse_prints_content() → Captures reader output for single verse.
├── test_get_passage_range_prints_content() → Captures range output.
├── test_get_passage_whole_chapter_prints_navigation() → Checks navigation hints printed.
├── test_get_passage_invalid_book_raises() → Validates book error handling.
├── test_get_passage_invalid_chapter_raises() → Validates chapter bounds error.
├── test_get_passage_invalid_range_raises() → Validates range validation.
├── test_get_passage_invalid_format_raises() → Ensures parse failure bubble-up.
├── test_get_passage_autosuggest_reports_correction() → Validates suggestion messaging.
├── test_get_passage_accepts_lowercase_book_without_warning() → Confirms case-insensitive handling.
├── test_get_passage_returns_rendered_text() → Confirms result string contains verse text.
├── test_cli_help_menu() → Exercises :help command path.
├── test_cli_single_verse_flow() → Covers main CLI flow from lookup to quit.
├── test_cli_navigation_errors_without_history() → Ensures navigation guards prevent invalid :next/:prev.
├── test_cli_navigation_advances_to_next_chapter() → Validates stateful navigation forward.
└── test_cli_handles_autosuggested_reference() → Confirms CLI+reader cooperative autosuggest messaging.

## Dependency Highlights
- CLI depends on `verbum.core.bible_io`, `verbum.core.reader`, and `verbum.core.reference` for data, rendering, and parsing.
- Reader centralizes validation/formatting, leveraging `bible_io` for structure and `formatting.format_verse` for display.
- Reference utilities power both CLI and reader parsing; consolidating `_build_reference` and `_autocorrect_book` here would remove duplication.
- Tests rely heavily on monkeypatching `console` objects, so shared console globals remain intentional (though dependency injection could simplify future refactors).
