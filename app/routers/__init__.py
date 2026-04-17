"""API routers."""

from fastapi import APIRouter

from app.routers import classification, fundamentals, profiles, stocks

api_router = APIRouter()

api_router.include_router(
    classification.router,
    prefix="/classification",
    tags=["classification"],
)

api_router.include_router(
    fundamentals.router,
    prefix="/fundamentals",
    tags=["fundamentals"],
)

api_router.include_router(
    profiles.router,
    prefix="/profiles",
    tags=["profiles"],
)

api_router.include_router(
    stocks.router,
    prefix="/stocks",
    tags=["stocks"],
)
