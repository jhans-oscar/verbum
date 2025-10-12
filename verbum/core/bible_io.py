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




def get_next_book(bible: Bible, book: str) -> str | None:
    books = list(bible.keys())
    try:
        idx = books.index(book)
    except ValueError:
        return None
    if idx + 1 < len(books):
        return books[idx + 1]
    return None


def get_prev_book(bible: Bible, book: str) -> str | None:
    books = list(bible.keys())

    try:
        idx = books.index(book)
    except ValueError:
        return None

    if idx - 1 >= 0:
        return books[idx - 1]
    return None


def find_text(bible: Bible, book: str, chapter: int, verse: int) -> str:
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
# Step 1: Planned migration of data access into infrastructure/repositories/json_bible_repository.py
# Step 1a: bible_io helpers will be wrapped or replaced by a BibleRepository interface.
# Step 1b: Call sites in CLI/Reader to be rewired to use services that depend on the repository.
