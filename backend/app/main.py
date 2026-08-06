from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup and shutdown logic will be added here later,
    such as Redis connection initialization.
    """
    # Startup logic can be placed here.
    yield

    # Shutdown logic.
    await engine.dispose()


app = FastAPI(
    title="AI Researcher Backend",
    description="Backend for AI-assisted academic paper search and review.",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend applications.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers.
app.include_router(auth.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}