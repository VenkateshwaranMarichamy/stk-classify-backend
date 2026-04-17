"""REST endpoints for stock detail."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.database import get_db_session
from app.schemas.stocks import StockDetailResponse, StockListResponse
from app.services.stocks import StockQueryError, fetch_stock, fetch_stocks

logger = get_logger(__name__)

router = APIRouter()


@router.get("/{stock_id}", response_model=StockDetailResponse)
async def get_stock(
    stock_id: int = Path(..., ge=1, description="Stock ID"),
    db: AsyncSession = Depends(get_db_session),
) -> StockDetailResponse:
    """Return full detail for a single stock (active or inactive)."""
    try:
        row = await fetch_stock(db, stock_id)
    except StockQueryError:
        raise HTTPException(status_code=500, detail="Failed to fetch stock")

    if row is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    return StockDetailResponse(**row)


@router.get("/", response_model=StockListResponse)
async def list_stocks(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    basic_ind_code: Optional[str] = Query(None, description="Filter by basic industry code"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    exchange: Optional[str] = Query(None, description="Filter by exchange, e.g. NSE, BSE"),
    market_cap_category: Optional[str] = Query(None, description="Filter by market cap category"),
    db: AsyncSession = Depends(get_db_session),
) -> StockListResponse:
    """Return paginated list of stocks with optional filters."""
    offset = (page - 1) * page_size

    try:
        rows, total = await fetch_stocks(
            db=db,
            offset=offset,
            limit=page_size,
            basic_ind_code=basic_ind_code.strip() if basic_ind_code else None,
            is_active=is_active,
            exchange=exchange.strip() if exchange else None,
            market_cap_category=market_cap_category.strip() if market_cap_category else None,
        )
    except StockQueryError:
        raise HTTPException(status_code=500, detail="Failed to fetch stocks")

    return StockListResponse(
        page=page,
        page_size=page_size,
        total=total,
        count=len(rows),
        data=[StockDetailResponse(**row) for row in rows],
    )
