"""Pydantic schemas for stock detail API."""

from typing import List, Optional

from pydantic import BaseModel, field_validator


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
    basic_ind_code: Optional[str]
    basic_industry_name: Optional[str]
    market_cap_category: Optional[str]
    comments: Optional[str]


class ActiveStockItem(BaseModel):
    """Minimal active stock row."""

    id: int
    name: Optional[str]
    symbol: Optional[str]


class ActiveStocksResponse(BaseModel):
    """All active stocks."""

    total: int
    data: List[ActiveStockItem]


class PaginatedActiveStocksResponse(BaseModel):
    """Paginated active stocks."""

    page: int
    page_size: int
    total: int
    count: int
    data: List[ActiveStockItem]


class StockListResponse(BaseModel):
    """Paginated list of stocks."""

    page: int
    page_size: int
    total: int
    count: int
    data: List[StockDetailResponse]


class UnclassifiedStockItem(BaseModel):
    """Minimal stock row for unclassified stocks list."""

    id: int
    name: Optional[str]
    trading_symbol: Optional[str]


class UnclassifiedStocksResponse(BaseModel):
    """List of unclassified stocks."""

    total: int
    data: List[UnclassifiedStockItem]


class ClassifyStockRequest(BaseModel):
    """Payload to classify a stock."""

    company_name: str
    basic_ind_code: str
    market_cap_category: str

    @field_validator("company_name", "basic_ind_code", "market_cap_category")
    @classmethod
    def non_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be empty")
        return v

    @field_validator("market_cap_category")
    @classmethod
    def normalize_market_cap(cls, v: str) -> str:
        return v.upper()


class ClassifyStockResponse(BaseModel):
    """Newly created classification row."""

    company_id: int
    company_name: str
    basic_ind_code: str
    market_cap_category: str
