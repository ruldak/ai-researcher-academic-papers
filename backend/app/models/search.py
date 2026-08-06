import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.search_result import SearchResult
    from app.models.user import User


class Search(Base):
    """
    Search history table.

    Stores each search request made by a user, including the original
    user query, parsed LLM parameters, generated AI summary, and result count.
    """

    __tablename__ = "searches"

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

    query_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    parsed_params: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    ai_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    result_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="searches",
    )

    results: Mapped[list["SearchResult"]] = relationship(
        back_populates="search",
        cascade="all, delete-orphan",
        order_by="SearchResult.result_rank",
    )