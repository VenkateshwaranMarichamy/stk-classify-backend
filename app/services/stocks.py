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
        cc.basic_ind_code,
        bi.basic_industry_name,
        cc.market_cap_category,
        cc.comments
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


async def fetch_active_stocks(db: AsyncSession) -> list[dict]:
    """Return all active stocks — id, name, trading_symbol."""
    stmt = text(
        """
        SELECT id, name, trading_symbol AS symbol
        FROM classification.ticker_symbol
        WHERE is_active = true
        ORDER BY name
        """
    )
    try:
        result = await db.execute(stmt)
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch active stocks")
        raise StockQueryError from exc
    return [dict(row) for row in result.mappings().all()]


async def fetch_active_stocks_paginated(
    db: AsyncSession,
    offset: int,
    limit: int,
) -> tuple[list[dict], int]:
    """Return paginated active stocks — id, name, trading_symbol."""
    count_stmt = text(
        "SELECT COUNT(*) FROM classification.ticker_symbol WHERE is_active = true"
    )
    rows_stmt = text(
        """
        SELECT id, name, trading_symbol AS symbol
        FROM classification.ticker_symbol
        WHERE is_active = true
        ORDER BY name
        LIMIT :limit OFFSET :offset
        """
    )
    try:
        total = int((await db.execute(count_stmt)).scalar() or 0)
        if total == 0:
            return [], 0
        result = await db.execute(rows_stmt, {"limit": limit, "offset": offset})
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch paginated active stocks")
        raise StockQueryError from exc
    return [dict(row) for row in result.mappings().all()], total


class StockAlreadyClassifiedError(ValueError):
    """Raised when a stock already has a classification row."""


async def fetch_unclassified_stocks(
    db: AsyncSession,
) -> list[dict]:
    """Return all stocks that have no entry in company_classification."""
    stmt = text(
        """
        SELECT id, name, trading_symbol
        FROM classification.ticker_symbol
        WHERE id NOT IN (
            SELECT company_id FROM classification.company_classification
        )
        ORDER BY id
        """
    )
    try:
        result = await db.execute(stmt)
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch unclassified stocks")
        raise StockQueryError from exc

    return [dict(row) for row in result.mappings().all()]


async def classify_stock(
    db: AsyncSession,
    company_id: int,
    company_name: str,
    basic_ind_code: str,
    market_cap_category: str,
) -> dict:
    """
    Insert into company_classification and create a matching stock_profiles row.
    Both inserts run in the same transaction — rolls back if either fails.
    Raises StockAlreadyClassifiedError if already classified.
    """
    check_stmt = text(
        """
        SELECT 1 FROM classification.company_classification
        WHERE company_id = :company_id
        """
    )
    insert_cc_stmt = text(
        """
        INSERT INTO classification.company_classification
            (company_id, company_name, basic_ind_code, market_cap_category)
        VALUES
            (:company_id, :company_name, :basic_ind_code, :market_cap_category)
        RETURNING company_id, company_name, basic_ind_code, market_cap_category
        """
    )
    insert_profile_stmt = text(
        """
        INSERT INTO classification.stock_profiles (stock_id, stock_name)
        VALUES (:stock_id, :stock_name)
        ON CONFLICT (stock_id) DO NOTHING
        """
    )
    try:
        existing = await db.execute(check_stmt, {"company_id": company_id})
        if existing.one_or_none() is not None:
            raise StockAlreadyClassifiedError(
                f"Stock {company_id} is already classified"
            )

        result = await db.execute(
            insert_cc_stmt,
            {
                "company_id": company_id,
                "company_name": company_name,
                "basic_ind_code": basic_ind_code,
                "market_cap_category": market_cap_category,
            },
        )
        row = result.mappings().one()

        await db.execute(
            insert_profile_stmt,
            {"stock_id": company_id, "stock_name": company_name},
        )

    except StockAlreadyClassifiedError:
        raise
    except SQLAlchemyError as exc:
        logger.exception("Failed to classify stock company_id=%s", company_id)
        raise StockQueryError from exc

    return dict(row)
