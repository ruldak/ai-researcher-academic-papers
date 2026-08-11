from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuthorInfo(BaseModel):
    """
    Author information extracted from OpenAlex.
    """

    name: str | None = None
    institution: str | None = None


class TopicInfo(BaseModel):
    """
    Topic information extracted from OpenAlex.
    """

    name: str | None = None
    score: float | None = None
    subfield: str | None = None
    field: str | None = None


class KeywordInfo(BaseModel):
    """
    Keyword information extracted from OpenAlex.
    """

    name: str | None = None
    score: float | None = None


class PaperDetail(BaseModel):
    """
    Full paper detail returned by GET /api/papers/{paper_id}.
    """

    id: UUID
    openalex_id: str
    doi: str | None = None
    title: str
    abstract: str | None = None
    publication_year: int | None = None
    publication_date: date | None = None
    type: str | None = None
    cited_by_count: int = 0
    authors: list[AuthorInfo] = []
    topics: list[TopicInfo] = []
    keywords: list[KeywordInfo] = []
    source_name: str | None = None
    is_oa: bool = False
    oa_url: str | None = None
    pdf_url: str | None = None
    landing_page_url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPaperStatusInfo(BaseModel):
    """
    User-specific status and note for a paper.
    """

    status: str = "unread"
    note: str | None = None
    updated_at: datetime | None = None


class PaperDetailResponse(BaseModel):
    """
    Combined response for paper detail endpoint.
    """

    paper: PaperDetail
    user_status: UserPaperStatusInfo