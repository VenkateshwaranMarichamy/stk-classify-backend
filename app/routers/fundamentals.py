"""REST endpoints for fundamentals peer comparison."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.database import get_db_session
from app.schemas.fundamentals import (
    PeerRow,
    PeerYearItem,
    PeerYearsResponse,
    PeersResponse,
    StockFundamentalsResponse,
    StockValuationResponse,
    ValuationPeersResponse,
    ValuationRow,
    ValuationYearsResponse,
)
from app.services.fundamentals import (
    DEFAULT_SORT,
    DEFAULT_VALUATION_SORT,
    SORTABLE_COLUMNS,
    VALUATION_SORTABLE_COLUMNS,
    FundamentalsQueryError,
    fetch_peer_years,
    fetch_peers,
    fetch_stock_fundamentals,
    fetch_stock_valuation,
    fetch_valuation_peers,
    fetch_valuation_years,
)

logger = get_logger(__name__)

router = APIRouter()


# ── Financials ───────────────────────────────────────────────────────────────

@router.get(
    "/stock/{stock_id}",
    response_model=StockFundamentalsResponse,
    summary="Annual financials for a single stock",
    description=(
        "Returns all available annual financial rows for a single stock from "
        "`stock_fundamentals_annual_display`, ordered newest year first. "
        "Includes size, growth, profitability, efficiency, leverage, liquidity, "
        "and cash flow quality metrics. Active or inactive stock — no filter applied."
    ),
)
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


@router.get(
    "/peer-years",
    response_model=PeerYearsResponse,
    summary="Available financial years for a peer group",
    description=(
        "Returns the distinct financial years for which annual financials exist "
        "for active stocks in the given `basic_ind_code`. "
        "Call this first to populate the year selector, then use the `default_year` "
        "to make the initial `/peers` request."
    ),
)
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

    annual_years = [y for y in years if y["period_type"] == "annual"]
    default = annual_years[0] if annual_years else years[0]

    return PeerYearsResponse(
        basic_ind_code=basic_ind_code,
        years=[PeerYearItem(**y) for y in years],
        default_year=default["financial_year"],
        default_period_type=default["period_type"],
    )


@router.get(
    "/peers",
    response_model=PeersResponse,
    summary="Peer financials comparison table",
    description=(
        "Returns a paginated, sortable table of annual financial metrics for all active stocks "
        "in the given `basic_ind_code`, `financial_year`, and `period_type`. "
        "Use `/peer-years` first to get available year + period_type combinations. "
        "Only active stocks (`ticker_symbol.is_active = true`) are included. "
        f"Sortable columns: `{'`, `'.join(sorted(SORTABLE_COLUMNS))}`."
    ),
)
async def get_peers(
    basic_ind_code: str = Query(..., description="Basic industry code"),
    financial_year: int = Query(..., description="Financial year, e.g. 2025"),
    period_type: str = Query("annual", description="Period type, e.g. 'annual' or 'ttm'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    sort_by: str = Query(DEFAULT_SORT, description="Column to sort by"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db_session),
) -> PeersResponse:
    """Return paginated peer financials for a basic industry, financial year, and period type."""
    basic_ind_code = basic_ind_code.strip()
    if not basic_ind_code:
        raise HTTPException(status_code=400, detail="basic_ind_code is required")

    offset = (page - 1) * page_size

    try:
        rows, total = await fetch_peers(
            db=db,
            basic_ind_code=basic_ind_code,
            financial_year=financial_year,
            period_type=period_type.strip().lower(),
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
            detail="No data found for the given basic_ind_code, financial_year, and period_type",
        )

    return PeersResponse(
        basic_ind_code=basic_ind_code,
        financial_year=financial_year,
        period_type=period_type.strip().lower(),
        page=page,
        page_size=page_size,
        total=total,
        sort_by=sort_by,
        sort_dir=sort_dir.lower(),
        rows=[PeerRow(**row) for row in rows],
    )


# ── Valuation ────────────────────────────────────────────────────────────────

@router.get(
    "/valuation/years",
    response_model=ValuationYearsResponse,
    summary="Available valuation years for a peer group",
    description=(
        "Returns the distinct financial years for which valuation metrics exist "
        "for active stocks in the given `basic_ind_code`. "
        "Call this first to populate the year selector, then use `default_year` "
        "to make the initial `/valuation/peers` request."
    ),
)
async def get_valuation_years(
    basic_ind_code: str = Query(..., description="Basic industry code"),
    db: AsyncSession = Depends(get_db_session),
) -> ValuationYearsResponse:
    """Return distinct financial years available in valuation data for a basic industry."""
    basic_ind_code = basic_ind_code.strip()
    if not basic_ind_code:
        raise HTTPException(status_code=400, detail="basic_ind_code is required")

    try:
        years = await fetch_valuation_years(db, basic_ind_code)
    except FundamentalsQueryError:
        raise HTTPException(status_code=500, detail="Failed to fetch valuation years")

    if not years:
        raise HTTPException(
            status_code=404,
            detail="No valuation data found for the given basic_ind_code",
        )

    return ValuationYearsResponse(
        basic_ind_code=basic_ind_code,
        years=years,
        default_year=years[0],
    )


@router.get(
    "/valuation/peers",
    response_model=ValuationPeersResponse,
    summary="Peer valuation metrics comparison table",
    description=(
        "Returns a paginated, sortable table of annual valuation metrics for all active stocks "
        "in the given `basic_ind_code` and `financial_year`. "
        "Includes price multiples (P/E, P/B, EV/EBITDA), per-share values, "
        "dividend info, and ownership breakdown. "
        "Use `/valuation/years` first to get available years. "
        "Only active stocks (`ticker_symbol.is_active = true`) are included. "
        "If `page` and `page_size` are omitted, all matching rows are returned. "
        f"Sortable columns: `{'`, `'.join(sorted(VALUATION_SORTABLE_COLUMNS))}`."
    ),
)
async def get_valuation_peers(
    basic_ind_code: str = Query(..., description="Basic industry code"),
    financial_year: int = Query(..., description="Financial year, e.g. 2025"),
    page: Optional[int] = Query(None, ge=1, description="Page number (1-based). Omit to return all rows."),
    page_size: Optional[int] = Query(None, ge=1, le=1000, description="Rows per page. Omit to return all rows."),
    sort_by: str = Query(DEFAULT_VALUATION_SORT, description="Column to sort by"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db_session),
) -> ValuationPeersResponse:
    """Return valuation metrics for active stocks in a basic industry and year. Returns all if page/page_size omitted."""
    basic_ind_code = basic_ind_code.strip()
    if not basic_ind_code:
        raise HTTPException(status_code=400, detail="basic_ind_code is required")

    # If either pagination param is missing, return everything
    paginated = page is not None and page_size is not None
    effective_page = page or 1
    effective_page_size = page_size or 10_000  # large enough to cover any peer group
    offset = (effective_page - 1) * effective_page_size

    try:
        rows, total = await fetch_valuation_peers(
            db=db,
            basic_ind_code=basic_ind_code,
            financial_year=financial_year,
            offset=offset,
            limit=effective_page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    except FundamentalsQueryError:
        raise HTTPException(status_code=500, detail="Failed to fetch valuation peer data")

    if total == 0:
        raise HTTPException(
            status_code=404,
            detail="No valuation data found for the given basic_ind_code and financial_year",
        )

    return ValuationPeersResponse(
        basic_ind_code=basic_ind_code,
        financial_year=financial_year,
        page=effective_page,
        page_size=len(rows) if not paginated else effective_page_size,
        total=total,
        sort_by=sort_by,
        sort_dir=sort_dir.lower(),
        rows=[ValuationRow(**row) for row in rows],
    )


@router.get(
    "/valuation/stock/{stock_id}",
    response_model=StockValuationResponse,
    summary="Annual valuation metrics for a single stock",
    description=(
        "Returns all available annual valuation rows for a single stock from "
        "`valuation_metric_annual`, ordered newest year first. "
        "Includes price multiples, per-share values, ratios, dividend info, "
        "and ownership percentages. Active or inactive stock — no filter applied."
    ),
)
async def get_stock_valuation(
    stock_id: int = Path(..., ge=1, description="Stock ID"),
    db: AsyncSession = Depends(get_db_session),
) -> StockValuationResponse:
    """Return all annual valuation metrics for a single stock, newest year first."""
    try:
        rows = await fetch_stock_valuation(db, stock_id)
    except FundamentalsQueryError:
        raise HTTPException(status_code=500, detail="Failed to fetch stock valuation")

    if not rows:
        raise HTTPException(status_code=404, detail="No valuation data found for this stock")

    return StockValuationResponse(
        stock_id=stock_id,
        stock=rows[0].get("stock"),
        count=len(rows),
        rows=[ValuationRow(**row) for row in rows],
    )
