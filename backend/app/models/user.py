import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.search import Search
    from app.models.user_paper_status import UserPaperStatus


class User(Base):
    """
    User account table.

    Stores authentication credentials and basic profile information.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    searches: Mapped[list["Search"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    paper_statuses: Mapped[list["UserPaperStatus"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )