# verbum/core/reference.py
from __future__ import annotations
import difflib
import re
from verbum.domain.reference import Reference



def normalize_reference_string(s: str) -> str:
    """
    Normalize a human-entered Bible reference.

        | Input               | Output          |
        | ------------------- | ----------------|
        | "  john 3 : 16  "   | "john 3:16"     |
        | "John 3 : 16 - 18 " | "John 3:16-18"  |
        | "John 3:16,"        |  "John 3:16"    |
    """
    s = s.strip()
    s = re.sub(r"\s*:\s*", ":", s)
    s = re.sub(r"\s*-\s*", "-", s)   
    s = s.rstrip(",.;:")
    s = re.sub(r"\s+", " ", s)
    return s



def parse_reference(reference: str) -> tuple[str | None, int | None, int | tuple[int, int] | None]:
    """Backward-compatible wrapper that parses using the Reference class."""
    try:
        normalized = normalize_reference_string(reference)
        ref = Reference.from_string(normalized)
        return ref.book, ref.chapter, ref.verses
    except Exception as e:
        return None, None, None 



def suggest_book(bible, user_input: str):
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
    """(Legacy) Assemble canonical reference string. Prefer str(Reference(...))."""
    if verse is None:
        return f"{book} {chapter}"
    if isinstance(verse, tuple):
        start, end = verse
        return f"{book} {chapter}:{start}-{end}"
    return f"{book} {chapter}:{verse}"




def resolve_book_name(bible, book: str) -> tuple[str, str | None]:
    canonical = next((name for name in bible if name.lower() == book.lower()), None)
    if canonical:
        return canonical, None

    suggestion = suggest_book(bible, book)
    if suggestion:
        return suggestion, suggestion
    return book, None
# Step 4: Reference parsing/normalization to be encapsulated in ReferenceParser service
# Step 4a: Keep build_reference_string for compatibility until services replace direct calls
