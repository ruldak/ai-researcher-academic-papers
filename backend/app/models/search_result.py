import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, Text, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.paper import Paper
    from app.models.search import Search


class SearchResult(Base):
    """
    Search result mapping table.

    Links a saved search with papers returned by OpenAlex.
    The rank column is named result_rank in Python to avoid collision
    with reserved SQL keywords while preserving rank as the DB column name.
    """

    __tablename__ = "search_results"

    __table_args__ = (
        UniqueConstraint(
            "search_id",
            "paper_id",
            name="uq_search_results_search_id_paper_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    search_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("searches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    paper_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    result_rank: Mapped[int] = mapped_column(
        "rank",
        Integer,
        nullable=False,
    )

    relevance_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    ai_paper_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    search: Mapped["Search"] = relationship(
        back_populates="results",
    )

    paper: Mapped["Paper"] = relationship(
        back_populates="search_results",
    )