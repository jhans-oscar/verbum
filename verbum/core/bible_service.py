import difflib
from rich.console import Console
from verbum.domain.reference import Reference
from verbum.infrastructure.repositories.bible_repository import BibleRepository

console = Console()
class EndOfBibleError(Exception):
    pass

class StartOfBibleError(Exception):
    pass
class BibleService:
    """Core logic layer for Bible navigation and reference lookup."""
    def __init__(self, repository: BibleRepository):
        self.repo = repository

    def get_passage_text(self, ref: Reference) -> str:
        verses = self.repo.get_passage(ref)
        lines = [f"{num}. {text}" for num, text in verses]
        return "\n".join(lines)

    def get_next(self, ref: Reference) -> Reference:
        """Return the next Reference (verse/chapter/book) after the given one."""
        if ref.verses is None:
            book = ref.book
            books = self.repo.list_books()
            i = books.index(book)
            chapter = ref.chapter
            max_chapter = self.repo.chapter_count(book)
            next_chapter = chapter + 1

            if next_chapter <= max_chapter:
                return Reference(book, next_chapter, None)
            
            if i + 1 < len(books):
                next_book = books[i + 1]
                return Reference(next_book, 1, None )
            
            raise EndOfBibleError("Reached the end of the Bible")
        
        else:
            verses = ref.verses or []
            last_verse = verses[-1]
            next_verse = last_verse + 1
            max_verse = self.repo.verse_count(ref.book, ref.chapter)

            if next_verse <= max_verse:
                return Reference(ref.book, ref.chapter, [next_verse])
            
            # roll over to next chapter / next book
            books = self.repo.list_books()
            i = books.index(ref.book)
            max_chapter = self.repo.chapter_count(ref.book)

            if ref.chapter < max_chapter:
                return Reference(ref.book, ref.chapter + 1, [1])
            elif i + 1 < len(books):
                next_book = books[i + 1]
                return Reference(next_book, 1, [1])
            else:
                raise EndOfBibleError("Reached the end of the Bible.")

    def get_prev(self, ref: Reference) -> Reference:
        """Return the previous Reference (verse/chapter/book) before the given one."""
        if ref.verses is None:
            if ref.chapter > 1:
                return Reference(ref.book, ref.chapter - 1, None)
            
            books = self.repo.list_books()
            i = books.index(ref.book)

            if i > 0:
                prev_book = books[i - 1]
                last_chapter = self.repo.chapter_count(prev_book)
                return Reference(prev_book, last_chapter, None)
            
            raise StartOfBibleError("You have reached the beginning of the Bible")
        
        else:
            verses = ref.verses or []
            first_verse = verses[0]
            prev_verse = first_verse - 1
            
            if prev_verse > 0:
                return Reference(ref.book, ref.chapter, [prev_verse])
            
            
            books = self.repo.list_books()
            i = books.index(ref.book)

            if ref.chapter > 1:
                prev_chapter = ref.chapter - 1
                last_verse = self.repo.verse_count(ref.book, prev_chapter)
                return Reference(ref.book, prev_chapter, [last_verse])
            
            if i == 0:
                raise StartOfBibleError("You have reached the beginning of the Bible.")
            
            prev_book = books[i - 1]
            last_chapter = self.repo.chapter_count(prev_book)
            last_verse = self.repo.verse_count(prev_book, last_chapter)
            return Reference(prev_book, last_chapter, [last_verse])
        

    def suggest_book(self, user_book: str) -> str:
        """
        Returns the closest valid book name to the user input.
        If an exact match exists, it returns it directly.
        Never raises errors.
        """
        books = self.repo.list_books()
        user_book = user_book.strip().title()

        for book in books:
            if book.lower() == user_book.lower():
                return book
            

        matches = difflib.get_close_matches(user_book, books, n=1, cutoff=0.6)
        if matches:
            suggestion = matches[0]
            console.print(f"[magenta]Did you mean '{suggestion}'? Using that.[/magenta]")
            return suggestion
        
        console.print(f"[yellow]⚠️  Unknown book '{user_book}'.[/yellow]")
        return user_book
    
    def summarize_search(self, query: str) -> dict[str, int]:
        results = self.repo.search(query, 10000)
        counts = {}
        for r in results:
            book = r["book"]
            counts[book] = counts.get(book, 0) + 1
        return counts


        

