import hashlib
import json
import logging
from datetime import date
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

import httpx

from app.cache import redis_client
from app.config import settings
from app.models.paper import Paper
from app.models.search import Search
from app.models.search_result import SearchResult
from app.models.user_paper_status import UserPaperStatus
from app.services import llm_service
from app.services.openalex_client import OpenAlexClient
from sqlalchemy.orm import joinedload


logger = logging.getLogger(__name__)

DEFAULT_SORT_BY = "relevance_score:desc"
MIN_PAGE = 1
DEFAULT_PER_PAGE = 25
MAX_PER_PAGE = 100


def _as_int(value: Any) -> int | None:
    """
    Safely convert a value to int.
    """
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    """
    Safely convert a value to float.
    """
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_publication_date(value: Any) -> date | None:
    """
    Convert ISO date string from OpenAlex into Python date.
    """
    if not value:
        return None

    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _normalize_pagination(page: Any, per_page: Any) -> tuple[int, int]:
    """
    Ensure pagination values are within safe boundaries.
    """
    normalized_page = _as_int(page) or MIN_PAGE
    normalized_per_page = _as_int(per_page) or DEFAULT_PER_PAGE

    normalized_page = max(MIN_PAGE, normalized_page)
    normalized_per_page = max(1, min(normalized_per_page, MAX_PER_PAGE))

    return normalized_page, normalized_per_page


def _build_search_hash(
    search_terms: str,
    filters: dict[str, Any],
    sort_by: str,
    page: int,
    per_page: int,
) -> str:
    """
    Build a deterministic hash for cache key.

    The cache key is based on parsed search terms and explicit user filters.
    """
    payload = {
        "search_terms": search_terms,
        "filters": filters or {},
        "sort_by": sort_by,
        "page": page,
        "per_page": per_page,
    }

    serialized = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _apply_paper_data(paper: Paper, data: dict[str, Any]) -> Paper:
    """
    Apply parsed OpenAlex data into a Paper ORM object.
    """
    paper.doi = data.get("doi")
    paper.title = data.get("title") or "Untitled"
    paper.abstract = data.get("abstract")
    paper.publication_year = _as_int(data.get("publication_year"))
    paper.publication_date = _parse_publication_date(data.get("publication_date"))
    paper.type = data.get("type")
    paper.cited_by_count = _as_int(data.get("cited_by_count")) or 0
    paper.authors = data.get("authors") or []
    paper.topics = data.get("topics") or []
    paper.keywords = data.get("keywords") or []
    paper.source_name = data.get("source_name")
    paper.is_oa = bool(data.get("is_oa", False))
    paper.oa_url = data.get("oa_url")
    paper.pdf_url = data.get("pdf_url")
    paper.landing_page_url = data.get("landing_page_url")
    paper.raw_data = data.get("raw_data")

    return paper


async def _fetch_openalex(
    search_terms: str,
    filters: dict[str, Any],
    sort_by: str,
    page: int,
    per_page: int,
) -> tuple[int, list[dict[str, Any]], str]:
    """
    Fetch papers from OpenAlex with Redis cache.

    Returns:
        total_count, parsed_papers, search_hash
    """
    search_hash = _build_search_hash(
        search_terms=search_terms,
        filters=filters,
        sort_by=sort_by,
        page=page,
        per_page=per_page,
    )

    openalex_cache_key = f"{settings.CACHE_PREFIX}:openalex:{search_hash}"

    # Try cache first.
    try:
        cached_payload = await redis_client.get(openalex_cache_key)
    except Exception:
        logger.exception("Redis get failed, continuing without cache")
        cached_payload = None

    if cached_payload:
        try:
            parsed_cache = json.loads(cached_payload)
            total_count = _as_int(parsed_cache.get("total_count")) or 0
            cached_papers = parsed_cache.get("papers") or []
            return total_count, cached_papers, search_hash
        except Exception:
            logger.exception("Invalid cached OpenAlex payload, ignoring cache")

    # Call OpenAlex.
    client = OpenAlexClient()

    try:
        raw_response = await client.search_works(
            search_query=search_terms,
            filters=filters,
            sort_by=sort_by,
            page=page,
            per_page=per_page,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("OpenAlex search failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Your query took too long, please narrow the query and try again" if "504 Gateway Timeout" in str(e) else "Failed to fetch papers from OpenAlex",
        )
    finally:
        await client.close()

    meta = raw_response.get("meta") or {}
    total_count = _as_int(meta.get("count")) or 0

    parsed_papers: list[dict[str, Any]] = []

    for item in raw_response.get("results", []):
        try:
            if not item.get("id"):
                continue

            parsed_papers.append(OpenAlexClient.parse_paper(item))
        except Exception:
            logger.exception("Failed to parse one OpenAlex paper, skipping it")

    # Store result in cache.
    try:
        serialized_payload = json.dumps(
            {
                "total_count": total_count,
                "papers": parsed_papers,
            },
            ensure_ascii=False,
            default=str,
        )

        await redis_client.set(
            openalex_cache_key,
            serialized_payload,
            ex=settings.SEARCH_CACHE_TTL_SECONDS,
        )
    except Exception:
        logger.exception("Redis set failed, continuing without caching OpenAlex result")

    return total_count, parsed_papers, search_hash


async def _get_or_generate_summary(
    search_hash: str,
    query: str,
    total_count: int,
    parsed_papers: list[dict[str, Any]],
) -> str | None:
    """
    Get search summary from cache or generate a new one using LLM.
    """
    if not parsed_papers:
        return None

    summary_cache_key = f"{settings.CACHE_PREFIX}:summary:{search_hash}"

    try:
        cached_summary = await redis_client.get(summary_cache_key)
        if cached_summary:
            return cached_summary
    except Exception:
        logger.exception("Redis get failed for summary cache")

    summary = await llm_service.generate_search_summary(
        query=query,
        total_count=total_count,
        papers=parsed_papers,
    )

    if summary:
        try:
            await redis_client.set(
                summary_cache_key,
                summary,
                ex=settings.SEARCH_CACHE_TTL_SECONDS,
            )
        except Exception:
            logger.exception("Redis set failed for summary cache")

    return summary


async def _upsert_papers(
    db: AsyncSession,
    parsed_papers: list[dict[str, Any]],
) -> list[Paper]:
    """
    Insert new papers or update existing papers by openalex_id.

    Returns Paper ORM objects in the same order as parsed_papers.
    """
    if not parsed_papers:
        return []

    openalex_ids = [
        paper_data["openalex_id"]
        for paper_data in parsed_papers
        if paper_data.get("openalex_id")
    ]

    result = await db.execute(
        select(Paper).where(Paper.openalex_id.in_(openalex_ids))
    )
    existing_papers = result.scalars().all()

    existing_by_openalex_id = {
        paper.openalex_id: paper
        for paper in existing_papers
    }

    papers: list[Paper] = []

    for paper_data in parsed_papers:
        openalex_id = paper_data.get("openalex_id")

        if not openalex_id:
            continue

        paper = existing_by_openalex_id.get(openalex_id)

        if paper is None:
            paper = Paper(openalex_id=openalex_id)
            db.add(paper)

        _apply_paper_data(paper, paper_data)
        papers.append(paper)

    await db.flush()

    return papers


async def _get_user_statuses(
    db: AsyncSession,
    user_id: UUID,
    paper_ids: list[UUID],
) -> dict[UUID, str]:
    """
    Fetch existing review statuses for the given user and papers.
    """
    if not paper_ids:
        return {}

    result = await db.execute(
        select(UserPaperStatus).where(
            UserPaperStatus.user_id == user_id,
            UserPaperStatus.paper_id.in_(paper_ids),
        )
    )

    records = result.scalars().all()

    return {
        record.paper_id: record.status.value
        for record in records
    }


async def _save_search_and_results(
    db: AsyncSession,
    user_id: UUID,
    query_text: str,
    parsed_params: dict[str, Any],
    ai_summary: str | None,
    total_count: int,
    papers: list[Paper],
    parsed_papers: list[dict[str, Any]],
) -> Search:
    """
    Save search history and search result mapping.
    """
    search = Search(
        user_id=user_id,
        query_text=query_text,
        parsed_params=parsed_params,
        ai_summary=ai_summary,
        result_count=total_count,
    )

    db.add(search)
    await db.flush()

    search_results: list[SearchResult] = []

    for rank, (paper, parsed_paper) in enumerate(
        zip(papers, parsed_papers),
        start=1,
    ):
        search_results.append(
            SearchResult(
                search_id=search.id,
                paper_id=paper.id,
                result_rank=rank,
                relevance_score=_as_float(parsed_paper.get("relevance_score")),
                ai_paper_summary=None,
            )
        )

    db.add_all(search_results)
    await db.flush()

    return search


async def search_papers(
    db: AsyncSession,
    user_id: UUID,
    query: str,
    filters: dict[str, Any] | None = None,
    sort_by: str = DEFAULT_SORT_BY,
    page: int = MIN_PAGE,
    per_page: int = DEFAULT_PER_PAGE,
) -> dict[str, Any]:
    """
    Main orchestration for paper search.

    Flow:
    1. Parse user query into search terms using LLM.
    2. Fetch OpenAlex results with cache.
    3. Generate or fetch cached AI summary.
    4. Upsert papers.
    5. Save search and search results.
    6. Attach user-specific paper statuses.
    """
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query is required",
        )

    normalized_query = query.strip()
    normalized_filters = filters or {}

    page, per_page = _normalize_pagination(page, per_page)

    # LLM only extracts search terms. Filters remain under user control.
    search_terms = await llm_service.parse_search_query(normalized_query)

    total_count, parsed_papers, search_hash = await _fetch_openalex(
        search_terms=search_terms,
        filters=normalized_filters,
        sort_by=sort_by,
        page=page,
        per_page=per_page,
    )

    ai_summary = await _get_or_generate_summary(
        search_hash=search_hash,
        query=normalized_query,
        total_count=total_count,
        parsed_papers=parsed_papers,
    )

    parsed_params = {
        "search_terms": search_terms,
        "filters": normalized_filters,
        "sort_by": sort_by,
        "page": page,
        "per_page": per_page,
        "provider": "groq",
        "model": settings.GROQ_MODEL,
    }

    try:
        papers = await _upsert_papers(db, parsed_papers)

        search = await _save_search_and_results(
            db=db,
            user_id=user_id,
            query_text=normalized_query,
            parsed_params=parsed_params,
            ai_summary=ai_summary,
            total_count=total_count,
            papers=papers,
            parsed_papers=parsed_papers,
        )

        paper_ids = [paper.id for paper in papers]
        user_statuses = await _get_user_statuses(
            db=db,
            user_id=user_id,
            paper_ids=paper_ids,
        )

        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error during search orchestration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    paper_items: list[dict[str, Any]] = []

    for paper in papers:
        author_names = [
            author.get("name")
            for author in (paper.authors or [])
            if author.get("name")
        ]

        simplified_topics = [
            {
                "name": topic.get("name"),
                "score": topic.get("score"),
            }
            for topic in (paper.topics or [])
            if topic.get("name")
        ]

        paper_items.append(
            {
                "id": paper.id,
                "openalex_id": paper.openalex_id,
                "title": paper.title,
                "authors": author_names,
                "publication_year": paper.publication_year,
                "type": paper.type,
                "cited_by_count": paper.cited_by_count,
                "is_oa": paper.is_oa,
                "source_name": paper.source_name,
                "topics": simplified_topics,
                "status": user_statuses.get(paper.id, "unread"),
                "abstract": paper.abstract,
            }
        )

    return {
        "search_id": search.id,
        "query_text": normalized_query,
        "ai_summary": ai_summary,
        "total_count": total_count,
        "page": page,
        "per_page": per_page,
        "papers": paper_items,
    }

async def list_user_searches(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 50,
) -> dict[str, Any]:
    """
    List search history for a specific user, ordered by most recent.
    """
    try:
        result = await db.execute(
            select(Search)
            .where(Search.user_id == user_id)
            .order_by(Search.created_at.desc())
            .limit(limit)
        )
        searches = result.scalars().all()
    except SQLAlchemyError:
        logger.exception("Database error while listing user searches")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    return {
        "searches": [
            {
                "id": s.id,
                "query_text": s.query_text,
                "result_count": s.result_count,
                "ai_summary": s.ai_summary,
                "created_at": s.created_at,
            }
            for s in searches
        ]
    }


async def get_search_detail(
    db: AsyncSession,
    user_id: UUID,
    search_id: UUID,
) -> dict[str, Any]:
    """
    Get detailed search results for a specific search.

    Returns the same structure as POST /api/search response,
    but loaded from the database instead of calling OpenAlex.
    """
    # Verify search exists and belongs to this user.
    try:
        result = await db.execute(
            select(Search).where(
                Search.id == search_id,
                Search.user_id == user_id,
            )
        )
        search = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while fetching search")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    if search is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found",
        )

    # Get search results joined with papers, ordered by rank.
    try:
        results = await db.execute(
            select(SearchResult, Paper)
            .join(Paper, SearchResult.paper_id == Paper.id)
            .where(SearchResult.search_id == search_id)
            .order_by(SearchResult.result_rank)
        )
        rows = results.all()
    except SQLAlchemyError:
        logger.exception("Database error while fetching search results")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    # Get user statuses for these papers.
    paper_ids = [paper.id for _, paper in rows]
    user_statuses = await _get_user_statuses(
        db=db,
        user_id=user_id,
        paper_ids=paper_ids,
    )

    # Build paper items.
    paper_items: list[dict[str, Any]] = []

    for search_result, paper in rows:
        author_names = [
            author.get("name")
            for author in (paper.authors or [])
            if author.get("name")
        ]

        simplified_topics = [
            {
                "name": topic.get("name"),
                "score": topic.get("score"),
            }
            for topic in (paper.topics or [])
            if topic.get("name")
        ]

        paper_items.append(
            {
                "id": paper.id,
                "openalex_id": paper.openalex_id,
                "title": paper.title,
                "authors": author_names,
                "publication_year": paper.publication_year,
                "type": paper.type,
                "cited_by_count": paper.cited_by_count,
                "is_oa": paper.is_oa,
                "source_name": paper.source_name,
                "topics": simplified_topics,
                "status": user_statuses.get(paper.id, "unread"),
                "abstract": paper.abstract,
            }
        )

    # Extract pagination info from parsed_params if available.
    parsed_params = search.parsed_params or {}
    page = parsed_params.get("page", 1)
    per_page = parsed_params.get("per_page", len(paper_items))

    return {
        "search_id": search.id,
        "query_text": search.query_text,
        "ai_summary": search.ai_summary,
        "total_count": search.result_count,
        "page": page,
        "per_page": per_page,
        "papers": paper_items,
    }