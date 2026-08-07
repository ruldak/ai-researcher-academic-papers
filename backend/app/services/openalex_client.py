import logging
from typing import Any

import httpx

from app.config import settings
from app.utils.abstract import reconstruct_abstract

logger = logging.getLogger(__name__)


class OpenAlexClient:
    """
    Async client for interacting with the OpenAlex API.
    """

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, client: httpx.AsyncClient | None = None):
        self._client = client or httpx.AsyncClient(
            timeout=settings.OPENALEX_TIMEOUT_SECONDS,
            headers={
                "User-Agent": f"AIResearcher/1.0 (mailto:{settings.OPENALEX_MAILTO})"
            },
        )
        self._mailto = settings.OPENALEX_MAILTO
        self._api_key = settings.OPENALEX_API_KEY

    async def search_works(
        self,
        search_query: str,
        filters: dict[str, Any] | None = None,
        sort_by: str = "relevance_score:desc",
        page: int = 1,
        per_page: int = 25,
    ) -> dict[str, Any]:
        """
        Search for academic works in OpenAlex.
        Returns the raw API response as a dictionary.
        """
        params: dict[str, Any] = {
            "sort": sort_by,
            "page": page,
            "per_page": per_page,
            "mailto": self._mailto,
        }

        # Include API key as query parameter when configured.
        if self._api_key:
            params["api_key"] = self._api_key

        if search_query:
            params["search"] = search_query

        if filters:
            filter_parts = []

            year_from = filters.get("year_from")
            year_to = filters.get("year_to")
            if year_from and year_to:
                filter_parts.append(f"publication_year:{year_from}-{year_to}")
            elif year_from:
                filter_parts.append(f"publication_year:{year_from}-")
            elif year_to:
                filter_parts.append(f"publication_year:-{year_to}")

            if filters.get("document_type"):
                filter_parts.append(f"type:{filters['document_type']}")

            if filters.get("open_access_only"):
                filter_parts.append("open_access.is_oa:true")

            if filter_parts:
                params["filter"] = ",".join(filter_parts)

        try:
            response = await self._client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.error("OpenAlex API timeout")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(
                "OpenAlex API HTTP error: %s - %s",
                e.response.status_code,
                e.response.text,
            )
            raise
        except httpx.RequestError as e:
            logger.error("OpenAlex API request error: %s", e)
            raise
        except Exception as e:
            logger.error("Unexpected error calling OpenAlex: %s", e)
            raise

    @staticmethod
    def parse_paper(raw_paper: dict[str, Any]) -> dict[str, Any]:
        """
        Extract and format relevant data from a raw OpenAlex paper object.
        """
        authors = []
        for authorship in raw_paper.get("authorships", []):
            author_name = authorship.get("author", {}).get("display_name")
            institutions = authorship.get("institutions", [])
            institution_name = (
                institutions[0].get("display_name") if institutions else None
            )
            authors.append(
                {"name": author_name, "institution": institution_name}
            )

        topics = []
        for topic in raw_paper.get("topics", []):
            topics.append(
                {
                    "name": topic.get("display_name"),
                    "score": topic.get("score"),
                    "subfield": topic.get("subfield", {}).get("display_name"),
                    "field": topic.get("field", {}).get("display_name"),
                }
            )

        keywords = []
        for kw in raw_paper.get("keywords", []):
            keywords.append(
                {
                    "name": kw.get("display_name") or kw.get("keyword"),
                    "score": kw.get("score"),
                }
            )

        oa_info = raw_paper.get("open_access", {})
        is_oa = oa_info.get("is_oa", False)
        oa_url = oa_info.get("oa_url")

        primary_location = raw_paper.get("primary_location") or {}
        source_name = (primary_location.get("source") or {}).get("display_name")
        landing_page_url = primary_location.get("landing_page_url")

        best_oa_location = raw_paper.get("best_oa_location") or {}
        pdf_url = best_oa_location.get("pdf_url")

        abstract = reconstruct_abstract(raw_paper.get("abstract_inverted_index"))

        return {
            "openalex_id": raw_paper.get("id"),
            "doi": raw_paper.get("doi"),
            "title": raw_paper.get("title") or raw_paper.get("display_name"),
            "abstract": abstract,
            "publication_year": raw_paper.get("publication_year"),
            "publication_date": raw_paper.get("publication_date"),
            "type": raw_paper.get("type"),
            "cited_by_count": raw_paper.get("cited_by_count", 0),
            "authors": authors,
            "topics": topics,
            "keywords": keywords,
            "source_name": source_name,
            "is_oa": is_oa,
            "oa_url": oa_url,
            "pdf_url": pdf_url,
            "landing_page_url": landing_page_url,
            "raw_data": raw_paper,
            "relevance_score": raw_paper.get("relevance_score"),
        }

    async def close(self) -> None:
        """
        Close the underlying HTTP client.
        """
        await self._client.aclose()