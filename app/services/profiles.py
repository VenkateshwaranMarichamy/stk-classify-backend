"""Service functions for stock profiles."""

from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)

_SELECT = """
    SELECT
        stock_id, stock_name, associated_brands, business_group,
        information, risk_level, location, ownership_type,
        keynotes, clients, parent_companies, subsidiaries,
        products, index_stock, cutting_edge_products
    FROM classification.stock_profiles
    WHERE stock_id = :stock_id
"""


class ProfileQueryError(RuntimeError):
    """Raised when a profile DB operation fails."""


async def fetch_profile(db: AsyncSession, profile_id: int) -> Optional[dict]:
    """Return a single profile row or None if not found."""
    try:
        result = await db.execute(text(_SELECT), {"stock_id": profile_id})
        row = result.mappings().one_or_none()
    except SQLAlchemyError as exc:
        logger.exception("Failed to fetch profile stock_id=%s", profile_id)
        raise ProfileQueryError from exc
    return dict(row) if row else None


async def patch_profile(
    db: AsyncSession,
    profile_id: int,
    associated_brands: Optional[list[str]],
    business_group: Optional[str],
    information: Optional[str],
    risk_level: Optional[str],
    location: Optional[list[str]],
    ownership_type: Optional[str],
    keynotes: Optional[list[str]],
    clients: Optional[list[str]],
    parent_companies: Optional[list[int]],
    subsidiaries: Optional[list[int]],
    products: Optional[list[str]],
    index_stock: Optional[list[str]],
    cutting_edge_products: Optional[list[str]],
) -> Optional[dict]:
    """
    Update only the supplied fields via COALESCE, always bump updated_at.
    Returns the updated row or None if not found.
    """
    stmt = text(
        """
        UPDATE classification.stock_profiles
        SET
            associated_brands    = COALESCE(:associated_brands,    associated_brands),
            business_group       = COALESCE(:business_group,       business_group),
            information          = COALESCE(:information,          information),
            risk_level           = COALESCE(:risk_level,           risk_level),
            location             = COALESCE(:location,             location),
            ownership_type       = COALESCE(:ownership_type,       ownership_type),
            keynotes             = COALESCE(:keynotes,             keynotes),
            clients              = COALESCE(:clients,              clients),
            parent_companies     = COALESCE(:parent_companies,     parent_companies),
            subsidiaries         = COALESCE(:subsidiaries,         subsidiaries),
            products             = COALESCE(:products,             products),
            index_stock          = COALESCE(:index_stock,          index_stock),
            cutting_edge_products = COALESCE(:cutting_edge_products, cutting_edge_products),
            updated_at           = CURRENT_TIMESTAMP
        WHERE stock_id = :stock_id
        RETURNING
            stock_id, stock_name, associated_brands, business_group,
            information, risk_level, location, ownership_type,
            keynotes, clients, parent_companies, subsidiaries,
            products, index_stock, cutting_edge_products
        """
    )
    try:
        result = await db.execute(
            stmt,
            {
                "stock_id": profile_id,
                "associated_brands": associated_brands,
                "business_group": business_group,
                "information": information,
                "risk_level": risk_level,
                "location": location,
                "ownership_type": ownership_type,
                "keynotes": keynotes,
                "clients": clients,
                "parent_companies": parent_companies,
                "subsidiaries": subsidiaries,
                "products": products,
                "index_stock": index_stock,
                "cutting_edge_products": cutting_edge_products,
            },
        )
        row = result.mappings().one_or_none()
    except SQLAlchemyError as exc:
        logger.exception("Failed to patch profile stock_id=%s", profile_id)
        raise ProfileQueryError from exc
    return dict(row) if row else None
