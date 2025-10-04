# verbum/core/reference.py
# Parses and normalizes Bible references entered by the user.
# Shared across verbum.cli.main and verbum.core.reader for consistent handling.
from __future__ import annotations

import difflib
import re


def parse_reference(reference: str) -> tuple[str | None, int | None, int | tuple[int, int] | None]:
    """
    Parse a human-entered reference into book, chapter, and verse details.
    Args:
        reference (str): Raw reference string supplied by a CLI user.
    Returns:
        tuple[str | None, int | None, int | tuple[int, int] | None]: Parsed components, or Nones on error.
    """
    try:
        normalized = reference.strip()
        normalized = re.sub(r"\s*:\s*", ":", normalized)
        normalized = re.sub(r"\s*-\s*", "-", normalized)
        normalized = normalized.rstrip(",.;:")
        parts = normalized.split()
        if len(parts) < 2:
            return None, None, None
        raw_book = " ".join(parts[:-1])
        book = raw_book.strip()

        last_part = parts[-1]

        if ":" not in last_part:
            chapter = int(last_part)
            return book, chapter, None

        chapter_str, verse_part = last_part.split(":")
        chapter = int(chapter_str)

        if "-" in verse_part:
            start_str, end_str = verse_part.split("-")
            start_verse = int(start_str)
            end_verse = int(end_str)
            return book, chapter, (start_verse, end_verse)
        else:
            verse = int(verse_part)
            return book, chapter, verse

    except Exception:
        return None, None, None


def suggest_book(bible, user_input: str):
    """
    Suggest the closest canonical book name for a user entry.
    Args:
        bible (dict): Loaded Bible dataset used to derive valid book names.
        user_input (str): Raw book name provided by the user.
    Returns:
        str | None: Suggested canonical name or None when no close match exists.
    """
    books = list(bible.keys())
    lowered_books = [b.lower() for b in books]
    match = difflib.get_close_matches(
        user_input.strip().lower(),
        lowered_books,
        n=1,
        cutoff=0.6
    )
    if match:
        idx = lowered_books.index(match[0])
        return books[idx]
    return None


def build_reference_string(book: str, chapter: int, verse: int | tuple[int, int] | None) -> str:
    """
    Assemble a canonical reference string from parsed components.
    Args:
        book (str): Canonical book name.
        chapter (int): Chapter index.
        verse (int | tuple[int, int] | None): Verse number, range, or None for whole chapters.
    Returns:
        str: Canonical reference suitable for downstream rendering.
    """
    if verse is None:
        return f"{book} {chapter}"
    if isinstance(verse, tuple):
        start, end = verse
        return f"{book} {chapter}:{start}-{end}"
    return f"{book} {chapter}:{verse}"


def resolve_book_name(bible, book: str) -> tuple[str, str | None]:
    """
    Resolve a book entry to its canonical form and provide suggestions.
    Args:
        bible (dict): Loaded Bible dataset used for lookups.
        book (str): User-supplied book name awaiting normalization.
    Returns:
        tuple[str, str | None]: Canonical book and optional suggestion message.
    """
    canonical = next((name for name in bible if name.lower() == book.lower()), None)
    if canonical:
        return canonical, None

    suggestion = suggest_book(bible, book)
    if suggestion:
        return suggestion, suggestion
    return book, None
