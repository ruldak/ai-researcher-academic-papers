from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.paper import PaperDetailResponse
from app.schemas.status import (
    NoteUpdateRequest,
    NoteUpdateResponse,
    StatusUpdateRequest,
    StatusUpdateResponse,
)
from app.services import paper_service
from app.utils.dependencies import get_current_user, get_db


router = APIRouter(
    prefix="/api/papers",
    tags=["Papers"],
)


@router.get(
    "/{paper_id}",
    response_model=PaperDetailResponse,
)
async def get_paper_detail(
    paper_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get full detail of a paper along with the user's review status and note.
    """
    return await paper_service.get_paper_detail(
        db=db,
        user_id=current_user.id,
        paper_id=paper_id,
    )


@router.patch(
    "/{paper_id}/status",
    response_model=StatusUpdateResponse,
)
async def update_paper_status(
    paper_id: UUID,
    payload: StatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Update the user's review status for a paper.

    Valid status values: unread, reading, reviewed, skipped.
    """
    return await paper_service.update_paper_status(
        db=db,
        user_id=current_user.id,
        paper_id=paper_id,
        new_status=payload.status,
    )


@router.patch(
    "/{paper_id}/note",
    response_model=NoteUpdateResponse,
)
async def update_paper_note(
    paper_id: UUID,
    payload: NoteUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Update the user's note for a paper.

    Set note to null to clear it.
    """
    return await paper_service.update_paper_note(
        db=db,
        user_id=current_user.id,
        paper_id=paper_id,
        note=payload.note,
    )