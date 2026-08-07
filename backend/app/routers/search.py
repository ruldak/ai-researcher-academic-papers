from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.search import (
    SearchHistoryResponse,
    SearchRequest,
    SearchResponse,
)
from app.services import search_service
from app.utils.dependencies import get_current_user, get_db


router = APIRouter(
    prefix="/api",
    tags=["Search"],
)


@router.post(
    "/search",
    response_model=SearchResponse,
)
async def search_papers(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Search academic papers using AI-assisted query parsing and OpenAlex.

    This is the main search endpoint. It:
    1. Parses the user query into search terms using LLM
    2. Calls OpenAlex API with user-provided filters
    3. Saves papers and search history to database
    4. Generates AI summary of results
    """
    filters_dict = payload.filters.model_dump() if payload.filters else {}

    return await search_service.search_papers(
        db=db,
        user_id=current_user.id,
        query=payload.query,
        filters=filters_dict,
        sort_by=payload.sort_by,
        page=payload.page,
        per_page=payload.per_page,
    )


@router.get(
    "/searches",
    response_model=SearchHistoryResponse,
)
async def list_searches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List search history for the current user.

    Returns the most recent searches ordered by creation date.
    """
    return await search_service.list_user_searches(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/searches/{search_id}",
    response_model=SearchResponse,
)
async def get_search_detail(
    search_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get detailed results for a specific search.

    Returns the same structure as POST /api/search but loaded
    from the database. Users can only access their own searches.
    """
    return await search_service.get_search_detail(
        db=db,
        user_id=current_user.id,
        search_id=search_id,
    )