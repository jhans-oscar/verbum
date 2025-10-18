import pytest

pytest.importorskip("rich")

from rich.console import Console

from verbum.cli import main as cli_main
from verbum.core.bible_service import BibleService

class DummyRepo:
    books = ["Genesis"]

    def __init__(self, *_args, **_kwargs):
        pass

    def get_passage(self, ref):
        if ref.book not in self.books:
            raise ValueError(f"Book '{ref.book}' not found")
        verses = ref.verses or [1]
        return [(verse, f"Verse {verse}") for verse in verses]

    def list_books(self):
        return list(self.books)

    def chapter_count(self, book):
        if book not in self.books:
            raise ValueError(f"Book '{book}' not in dataset")
        return 2

    def verse_count(self, book, chapter):
        if book not in self.books:
            raise ValueError(f"Book '{book}' not in dataset")
        if chapter not in {1, 2}:
            raise ValueError(f"Invalid chapter {chapter}")
        return 3

    def search(self, query, limit=None):
        return [
            {"book": "Genesis", "chapter": 1, "verse": 1, "text": f"Result for {query}"}
        ][:limit if limit else None]


class _DummyFiles:
    def joinpath(self, _name):
        return "dummy"


@pytest.fixture
def patched_cli(monkeypatch):
    console = Console(record=True)
    monkeypatch.setattr(cli_main, "console", console)
    repo = DummyRepo()
    service = BibleService(repo)
    monkeypatch.setattr(cli_main, "build_service", lambda: (repo, service))
    return console


def test_cli_flow_handles_reference_and_navigation(monkeypatch, patched_cli):
    user_inputs = iter(["Genesis 1:1-2", ":next", ":prev", ":help", ":quit"])
    monkeypatch.setattr(cli_main.Prompt, "ask", lambda *_args, **_kwargs: next(user_inputs))

    cli_main.main()

    output = patched_cli.export_text()
    assert "Genesis 1:1-2" in output
    assert "Verse 1" in output and "Verse 2" in output
    assert "Tips: :next" in output


def test_cli_invalid_reference(monkeypatch, patched_cli):
    user_inputs = iter(["Unknown 1", ":quit"])
    monkeypatch.setattr(cli_main.Prompt, "ask", lambda *_args, **_kwargs: next(user_inputs))

    cli_main.main()

    output = patched_cli.export_text()
    assert "Unknown book" in output or "Error" in output
