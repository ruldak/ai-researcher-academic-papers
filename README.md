# AI Researcher

> A full-stack application that helps researchers **find**, **understand**, and **organize** academic papers using AI.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF.svg)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791.svg)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Table of Contents

- [For Non-Technical Readers](#-for-non-technical-readers)
- [How It Works — The Full Picture](#-how-it-works--the-full-picture)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Backend Details](#-backend-details)
  - [Database Design](#-database-design)
  - [Configuration](#️-configuration)
  - [Key Design Decisions](#-key-design-decisions)
  - [API Documentation](#-api-documentation)

---

## For Non-Technical Readers

### What is this?

Imagine you're a researcher. You want to find academic papers about a topic, but:

- Searching through **millions of papers** is overwhelming.
- Writing the "right" search query in a database is hard.
- Reading every paper's abstract to decide if it's relevant takes forever.
- Keeping track of which papers you've already read is a mess.

**This application is a tool that solves all of that.**

Think of it as a **smart research assistant** that:

1. **Understands** what you're looking for — even if you describe it in your own words.
2. **Searches** through a massive database of academic papers for you.
3. **Summarizes** what it found, so you get the big picture instantly.
4. **Helps you keep track** of papers you've read, are reading, or want to skip.

### A Real Example

Let's say a researcher types this into the app:

> *"dampak long COVID pada sistem kardiovaskular"*
> (the impact of long COVID on the cardiovascular system)

Here's what the application does **behind the scenes**:

1. **Translates & refines the query.** It uses AI to turn that natural sentence into sharp English search keywords like `"long COVID cardiovascular impact"`.

2. **Searches a huge academic database.** It queries [OpenAlex](https://openalex.org) — a free, open catalog of over 250 million academic papers.

3. **Reads and cleans the results.** For each paper found, it extracts the title, authors, abstract, year, and more — and reconstructs the full abstract from a compressed format.

4. **Writes a summary.** It asks an AI to read the top results and write a short paragraph like:
   > *"Found 70 papers. Most focus on cardiac complications in long COVID patients. Several highly-cited studies highlight myocarditis as a key risk. There's a gap in long-term pediatric outcomes."*

5. **Saves everything.** It stores the papers and your search so you can come back to them later.

6. **Returns a clean result.** The app shows you a list of papers, each with a status label like `unread`, so you can mark them as you go.

**You didn't have to write a technical search query. You didn't have to read 70 abstracts. You got a summary and an organized list.** That's what this application makes possible.

---

## How It Works — The Full Picture

This section explains the entire flow in detail, so you can understand the system **without running it**.

### The Main Flow: Searching for Papers

When a user submits a search, the backend runs a **pipeline** with several stages. Let's walk through each one.

```
User's natural-language query
        │
        ▼
┌─────────────────────────┐
│ 1. Parse query with AI  │  → Turn plain language into search keywords
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 2. Check Redis cache    │  → Have we seen this exact search recently?
└───────────┬─────────────┘
            ▼ (cache miss)
┌─────────────────────────┐
│ 3. Call OpenAlex API    │  → Search 250M+ academic papers
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 4. Clean & normalize    │  → Reconstruct abstracts, extract metadata
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 5. Cache results        │  → Save to Redis so next time is instant
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 6. Generate AI summary  │  → Summarize top results in user's language
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 7. Save to database     │  → Upsert papers, save search + results
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 8. Attach user statuses │  → Mark each paper as unread/reading/etc.
└───────────┬─────────────┘
            ▼
      Return response
```

#### Stage 1: Parse the query with AI

The user might type anything — in any language, in plain words. The backend sends this to a **Large Language Model (LLM)** to extract clean English search keywords.

- **Input:** `"dampak long COVID pada sistem kardiovaskular"`
- **Output:** `"long COVID cardiovascular impact"`

> **Design decision:** The AI *only* extracts search keywords. It does **not** decide filters like year range or document type. Those filters always come from the user's explicit choices. This keeps the user in control.

> **Graceful fallback:** If the AI is unavailable or fails, the backend just uses the user's original query as-is. The search still works.

#### Stage 2: Check the cache

Before making an expensive external API call, the backend checks **Redis** (an in-memory cache). It builds a fingerprint (hash) of the search terms + filters + pagination. If that exact combination was searched recently, it returns the cached result instantly.

> This saves API quota, reduces latency, and lowers cost.

#### Stage 3: Call OpenAlex

If there's no cache hit, the backend calls the [OpenAlex API](https://openalex.org). OpenAlex is a free, open catalog of scholarly works. The request looks like:

```
GET https://api.openalex.org/works
  ?search=long+COVID+cardiovascular+impact
  &filter=publication_year:2023-2026
  &sort=relevance_score:desc
  &per_page=25
  &mailto=you@example.com
```

OpenAlex returns a list of matching papers with rich metadata.

#### Stage 4: Clean and normalize the data

OpenAlex returns data in a raw format that needs processing:

- **Abstracts are compressed.** OpenAlex stores abstracts as an "inverted index" (a map of word → positions) to save bandwidth. The backend **reconstructs** the readable abstract from this.
- **Metadata is extracted.** Authors, topics, keywords, journal name, open-access links, and DOI are pulled out and normalized into a clean structure.

#### Stage 5: Cache the results

The cleaned results are stored in Redis with a time-to-live (default 5 minutes). The next identical search will be served from cache.

#### Stage 6: Generate an AI summary

The backend takes the **top papers** and asks the LLM to write a short summary **in the same language as the user's query**. This summary covers:

1. What was found overall.
2. The main themes across the papers.
3. Notable or highly-cited findings.
4. Gaps or interesting patterns.

> **Graceful fallback:** If summarization fails, the response simply omits the summary. The papers are still returned.

#### Stage 7: Save to the database

The backend performs an **upsert** on papers:

- If a paper (identified by its `openalex_id`) already exists in the database, it **updates** it.
- If it's new, it **inserts** it.

It then saves:
- A record in the `searches` table (who searched, what they typed, the AI summary, how many results).
- Records in the `search_results` table linking this search to each paper, with rank and relevance score.

#### Stage 8: Attach user-specific statuses

Each user tracks their own review progress. The backend looks up whether the current user has marked each paper as `unread`, `reading`, `reviewed`, or `skipped`, and attaches that status to the response. Papers with no record default to `unread`.

> **Important:** This status is **per user**. Two users can have completely different statuses for the same paper. This is why statuses are *not* cached — they're always fetched fresh from the database.

### The Review Flow: Tracking Papers

After searching, a user can manage individual papers via the frontend UI:

- **View detail:** Fetch a paper's full information plus the user's status and note.
- **Update status:** Mark a paper as `reading`, `reviewed`, `skipped`, etc.
- **Add a note:** Write personal notes about the paper.

These actions update the `user_paper_status` table, which stores one row per (user, paper) pair.

---

## Architecture

### System Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                      CLIENT (Frontend)                       │
│                   React 19 + Vite + Tailwind                 │
└──────────────────────────┬───────────────────────────────────┘
                           │  HTTP (REST API + JWT Auth)
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                   FASTAPI APPLICATION                        │
│                                                              │
│   Routers          Services                External Calls    │
│  ┌──────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │ Auth     │───▶│ Auth Service     │    │ LLM (Groq)    │  │
│  │ Search   │───▶│ Search Service   │───▶│ OpenAlex API  │  │
│  │ Papers   │───▶│ Paper Service    │    └───────────────┘  │
│  └──────────┘    │ LLM Service      │                       │
│                  │ OpenAlex Client  │                       │
│                  └────────┬─────────┘                       │
│                           │                                  │
│        ┌──────────────────┼──────────────────┐              │
│        ▼                  ▼                  ▼              │
│  ┌──────────┐      ┌──────────┐       ┌──────────┐         │
│  │PostgreSQL│      │  Redis   │       │  Cache   │         │
│  │(primary) │      │ (cache)  │       │  layer   │         │
│  └──────────┘      └──────────┘       └──────────┘         │
└──────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend Stack

| Layer | Technology | Why |
|---|---|---|
| Framework | **React 19** | Modern UI library |
| Bundler | **Vite 6** | Extremely fast development server and bundler |
| Styling | **Tailwind CSS 4** | Utility-first CSS framework |
| Components | **Shadcn UI** | Accessible and customizable component system |
| State/Data | **React Query** | Powerful asynchronous state management |
| Routing | **React Router 7** | Client-side routing |

### Backend Stack

| Layer | Technology | Why |
|---|---|---|
| Framework | **FastAPI** | Async, fast, auto-generates API docs |
| Language | **Python 3.11+** | Modern, great async support |
| Database | **PostgreSQL** | Reliable, supports JSONB for flexible metadata |
| ORM | **SQLAlchemy 2.0** (async) | Mature, powerful, async-ready |
| Migrations | **Alembic** | Standard for SQLAlchemy schema migrations |
| Auth | **JWT** (`python-jose`) | Stateless token authentication |
| Password hashing | **bcrypt** | Industry-standard secure hashing |
| LLM Provider | **Groq** (OpenAI-compatible) | Fast inference, hosts open models |
| HTTP Client | **httpx** (async) | Modern async HTTP for external API calls |
| Validation | **Pydantic v2** | Fast, type-safe request/response validation |
| Cache | **Redis** | Low-latency caching |
| Server | **uvicorn** | ASGI server for FastAPI |

---

## Project Structure

This is a monorepo consisting of both the backend and frontend components.

```
ai-researcher/
├── backend/                    # FastAPI application
│   ├── alembic/                # Database migrations
│   ├── app/                    # Main backend application code
│   ├── venv/                   # Python virtual environment (if created)
│   ├── .env.example            # Backend environment template
│   ├── api-spec.md             # Detailed API specifications
│   └── requirements.txt        # Python dependencies
├── frontend/                   # React frontend application
│   ├── node_modules/           # Node.js dependencies (if installed)
│   ├── src/                    # Frontend source code
│   ├── .env.example            # Frontend environment template
│   ├── components.json         # Shadcn configuration
│   ├── package.json            # Node dependencies
│   └── vite.config.js          # Vite configuration
└── README.md                   # This file
```

---

## Getting Started

### Prerequisites

Make sure you have these installed:

- **Node.js 20+** (for frontend)
- **Python 3.11+** (for backend)
- **PostgreSQL 14+** (running locally or accessible)
- **Redis** (running locally or accessible)
- **Git**

### Step 1: Clone the repository

```bash
git clone <your-repo-url>
cd ai-researcher
```

### Step 2: Backend Setup

Open a terminal and navigate to the backend directory:

```bash
cd backend
```

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux / macOS:
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```

4. **Create the database & run migrations:**
   ```bash
   createdb ai_researcher
   alembic upgrade head
   ```

5. **Start the backend server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will run at `http://127.0.0.1:8000`.

### Step 3: Frontend Setup

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables (if required):**
   Copy `.env.example` to `.env`. Ensure your backend API URL is configured (usually defaults to `http://127.0.0.1:8000`).
   ```bash
   cp .env.example .env
   ```

3. **Start the frontend development server:**
   ```bash
   npm run dev
   ```
   The web application will run at `http://localhost:5173`.

---

## Backend Details

### Database Design

The database has **5 tables**:

#### `users`
Stores account credentials and profile info.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `email` | VARCHAR(255) | Unique, used for login |
| `password_hash` | VARCHAR(255) | Bcrypt hash, never plain text |
| `name` | VARCHAR(255) | Display name |
| `created_at` | TIMESTAMP | Auto-set |

#### `searches`
Stores each search a user performs.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK → `users.id` |
| `query_text` | TEXT | Original user query |
| `parsed_params` | JSONB | What the AI extracted |
| `ai_summary` | TEXT | AI-generated summary |
| `result_count` | INTEGER | Total papers found |
| `created_at` | TIMESTAMP | Auto-set |

#### `papers`
Stores paper metadata. One row per unique paper (deduplicated by `openalex_id`).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `openalex_id` | VARCHAR(255) | Unique external ID |
| `doi`, `title`, `abstract` | TEXT | Core metadata |
| `publication_year`, `publication_date`, `type` | various | Publication info |
| `cited_by_count` | INTEGER | Citation count |
| `authors`, `topics`, `keywords` | JSONB | Structured arrays |
| `is_oa`, `oa_url`, `pdf_url`, `landing_page_url` | various | Open-access info |
| `raw_data` | JSONB | Full original OpenAlex response |
| `created_at` | TIMESTAMP | Auto-set |

#### `search_results`
Links a search to the papers it returned (many-to-many).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `search_id` | UUID | FK → `searches.id` |
| `paper_id` | UUID | FK → `papers.id` |
| `rank` | INTEGER | Position in results |
| `relevance_score` | FLOAT | From OpenAlex |
| Unique constraint | | `(search_id, paper_id)` |

#### `user_paper_status`
Tracks each user's review progress per paper.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK → `users.id` |
| `paper_id` | UUID | FK → `papers.id` |
| `status` | VARCHAR(20) | `unread` / `reading` / `reviewed` / `skipped` |
| `note` | TEXT | Personal note |
| `updated_at` | TIMESTAMP | Auto-updated |
| Unique constraint | | `(user_id, paper_id)` |

### Configuration

All backend configuration is loaded from environment variables (or the `backend/.env` file).

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | PostgreSQL async connection string |
| `REDIS_URL` | ✅ | `redis://localhost:6379/0` | Redis connection string |
| `SEARCH_CACHE_TTL_SECONDS` | ❌ | `300` | Cache lifetime for search results |
| `CACHE_PREFIX` | ❌ | `ai_researcher` | Prefix for Redis keys |
| `GROQ_API_KEY` | ❌ | — | LLM provider key. If empty, AI features are disabled gracefully |
| `GROQ_BASE_URL` | ❌ | `https://api.groq.com/openai/v1` | LLM API base URL |
| `GROQ_MODEL` | ❌ | `openai/gpt-oss-120b` | LLM model to use |
| `LLM_TIMEOUT_SECONDS` | ❌ | `30` | Timeout for LLM calls |
| `OPENALEX_API_KEY` | ❌ | — | OpenAlex API key (sent as query param) |
| `OPENALEX_MAILTO` | ✅ | — | Email for OpenAlex polite pool |
| `OPENALEX_TIMEOUT_SECONDS` | ❌ | `30` | Timeout for OpenAlex calls |
| `JWT_SECRET_KEY` | ✅ | — | Secret for signing JWTs. **Use a long random string** |
| `JWT_ALGORITHM` | ❌ | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_DAYS` | ❌ | `7` | Token lifetime in days |
| `CORS_ORIGINS` | ❌ | `http://localhost:5173,http://localhost:3000` | Allowed frontend origins |
| `ENVIRONMENT` | ❌ | `development` | Environment name |

### Key Design Decisions

#### 1. Graceful degradation when AI is unavailable

The AI (LLM) is an **enhancement**, not a hard dependency. If the LLM key is missing or a call fails:

- **Query parsing** falls back to using the user's original query.
- **Summarization** is skipped, and the response omits `ai_summary`.

The search **always returns papers**. The app never breaks because of AI.

#### 2. Caching strategy

- **What's cached:** OpenAlex results and AI summaries, keyed by a hash of (search terms + filters + pagination).
- **What's NOT cached:** User-specific review statuses. These are always fetched fresh from the database so each user sees their own correct state.
- **TTL:** Configurable via `SEARCH_CACHE_TTL_SECONDS` (default 5 minutes).
- **Resilience:** If Redis is down, the app logs the error and continues without caching.

#### 3. Paper upsert by `openalex_id`

Papers are deduplicated globally. The same paper found in multiple searches is stored **once** and updated if its metadata changes. This keeps the database lean.

#### 4. Per-user review state

Status (`unread`/`reading`/`reviewed`/`skipped`) and notes are stored per **(user, paper)** pair. This means:

- Every user has an independent reading list.
- The same paper can be `reviewed` by one user and `unread` by another.

#### 5. LLM only extracts search terms

The AI parses the query into search keywords **only**. All filters (year range, document type, open-access) come from the user's explicit input. This keeps filtering predictable and user-controlled.

#### 6. OpenAlex API key as query parameter

The OpenAlex API key (if configured) is sent as a query parameter `api_key`, alongside `mailto` for the polite pool.

### API Documentation

For the **complete API reference** intended for the frontend team, see:

👉 **[api-spec.md](./backend/api-spec.md)**

It includes every endpoint with request/response schemas, examples, error codes, and authentication details.

#### Quick endpoint summary

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | ❌ | Register a new user |
| `POST` | `/api/auth/login` | ❌ | Login, get JWT |
| `GET` | `/api/auth/me` | ✅ | Get current user |
| `POST` | `/api/search` | ✅ | Search papers (main endpoint) |
| `GET` | `/api/searches` | ✅ | List search history |
| `GET` | `/api/searches/{search_id}` | ✅ | Get search detail |
| `GET` | `/api/papers/{paper_id}` | ✅ | Get paper detail + user status |
| `PATCH` | `/api/papers/{paper_id}/status` | ✅ | Update review status |
| `PATCH` | `/api/papers/{paper_id}/note` | ✅ | Update note |
| `GET` | `/api/health` | ❌ | Health check |

---

## Health Check

```
GET /api/health
```

Returns:

```json
{ "status": "ok" }
```

Use this to verify the backend service is running.

---

*Built with React, FastAPI, PostgreSQL, Redis, OpenAlex, and Groq.*
