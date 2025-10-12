# verbum/cli/main.py
# Entry point for the Verbum CLI interface.
# Coordinates user input parsing, navigation, and passage rendering.
# Collaborates with verbum.core.bible_io, verbum.core.reference, and verbum.core.reader.
from __future__ import annotations

import time
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel

from verbum.core.bible_io import (
    open_bible,
    pass_next,
    pass_prev,
)
from verbum.core.reader import get_passage
from verbum.core.reference import build_reference_string, parse_reference, resolve_book_name


console = Console()

BANNER = """[bold gold1]📜  VERBUM[/bold gold1] — Scripture at your fingertips.
[dim]Type a reference (e.g. 'John 1' or 'Psalm 23:1-4')[/dim]
[dim]Commands: :help  |  :next / :prev  |  :quit[/dim]
"""

HELP_TEXT = """[bold gold1]Available commands[/bold gold1]
[dim]────────────────────────────[/dim]
:next       Move forward to the next passage
:prev       Return to the previous passage
:help       Show this list
:quit, q    Exit Verbum

You can enter any reference directly:
  [italic]John 3:16[/italic] — single verse
  [italic]Genesis 1[/italic] — full chapter
  [italic]Psalm 23:1-4[/italic] — range
"""


@dataclass
class NavigationState:
    book: str | None = None
    chapter: int | None = None
    verse: int | None = None

    def is_ready(self) -> bool:
        return self.book is not None and self.chapter is not None

    def update(self, book: str, chapter: int, verse: int | None) -> None:
        self.book = book
        self.chapter = chapter
        self.verse = verse

    def reset(self) -> None:
        self.book = self.chapter = self.verse = None

    def store(
        self,
        book: str,
        chapter: int,
        verse: int | tuple[int, int] | None,
    ) -> None:
        stored_verse = verse[1] if isinstance(verse, tuple) else verse
        self.update(book, chapter, stored_verse)


def show_welcome() -> None:
    console.print("[dim][italic]Initializing...[/italic][/dim]")
    time.sleep(0.3)
    console.print(Panel.fit(BANNER, border_style="gold1"))


def show_help() -> None:
    console.print(Panel.fit(HELP_TEXT, border_style="blue"))


def friendly_error(message: str, hint: str | None = None) -> None:
    """
    Render a composed error and optional hint.
    Args:
        message (str): Human-readable description of the issue.
        hint (str | None): Supplementary guidance for recovery.
    Returns:
        None: The message is written to the Rich console.
    """
    console.print(f"[bold red]{message}[/bold red]")
    if hint:
        console.print(f"[italic dim]{hint}[/italic dim]")
    console.print()


def main() -> None:
    """
    Run the interactive Verbum CLI session.
    Returns:
        None: Execution terminates when the user issues a quit command.
    """
    bible = open_bible()
    show_welcome()

    current = NavigationState()

    while True:
        raw = input("\n📖 ").strip()
        command = raw.lower()

        if command in {"quit", "exit", "q"}:
            console.print("[dim]Closing.[/dim]")
            break

        if command in {":help", "help", "h", "?"}:
            show_help()
            continue

        if command in {":next", "next", "nxt"}:
            if not current.is_ready():
                friendly_error(
                    "No prior passage stored. Enter a reference before moving ahead.",
                )
                continue

            nxt = pass_next(bible, current.book, current.chapter, current.verse)
            if nxt is None:
                friendly_error("No further passage found in this direction.")
                continue

            book, chapter, verse = nxt
            reference = build_reference_string(book, chapter, verse)
            try:
                get_passage(bible, reference)
            except ValueError as exc:
                friendly_error(str(exc))
                continue

            current.store(book, chapter, verse)
            console.print(f"[gold1]Loaded passage:[/gold1] [italic]{reference}[/italic]")
            continue

        if command in {":prev", "prev", "previous", "back"}:
            if not current.is_ready():
                friendly_error(
                    "No prior passage stored. Enter a reference before moving back.",
                )
                continue

            prv = pass_prev(bible, current.book, current.chapter, current.verse)
            if prv is None:
                friendly_error("No further passage found in this direction.")
                continue

            book, chapter, verse = prv
            reference = build_reference_string(book, chapter, verse)
            try:
                get_passage(bible, reference)
            except ValueError as exc:
                friendly_error(str(exc))
                continue

            current.store(book, chapter, verse)
            console.print(f"[gold1]Loaded passage:[/gold1] [italic]{reference}[/italic]")
            continue

        if command.startswith(":"):
            console.print("[italic dim]Unrecognized command. Type :help for guidance.[/italic dim]")
            continue

        book, chapter, verse = parse_reference(raw)
        if not book or chapter is None:
            friendly_error(
                "Reference not recognized. Check your input and try again.",
                "Examples: John 1, John 1:1, Psalm 23:1-4",
            )
            continue

        resolved_book, suggestion = resolve_book_name(bible, book)
        if suggestion and resolved_book != book:
            console.print(
                f"[gold1]Interpreting book as[/gold1] [italic]{resolved_book}[/italic] "
                f"[italic dim](entered '{book}')[/italic dim]"
            )
        book = resolved_book

        reference = build_reference_string(book, chapter, verse)
        try:
            get_passage(bible, reference)
        except ValueError as exc:
            friendly_error(str(exc))
            continue

        current.store(book, chapter, verse)
        console.print(f"[gold1]Loaded passage:[/gold1] [italic]{reference}[/italic]")


if __name__ == "__main__":
    main()
# Step 3: CLI to depend on CommandRouter and injected services
# Step 3a: Orchestrate input/output only; move logic to services
# Step 3b: Keep CLI surface stable while refactor proceeds under-the-hood
