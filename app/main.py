"""FastAPI app: REST API backed by database."""

from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.core.config import settings
from app.core.logger import get_logger
from app.database import init_db
from app.routers import api_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB. Shutdown: nothing for now."""
    logger.info("Starting %s", settings.app_name)
    await init_db()
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
def health() -> dict:
    """Health check."""
    return {"status": "ok", "app": settings.app_name}
