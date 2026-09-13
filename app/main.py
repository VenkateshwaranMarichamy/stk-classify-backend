"""FastAPI app: REST API backed by database."""

import json
import math
from contextlib import asynccontextmanager
from typing import Any

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logger import get_logger
from app.database import init_db
from app.routers import api_router

logger = get_logger(__name__)


class _SafeEncoder(json.JSONEncoder):
    """JSON encoder that converts inf/nan floats to null."""

    def iterencode(self, o: Any, _one_shot: bool = False):
        return super().iterencode(self._sanitize(o), _one_shot)

    def _sanitize(self, obj: Any) -> Any:
        if isinstance(obj, float) and (math.isinf(obj) or math.isnan(obj)):
            return None
        if isinstance(obj, dict):
            return {k: self._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._sanitize(v) for v in obj]
        return obj


class SafeJSONResponse(JSONResponse):
    """JSONResponse that converts inf/nan floats to null before serializing."""

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            cls=_SafeEncoder,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")


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
    description=(
        "Stock classification and fundamentals API. "
        "Provides hierarchy reference data, stock identity, qualitative profiles, "
        "and annual financial peer comparison. "
        "See `/docs` for full interactive documentation."
    ),
    lifespan=lifespan,
    default_response_class=SafeJSONResponse,
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
