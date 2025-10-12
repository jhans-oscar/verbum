class Reference():
    def __init__(self, book, chapter, verses):
        self.book = book
        self.chapter = chapter
        self.verses = verses
        
    def __str__(self):
        if self.verses is None:
            return f"{self.book} {self.chapter}"
        if isinstance(self.verses, tuple):
            start, end = self.verses
            return f"{self.book} {self.chapter}:{start}-{end}"
        else:
            return f"{self.book} {self.chapter}:{self.verses}"
    
    @classmethod
    def from_string(cls, description: str):
        book_part, rest = description.split(" ", 1)
        book = book_part.strip().title()
        

        if ":" in rest:
            chapter_part, verse_part = rest.split(":", 1)
            chapter = int(chapter_part)

            if "-" in verse_part:
                start, end = map(int, verse_part.split("-"))
                verses = (start, end)
            else:
                verses = int(verse_part)
        else:

            chapter = int(rest)
            verses = None

        return cls(book, chapter, verses) 
    
        
# Step 7: Domain Reference remains a data model; parsing moved to services
