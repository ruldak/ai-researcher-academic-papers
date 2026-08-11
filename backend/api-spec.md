# AI Researcher Backend — API Specification

> All endpoints return JSON. All timestamps are ISO 8601 (UTC).

---

## Table of Contents

- [1. Base URL](#1-base-url)
- [2. Authentication](#2-authentication)
- [3. Error Handling](#3-error-handling)
- [4. Common Data Types](#4-common-data-types)
- [5. Auth Endpoints](#5-auth-endpoints)
- [6. Search Endpoints](#6-search-endpoints)
- [7. Paper Endpoints](#7-paper-endpoints)
- [8. Health Endpoint](#8-health-endpoint)
- [9. Typical Frontend Flows](#9-typical-frontend-flows)

---

## 1. Base URL

| Environment | Base URL |
|---|---|
| Local development | `http://127.0.0.1:8000` |
| Production | *(provided by deployment)* |

All endpoint paths below are **relative to this base URL**.

Interactive docs (Swagger UI) during development:

```
http://127.0.0.1:8000/docs
```

---

## 2. Authentication

Most endpoints require a **JWT Bearer token**.

### How to authenticate

1. Call `POST /api/auth/register` or `POST /api/auth/login` to get an `access_token`.
2. Include it in the `Authorization` header of every protected request:

```
Authorization: Bearer <access_token>
```

### Example

```http
GET /api/auth/me HTTP/1.1
Host: 127.0.0.1:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token details

- **Type:** JWT (signed with HS256).
- **Lifetime:** 7 days (configurable).
- **Format in response:** `{ "access_token": "...", "token_type": "bearer" }`.

### Protected vs public endpoints

| Endpoint | Requires Auth |
|---|---|
| `POST /api/auth/register` | ❌ No |
| `POST /api/auth/login` | ❌ No |
| `GET /api/health` | ❌ No |
| **All other endpoints** | ✅ Yes |

If a protected endpoint is called without a valid token, it returns:

```json
{ "detail": "Not authenticated" }
```

with status **`401 Unauthorized`**.

---

## 3. Error Handling

### Error response shape

All errors return a JSON body with a `detail` field:

```json
{ "detail": "Human-readable error message" }
```

For validation errors (status `422`), `detail` is an **array** of error objects:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 6 characters",
      "input": "abc"
    }
  ]
}
```

### Common status codes

| Code | Meaning | When |
|---|---|---|
| `200` | OK | Successful GET / PATCH |
| `201` | Created | Successful registration |
| `401` | Unauthorized | Missing/invalid/expired token |
| `404` | Not Found | Resource doesn't exist or isn't yours |
| `409` | Conflict | Email already registered |
| `422` | Validation Error | Malformed request body |
| `500` | Internal Server Error | Unexpected server issue |
| `502` | Bad Gateway | OpenAlex API failure |

---

## 4. Common Data Types

### User

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "user@example.com",
  "name": "John"
}
```

### Paper Status (enum)

One of:

```
"unread" | "reading" | "reviewed" | "skipped"
```

### Author

```json
{ "name": "Marcus Webb", "institution": "MIT" }
```

### Topic

```json
{
  "name": "Parasites and Host Interactions",
  "score": 0.86,
  "subfield": "Infectious Disease",
  "field": "Medicine"
}
```

### Keyword

```json
{ "name": "long COVID", "score": 0.9 }
```

---

## 5. Auth Endpoints

### 5.1 Register a new user

```
POST /api/auth/register
```

**Auth:** Not required.

**Request body:**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `email` | string (email) | ✅ | Valid email |
| `password` | string | ✅ | Min 6 chars, ≤ 72 bytes |
| `name` | string | ✅ | 1–255 chars |

**Example request:**

```json
{
  "email": "user@example.com",
  "password": "pass123",
  "name": "John"
}
```

**Success response — `201 Created`:**

```json
{
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "user@example.com",
    "name": "John"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error responses:**

| Code | Condition |
|---|---|
| `409` | Email already registered |
| `422` | Validation failed |
| `500` | Server error |

---

### 5.2 Login

```
POST /api/auth/login
```

**Auth:** Not required.

**Request body:**

| Field | Type | Required |
|---|---|---|
| `email` | string (email) | ✅ |
| `password` | string | ✅ |

**Example request:**

```json
{
  "email": "user@example.com",
  "password": "pass123"
}
```

**Success response — `200 OK`:**

```json
{
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "email": "user@example.com",
    "name": "John"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error responses:**

| Code | Condition |
|---|---|
| `401` | Invalid email or password |
| `422` | Validation failed |
| `500` | Server error |

---

### 5.3 Get current user

```
GET /api/auth/me
```

**Auth:** ✅ Required.

**Request body:** None.

**Success response — `200 OK`:**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "user@example.com",
  "name": "John"
}
```

**Error responses:**

| Code | Condition |
|---|---|
| `401` | Missing/invalid token |

---

## 6. Search Endpoints

### 6.1 Search papers (main endpoint)

```
POST /api/search
```

**Auth:** ✅ Required.

This is the core endpoint. It parses the query with AI, searches OpenAlex, generates a summary, and saves everything.

**Request body:**

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `query` | string | ✅ | — | Natural-language query (1–2000 chars) |
| `filters` | object | ❌ | `null` | See below |
| `filters.year_from` | integer | ❌ | `null` | Start publication year |
| `filters.year_to` | integer | ❌ | `null` | End publication year |
| `filters.document_type` | string | ❌ | `null` | `article` / `review` / `preprint` / `book-chapter` |
| `filters.open_access_only` | boolean | ❌ | `false` | Only open-access papers |
| `sort_by` | string | ❌ | `relevance_score:desc` | `relevance_score:desc` or `cited_by_count:desc` |
| `page` | integer | ❌ | `1` | Page number (≥ 1) |
| `per_page` | integer | ❌ | `25` | Results per page (1–100) |

> **Note:** Filters are provided by the **user/frontend**, not generated by the AI. The AI only refines the search keywords from `query`.

**Example request:**

```json
{
  "query": "dampak long COVID pada sistem kardiovaskular",
  "filters": {
    "year_from": 2023,
    "year_to": 2026,
    "document_type": null,
    "open_access_only": false
  },
  "sort_by": "relevance_score:desc",
  "page": 1,
  "per_page": 25
}
```

**Success response — `200 OK`:**

```json
{
  "search_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "query_text": "dampak long COVID pada sistem kardiovaskular",
  "ai_summary": "Ditemukan 70 paper yang membahas dampak kardiovaskular dari long COVID. Sebagian besar fokus pada komplikasi jantung...",
  "total_count": 70,
  "page": 1,
  "per_page": 25,
  "papers": [
    {
      "id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "openalex_id": "https://openalex.org/W4312345678",
      "title": "Cardiovascular Manifestations of Long COVID",
      "authors": ["Marcus Webb", "Jane Smith"],
      "publication_year": 2024,
      "type": "article",
      "cited_by_count": 19,
      "is_oa": true,
      "source_name": "Nature Medicine",
      "topics": [
        { "name": "Parasites and Host Interactions", "score": 0.86 }
      ],
      "status": "unread",
      "abstract": "This study investigates cardiovascular outcomes in long COVID patients..."
    }
  ]
}
```

**Field notes for frontend:**

| Field | Notes |
|---|---|
| `ai_summary` | May be `null` if AI is unavailable. Handle gracefully. |
| `papers[].status` | User's review status. Defaults to `"unread"`. |
| `papers[].abstract` | May be `null` if OpenAlex has no abstract. |
| `papers[].authors` | Array of author **names** (strings) for list display. |
| `total_count` | Total matches on OpenAlex (may exceed `per_page`). |

**Error responses:**

| Code | Condition |
|---|---|
| `401` | Missing/invalid token |
| `422` | Validation failed (e.g., empty query) |
| `502` | OpenAlex API failure |
| `500` | Server error |

---

### 6.2 List search history

```
GET /api/searches
```

**Auth:** ✅ Required.

Returns the current user's past searches, most recent first.

**Request body:** None.

**Success response — `200 OK`:**

```json
{
  "searches": [
    {
      "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "query_text": "dampak long COVID pada sistem kardiovaskular",
      "result_count": 70,
      "ai_summary": "Ditemukan 70 paper yang membahas...",
      "created_at": "2026-01-15T10:30:00"
    },
    {
      "id": "8a2deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "query_text": "machine learning for protein folding",
      "result_count": 120,
      "ai_summary": null,
      "created_at": "2026-01-14T08:12:00"
    }
  ]
}
```

**Field notes:**

- `ai_summary` may be `null`.
- Returns up to the 50 most recent searches.

**Error responses:**

| Code | Condition |
|---|---|
| `401` | Missing/invalid token |
| `500` | Server error |

---

### 6.3 Get search detail

```
GET /api/searches/{search_id}
```

**Auth:** ✅ Required.

Returns the full results of a previously saved search. Same shape as `POST /api/search`.

**Path parameters:**

| Param | Type | Notes |
|---|---|---|
| `search_id` | UUID | ID from a search |

**Success response — `200 OK`:**

Same structure as the `POST /api/search` response (see [6.1](#61-search-papers-main-endpoint)).

**Error responses:**

| Code | Condition |
|---|---|
| `401` | Missing/invalid token |
| `404` | Search not found or belongs to another user |
| `500` | Server error |

---

## 7. Paper Endpoints

### 7.1 Get paper detail

```
GET /api/papers/{paper_id}
```

**Auth:** ✅ Required.

Returns full paper metadata plus the current user's review status and note.

**Path parameters:**

| Param | Type | Notes |
|---|---|---|
| `paper_id` | UUID | Paper ID |

**Success response — `200 OK`:**

```json
{
  "paper": {
    "id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
    "openalex_id": "https://openalex.org/W4312345678",
    "doi": "https://doi.org/10.1038/s41591-024-1234",
    "title": "Cardiovascular Manifestations of Long COVID",
    "abstract": "This study investigates cardiovascular outcomes...",
    "publication_year": 2024,
    "publication_date": "2024-03-15",
    "type": "article",
    "cited_by_count": 19,
    "authors": [
      { "name": "Marcus Webb", "institution": "MIT" },
      { "name": "Jane Smith", "institution": "Harvard" }
    ],
    "topics": [
      {
        "name": "Parasites and Host Interactions",
        "score": 0.86,
        "subfield": "Infectious Disease",
        "field": "Medicine"
      }
    ],
    "keywords": [
      { "name": "long COVID", "score": 0.9 },
      { "name": "cardiovascular", "score": 0.85 }
    ],
    "source_name": "Nature Medicine",
    "is_oa": true,
    "oa_url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123",
    "pdf_url": "https://www.nature.com/articles/123.pdf",
    "landing_page_url": "https://www.nature.com/articles/123",
    "created_at": "2026-01-15T10:30:00"
  },
  "user_status": {
    "status": "reading",
    "note": "Paper ini relevan untuk riset saya tentang long COVID.",
    "updated_at": "2026-01-15T11:00:00"
  }
}
```

**Field notes:**

| Field | Notes |
|---|---|
| `paper.authors` | Full objects with `name` + `institution` (unlike search list which has names only) |
| `user_status.status` | Defaults to `"unread"` if never set |
| `user_status.note` | `null` if no note |
| `user_status.updated_at` | `null` if status was never set |

**Error responses:**

| Code | Condition |
|---|---|
| `401` | Missing/invalid token |
| `404` | Paper not found |
| `500` | Server error |

---

### 7.2 Update paper status

```
PATCH /api/papers/{paper_id}/status
```

**Auth:** ✅ Required.

Updates the current user's review status for a paper. Creates the record if it doesn't exist.

**Path parameters:**

| Param | Type | Notes |
|---|---|---|
| `paper_id` | UUID | Paper ID |

**Request body:**

| Field | Type | Required | Allowed values |
|---|---|---|---|
| `status` | string | ✅ | `unread` / `reading` / `reviewed` / `skipped` |

**Example request:**

```json
{ "status": "reviewed" }
```

**Success response — `200 OK`:**

```json
{
  "status": "reviewed",
  "updated_at": "2026-01-15T12:00:00"
}
```

**Error responses:**

| Code | Condition |
|---|---|
| `401` | Missing/invalid token |
| `404` | Paper not found |
| `422` | Invalid status value |
| `500` | Server error |

---

### 7.3 Update paper note

```
PATCH /api/papers/{paper_id}/note
```

**Auth:** ✅ Required.

Updates the current user's note for a paper. Creates the record if it doesn't exist. Set `note` to `null` to clear it.

**Path parameters:**

| Param | Type | Notes |
|---|---|---|
| `paper_id` | UUID | Paper ID |

**Request body:**

| Field | Type | Required | Constraints |
|---|---|---|---|
| `note` | string \| null | ✅ | Max 10,000 chars. `null` clears the note. |

**Example request (set note):**

```json
{ "note": "Metode menarik, perlu dibandingkan dengan studi 2023." }
```

**Example request (clear note):**

```json
{ "note": null }
```

**Success response — `200 OK`:**

```json
{
  "note": "Metode menarik, perlu dibandingkan dengan studi 2023.",
  "updated_at": "2026-01-15T12:30:00"
}
```

**Error responses:**

| Code | Condition |
|---|---|
| `401` | Missing/invalid token |
| `404` | Paper not found |
| `422` | Note too long |
| `500` | Server error |

---

## 8. Health Endpoint

### 8.1 Health check

```
GET /api/health
```

**Auth:** Not required.

**Success response — `200 OK`:**

```json
{ "status": "ok" }
```

Use this to verify the backend is up (e.g., for load balancer checks or startup probes).

---

## 9. Typical Frontend Flows

### Flow A: User signs up and searches

1. `POST /api/auth/register` → get `access_token`.
2. Store the token.
3. `POST /api/search` with the token + query → show results.
4. Render each paper with its `status` (default `unread`).

### Flow B: User opens a paper and takes notes

1. From search results, take a `paper.id`.
2. `GET /api/papers/{paper_id}` → show full detail + existing status/note.
3. User clicks "Mark as reading" → `PATCH /api/papers/{paper_id}/status` with `{ "status": "reading" }`.
4. User types a note → `PATCH /api/papers/{paper_id}/note` with `{ "note": "..." }`.

### Flow C: User revisits past searches

1. `GET /api/searches` → list of past searches.
2. User clicks one → `GET /api/searches/{search_id}` → show saved results.

### Handling `ai_summary`

- `ai_summary` can be `null` (AI unavailable or no results).
- **Frontend should hide or gracefully handle** the summary section when it's `null`.

### Handling pagination

- `POST /api/search` returns `total_count`, `page`, and `per_page`.
- To load more, re-call `POST /api/search` with the same query/filters and an incremented `page`.

---

## Security Notes for Frontend

- **Never** store passwords. Only the JWT token.
- Send the token in the `Authorization: Bearer <token>` header on every protected request.
- On a `401` response, redirect the user to login (token likely expired).
- The backend enforces password length (max 72 bytes due to bcrypt). Surface `422` validation messages to the user.