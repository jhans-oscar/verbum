import difflib
import math

from fastapi import FastAPI, HTTPException, Query

from verbum import __version__ as verbum_version
from verbum.core.factory import build_service
from verbum.core.normalizer import normalize_reference_raw
from verbum.domain.reference import Reference

from models import ReferenceResponse, SearchResult, Verse, WordSearchResponse

DATASET_NAME = "KJV.json"
PAGE_SIZE_LIMIT = 100


repo, service = build_service(DATASET_NAME)
app = FastAPI(title="Verbum API", version=verbum_version)


def _parse_reference(query: str) -> Reference | None:
    normalized = normalize_reference_raw(query)
    try:
        ref = Reference.from_string(normalized)
    except ValueError:
        return None
    return ref


def _canonical_book_name(book: str) -> str:
    books = repo.list_books()
    lookup = {name.lower(): name for name in books}
    key = book.strip().lower()
    if key in lookup:
        return lookup[key]

    matches = difflib.get_close_matches(book.strip(), books, n=1, cutoff=0.6)
    if matches:
        return matches[0]

    raise HTTPException(status_code=404, detail=f"Book '{book}' not found")


@app.get(
    "/lookup",
    response_model=ReferenceResponse | WordSearchResponse,
    summary="Look up a passage or run a word search",
)
def lookup(
    q: str = Query(..., description="Word or reference to look up"),
    book: str | None = Query(None, description="Optional book filter"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(0, ge=0, le=PAGE_SIZE_LIMIT, description="Results per page (0 returns all matches)"),
):
    trimmed_query = q.strip()
    if not trimmed_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    reference = _parse_reference(trimmed_query)
    if reference is not None:
        reference.book = service.suggest_book(reference.book)
        try:
            verses = repo.get_passage(reference)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        verse_models = [Verse(number=num, text=text.strip()) for num, text in verses]
        return ReferenceResponse(book=reference.book, chapter=reference.chapter, verses=verse_models)

    search_results = repo.search(trimmed_query)

    if book:
        canonical = _canonical_book_name(book)
        search_results = [r for r in search_results if r["book"].lower() == canonical.lower()]

    total_results = len(search_results)
    if total_results == 0:
        raise HTTPException(status_code=404, detail="No results found")

    if page_size == 0:
        paginated_results = search_results
        total_pages = 1
        response_page = 1
        response_page_size = len(paginated_results)
    else:
        total_pages = math.ceil(total_results / page_size)
        if page > total_pages:
            raise HTTPException(status_code=404, detail="Page out of range")

        start = (page - 1) * page_size
        end = start + page_size
        paginated_results = search_results[start:end]
        if not paginated_results:
            raise HTTPException(status_code=404, detail="Page out of range")

        response_page = page
        response_page_size = page_size

    result_models = [
        SearchResult(book=item["book"], chapter=item["chapter"], verse=item["verse"], text=item["text"])
        for item in paginated_results
    ]

    return WordSearchResponse(
        query=q,
        page=response_page,
        page_size=response_page_size or total_results or 1,
        total_pages=total_pages,
        total_results=total_results,
        results=result_models,
    )
