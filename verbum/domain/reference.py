import re

class Reference:
    """ A reference to a specific location in a text, such as a book, chapter, and verse. """

    def __init__(self, book: str, chapter: int, verses: list[int] | None = None):
        self.book = book
        self.chapter = chapter
        self.verses = verses

    @classmethod
    def from_string(cls, reference: str):
        """
        Parse a reference string like:
        - 'Genesis 1'
        - 'John 3:16'
        - 'Psalm 23:1-4'
        - '1 John 3:16'
        - 'Song of Solomon 1:2'

        Returns a Reference(book, chapter, verses).
        """
        
        m = re.match(r"^(?P<book>.+?)\s+(?P<chap>\d+)(?::(?P<verses>[\d-]+))?$", reference.strip())
        if not m:
            raise ValueError(f"Invalid reference: {reference}")
        
        book = m["book"].title() 
        chapter = int(m["chap"])
        verses = None

        if m["verses"]:
            v = m["verses"]
            if "-" in v:
                start, end = map(int, v.split("-"))
                verses = list(range(start, end + 1))
            else:
                verses = [int(v)]
        else:
            verses = None

        return cls(book, chapter, verses)

    
    def __str__(self): 
        """Return a human-readable representation of the reference."""

        if self.verses is None:
            return f"{self.book} {self.chapter}"
        
        if len(self.verses) == 1:
            return f"{self.book} {self.chapter}:{self.verses[0]}"
        

        return f"{self.book} {self.chapter}:{self.verses[0]}-{self.verses[-1]}"
            
        

