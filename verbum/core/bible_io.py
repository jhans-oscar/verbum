# verbum/core/bible_io.py
# Loads Bible text data and exposes helpers for passage lookup.
# Provides navigation mechanics consumed by verbum.cli.main and verbum.core.reader.
from __future__ import annotations

import json
import os
from importlib.resources import files
from pathlib import Path
from typing import Dict, List

Bible = Dict[str, Dict[str, List[str]]]

_env_path = os.environ.get("BIBLE_PATH")

if _env_path:
    BIBLE_PATH = Path(_env_path).resolve()
else:
    BIBLE_PATH = files("verbum.data") / "KJV.json"


def open_bible() -> Bible:
    """
    Load the configured Bible dataset into memory.
    Returns:
        Bible: Nested mapping of books to chapter and verse text.
    """
    if hasattr(BIBLE_PATH, "is_file"):
        exists = BIBLE_PATH.is_file()
    else:
        exists = Path(BIBLE_PATH).is_file()

    if not exists:
        raise FileNotFoundError(
            f"Dataset not found. Verify your BIBLE_PATH setting: {BIBLE_PATH}"
        )

    with BIBLE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_chapter_count(bible: Bible, book: str) -> int:
    """
    Count the chapters available for a given book.
    Args:
        bible (Bible): Loaded Bible dataset.
        book (str): Canonical book name to inspect.
    Returns:
        int: Number of chapters, or 0 when the book is missing.
    """
    return len(bible.get(book, {}))


def get_verse_count(bible: Bible, book: str, chapter: int) -> int:
    """
    Count the verses contained in a specific chapter.
    Args:
        bible (Bible): Loaded Bible dataset.
        book (str): Canonical book name to inspect.
        chapter (int): Chapter index within the selected book.
    Returns:
        int: Number of verses for the chapter, defaulting to 0 when missing.
    """
    book_data = bible.get(book, {})
    return len(book_data.get(str(chapter), []))


def get_next_book(bible: Bible, book: str) -> str | None:
    """
    Resolve the book that follows the supplied title.
    Args:
        bible (Bible): Loaded Bible dataset.
        book (str): Canonical book name used as the starting point.
    Returns:
        str | None: Next book title or None when at the end of the canon.
    """
    books = list(bible.keys())
    try:
        idx = books.index(book)
    except ValueError:
        return None
    if idx + 1 < len(books):
        return books[idx + 1]
    return None


def get_prev_book(bible: Bible, book: str) -> str | None:
    """
    Resolve the book that precedes the supplied title.
    Args:
        bible (Bible): Loaded Bible dataset.
        book (str): Canonical book name used as the starting point.
    Returns:
        str | None: Previous book title or None when at the beginning.
    """
    books = list(bible.keys())

    try:
        idx = books.index(book)
    except ValueError:
        return None

    if idx - 1 >= 0:
        return books[idx - 1]
    return None


def find_text(bible: Bible, book: str, chapter: int, verse: int) -> str:
    """
    Fetch the text of a single verse after validating bounds.
    Args:
        bible (Bible): Loaded Bible dataset.
        book (str): Canonical book name to read from.
        chapter (int): Chapter index expected to contain the verse.
        verse (int): Verse index within the chapter.
    Returns:
        str: Verse text stripped of numbering artifacts.
    """
    if book not in bible:
        raise ValueError(f"Unable to locate the book '{book}'.")

    book_data = bible[book]
    if str(chapter) not in book_data:
        raise ValueError(
            f"Chapter {chapter} not found in {book}. The text contains {len(book_data)} chapters."
        )

    chapter_data = book_data[str(chapter)]
    if verse < 1 or verse > len(chapter_data):
        raise ValueError(
            f"Verse {verse} not found in {book} {chapter}. That chapter contains {len(chapter_data)} verses."
        )

    text = chapter_data[verse - 1]
    if "\t" in text:
        text = text.split("\t", 1)[1]
    elif " " in text and text.split(" ")[0].lower() == book.lower():
        text = " ".join(text.split(" ")[2:])

    return text


def pass_next(
    bible: Bible,
    book: str,
    chapter: int,
    verse: int | None = None,
) -> tuple[str, int, int | None] | None:
    """
    Determine the next sequential reference.
    Args:
        bible (Bible): Loaded Bible dataset.
        book (str): Current canonical book name.
        chapter (int): Current chapter index.
        verse (int | None): Current verse or None when on a whole chapter.
    Returns:
        tuple[str, int, int | None] | None: Next reference tuple or None at the end.
    """
    if chapter is None:
        return None

    if verse is not None:
        max_verses = get_verse_count(bible, book, chapter)
        if verse < max_verses:
            return book, chapter, verse + 1

        max_chapter = get_chapter_count(bible, book)
        if chapter < max_chapter:
            return book, chapter + 1, 1

        next_book = get_next_book(bible, book)
        if next_book:
            return next_book, 1, 1
        return None

    max_chapter = get_chapter_count(bible, book)
    if chapter < max_chapter:
        return book, chapter + 1, None

    next_book = get_next_book(bible, book)
    if next_book:
        return next_book, 1, None
    return None


def pass_prev(
    bible: Bible,
    book: str,
    chapter: int,
    verse: int | None = None,
) -> tuple[str, int, int | None] | None:
    """
    Determine the previous sequential reference.
    Args:
        bible (Bible): Loaded Bible dataset.
        book (str): Current canonical book name.
        chapter (int): Current chapter index.
        verse (int | None): Current verse or None when on a whole chapter.
    Returns:
        tuple[str, int, int | None] | None: Previous reference tuple or None at the start.
    """
    if chapter is None:
        return None

    if verse is not None:
        if verse > 1:
            return book, chapter, verse - 1

        if chapter > 1:
            last_verse_prev_ch = get_verse_count(bible, book, chapter - 1)
            return book, chapter - 1, last_verse_prev_ch

        prev_book = get_prev_book(bible, book)
        if prev_book:
            last_ch = get_chapter_count(bible, prev_book)
            last_vs = get_verse_count(bible, prev_book, last_ch)
            return prev_book, last_ch, last_vs
        return None

    if chapter > 1:
        return book, chapter - 1, None

    prev_book = get_prev_book(bible, book)
    if prev_book:
        last_ch = get_chapter_count(bible, prev_book)
        return prev_book, last_ch, None
    return None
