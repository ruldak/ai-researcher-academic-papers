import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.cache import redis_client
from app.config import settings
from app.database import engine
from app.routers import auth, search


logger = logging.getLogger(__name__)

# Basic logging configuration for development.
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    """
    # Startup logic can be placed here.
    yield

    # Shutdown logic.
    await engine.dispose()
    await redis_client.close()


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
app.include_router(search.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Global handler for unexpected errors.
    """
    logger.exception(
        "Unhandled error on %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/api/health")
async def health() -> dict[str, str]:
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}