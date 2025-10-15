from pydantic import BaseModel

class Verse(BaseModel):
    number: int | None
    text: str

class ReferenceResponse(BaseModel):
    book: str
    chapter: int
    verses: list[Verse]

class SearchResult(BaseModel):
    book: str
    chapter: int
    verse: int
    text: str

class WordSearchResponse(BaseModel):
    query: str
    page: int
    page_size: int
    total_pages: int
    total_results: int
    results: list[SearchResult]

class SummaryResponse(BaseModel):
    book: str
    count: int

class WordSummaryResponse(BaseModel):
    query: str
    summary: list[SummaryResponse]