from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class StatusUpdateRequest(BaseModel):
    """
    Request schema for updating paper review status.
    """

    status: Literal["unread", "reading", "reviewed", "skipped"]


class StatusUpdateResponse(BaseModel):
    """
    Response schema after status update.
    """

    status: str
    updated_at: datetime


class NoteUpdateRequest(BaseModel):
    """
    Request schema for updating paper note.
    Set note to null to clear it.
    """

    note: str | None = Field(default=None, max_length=10000)


class NoteUpdateResponse(BaseModel):
    """
    Response schema after note update.
    """

    note: str | None
    updated_at: datetime