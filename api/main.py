from fastapi import FastAPI, Query, HTTPException
from verbum.infrastructure.repositories.json_bible_repository import JsonBibleRepository
from verbum.core.bible_service import BibleService
from verbum.core.normalizer import normalize_reference_raw
from verbum.domain.reference import Reference
import re
import pathlib
from pydantic import BaseModel 

app = FastAPI()

DATA_PATH = pathlib.Path(__file__).parent.parent / "verbum" / "data" / "ACV.json"
repo = JsonBibleRepository(str(DATA_PATH))
service = BibleService(repo)

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
    results: list[SearchResult]


@app.get("/lookup", response_model=ReferenceResponse | WordSearchResponse)
def get_query(q: str = Query(..., description="To lookf for a reference or a word")):
    cmd = q.lower().strip()

    if not cmd:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if re.search(r"\s+\d+(:\d+)?", cmd):
        raw = normalize_reference_raw(cmd)
        ref = Reference.from_string(raw)
        ref.book = service.suggest_book(ref.book)
        lines = service.get_passage_text(ref)

        if isinstance(lines, str):
            lines = lines.splitlines()

        verses_data = []
        for line in lines:
            try:
                num, txt = line.split(". ", 1)
                verses_data.append({"number": int(num), "text": txt.strip()})
            except ValueError:
                verses_data.append({"number": None, "text": line.strip()})
        return ReferenceResponse(book=ref.book, chapter=ref.chapter, verses=verses_data)
    
    else:
        results = repo.search(cmd, 100)
        search_results = [SearchResult(**r) for r in results]
        return WordSearchResponse(query=q, results=search_results)