"""REST endpoints for stock profiles."""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.database import get_db_session
from app.schemas.profiles import StockProfilePatchRequest, StockProfileResponse
from app.services.profiles import ProfileQueryError, fetch_profile, patch_profile

logger = get_logger(__name__)

router = APIRouter()


@router.get("/{profile_id}", response_model=StockProfileResponse)
async def get_profile(
    profile_id: int = Path(..., ge=1, description="Stock profile ID"),
    db: AsyncSession = Depends(get_db_session),
) -> StockProfileResponse:
    """Return the full profile for a given ID."""
    try:
        row = await fetch_profile(db, profile_id)
    except ProfileQueryError:
        raise HTTPException(status_code=500, detail="Failed to fetch profile")

    if row is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return StockProfileResponse(**row)


@router.patch("/{profile_id}", response_model=StockProfileResponse)
async def update_profile(
    payload: StockProfilePatchRequest,
    profile_id: int = Path(..., ge=1, description="Stock profile ID"),
    db: AsyncSession = Depends(get_db_session),
) -> StockProfileResponse:
    """Partially update a stock profile. Only supplied fields are changed."""
    try:
        row = await patch_profile(
            db=db,
            profile_id=profile_id,
            associated_brands=payload.associated_brands,
            business_group=payload.business_group,
            information=payload.information,
            risk_level=payload.risk_level,
            location=payload.location,
            ownership_type=payload.ownership_type,
            keynotes=payload.keynotes,
            clients=payload.clients,
        )
    except ProfileQueryError:
        raise HTTPException(status_code=500, detail="Failed to update profile")

    if row is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return StockProfileResponse(**row)
