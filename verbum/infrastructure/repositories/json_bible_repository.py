"""
# Step 1: Introduced JsonBibleRepository to own JSON data access
# Step 1a: Implements BibleRepository; replaces direct use of core/bible_io in consumers
"""
# verbum/infrastructure/repositories/json_bible_repository.py
import json
from verbum.domain.reference import Reference
from verbum.domain.verse import Verse
from verbum.domain.passage import Passage
from .bible_repository import BibleRepository

class JsonBibleRepository(BibleRepository):
    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.bible = json.load(f)

            
    def get_book(self) -> list[str]:
        return list(self.bible.keys())
    

    def get_chapter_count(self, book: str) -> int:
        book_data = self.bible.get(book, {})
        return len(book_data)
    

    def get_verse_count(self, book: str, chapter: int) -> int:
        book_data = self.bible.get(book, {})
        chapter_data = book_data.get(str(chapter), {})
        return len(chapter_data)
    

    def get_passage(self, ref: Reference) -> Passage:
        book_data = self.bible.get(ref.book, {})
        chapter_data = book_data.get(str(ref.chapter))
        if chapter_data is None:
            raise ValueError(f"Chapter {ref.chapter} not found in {ref.book}")
        # 1️⃣ Convert the list of strings into a {verse_num: text} dict
        verse_dict = {}
        for entry in chapter_data:
            try:
                left, right = entry.split("\t", 1)
                # left looks like "John 3:16"
                verse_num = int(left.split(":")[1])
                verse_dict[verse_num] = right.strip()
            except Exception as e:
                print("Skipping malformed line:", entry, e)
        # 2️⃣ Figure out which verses we need
        if ref.verses is None:
            verse_numbers = sorted(verse_dict.keys())
        elif isinstance(ref.verses, tuple):
            start, end = ref.verses
            verse_numbers = range(start, end + 1)
        elif isinstance(ref.verses, list):
            verse_numbers = ref.verses
        else:
            verse_numbers = [ref.verses]
        # 3️⃣ Build list of Verse objects
        verses = []
        for num in verse_numbers:
            text = verse_dict.get(num)
            if text:
                vref = Reference(ref.book, ref.chapter, [num])
                verses.append(Verse(vref, text))
            else:
                print(f"Warning: Verse {num} not found in {ref.book} {ref.chapter}")
        # 4️⃣ Return the Passage
        return Passage(ref, verses)

            

