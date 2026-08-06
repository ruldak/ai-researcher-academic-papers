import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.search_result import SearchResult
    from app.models.user_paper_status import UserPaperStatus


class Paper(Base):
    """
    Academic paper table.

    Stores paper metadata retrieved from OpenAlex.
    Papers are upserted using openalex_id as the unique external identifier.
    """

    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    openalex_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    doi: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    abstract: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    publication_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    publication_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    cited_by_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    authors: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    topics: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    keywords: Mapped[list[dict]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    source_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_oa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    oa_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    pdf_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    landing_page_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    raw_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    search_results: Mapped[list["SearchResult"]] = relationship(
        back_populates="paper",
    )

    user_statuses: Mapped[list["UserPaperStatus"]] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
    )