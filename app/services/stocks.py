"""Service functions for stock detail queries."""

from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)


class StockQueryError(RuntimeError):
    """Raised when a stock query fails."""


# Shared SELECT + JOIN used by both fetch_stock and fetch_stocks
_SELECT = """
    SELECT
        ts.id,
        ts.name,
        ts.short_name,
        ts.trading_symbol,
        ts.exchange,
        ts.instrument_type,
        ts.instrument_code,
        ts.security_type,
        ts.is_active,
        ts.inactive_reason,
        ts.derivate_stock,
        ts.yfinance_ticker,
        cc.company_name,
        cc.nse_symbol,
        cc.bse_code,
        cc.basic_ind_code,
        bi.basic_industry_name,
        cc.index_stock,
        cc.market_cap_category,
        cc.comments,
        cc.cutting_edge_products
    FROM classification.ticker_symbol ts
    LEFT JOIN classification.company_classification cc
           ON cc.company_id = ts.id
    LEFT JOIN classification.basic_industries bi
           ON bi.basic_ind_code = cc.basic_ind_code
"""


async def fetch_stock(db: AsyncSession, stock_id: int) -> Optional[dict]:
    """Return full stock detail for a single ID (active or inactive)."""
    stmt = text(f"{_SELECT} WHERE ts.id = :id")
    try:
        result = await db.execute(stmt, {"id": stock_id})
        row = result.mappings().one_or_none()
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch stock id=%s", stock_id)
        raise StockQueryError from exc
    return dict(row) if row else None


async def fetch_stocks(
    db: AsyncSession,
    offset: int,
    limit: int,
    basic_ind_code: Optional[str] = None,
    is_active: Optional[bool] = None,
    exchange: Optional[str] = None,
    market_cap_category: Optional[str] = None,
) -> tuple[list[dict], int]:
    """Return paginated stock list with optional filters."""
    filters = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if basic_ind_code is not None:
        filters.append("cc.basic_ind_code = :basic_ind_code")
        params["basic_ind_code"] = basic_ind_code

    if is_active is not None:
        filters.append("ts.is_active = :is_active")
        params["is_active"] = is_active

    if exchange is not None:
        filters.append("ts.exchange = :exchange")
        params["exchange"] = exchange.upper()

    if market_cap_category is not None:
        filters.append("cc.market_cap_category = :market_cap_category")
        params["market_cap_category"] = market_cap_category.upper()

    where = "WHERE " + " AND ".join(filters)

    count_stmt = text(
        f"""
        SELECT COUNT(*) AS total
        FROM classification.ticker_symbol ts
        LEFT JOIN classification.company_classification cc
               ON cc.company_id = ts.id
        {where}
        """
    )

    rows_stmt = text(
        f"""
        {_SELECT}
        {where}
        ORDER BY ts.id
        LIMIT :limit OFFSET :offset
        """
    )

    try:
        total_result = await db.execute(count_stmt, params)
        total = int(total_result.scalar() or 0)

        if total == 0:
            return [], 0

        result = await db.execute(rows_stmt, params)
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch stocks list")
        raise StockQueryError from exc

    return [dict(row) for row in result.mappings().all()], total
