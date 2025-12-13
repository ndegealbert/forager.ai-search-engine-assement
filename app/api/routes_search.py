# app/api/routes_search.py
from fastapi import APIRouter, Query, Depends
from typing import Optional
from app.models import schemas
from app.services.cache import CacheService
from app.services.search import SearchService
from app.services.rate_limit import RateLimitService
from app.utils.auth import verify_api_key

router = APIRouter()

cache_service = CacheService()
search_service = SearchService()
rate_limit_service = RateLimitService()

async def check_rate_limit(api_key: str = Depends(verify_api_key)):
    if not await rate_limit_service.check_rate_limit(api_key):
        from fastapi import HTTPException
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

@router.get("/search", response_model=schemas.SearchResponse)
async def search(
    q: str = Query(..., max_length=500),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    language: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort: schemas.SortOrder = schemas.SortOrder.RELEVANCE,
    safe_search: bool = False,
    fields: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit)
):
    filters = {
        "page": page,
        "per_page": per_page,
        "language": language,
        "date_from": date_from,
        "date_to": date_to,
        "sort": sort.value,
        "safe_search": safe_search
    }
    cache_key = cache_service.generate_key(q, filters)
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        return cached_result

    search_result = await search_service.search(q, filters)
    total_results = search_result["total"]
    total_pages = (total_results + per_page - 1) // per_page

    response = {
        "query": q,
        "total_results": total_results,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "search_time_ms": search_result["search_time_ms"],
        "results": search_result["results"],
        "pagination": {
            "next": f"/search?q={q}&page={page+1}" if page < total_pages else None,
            "previous": f"/search?q={q}&page={page-1}" if page > 1 else None,
            "first": f"/search?q={q}&page=1",
            "last": f"/search?q={q}&page={total_pages}"
        }
    }
    await cache_service.set(cache_key, response, ttl=3600)
    return response