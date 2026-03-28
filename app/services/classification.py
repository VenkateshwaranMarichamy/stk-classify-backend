"""Service functions for classification-related reads."""

from typing import TypedDict

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)


class CompanyClassificationRow(TypedDict):
    """Row shape returned from classification.company_classification."""

    company_id: int | None
    company_name: str
    comments: str | None
    market_cap_category: str | None


class CompanyClassificationQueryError(RuntimeError):
    """Raised when fetching company classification rows fails."""


class CompanyClassificationNameMismatchError(ValueError):
    """Raised when provided company_name does not match company_id."""


class CompanyClassificationUpdateError(RuntimeError):
    """Raised when updating classification.company_classification fails."""


class CompanyClassificationUpdateRow(TypedDict):
    """Updated row shape for classification.company_classification."""

    company_id: int
    company_name: str
    basic_ind_code: str
    market_cap_category: str


async def fetch_stocks_by_basic_ind_code(
    db: AsyncSession,
    basic_ind_code: str,
) -> list[CompanyClassificationRow]:
    """Fetch stocks for a basic industry code from classification.company_classification."""
    stmt = text(
        """
        SELECT
            company_id,
            company_name,
            comments,
            market_cap_category
        FROM classification.company_classification
        WHERE basic_ind_code = :basic_ind_code
        ORDER BY company_name
        """
    )

    try:
        result = await db.execute(stmt, {"basic_ind_code": basic_ind_code})
    except SQLAlchemyError as exc:
        logger.exception(
            "Failed to query stocks for basic_ind_code=%s",
            basic_ind_code,
        )
        raise CompanyClassificationQueryError from exc

    return [
        CompanyClassificationRow(
            company_id=row["company_id"],
            company_name=row["company_name"],
            comments=row["comments"],
            market_cap_category=row["market_cap_category"],
        )
        for row in result.mappings().all()
    ]


async def fetch_stocks_by_basic_ind_code_paginated(
    db: AsyncSession,
    basic_ind_code: str,
    offset: int,
    limit: int,
) -> tuple[list[CompanyClassificationRow], int]:
    """Fetch paginated stocks and total count for a basic industry code."""
    count_stmt = text(
        """
        SELECT COUNT(*) AS total
        FROM classification.company_classification
        WHERE basic_ind_code = :basic_ind_code
        """
    )

    rows_stmt = text(
        """
        SELECT
            company_id,
            company_name,
            comments,
            market_cap_category
        FROM classification.company_classification
        WHERE basic_ind_code = :basic_ind_code
        ORDER BY company_name
        LIMIT :limit OFFSET :offset
        """
    )

    try:
        total_result = await db.execute(
            count_stmt,
            {"basic_ind_code": basic_ind_code},
        )
        total = int(total_result.scalar() or 0)

        if total == 0:
            return [], 0

        result = await db.execute(
            rows_stmt,
            {
                "basic_ind_code": basic_ind_code,
                "limit": limit,
                "offset": offset,
            },
        )
    except SQLAlchemyError as exc:
        logger.exception(
            "Failed to query paginated stocks for basic_ind_code=%s",
            basic_ind_code,
        )
        raise CompanyClassificationQueryError from exc

    rows = [
        CompanyClassificationRow(
            company_id=row["company_id"],
            company_name=row["company_name"],
            comments=row["comments"],
            market_cap_category=row["market_cap_category"],
        )
        for row in result.mappings().all()
    ]

    return rows, total


async def update_stock_classification_by_company_id(
    db: AsyncSession,
    company_id: int,
    company_name: str,
    basic_ind_code: str,
    market_cap_category: str,
) -> CompanyClassificationUpdateRow | None:
    """Update classification fields for one company by company_id."""
    lookup_stmt = text(
        """
        SELECT company_name
        FROM classification.company_classification
        WHERE company_id = :company_id
        """
    )
    update_stmt = text(
        """
        UPDATE classification.company_classification
        SET
            basic_ind_code = :basic_ind_code,
            market_cap_category = :market_cap_category,
            updated_at = NOW()
        WHERE company_id = :company_id
        RETURNING
            company_id,
            company_name,
            basic_ind_code,
            market_cap_category
        """
    )

    try:
        existing_result = await db.execute(lookup_stmt, {"company_id": company_id})
        existing = existing_result.mappings().one_or_none()
        if existing is None:
            return None

        if existing["company_name"].strip() != company_name.strip():
            raise CompanyClassificationNameMismatchError(
                "company_name does not match the provided company_id"
            )

        updated_result = await db.execute(
            update_stmt,
            {
                "company_id": company_id,
                "basic_ind_code": basic_ind_code,
                "market_cap_category": market_cap_category,
            },
        )
        updated = updated_result.mappings().one_or_none()
    except CompanyClassificationNameMismatchError:
        raise
    except SQLAlchemyError as exc:
        logger.exception(
            "Failed to update stock classification for company_id=%s",
            company_id,
        )
        raise CompanyClassificationUpdateError from exc

    if updated is None:
        return None

    return CompanyClassificationUpdateRow(
        company_id=updated["company_id"],
        company_name=updated["company_name"],
        basic_ind_code=updated["basic_ind_code"],
        market_cap_category=updated["market_cap_category"],
    )
