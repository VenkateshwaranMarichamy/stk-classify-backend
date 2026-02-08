"""API routers."""

from fastapi import APIRouter

from app.routers import classification

api_router = APIRouter()

api_router.include_router(
    classification.router,
    prefix="/classification",
    tags=["classification"],
)
