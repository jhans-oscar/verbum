from fastapi import FastAPI, Query, HTTPException
from verbum.infrastructure.repositories.json_bible_repository import JsonBibleRepository
from verbum.core.bible_service import BibleService
from verbum.core.normalizer import normalize_reference_raw
from verbum.domain.reference import Reference
import re
import math
import pathlib
from models import (
    ReferenceResponse,
    WordSearchResponse,
    WordSummaryResponse,
    Verse,
    SearchResult,
    SummaryResponse,
)

app = FastAPI()

DATA_PATH = pathlib.Path(__file__).parent.parent / "verbum" / "data" / "ACV.json"
repo = JsonBibleRepository(str(DATA_PATH))
service = BibleService(repo)



@app.get("/lookup", response_model=ReferenceResponse | WordSearchResponse | WordSummaryResponse)
def get_query(
    q: str = Query(..., description="Word or reference to look up"),
    book: str = Query(None, description="Optional book filter"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(0, ge=1, le=100, description="Results per page (0 returns all matches, up to 100 per page)")
    ):
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
        lines = repo.search(cmd)
        total_results = len(lines)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_lines = lines[start:end]
        total_pages = math.ceil(len(lines) / page_size)
        if not paginated_lines:
            raise HTTPException(status_code=404, detail="Page out of range")

        results_data = [
            {"book": r["book"], "chapter": r["chapter"], "verse": r["verse"], "text": r["text"]}
            for r in paginated_lines
        ]
        return WordSearchResponse(
            query=q,
            page=page,
            page_size=page_size or len(lines) or 1,
            total_pages=total_pages,
            total_results=total_results,
            results=results_data
        ) 
    


         