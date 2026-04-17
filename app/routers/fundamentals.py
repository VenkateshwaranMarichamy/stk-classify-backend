"""REST endpoints for fundamentals peer comparison."""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.database import get_db_session
from app.schemas.fundamentals import PeerRow, PeerYearsResponse, PeersResponse, StockFundamentalsResponse
from app.services.fundamentals import (
    DEFAULT_SORT,
    SORTABLE_COLUMNS,
    FundamentalsQueryError,
    fetch_peer_years,
    fetch_peers,
    fetch_stock_fundamentals,
)

logger = get_logger(__name__)

router = APIRouter()


@router.get("/stock/{stock_id}", response_model=StockFundamentalsResponse)
async def get_stock_fundamentals(
    stock_id: int = Path(..., ge=1, description="Stock ID"),
    db: AsyncSession = Depends(get_db_session),
) -> StockFundamentalsResponse:
    """Return all annual fundamentals for a single stock, newest year first."""
    try:
        rows = await fetch_stock_fundamentals(db, stock_id)
    except FundamentalsQueryError:
        raise HTTPException(status_code=500, detail="Failed to fetch stock fundamentals")

    if not rows:
        raise HTTPException(status_code=404, detail="No fundamentals data found for this stock")

    return StockFundamentalsResponse(
        stock_id=stock_id,
        stock_name=rows[0].get("stock_name"),
        count=len(rows),
        rows=[PeerRow(**row) for row in rows],
    )


@router.get("/peer-years", response_model=PeerYearsResponse)
async def get_peer_years(
    basic_ind_code: str = Query(..., description="Basic industry code"),
    db: AsyncSession = Depends(get_db_session),
) -> PeerYearsResponse:
    """Return distinct financial years available for a basic industry peer group."""
    basic_ind_code = basic_ind_code.strip()
    if not basic_ind_code:
        raise HTTPException(status_code=400, detail="basic_ind_code is required")

    try:
        years = await fetch_peer_years(db, basic_ind_code)
    except FundamentalsQueryError:
        raise HTTPException(status_code=500, detail="Failed to fetch peer years")

    if not years:
        raise HTTPException(
            status_code=404,
            detail="No fundamentals data found for the given basic_ind_code",
        )

    return PeerYearsResponse(
        basic_ind_code=basic_ind_code,
        years=years,
        default_year=years[0],
    )


@router.get("/peers", response_model=PeersResponse)
async def get_peers(
    basic_ind_code: str = Query(..., description="Basic industry code"),
    financial_year: int = Query(..., description="Financial year, e.g. 2025"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    sort_by: str = Query(DEFAULT_SORT, description=f"Column to sort by. Allowed: {', '.join(sorted(SORTABLE_COLUMNS))}"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db_session),
) -> PeersResponse:
    """Return paginated peer fundamentals for a basic industry and financial year."""
    basic_ind_code = basic_ind_code.strip()

    if not basic_ind_code:
        raise HTTPException(status_code=400, detail="basic_ind_code is required")

    offset = (page - 1) * page_size

    try:
        rows, total = await fetch_peers(
            db=db,
            basic_ind_code=basic_ind_code,
            financial_year=financial_year,
            offset=offset,
            limit=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    except FundamentalsQueryError:
        raise HTTPException(status_code=500, detail="Failed to fetch peer data")

    if total == 0:
        raise HTTPException(
            status_code=404,
            detail="No data found for the given basic_ind_code and financial_year",
        )

    return PeersResponse(
        basic_ind_code=basic_ind_code,
        financial_year=financial_year,
        page=page,
        page_size=page_size,
        total=total,
        sort_by=sort_by,
        sort_dir=sort_dir.lower(),
        rows=[PeerRow(**row) for row in rows],
    )
