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
