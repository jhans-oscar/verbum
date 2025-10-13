from collections import defaultdict
import math
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from importlib.resources import files

from verbum.core.bible_service import BibleService, EndOfBibleError, StartOfBibleError
from verbum.core.normalizer import normalize_reference_raw
from verbum.domain.reference import Reference
from verbum.infrastructure.repositories.json_bible_repository import JsonBibleRepository

DEFAULT_MODE = "word"
VALID_MODES = {"word", "reference"}
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100
MAX_KEYWORD_RESULTS = 5000

app = FastAPI(title="Verbum API", version="0.2.0")

data_path = files("verbum.data").joinpath("KJV.json")
repo = JsonBibleRepository(data_path)
service = BibleService(repo)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _format_passage(reference: Reference | str, text: str) -> dict[str, Any]:
    ref_str = str(reference) if isinstance(reference, Reference) else reference
    verses = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ". " in stripped:
            number, verse_text = stripped.split(". ", 1)
        else:
            number, verse_text = "", stripped
        verses.append({"number": number.strip(), "text": verse_text.strip()})
    return {"reference": ref_str, "verses": verses, "raw_text": text}


def _group_search_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        grouped[item["book"]].append(item)

    grouped_results: list[dict[str, Any]] = []
    for book, verses in grouped.items():
        formatted = [
            {
                "book": book,
                "chapter": verse["chapter"],
                "verse": verse["verse"],
                "text": verse["text"],
                "reference": f"{book} {verse['chapter']}:{verse['verse']}",
            }
            for verse in verses
        ]
        grouped_results.append({"book": book, "count": len(formatted), "verses": formatted})
    return grouped_results


def _paginate_keyword_results(
    results: list[dict[str, Any]],
    page: int,
    per_page: int,
) -> tuple[list[dict[str, Any]], int, int, int, int]:
    per_page = max(1, min(per_page, MAX_PER_PAGE))
    total = len(results)
    total_pages = max(1, math.ceil(total / per_page)) if total else 1
    current_page = max(1, min(page, total_pages))
    start = (current_page - 1) * per_page
    end = start + per_page
    return results[start:end], total, total_pages, current_page, per_page


def _render_passage_partial(
    request: Request,
    passage: dict[str, Any] | None = None,
    error: str | None = None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        "partials/passage.html",
        {"request": request, "passage": passage, "error": error},
        status_code=status_code,
    )


def _render_groups_partial(
    request: Request,
    *,
    query: str,
    groups: list[dict[str, Any]],
    total_count: int,
    message: str | None = None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        "partials/search.html",
        {
            "request": request,
            "query": query,
            "groups": groups,
            "total_count": total_count,
            "message": message,
        },
        status_code=status_code,
    )


def _render_page(
    request: Request,
    *,
    mode: str,
    query: str | None = None,
    passage: dict[str, Any] | None = None,
    groups: list[dict[str, Any]] | None = None,
    total_count: int | None = None,
    message: str | None = None,
    passage_error: str | None = None,
    status_code: int = 200,
):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "mode": mode,
            "query": query,
            "passage": passage,
            "groups": groups,
            "total_count": total_count,
            "message": message,
            "passage_error": passage_error,
            "per_page": DEFAULT_PER_PAGE,
        },
        status_code=status_code,
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request, mode: str = Query(DEFAULT_MODE)):
    normalized_mode = mode if mode in VALID_MODES else DEFAULT_MODE
    return _render_page(request, mode=normalized_mode, passage=None, groups=None)


@app.get("/read", response_class=HTMLResponse)
def read_reference(request: Request, ref: str = Query(..., description="e.g. John 3:16")):
    hx_request = bool(request.headers.get("hx-request"))
    accept = request.headers.get("accept", "")

    try:
        clean = normalize_reference_raw(ref)
        reference = Reference.from_string(clean)
        reference.book = service.suggest_book(reference.book)
        text = service.get_passage_text(reference)
    except Exception as exc:
        detail = f"Invalid reference: {exc}"
        if hx_request:
            return _render_passage_partial(request, error=detail, status_code=400)
        if "application/json" in accept:
            raise HTTPException(status_code=400, detail=detail) from exc
        return _render_page(
            request,
            mode="reference",
            query=ref,
            passage=None,
            groups=None,
            message=None,
            passage_error=detail,
            status_code=400,
        )

    passage = _format_passage(reference, text)

    if hx_request:
        return _render_passage_partial(request, passage=passage)

    if "application/json" in accept:
        return JSONResponse(
            {
                "reference": passage["reference"],
                "verse_count": len(passage["verses"]),
                "text": text,
            }
        )

    return _render_page(
        request,
        mode="reference",
        query=ref,
        passage=passage,
        groups=None,
        total_count=None,
        message=None,
    )


@app.get("/read/{book}/{chapter}", response_class=HTMLResponse)
def read_chapter(request: Request, book: str, chapter: int):
    hx_request = bool(request.headers.get("hx-request"))
    accept = request.headers.get("accept", "")
    ref = Reference(book.title(), chapter)

    try:
        text = service.get_passage_text(ref)
    except Exception as exc:
        detail = f"Could not load passage: {exc}"
        if hx_request:
            return _render_passage_partial(request, error=detail, status_code=500)
        if "application/json" in accept:
            raise HTTPException(status_code=500, detail=detail) from exc
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=detail,
            status_code=500,
        )

    passage = _format_passage(ref, text)

    if hx_request:
        return _render_passage_partial(request, passage=passage)

    if "application/json" in accept:
        return JSONResponse(
            {
                "reference": passage["reference"],
                "verse_count": len(passage["verses"]),
                "text": text,
            }
        )

    return _render_page(
        request,
        mode="reference",
        passage=passage,
        groups=None,
    )


@app.get("/range/{book}/{chapter}/{start}/{end}", response_class=HTMLResponse)
def read_range(request: Request, book: str, chapter: int, start: int, end: int):
    hx_request = bool(request.headers.get("hx-request"))
    accept = request.headers.get("accept", "")
    normalized_book = book.title()

    try:
        if start < 1:
            raise HTTPException(status_code=400, detail="Start verse must be at least 1.")
        if end < start:
            raise HTTPException(status_code=400, detail="End verse must be greater than or equal to start verse.")

        max_verse = repo.verse_count(normalized_book, chapter)
        if max_verse is None:
            raise HTTPException(status_code=404, detail="Chapter not found.")
        if end > max_verse:
            raise HTTPException(
                status_code=400,
                detail=f"End verse {end} is greater than the number of verses in {normalized_book} {chapter}.",
            )

        verses = list(range(start, end + 1))
        ref = Reference(normalized_book, chapter, verses)
        text = service.get_passage_text(ref)
    except HTTPException as exc:
        if hx_request:
            return _render_passage_partial(request, error=exc.detail, status_code=exc.status_code)
        if "application/json" in accept:
            raise
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=exc.detail,
            status_code=exc.status_code,
        )
    except Exception as exc:
        detail = f"Could not load passage: {exc}"
        if hx_request:
            return _render_passage_partial(request, error=detail, status_code=500)
        if "application/json" in accept:
            raise HTTPException(status_code=500, detail=detail) from exc
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=detail,
            status_code=500,
        )

    passage = _format_passage(ref, text)

    if hx_request:
        return _render_passage_partial(request, passage=passage)

    if "application/json" in accept:
        return JSONResponse(
            {
                "reference": passage["reference"],
                "book": normalized_book,
                "chapter": chapter,
                "verses": verses,
                "text": text,
            }
        )

    return _render_page(
        request,
        mode="reference",
        passage=passage,
        groups=None,
    )


@app.get("/read/{book}/{chapter}/{verses}", response_class=HTMLResponse)
def read_verse(request: Request, book: str, chapter: int, verses: str):
    hx_request = bool(request.headers.get("hx-request"))
    accept = request.headers.get("accept", "")
    normalized_book = book.title()

    try:
        verse_numbers = [int(value) for value in verses.split(",")]
    except ValueError:
        detail = "Verses must be numeric, for example 3:16 or 3:16,17."
        if hx_request:
            return _render_passage_partial(request, error=detail, status_code=400)
        if "application/json" in accept:
            raise HTTPException(status_code=400, detail=detail)
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=detail,
            status_code=400,
        )

    try:
        max_verse = repo.verse_count(normalized_book, chapter)
    except ValueError as exc:
        detail = str(exc)
        if hx_request:
            return _render_passage_partial(request, error=detail, status_code=404)
        if "application/json" in accept:
            raise HTTPException(status_code=404, detail=detail)
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=detail,
            status_code=404,
        )

    if max_verse is None:
        detail = "Chapter not found."
        if hx_request:
            return _render_passage_partial(request, error=detail, status_code=404)
        if "application/json" in accept:
            raise HTTPException(status_code=404, detail=detail)
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=detail,
            status_code=404,
        )

    if max(verse_numbers) > max_verse:
        detail = f"Verse(s) {verses} not found in {normalized_book}."
        if hx_request:
            return _render_passage_partial(request, error=detail, status_code=400)
        if "application/json" in accept:
            raise HTTPException(status_code=400, detail=detail)
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=detail,
            status_code=400,
        )

    reference = Reference(normalized_book, chapter, verse_numbers)

    try:
        text = service.get_passage_text(reference)
    except Exception as exc:
        detail = f"Could not load passage: {exc}"
        if hx_request:
            return _render_passage_partial(request, error=detail, status_code=500)
        if "application/json" in accept:
            raise HTTPException(status_code=500, detail=detail) from exc
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=detail,
            status_code=500,
        )

    passage = _format_passage(reference, text)

    if hx_request:
        return _render_passage_partial(request, passage=passage)

    if "application/json" in accept:
        return JSONResponse(
            {
                "reference": passage["reference"],
                "book": normalized_book,
                "chapter": chapter,
                "verses": verse_numbers,
                "text": text,
            }
        )

    return _render_page(
        request,
        mode="reference",
        passage=passage,
        groups=None,
    )


@app.get("/next")
def next_passage(request: Request, ref: str = Query(..., description="Reference like 'John 3:16'")):
    hx_request = bool(request.headers.get("hx-request"))
    accept = request.headers.get("accept", "")

    try:
        clean = normalize_reference_raw(ref)
        current = Reference.from_string(clean)
        next_ref = service.get_next(current)
        text = service.get_passage_text(next_ref)
    except EndOfBibleError:
        message = "You have reached the end of the Bible."
        if hx_request:
            return _render_passage_partial(request, error=message, status_code=400)
        if "application/json" in accept:
            raise HTTPException(status_code=400, detail=message)
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=message,
            status_code=400,
        )
    except Exception as exc:
        detail = f"Invalid reference: {exc}"
        if hx_request:
            return _render_passage_partial(request, error=detail, status_code=400)
        if "application/json" in accept:
            raise HTTPException(status_code=400, detail=detail) from exc
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=detail,
            status_code=400,
        )

    passage = _format_passage(next_ref, text)

    if hx_request:
        return _render_passage_partial(request, passage=passage)

    if "application/json" in accept:
        return {
            "reference": str(next_ref),
            "book": next_ref.book,
            "chapter": next_ref.chapter,
            "verses": next_ref.verses,
            "text": text,
        }

    return _render_page(
        request,
        mode="reference",
        passage=passage,
        groups=None,
    )


@app.get("/prev")
def prev_passage(request: Request, ref: str = Query(..., description="Reference like 'John 3:16'")):
    hx_request = bool(request.headers.get("hx-request"))
    accept = request.headers.get("accept", "")

    try:
        clean = normalize_reference_raw(ref)
        current = Reference.from_string(clean)
        prev_ref = service.get_prev(current)
        text = service.get_passage_text(prev_ref)
    except StartOfBibleError:
        message = "You are at the beginning of the Bible."
        if hx_request:
            return _render_passage_partial(request, error=message, status_code=400)
        if "application/json" in accept:
            raise HTTPException(status_code=400, detail=message)
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=message,
            status_code=400,
        )
    except Exception as exc:
        detail = f"Invalid reference: {exc}"
        if hx_request:
            return _render_passage_partial(request, error=detail, status_code=400)
        if "application/json" in accept:
            raise HTTPException(status_code=400, detail=detail) from exc
        return _render_page(
            request,
            mode="reference",
            passage=None,
            groups=None,
            passage_error=detail,
            status_code=400,
        )

    passage = _format_passage(prev_ref, text)

    if hx_request:
        return _render_passage_partial(request, passage=passage)

    if "application/json" in accept:
        return {
            "reference": str(prev_ref),
            "book": prev_ref.book,
            "chapter": prev_ref.chapter,
            "verses": prev_ref.verses,
            "text": text,
        }

    return _render_page(
        request,
        mode="reference",
        passage=passage,
        groups=None,
    )


@app.get("/lookup")
def lookup(
    request: Request,
    query: str = Query(..., description="Reference or keyword to search for"),
    page: int = Query(1, ge=1),
    per_page: int = Query(DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE),
):
    trimmed = query.strip()
    if not trimmed:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    per_page = max(1, min(per_page, MAX_PER_PAGE))
    page = max(1, page)

    try:
        normalized = normalize_reference_raw(trimmed)
        reference = Reference.from_string(normalized)
        reference.book = service.suggest_book(reference.book)
        text = service.get_passage_text(reference)
    except Exception:
        raw_results = repo.search(trimmed, max_results=MAX_KEYWORD_RESULTS)
        page_items, total, total_pages, current_page, per_page = _paginate_keyword_results(
            raw_results, page, per_page
        )
        payload: dict[str, Any] = {
            "mode": "keyword",
            "query": trimmed,
            "page": current_page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "results": _group_search_results(page_items),
        }
        if total == MAX_KEYWORD_RESULTS:
            payload["truncated"] = True
        return JSONResponse(payload)

    passage = _format_passage(reference, text)
    return JSONResponse(
        {
            "mode": "reference",
            "query": trimmed,
            "result": passage,
        }
    )


@app.get("/search", response_class=HTMLResponse)
def search_verses(
    request: Request,
    query: str = Query(..., description="Word or phrase to search for"),
    limit: int = Query(200, ge=1, le=500),
    mode: str = Query(DEFAULT_MODE),
):
    hx_request = bool(request.headers.get("hx-request"))
    trimmed = query.strip()
    if len(trimmed) < 2:
        message = "Search term must be at least 2 characters."
        if hx_request:
            return _render_groups_partial(
                request,
                query=trimmed,
                groups=[],
                total_count=0,
                message=message,
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=message)

    raw_results = repo.search(trimmed, max_results=limit)
    groups = _group_search_results(raw_results)
    total_count = sum(group["count"] for group in groups)
    message = None if groups else "No results found."

    if hx_request:
        return _render_groups_partial(
            request,
            query=trimmed,
            groups=groups,
            total_count=total_count,
            message=message,
        )

    normalized_mode = mode if mode in VALID_MODES else DEFAULT_MODE
    return _render_page(
        request,
        mode=normalized_mode,
        query=trimmed,
        passage=None,
        groups=groups,
        total_count=total_count,
        message=message,
    )
