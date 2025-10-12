# verbum/core/formatting.py
# Provides display helpers for formatting verse output.
# Used by verbum.core.reader to render superscript verse numbers.
from __future__ import annotations

SUPERSCRIPTS = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def format_verse(number: int, text: str) -> str:
    """
    Combine a verse number and text using superscript digits.
    Args:
        number (int): Verse index to render.
        text (str): Verse content associated with the number.
    Returns:
        str: Formatted verse string ready for console output.
    """
    return f"{str(number).translate(SUPERSCRIPTS)} {text}"
# Step 5: Formatting will be used by presentation-specific formatters (e.g., RichFormatter)
# Step 5a: Keep helpers small and pure for reuse across interfaces
