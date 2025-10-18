import json
from pathlib import Path
from importlib.abc import Traversable
from verbum.domain.reference import Reference
from .bible_repository import BibleRepository

class JsonBibleRepository(BibleRepository):
    def __init__(self, file_path: Path | Traversable | str):
        """Load Bible data from a filesystem path or importlib.resources Traversable."""
        if hasattr(file_path, "read_text"):
            text = file_path.read_text(encoding="utf-8")  # type: ignore[attr-defined]
        else:
            text = Path(file_path).read_text(encoding="utf-8")
        self.data = json.loads(text)

    def get_passage(self, ref: Reference) -> list[tuple[int, str]]:

        # 1️⃣ Get the book
        books = self.data.get("books", [])
        book_data = next((b for b in books if b["name"].lower() == ref.book.lower()), None)
        if not book_data:
            raise ValueError(f"Book '{ref.book}' not found. ")
        
        # 2️⃣ Get the chapter
        chapters = book_data.get("chapters", [])
        chapter_data = next((c for c in chapters if c["chapter"] == ref.chapter), None)
        if not chapter_data:
            raise ValueError(f"Chapter '{ref.chapter}' not found in '{ref.book}'.")
        
        # 3️⃣ Get the verses
        verses = chapter_data.get("verses", [])
        if ref.verses is None:
            return [(v["verse"], v["text"]) for v in verses]
        
        else:
            result = []
            for vnum in ref.verses:
                verse_obj = next((v for v in verses if v["verse"] == vnum), None)
                if verse_obj:
                    result.append((verse_obj["verse"], verse_obj["text"]))
            return result

    def list_books(self) -> list[str]:
        return [book["name"] for book in self.data["books"]]

    def chapter_count(self, book: str) -> int:
        for b in self.data["books"]:
            if b["name"] == book:
                return len(b["chapters"])
        raise ValueError(f"Book not found: {book}")
    
    def verse_count(self, book: str, chapter: int) -> int:
        for b in self.data["books"]:
            if b["name"] == book:
                chapters = b["chapters"]
                if 1 <= chapter <= len(chapters):
                    return len(chapters[chapter - 1]["verses"])
                raise ValueError(f"Invalid chapter number {chapter} for book {book}")
        raise ValueError(f"Book not found: {book}")

    def search(self, query: str, limit: int | None = None) -> list[dict]:
        query = query.lower()
        results = []

        if not query:
            return []

        for book in self.data["books"]:
            book_name = book["name"]
            for chapter_data in book["chapters"]:
                chap = chapter_data["chapter"]
                for verse in chapter_data["verses"]:
                    text = verse["text"]
                    if query in text.lower():
                        results.append({
                            "book": book_name,
                            "chapter": chap,
                            "verse": verse["verse"],
                            "text": text.strip()
                        })
                        if limit is not None and len(results) >= limit:
                            return results[:limit]
        return results
