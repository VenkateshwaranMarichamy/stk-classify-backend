"""Service functions for fundamentals peer queries."""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)

# Columns allowed for sorting (whitelist to prevent SQL injection)
SORTABLE_COLUMNS = {
    "stock_name", "financial_year", "financial_date",
    "total_revenue", "net_income", "ebitda", "free_cash_flow",
    "diluted_eps", "book_value_per_share", "fcf_per_share",
    "revenue_growth_pct", "net_income_growth_pct", "eps_growth_pct",
    "ebitda_growth_pct", "fcf_growth_pct",
    "gross_margin_pct", "operating_margin_pct", "ebitda_margin_pct",
    "net_margin_pct", "roa_pct", "roe_pct", "roic_pct", "roce_pct",
    "receivables_turnover_x", "inventory_turnover_x", "payables_turnover_x",
    "debt_to_equity_x", "debt_to_assets_pct", "net_debt_to_ebitda_x",
    "interest_coverage_x", "current_ratio_x", "quick_ratio_x",
    "cash_flow_to_net_income_x", "free_cash_flow_margin_pct",
    "capex_intensity_pct", "cash_change",
}

DEFAULT_SORT = "total_revenue"

_FUNDAMENTALS_COLUMNS = """
    stock_id,
    stock_name,
    financial_year,
    CAST(financial_date AS TEXT) AS financial_date,
    total_revenue, net_income, ebitda, free_cash_flow,
    diluted_eps, book_value_per_share, fcf_per_share,
    revenue_growth_pct, net_income_growth_pct, eps_growth_pct,
    ebitda_growth_pct, fcf_growth_pct,
    gross_margin_pct, operating_margin_pct, ebitda_margin_pct,
    net_margin_pct, roa_pct, roe_pct, roic_pct, roce_pct,
    receivables_turnover_x, inventory_turnover_x, payables_turnover_x,
    debt_to_equity_x, debt_to_assets_pct, net_debt_to_ebitda_x,
    interest_coverage_x, current_ratio_x, quick_ratio_x,
    cash_flow_to_net_income_x, free_cash_flow_margin_pct,
    capex_intensity_pct, cash_change,
    has_balance_sheet, has_cashflow
"""


class FundamentalsQueryError(RuntimeError):
    """Raised when a fundamentals query fails."""


async def fetch_peer_years(
    db: AsyncSession,
    basic_ind_code: str,
) -> list[str]:
    """Return distinct financial_year values for a basic industry, newest first."""
    stmt = text(
        """
        SELECT DISTINCT f.financial_year
        FROM fundamentals.stock_fundamentals_annual_display f
        WHERE f.basic_ind_code = :basic_ind_code
          AND f.financial_year IS NOT NULL
          AND f.stock_id IN (
              SELECT id FROM classification.ticker_symbol WHERE is_active = true
          )
        ORDER BY f.financial_year DESC
        """
    )
    try:
        result = await db.execute(stmt, {"basic_ind_code": basic_ind_code})
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch peer years for basic_ind_code=%s", basic_ind_code)
        raise FundamentalsQueryError from exc

    return [str(row[0]) for row in result.fetchall()]


async def fetch_stock_fundamentals(
    db: AsyncSession,
    stock_id: int,
) -> list[dict]:
    """Return all annual fundamentals rows for a single stock, newest year first."""
    stmt = text(
        f"""
        SELECT {_FUNDAMENTALS_COLUMNS}
        FROM fundamentals.stock_fundamentals_annual_display
        WHERE stock_id = :stock_id
        ORDER BY financial_year DESC
        """
    )
    try:
        result = await db.execute(stmt, {"stock_id": stock_id})
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch fundamentals for stock_id=%s", stock_id)
        raise FundamentalsQueryError from exc

    return [dict(row) for row in result.mappings().all()]


async def fetch_peers(
    db: AsyncSession,
    basic_ind_code: str,
    financial_year: int,
    offset: int,
    limit: int,
    sort_by: str,
    sort_dir: str,
) -> tuple[list[dict], int]:
    """Return paginated peer rows and total count for a basic industry + year."""
    safe_sort_by = sort_by if sort_by in SORTABLE_COLUMNS else DEFAULT_SORT
    safe_sort_dir = "DESC" if sort_dir.upper() == "DESC" else "ASC"

    count_stmt = text(
        """
        SELECT COUNT(*) AS total
        FROM fundamentals.stock_fundamentals_annual_display
        WHERE basic_ind_code = :basic_ind_code
          AND financial_year = :financial_year
          AND stock_id IN (
              SELECT id FROM classification.ticker_symbol WHERE is_active = true
          )
        """
    )

    rows_stmt = text(
        f"""
        SELECT {_FUNDAMENTALS_COLUMNS}
        FROM fundamentals.stock_fundamentals_annual_display
        WHERE basic_ind_code = :basic_ind_code
          AND financial_year = :financial_year
          AND stock_id IN (
              SELECT id FROM classification.ticker_symbol WHERE is_active = true
          )
        ORDER BY {safe_sort_by} {safe_sort_dir} NULLS LAST
        LIMIT :limit OFFSET :offset
        """
    )

    try:
        total_result = await db.execute(
            count_stmt,
            {"basic_ind_code": basic_ind_code, "financial_year": financial_year},
        )
        total = int(total_result.scalar() or 0)

        if total == 0:
            return [], 0

        result = await db.execute(
            rows_stmt,
            {
                "basic_ind_code": basic_ind_code,
                "financial_year": financial_year,
                "limit": limit,
                "offset": offset,
            },
        )
    except SQLAlchemyError as exc:
        logger.exception(
            "Failed to fetch peers for basic_ind_code=%s year=%s",
            basic_ind_code,
            financial_year,
        )
        raise FundamentalsQueryError from exc

    rows = [dict(row) for row in result.mappings().all()]
    return rows, total


# Columns allowed for valuation sorting
VALUATION_SORTABLE_COLUMNS = {
    "stock", "financial_year", "financial_date",
    "current_price", "market_cap", "enterprise_value",
    "trailing_pe", "forward_pe", "peg_ratio",
    "price_to_sales", "price_to_book",
    "enterprise_to_revenue", "enterprise_to_ebitda",
    "trailing_eps", "forward_eps", "book_value", "total_cash_per_share",
    "current_ratio", "quick_ratio", "debt_to_equity",
    "return_on_assets", "return_on_equity",
    "dividend_yield", "payout_ratio",
    "shares_outstanding", "float_shares",
    "held_percent_insiders", "held_percent_institutions",
}

DEFAULT_VALUATION_SORT = "market_cap"

_VALUATION_COLUMNS = """
    stock_id,
    stock,
    financial_year,
    CAST(financial_date AS TEXT) AS financial_date,
    current_price, market_cap, enterprise_value,
    trailing_pe, forward_pe, peg_ratio,
    price_to_sales, price_to_book,
    enterprise_to_revenue, enterprise_to_ebitda,
    trailing_eps, forward_eps, book_value, total_cash_per_share,
    current_ratio, quick_ratio, debt_to_equity,
    return_on_assets, return_on_equity,
    dividend_yield, payout_ratio,
    shares_outstanding, float_shares,
    held_percent_insiders, held_percent_institutions
"""


async def fetch_valuation_peers(
    db: AsyncSession,
    basic_ind_code: str,
    financial_year: int,
    offset: int,
    limit: int,
    sort_by: str,
    sort_dir: str,
) -> tuple[list[dict], int]:
    """Return paginated valuation rows for active stocks in a basic industry + year."""
    safe_sort_by = sort_by if sort_by in VALUATION_SORTABLE_COLUMNS else DEFAULT_VALUATION_SORT
    safe_sort_dir = "DESC" if sort_dir.upper() == "DESC" else "ASC"

    count_stmt = text(
        """
        SELECT COUNT(*) AS total
        FROM fundamentals.valuation_metric_annual
        WHERE financial_year = :financial_year
          AND stock_id IN (
              SELECT company_id FROM classification.company_classification
              WHERE basic_ind_code = :basic_ind_code
          )
          AND stock_id IN (
              SELECT id FROM classification.ticker_symbol WHERE is_active = true
          )
        """
    )

    rows_stmt = text(
        f"""
        SELECT {_VALUATION_COLUMNS}
        FROM fundamentals.valuation_metric_annual
        WHERE financial_year = :financial_year
          AND stock_id IN (
              SELECT company_id FROM classification.company_classification
              WHERE basic_ind_code = :basic_ind_code
          )
          AND stock_id IN (
              SELECT id FROM classification.ticker_symbol WHERE is_active = true
          )
        ORDER BY {safe_sort_by} {safe_sort_dir} NULLS LAST
        LIMIT :limit OFFSET :offset
        """
    )

    try:
        total_result = await db.execute(
            count_stmt,
            {"basic_ind_code": basic_ind_code, "financial_year": financial_year},
        )
        total = int(total_result.scalar() or 0)

        if total == 0:
            return [], 0

        result = await db.execute(
            rows_stmt,
            {
                "basic_ind_code": basic_ind_code,
                "financial_year": financial_year,
                "limit": limit,
                "offset": offset,
            },
        )
    except SQLAlchemyError as exc:
        logger.exception(
            "Failed to fetch valuation peers for basic_ind_code=%s year=%s",
            basic_ind_code, financial_year,
        )
        raise FundamentalsQueryError from exc

    return [dict(row) for row in result.mappings().all()], total


async def fetch_stock_valuation(
    db: AsyncSession,
    stock_id: int,
) -> list[dict]:
    """Return all annual valuation rows for a single stock, newest year first."""
    stmt = text(
        f"""
        SELECT {_VALUATION_COLUMNS}
        FROM fundamentals.valuation_metric_annual
        WHERE stock_id = :stock_id
        ORDER BY financial_year DESC
        """
    )
    try:
        result = await db.execute(stmt, {"stock_id": stock_id})
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch valuation for stock_id=%s", stock_id)
        raise FundamentalsQueryError from exc

    return [dict(row) for row in result.mappings().all()]


async def fetch_valuation_years(
    db: AsyncSession,
    basic_ind_code: str,
) -> list[str]:
    """Return distinct financial_year values for valuation data in a basic industry, newest first."""
    stmt = text(
        """
        SELECT DISTINCT financial_year
        FROM fundamentals.valuation_metric_annual
        WHERE financial_year IS NOT NULL
          AND stock_id IN (
              SELECT company_id FROM classification.company_classification
              WHERE basic_ind_code = :basic_ind_code
          )
          AND stock_id IN (
              SELECT id FROM classification.ticker_symbol WHERE is_active = true
          )
        ORDER BY financial_year DESC
        """
    )
    try:
        result = await db.execute(stmt, {"basic_ind_code": basic_ind_code})
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch valuation years for basic_ind_code=%s", basic_ind_code)
        raise FundamentalsQueryError from exc

    return [str(row[0]) for row in result.fetchall()]
