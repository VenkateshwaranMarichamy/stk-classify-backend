"""Pydantic schemas for stock detail API."""

from typing import List, Optional

from pydantic import BaseModel


class StockDetailResponse(BaseModel):
    """Full stock detail combining ticker_symbol, company_classification, basic_industries."""

    # Identity
    id: int
    name: Optional[str]
    short_name: Optional[str]

    # Ticker
    trading_symbol: Optional[str]
    exchange: Optional[str]
    instrument_type: Optional[str]
    instrument_code: Optional[str]
    security_type: Optional[str]
    is_active: Optional[bool]
    inactive_reason: Optional[str]
    derivate_stock: Optional[bool]
    yfinance_ticker: Optional[str]

    # Classification
    company_name: Optional[str]
    nse_symbol: Optional[str]
    bse_code: Optional[str]
    basic_ind_code: Optional[str]
    basic_industry_name: Optional[str]
    index_stock: Optional[str]
    market_cap_category: Optional[str]
    comments: Optional[str]
    cutting_edge_products: Optional[str]


class StockListResponse(BaseModel):
    """Paginated list of stocks."""

    page: int
    page_size: int
    total: int
    count: int
    data: List[StockDetailResponse]
