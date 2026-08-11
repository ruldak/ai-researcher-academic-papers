import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paper import Paper
from app.models.user_paper_status import PaperStatus, UserPaperStatus


logger = logging.getLogger(__name__)


async def get_paper_detail(
    db: AsyncSession,
    user_id: UUID,
    paper_id: UUID,
) -> dict:
    """
    Get full paper detail along with the user's review status and note.
    """
    # Fetch paper.
    try:
        result = await db.execute(
            select(Paper).where(Paper.id == paper_id)
        )
        paper = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while fetching paper")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    # Fetch user-specific status for this paper.
    try:
        result = await db.execute(
            select(UserPaperStatus).where(
                UserPaperStatus.user_id == user_id,
                UserPaperStatus.paper_id == paper_id,
            )
        )
        user_status = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while fetching user paper status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    status_info = {
        "status": user_status.status.value if user_status else "unread",
        "note": user_status.note if user_status else None,
        "updated_at": user_status.updated_at if user_status else None,
    }

    return {
        "paper": paper,
        "user_status": status_info,
    }


async def update_paper_status(
    db: AsyncSession,
    user_id: UUID,
    paper_id: UUID,
    new_status: str,
) -> dict:
    """
    Update or create the user's review status for a paper.

    Uses upsert logic: if a record exists, update it;
    otherwise, create a new one.
    """
    # Verify paper exists.
    try:
        result = await db.execute(
            select(Paper).where(Paper.id == paper_id)
        )
        paper = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while verifying paper")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    # Upsert user_paper_status.
    try:
        result = await db.execute(
            select(UserPaperStatus).where(
                UserPaperStatus.user_id == user_id,
                UserPaperStatus.paper_id == paper_id,
            )
        )
        record = result.scalar_one_or_none()

        if record is not None:
            record.status = PaperStatus(new_status)
        else:
            record = UserPaperStatus(
                user_id=user_id,
                paper_id=paper_id,
                status=PaperStatus(new_status),
            )
            db.add(record)

        await db.commit()
        await db.refresh(record)
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while updating paper status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    return {
        "status": record.status.value,
        "updated_at": record.updated_at,
    }


async def update_paper_note(
    db: AsyncSession,
    user_id: UUID,
    paper_id: UUID,
    note: str | None,
) -> dict:
    """
    Update or create the user's note for a paper.

    Uses upsert logic: if a record exists, update the note;
    otherwise, create a new one with default status 'unread'.
    Setting note to null clears it.
    """
    # Verify paper exists.
    try:
        result = await db.execute(
            select(Paper).where(Paper.id == paper_id)
        )
        paper = result.scalar_one_or_none()
    except SQLAlchemyError:
        logger.exception("Database error while verifying paper")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found",
        )

    # Upsert user_paper_status.
    try:
        result = await db.execute(
            select(UserPaperStatus).where(
                UserPaperStatus.user_id == user_id,
                UserPaperStatus.paper_id == paper_id,
            )
        )
        record = result.scalar_one_or_none()

        if record is not None:
            record.note = note
        else:
            record = UserPaperStatus(
                user_id=user_id,
                paper_id=paper_id,
                status=PaperStatus.UNREAD,
                note=note,
            )
            db.add(record)

        await db.commit()
        await db.refresh(record)
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Database error while updating paper note")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    return {
        "note": record.note,
        "updated_at": record.updated_at,
    }