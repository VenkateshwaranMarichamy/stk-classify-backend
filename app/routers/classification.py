"""REST endpoints for classification (macro_economic_sectors, sectors, industries, basic_industries)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.classification import (
    BasicIndustry,
    Industry,
    MacroEconomicSector,
    Sector,
)
from app.schemas.classification import (
    BasicIndustryResponse,
    DropdownDataResponse,
    IndustryResponse,
    MacroEconomicSectorResponse,
    SectorResponse,
)
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ---------- Dropdown data (single call for React UI) ----------


@router.get("/dropdown-data", response_model=DropdownDataResponse)
async def get_dropdown_data(
    db: AsyncSession = Depends(get_db_session),
) -> DropdownDataResponse:
    """Return all four lists in one response for populating the four cascading dropdowns."""
    stmt_mes = select(MacroEconomicSector).order_by(MacroEconomicSector.mes_code)
    stmt_sect = select(Sector).order_by(Sector.sect_code)
    stmt_ind = select(Industry).order_by(Industry.ind_code)
    stmt_basic = select(BasicIndustry).order_by(BasicIndustry.basic_ind_code)

    r_mes = await db.execute(stmt_mes)
    r_sect = await db.execute(stmt_sect)
    r_ind = await db.execute(stmt_ind)
    r_basic = await db.execute(stmt_basic)

    return DropdownDataResponse(
        macro_economic_sectors=r_mes.scalars().all(),
        sectors=r_sect.scalars().all(),
        industries=r_ind.scalars().all(),
        basic_industries=r_basic.scalars().all(),
    )


# ---------- Macro Economic Sectors ----------


@router.get("/macro-economic-sectors", response_model=dict)
async def list_macro_economic_sectors(
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """List all macro economic sectors."""
    stmt = select(MacroEconomicSector).order_by(MacroEconomicSector.mes_code)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return {"data": [MacroEconomicSectorResponse.model_validate(x) for x in items], "count": len(items)}


@router.get("/macro-economic-sectors/{mes_code}", response_model=MacroEconomicSectorResponse)
async def get_macro_economic_sector(
    mes_code: str,
    db: AsyncSession = Depends(get_db_session),
) -> MacroEconomicSector:
    """Get one macro economic sector by code."""
    result = await db.execute(
        select(MacroEconomicSector).where(MacroEconomicSector.mes_code == mes_code)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Macro economic sector not found")
    return row


# ---------- Sectors ----------


@router.get("/sectors", response_model=dict)
async def list_sectors(
    mes_code: Optional[str] = Query(None, description="Filter by macro economic sector"),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """List all sectors, optionally filtered by mes_code."""
    stmt = select(Sector).order_by(Sector.sect_code)
    if mes_code is not None:
        stmt = stmt.where(Sector.mes_code == mes_code)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return {"data": [SectorResponse.model_validate(x) for x in items], "count": len(items)}


@router.get("/sectors/{sect_code}", response_model=SectorResponse)
async def get_sector(
    sect_code: str,
    db: AsyncSession = Depends(get_db_session),
) -> Sector:
    """Get one sector by code."""
    result = await db.execute(select(Sector).where(Sector.sect_code == sect_code))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Sector not found")
    return row


# ---------- Industries ----------


@router.get("/industries", response_model=dict)
async def list_industries(
    sect_code: Optional[str] = Query(None, description="Filter by sector"),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """List all industries, optionally filtered by sect_code."""
    stmt = select(Industry).order_by(Industry.ind_code)
    if sect_code is not None:
        stmt = stmt.where(Industry.sect_code == sect_code)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return {"data": [IndustryResponse.model_validate(x) for x in items], "count": len(items)}


@router.get("/industries/{ind_code}", response_model=IndustryResponse)
async def get_industry(
    ind_code: str,
    db: AsyncSession = Depends(get_db_session),
) -> Industry:
    """Get one industry by code."""
    result = await db.execute(select(Industry).where(Industry.ind_code == ind_code))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Industry not found")
    return row


# ---------- Basic Industries ----------


@router.get("/basic-industries", response_model=dict)
async def list_basic_industries(
    ind_code: Optional[str] = Query(None, description="Filter by industry"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """List basic industries with optional filter and pagination."""
    base = select(BasicIndustry)
    if ind_code is not None:
        base = base.where(BasicIndustry.ind_code == ind_code)
    count_stmt = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = base.order_by(BasicIndustry.basic_ind_code).offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return {
        "data": [BasicIndustryResponse.model_validate(x) for x in items],
        "count": len(items),
        "total": total,
    }


@router.get("/basic-industries/{basic_ind_code}", response_model=BasicIndustryResponse)
async def get_basic_industry(
    basic_ind_code: str,
    db: AsyncSession = Depends(get_db_session),
) -> BasicIndustry:
    """Get one basic industry by code."""
    result = await db.execute(
        select(BasicIndustry).where(BasicIndustry.basic_ind_code == basic_ind_code)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Basic industry not found")
    return row
