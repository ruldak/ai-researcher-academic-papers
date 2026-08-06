import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint, DateTime, Enum as SQLEnum, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.paper import Paper
    from app.models.user import User


class PaperStatus(str, Enum):
    """
    Review status options for a paper from the perspective of a user.
    """

    UNREAD = "unread"
    READING = "reading"
    REVIEWED = "reviewed"
    SKIPPED = "skipped"


class UserPaperStatus(Base):
    """
    User-specific status and note for a paper.

    Each user can have only one status record per paper.
    """

    __tablename__ = "user_paper_status"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "paper_id",
            name="uq_user_paper_status_user_id_paper_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    paper_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[PaperStatus] = mapped_column(
        SQLEnum(
            PaperStatus,
            name="paper_status",
            native_enum=False,
            length=20,
            values_callable=lambda obj: [item.value for item in obj],
        ),
        nullable=False,
        default=PaperStatus.UNREAD,
        server_default=text("'unread'"),
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="paper_statuses",
    )

    paper: Mapped["Paper"] = relationship(
        back_populates="user_statuses",
    )