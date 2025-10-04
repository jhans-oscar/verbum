import builtins
import io
import json

import pytest
from rich.console import Console

from verbum.core import bible_io, formatting, reader, reference
from verbum.cli import main as cli_main
from verbum.cli.main import NavigationState


@pytest.fixture(scope="module")
def bible():
    return bible_io.open_bible()


@pytest.fixture
def cli_runner(monkeypatch, bible):
    def run_session(inputs, bible_override=None):
        iterator = iter(inputs)

        def fake_input(_):
            try:
                return next(iterator)
            except StopIteration as exc:
                raise AssertionError("CLI requested more input than provided") from exc

        monkeypatch.setattr(builtins, "input", fake_input)

        cli_console = Console(
            file=io.StringIO(),
            force_terminal=False,
            color_system=None,
            record=True,
        )
        reader_console = Console(
            file=io.StringIO(),
            force_terminal=False,
            color_system=None,
            record=True,
        )

        monkeypatch.setattr(cli_main, "console", cli_console)
        monkeypatch.setattr(reader, "console", reader_console)
        monkeypatch.setattr(cli_main, "open_bible", lambda: bible_override or bible)

        cli_main.main()

        return cli_console.file.getvalue(), reader_console.file.getvalue()

    return run_session


def test_open_bible_contains_expected_books(bible):
    assert "Genesis" in bible
    assert "1" in bible["Genesis"]
    assert isinstance(bible["Genesis"]["1"], list)


def test_open_bible_reads_from_custom_path(tmp_path, monkeypatch):
    custom_data = {"Test": {"1": ["Only verse."]}}
    custom_path = tmp_path / "custom.json"
    custom_path.write_text(json.dumps(custom_data), encoding="utf-8")
    monkeypatch.setattr(bible_io, "BIBLE_PATH", custom_path)

    loaded = bible_io.open_bible()

    assert loaded == custom_data


def test_get_chapter_count(bible):
    assert bible_io.get_chapter_count(bible, "Genesis") == len(bible["Genesis"])


def test_get_verse_count(bible):
    assert bible_io.get_verse_count(bible, "Genesis", 1) == len(bible["Genesis"]["1"])


def test_find_text_returns_expected_verse(bible):
    verse = bible_io.find_text(bible, "Genesis", 1, 1)
    assert verse.startswith("In the beginning")


def test_find_text_invalid_book_raises():
    with pytest.raises(ValueError, match="Unable to locate the book 'NotABook'."):
        bible_io.find_text({}, "NotABook", 1, 1)


def test_find_text_invalid_chapter_raises(bible):
    with pytest.raises(ValueError, match="Chapter 999 not found"):
        bible_io.find_text(bible, "Genesis", 999, 1)


def test_find_text_invalid_verse_raises(bible):
    with pytest.raises(ValueError, match="Verse 999 not found"):
        bible_io.find_text(bible, "Genesis", 1, 999)


def test_pass_next_advances_verse(bible):
    assert bible_io.pass_next(bible, "Genesis", 1, 1) == ("Genesis", 1, 2)


def test_pass_next_moves_to_next_chapter(bible):
    last_verse = bible_io.get_verse_count(bible, "Genesis", 1)
    assert bible_io.pass_next(bible, "Genesis", 1, last_verse) == ("Genesis", 2, 1)


def test_pass_next_moves_to_next_book_when_no_verse(bible):
    max_chapter = bible_io.get_chapter_count(bible, "Genesis")
    assert bible_io.pass_next(bible, "Genesis", max_chapter, None) == ("Exodus", 1, None)


def test_pass_next_returns_none_at_end(bible):
    books = list(bible.keys())
    last_book = books[-1]
    last_chapter = bible_io.get_chapter_count(bible, last_book)
    last_verse = bible_io.get_verse_count(bible, last_book, last_chapter)
    assert bible_io.pass_next(bible, last_book, last_chapter, last_verse) is None


def test_pass_prev_moves_back_a_verse(bible):
    assert bible_io.pass_prev(bible, "Genesis", 1, 2) == ("Genesis", 1, 1)


def test_pass_prev_rolls_to_previous_chapter(bible):
    prev = bible_io.pass_prev(bible, "Genesis", 2, 1)
    last_verse_prev = bible_io.get_verse_count(bible, "Genesis", 1)
    assert prev == ("Genesis", 1, last_verse_prev)


def test_pass_prev_returns_none_before_start(bible):
    assert bible_io.pass_prev(bible, "Genesis", 1, 1) is None


def test_pass_prev_moves_to_previous_book_when_no_verse(bible):
    result = bible_io.pass_prev(bible, "Exodus", 1, None)
    last_chapter = bible_io.get_chapter_count(bible, "Genesis")
    assert result == ("Genesis", last_chapter, None)


def test_format_verse_uses_superscript_numerals():
    formatted = formatting.format_verse(23, "text")
    assert formatted.startswith("²³ text")


def test_format_verse_preserves_text():
    formatted = formatting.format_verse(1, "Hello world")
    assert formatted.endswith("Hello world")


def test_parse_reference_single_verse():
    book, chapter, verse = reference.parse_reference("Genesis 1:3")
    assert book == "Genesis"
    assert chapter == 1
    assert verse == 3


def test_parse_reference_range():
    book, chapter, verse = reference.parse_reference("Genesis 1:1-5")
    assert book == "Genesis"
    assert chapter == 1
    assert verse == (1, 5)


def test_parse_reference_whole_chapter():
    book, chapter, verse = reference.parse_reference("Genesis 1")
    assert book == "Genesis"
    assert chapter == 1
    assert verse is None


def test_parse_reference_handles_spacing_and_dashes():
    book, chapter, verse = reference.parse_reference("Genesis   1 : 1 - 3")
    assert book == "Genesis"
    assert chapter == 1
    assert verse == (1, 3)


def test_parse_reference_trailing_punctuation():
    book, chapter, verse = reference.parse_reference("Genesis 1:1;")
    assert book == "Genesis"
    assert chapter == 1
    assert verse == 1


def test_parse_reference_invalid_input():
    assert reference.parse_reference("nonsense") == (None, None, None)


def test_parse_reference_non_numeric_chapter():
    assert reference.parse_reference("Genesis one:1") == (None, None, None)


def test_parse_reference_keeps_user_spacing():
    book, chapter, verse = reference.parse_reference("Song of Solomon 1:1")
    assert book == "Song of Solomon"
    assert chapter == 1
    assert verse == 1


def test_build_reference_string_whole_chapter():
    assert reference.build_reference_string("Genesis", 1, None) == "Genesis 1"


def test_build_reference_string_range():
    assert reference.build_reference_string("Genesis", 1, (2, 5)) == "Genesis 1:2-5"


def test_build_reference_string_single_verse():
    assert reference.build_reference_string("Genesis", 1, 3) == "Genesis 1:3"


def test_resolve_book_name_canonical_passthrough(bible):
    name, suggestion = reference.resolve_book_name(bible, "Genesis")
    assert name == "Genesis"
    assert suggestion is None


def test_resolve_book_name_autosuggest(bible):
    name, suggestion = reference.resolve_book_name(bible, "Genessis")
    assert name == "Genesis"
    assert suggestion == "Genesis"


def test_resolve_book_name_unknown_returns_input(bible):
    name, suggestion = reference.resolve_book_name(bible, "MadeUpBook")
    assert name == "MadeUpBook"
    assert suggestion is None


def test_suggest_book_returns_closest_match(bible):
    suggestion = reference.suggest_book(bible, "Genessis")
    assert suggestion == "Genesis"


def test_suggest_book_returns_none_for_unknown(bible):
    assert reference.suggest_book(bible, "NotABook") is None


def test_get_passage_single_verse_prints_content(bible):
    with reader.console.capture() as capture:
        result = reader.get_passage(bible, "Genesis 1:1")
    rendered = capture.get()
    assert "Genesis 1:1" in rendered
    assert "In the beginning" in rendered
    assert "In the beginning" in result


def test_get_passage_range_prints_content(bible):
    with reader.console.capture() as capture:
        result = reader.get_passage(bible, "Genesis 1:1-2")
    rendered = capture.get()
    assert "Genesis 1:1-2" in rendered
    assert "Spirit of God" in rendered
    assert "Spirit of God" in result


def test_get_passage_whole_chapter_prints_navigation(bible):
    with reader.console.capture() as capture:
        result = reader.get_passage(bible, "Genesis 1")
    rendered = capture.get()
    assert "Genesis 1" in rendered
    assert "← back  ·  next →" in rendered
    assert "← back  ·  next →" in result


def test_get_passage_invalid_book_raises(bible):
    with pytest.raises(ValueError, match="Unable to locate the book 'NotABook'."):
        reader.get_passage(bible, "NotABook 1:1")


def test_get_passage_invalid_chapter_raises(bible):
    with pytest.raises(ValueError, match="contains only"):
        reader.get_passage(bible, "Genesis 999")


def test_get_passage_single_verse_above_max_raises(bible):
    with pytest.raises(ValueError, match="Genesis 1 contains only"):
        reader.get_passage(bible, "Genesis 1:999")


def test_get_passage_verse_below_one_raises(bible):
    with pytest.raises(ValueError, match="Verses begin at 1"):
        reader.get_passage(bible, "Genesis 1:0")


def test_get_passage_invalid_range_raises(bible):
    with pytest.raises(ValueError, match="Verse range invalid"):
        reader.get_passage(bible, "Genesis 1:50-10")


def test_get_passage_range_exceeding_bounds_raises(bible):
    with pytest.raises(ValueError, match="Verse range invalid"):
        reader.get_passage(bible, "Genesis 1:1-999")


def test_get_passage_invalid_format_raises(bible):
    with pytest.raises(ValueError, match="Reference not recognized"):
        reader.get_passage(bible, "JustSomeRandomText")


def test_get_passage_autosuggest_reports_correction(bible):
    with reader.console.capture() as capture:
        reader.get_passage(bible, "Genessis 1:1")
    rendered = capture.get()
    assert "Interpreting book as Genesis (entered 'Genessis')" in rendered


def test_get_passage_accepts_lowercase_book_without_warning(bible):
    with reader.console.capture() as capture:
        result = reader.get_passage(bible, "song of solomon 1:1")
    rendered = capture.get()
    assert "Using '" not in rendered
    assert "Song of Solomon" in rendered
    assert "Song of Solomon" in result


def test_get_passage_returns_rendered_text(bible):
    result = reader.get_passage(bible, "Genesis 1:1")
    assert "In the beginning" in result


def test_navigation_state_initial_not_ready():
    state = NavigationState()
    assert not state.is_ready()


def test_navigation_state_store_with_tuple():
    state = NavigationState()
    state.store("Genesis", 1, (2, 5))
    assert state.book == "Genesis"
    assert state.chapter == 1
    assert state.verse == 5


def test_navigation_state_store_with_single_verse():
    state = NavigationState()
    state.store("Genesis", 1, 3)
    assert state.verse == 3


def test_navigation_state_reset():
    state = NavigationState(book="Genesis", chapter=1, verse=3)
    state.reset()
    assert state.book is None
    assert state.chapter is None
    assert state.verse is None


def test_cli_help_menu(cli_runner):
    cli_output, reader_output = cli_runner([":help", "quit"])
    assert "Available commands" in cli_output
    assert "Closing." in cli_output
    assert reader_output == ""


def test_cli_single_verse_flow(cli_runner):
    cli_output, reader_output = cli_runner(["Genesis 1:1", "quit"])
    assert "VERBUM" in cli_output
    assert "Genesis 1:1" in reader_output
    assert "In the beginning" in reader_output


def test_cli_navigation_requires_history(cli_runner):
    cli_output, reader_output = cli_runner([":next", ":prev", "quit"])
    assert "No prior passage stored. Enter a reference before moving ahead." in cli_output
    assert "No prior passage stored. Enter a reference before moving back." in cli_output
    assert reader_output == ""


def test_cli_navigation_advances_to_next_chapter(cli_runner):
    _, reader_output = cli_runner(["Genesis 1", ":next", "quit"])
    assert "Genesis 1" in reader_output
    assert "Genesis 2" in reader_output


def test_cli_handles_autosuggested_reference(cli_runner):
    cli_output, reader_output = cli_runner(["Genessis 1:1", "quit"])
    combined_output = cli_output + reader_output
    assert "Interpreting book as Genesis (entered 'Genessis')" in combined_output
    assert "In the beginning" in combined_output


def test_cli_next_from_single_verse_advances(cli_runner):
    _, reader_output = cli_runner(["Genesis 1:1", ":next", "quit"])
    assert "Genesis 1:1" in reader_output
    assert "Genesis 1:2" in reader_output


def test_cli_prev_after_next_returns_previous(cli_runner):
    _, reader_output = cli_runner(["Genesis 1:2", ":prev", "quit"])
    assert "Genesis 1:2" in reader_output
    assert "Genesis 1:1" in reader_output


def test_cli_range_next_continues_from_end(cli_runner):
    _, reader_output = cli_runner(["Genesis 1:1-3", ":next", "quit"])
    assert "Genesis 1:1-3" in reader_output
    assert "Genesis 1:4" in reader_output


def test_cli_prev_from_chapter_moves_back(cli_runner):
    _, reader_output = cli_runner(["Genesis 2", ":prev", "quit", "back"])
    assert "Genesis 2" in reader_output
    assert "Genesis 1" in reader_output


def test_cli_invalid_reference_shows_example(cli_runner):
    cli_output, _ = cli_runner(["not a reference", "quit"])
    assert "Reference not recognized. Check your input and try again." in cli_output
    assert "Examples: John 1, John 1:1, Psalm 23:1-4" in cli_output


def test_cli_reports_end_of_bible(cli_runner):
    custom_bible = {"Test": {"1": ["Only verse."]}}
    cli_output, reader_output = cli_runner(["Test 1:1", ":next", "quit"], bible_override=custom_bible)
    assert "Test 1:1" in reader_output
    assert "No further passage found in this direction." in cli_output


def test_cli_reports_start_of_bible_on_prev(cli_runner):
    custom_bible = {"Test": {"1": ["Only verse."]}}
    cli_output, reader_output = cli_runner(["Test 1:1", ":prev", "quit"], bible_override=custom_bible)
    assert "Test 1:1" in reader_output
    assert "No further passage found in this direction." in cli_output


def test_cli_help_command_does_not_touch_reader(cli_runner):
    cli_output, reader_output = cli_runner([":help", ":help", "quit"])
    assert reader_output == ""
    assert cli_output.count("Available commands") == 2


def test_cli_quit_aliases(cli_runner):
    cli_output, _ = cli_runner(["Genesis 1:1", "q"])
    assert "Closing." in cli_output
