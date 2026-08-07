import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# Lazily-initialized async client.
# Groq exposes an OpenAI-compatible API, so we reuse the OpenAI SDK
# and point base_url to Groq's endpoint.
_client: AsyncOpenAI | None = None


def get_llm_client() -> AsyncOpenAI | None:
    """
    Return a cached async LLM client, or None if no API key is configured.

    Returning None allows callers to gracefully fall back when the LLM
    provider is not configured.
    """
    global _client

    if not settings.GROQ_API_KEY:
        return None

    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )

    return _client


def _extract_json(text: str) -> dict | None:
    """
    Attempt to extract a JSON object from LLM response text.

    Handles cases where the model wraps JSON in markdown code fences
    or adds extra explanatory text around it.
    """
    text = text.strip()

    # Try direct parse first.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to locate a JSON object within the text.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


async def parse_search_query(query: str) -> str:
    """
    Parse a user's natural language query into concise English search terms.

    Per project decision, the LLM only produces search terms.
    All filters (year, document type, open access) come from the user request.

    Falls back to the original query if the LLM call fails or is not configured.
    """
    client = get_llm_client()
    if client is None:
        logger.warning("GROQ_API_KEY not set, using original query for search")
        return query

    prompt = f"""You are a search query parser for an academic paper search engine.
Given a user's natural language query, extract concise English search keywords
suitable for an academic search API.

User query: "{query}"

Respond ONLY with valid JSON in this exact shape:
{{
    "search_terms": "concise English keywords for academic search"
}}
"""

    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        content = response.choices[0].message.content or ""
        parsed = _extract_json(content)

        if parsed is None:
            logger.warning("LLM returned non-JSON response, using original query")
            return query

        search_terms = str(parsed.get("search_terms", "")).strip()
        return search_terms if search_terms else query

    except Exception:
        logger.exception("LLM query parsing failed, falling back to original query")
        return query


async def generate_search_summary(
    query: str,
    total_count: int,
    papers: list[dict[str, Any]],
) -> str | None:
    """
    Generate a concise summary of search results.

    Returns None if generation fails or the LLM is not configured,
    so the frontend can handle the absence gracefully.
    """
    client = get_llm_client()
    if client is None:
        logger.warning("GROQ_API_KEY not set, skipping search summary")
        return None

    if not papers:
        return None

    # Build short snippets for the top papers.
    paper_snippets = []
    for index, paper in enumerate(papers[:5], start=1):
        abstract = (paper.get("abstract") or "")[:200]
        authors = ", ".join(
            author.get("name", "")
            for author in (paper.get("authors") or [])[:3]
        )
        paper_snippets.append(
            f"{index}. Title: {paper.get('title')}\n"
            f"   Year: {paper.get('publication_year')}\n"
            f"   Authors: {authors}\n"
            f"   Type: {paper.get('type')}\n"
            f"   Abstract: {abstract}"
        )

    papers_text = "\n\n".join(paper_snippets)

    prompt = f"""You are a research assistant helping a researcher understand search results.

Search query: "{query}"
Total papers found: {total_count}

Top papers:
{papers_text}

Write a concise summary (3-5 sentences) in the same language as the user's query. Cover:
1. Overview of what was found
2. Main themes/topics across the papers
3. Notable findings or highly-cited papers
4. Any gaps or interesting patterns

Do NOT use markdown. Write in plain text.
"""

    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content or ""
        return content.strip() or None
    except Exception:
        logger.exception("LLM search summary generation failed")
        return None


async def generate_paper_summary(
    paper: dict[str, Any],
    language: str = "English",
) -> str | None:
    """
    Generate a short summary for a single paper.

    Returns None if generation fails or the LLM is not configured.
    """
    client = get_llm_client()
    if client is None:
        logger.warning("GROQ_API_KEY not set, skipping paper summary")
        return None

    abstract = paper.get("abstract") or ""
    authors = ", ".join(
        author.get("name", "")
        for author in (paper.get("authors") or [])
    )

    prompt = f"""Summarize this academic paper in 2-3 sentences in {language}:

Title: {paper.get('title')}
Authors: {authors}
Year: {paper.get('publication_year')}
Type: {paper.get('type')}
Abstract: {abstract}

Focus on: objective, method, and key finding.
"""

    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content or ""
        return content.strip() or None
    except Exception:
        logger.exception("LLM paper summary generation failed")
        return None