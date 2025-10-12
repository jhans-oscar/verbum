import os
from pathlib import Path
from verbum.infrastructure.repositories.json_bible_repository import JsonBibleRepository

def make_repository():
    path = os.environ.get("BIBLE_PATH")
    return JsonBibleRepository(bible_path=path)

class Passage:
    def __init__(self, reference, verses):
        self.reference = reference
        self.verses = verses

    def __str__(self):
        lines = []
        for verse in self.verses:
            if isinstance(verse.reference.verses, list):
                num = verse.reference.verses[0]
            else:
                num = verse.reference.verses
            lines.append(f"{num}. {verse.text}")
        joined = "\n".join(lines)
        return f"{self.reference}\n\n{joined}"

    @classmethod
    def from_bible(cls, bible_data, reference):
        # 1. Get book
        book_data = bible_data.get(reference.book)
        if not book_data:
            raise ValueError(f"Book '{reference.book}' not found in Bible data.")

        # 2. Get chapter (make sure to convert to string)
        chapter_data = book_data.get(str(reference.chapter))
        if not chapter_data:
            raise ValueError(f"Chapter '{reference.chapter}' not found in '{reference.book}'.")

        # 3. Convert the list into a dict{verse_number: text}
        verse_dict = {}
        for entry in chapter_data:
            try:
                left, right = entry.split("\t", 1)
                # left example: "Genesis 1:3"
                verse_num = int(left.split(":")[1])
                verse_dict[verse_num] = right.strip()
            except Exception as e:
                print("Skipping malformed line:", entry, e)

        if reference.verses is None:
            verse_numbers = sorted(verse_dict.keys())

        elif isinstance(reference.verses, int):
            verse_numbers = [reference.verses]
        else:
            start, end = reference.verses
            verse_numbers = list(range(start, end + 1))

        # 4. Build list of (num, text)
        verses = []
        for num in verse_numbers:
            text = verse_dict.get(num)
            if text is None:
                raise ValueError(f"Verse {num} not found in {reference.book} {reference.chapter}.")
            verses.append((num, text))

        return cls(reference, verses)
"""
# Step 6: Domain models remain pure; no I/O or infrastructure imports
"""
