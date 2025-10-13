from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from verbum.core.bible_service import BibleService, EndOfBibleError, StartOfBibleError
from verbum.infrastructure.repositories.json_bible_repository import JsonBibleRepository
from verbum.domain.reference import Reference
from verbum.core.normalizer import normalize_reference_raw
from importlib.resources import files

# 1. Inicia FastAPI
app = FastAPI(title="Verbum API", version="0.1.0")

# 2. Carga la Biblia (igual que en tu CLI)
data_path = files("verbum.data").joinpath("KJV.json")
repo = JsonBibleRepository(data_path)
service = BibleService(repo)

# 3. Endpoint básico
@app.get("/read/{book}/{chapter}", response_class=JSONResponse)
def read_chapter(book: str, chapter: int):
    ref = Reference(book.title(), chapter)
    text = service.get_passage_text(ref)
    return JSONResponse(content={
        "reference": f"{book.title()} {chapter}",
        "verse_count": len(text.split("\n")),
        "text": text
    })

@app.get("/books")
def get_books():
    try:
        books = repo.list_books()
        return {"books": books, "count": len(books)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading books: {e}")

@app.get("/range/{book}/{chapter}/{start}/{end}")
def read_range(book: str, chapter: int, start: int, end: int):
    norm_book = book.title()
    if start < 1:
        raise HTTPException(status_code=400, detail="start must be >= 1")
    if end < start:
        raise HTTPException(status_code=400, detail="end must be >= start")
    
    try:
        max_verse = repo.verse_count(norm_book, chapter)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    if max_verse is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    if end > max_verse:
        raise HTTPException(
            status_code=400,
            detail=f"end ({end}) exceeds max verse ({max_verse}) for {norm_book} {chapter}"
        )
    
    verses = list(range(start, end + 1))
    ref = Reference(norm_book, chapter, verses)

    try:
        text = service.get_passage_text(ref)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrive passage: {e}")
    
    return {
        "reference": f"{norm_book} {chapter}:{start}-{end}",
        "book": norm_book,
        "chapter": chapter,
        "verses": verses,
        "text": text
    }

@app.get("/read/{book}/{chapter}/{verses}")
def read_verse(book: str, chapter: int, verses: str):
    norm_book = book.title()

    try:
        verse_list = [int(v) for v in verses.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Verses must be numeric, e.g. 3:16 or 3:16,17,18")
    
    try:
        max_verse = repo.verse_count(norm_book, chapter)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    if max_verse is None:
       raise HTTPException(status_code=404, detail="Chapter not found")
     
    
    if max(verse_list) > max_verse:
        raise HTTPException(status_code=400, detail=f"{verses} not found in {norm_book}")
    
    ref = Reference(norm_book, chapter, verse_list)

    try:
        text = service.get_passage_text(ref)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrive passage: {e}")
    
    return {
        "reference": f"{norm_book} {chapter}:{verse_list}",
        "book": norm_book,
        "chapter": chapter,
        "verses": verse_list,
        "text": text
    }

@app.get("/next")
def next_passage(ref: str = Query(..., description="Reference like 'John 3:16'")):
    try:
        clean = normalize_reference_raw(ref)
        current = Reference.from_string(clean)

        next_ref = service.get_next(current)
        text = service.get_passage_text(next_ref)
        return {
            "reference": str(next_ref),
            "book": next_ref.book,
            "chapter": next_ref.chapter,
            "verses": next_ref.verses,
            "text": text
        }
    
    except EndOfBibleError:
        raise HTTPException(status_code=400, detail="Reached the end of the Bible")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid reference: {e}")
    
@app.get("/prev")
def prev_passage(ref: str = Query(..., description="Reference like 'John 3:16'")):
    try:
        clean = normalize_reference_raw(ref)
        current = Reference.from_string(clean)

        prev_ref = service.get_prev(current)
        text = service.get_passage_text(prev_ref)
        return {
            "reference": str(prev_ref),
            "book": prev_ref.book,
            "chapter": prev_ref.chapter,
            "verses": prev_ref.verses,
            "text": text
        }
    
    except StartOfBibleError:
        raise HTTPException(status_code=400, detail="Reached the start of the Bible")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid reference: {e}")
    

@app.get("/search")
def search_verses(query: str = Query(..., description="Word or phrase to search for"),
                  limit: int = Query(20, ge=1, le=100)):
    if len(query) < 2:
        raise HTTPException(status_code=400, detail="Search term too short")
    
    results = repo.search(query, max_results=limit)
    if not results:
        return {"query": query, "results": [], "count": 0, "message": "No matches found"}
    return {"query": query, "count": len(results), "results":results}
    