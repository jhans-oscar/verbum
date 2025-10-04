# verbum/core/reader.py
# Validates user references and streams formatted passages to the console.
# Called by verbum.cli.main after resolving navigation state and reference strings.
# Depends on verbum.core.bible_io, verbum.core.reference, and verbum.core.formatting.
from __future__ import annotations

import logging

from rich.console import Console

from verbum.core.bible_io import (
    Bible,
    find_text,
    get_chapter_count,
    get_verse_count,
)
from verbum.core.formatting import format_verse
from verbum.core.reference import parse_reference, suggest_book

console = Console()


def render_passage(reference: str, verses: list[str]) -> str:
    """
    Render a passage with numbered verses and a uniform footer.
    Args:
        reference (str): Canonical reference string to display.
        verses (list[str]): Plain verse text lines in reading order.
    Returns:
        str: Aggregated plain-text representation of the rendered content.
    """
    divider = "─" * 40
    console.print(f"[bold blue]{reference}[/bold blue]")
    console.print(f"[dim]{divider}[/dim]")

    rendered_lines: list[str] = [reference, divider]
    for index, text in enumerate(verses, start=1):
        numbered_line = format_verse(index, text)
        console.print(f"[dim]{index:02d}[/dim] {text}")
        rendered_lines.append(numbered_line)

    footer = "← back  ·  next →"
    console.print("\n[dim]← back  ·  next →[/dim]")
    rendered_lines.extend(["", footer])
    return "\n".join(rendered_lines)


def get_passage(bible: Bible, reference: str) -> str:
    """
    Validate a reference and render the requested passage to the console.
    Args:
        bible (Bible): Loaded Bible dataset shared across the session.
        reference (str): Canonical or user-entered reference string.
    Returns:
        str: Concatenated text representation of the rendered passage.
    """
    book, chapter, verse = parse_reference(reference)
    if not book or chapter is None:
        raise ValueError("Reference not recognized. Provide a book and chapter.")
    if chapter < 1:
        raise ValueError("Chapters begin at 1.")

    canonical = next((name for name in bible if name.lower() == book.lower()), None)
    if canonical:
        book = canonical
    elif book not in bible:
        suggestion = suggest_book(bible, book)
        if suggestion:
            console.print(
                f"[gold1]Interpreting book as[/gold1] [italic]{suggestion}[/italic] "
                f"[italic dim](entered '{book}')[/italic dim]"
            )
            logging.info("Autosuggest: corrected '%s' to '%s'", book, suggestion)
            book = suggestion
        else:
            raise ValueError(f"Unable to locate the book '{book}'.")

    max_chapter = get_chapter_count(bible, book)
    if chapter > max_chapter:
        raise ValueError(f"{book} contains only {max_chapter} chapters.")

    if verse is None:
        max_verse = get_verse_count(bible, book, chapter)
        verses = [find_text(bible, book, chapter, idx) for idx in range(1, max_verse + 1)]
        reference_label = f"{book} {chapter}"
        return render_passage(reference_label, verses)

    if isinstance(verse, tuple):
        start, end = verse
        max_verse = get_verse_count(bible, book, chapter)
        if start < 1 or end > max_verse or start > end:
            raise ValueError(
                f"Verse range invalid. {book} {chapter} contains {max_verse} verses."
            )
        verses = [find_text(bible, book, chapter, idx) for idx in range(start, end + 1)]
        reference_label = f"{book} {chapter}:{start}-{end}"
        return render_passage(reference_label, verses)

    max_verse = get_verse_count(bible, book, chapter)
    if verse < 1:
        raise ValueError("Verses begin at 1.")
    if verse > max_verse:
        raise ValueError(f"{book} {chapter} contains only {max_verse} verses.")

    verse_text = find_text(bible, book, chapter, verse)
    reference_label = f"{book} {chapter}:{verse}"
    return render_passage(reference_label, [verse_text])
