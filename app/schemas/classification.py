"""Pydantic schemas for classification API."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class MacroEconomicSectorResponse(BaseModel):
    """Macro economic sector as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    mes_code: str
    macro_economic_sector: str


class SectorResponse(BaseModel):
    """Sector as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    sect_code: str
    sector_name: str
    mes_code: str


class IndustryResponse(BaseModel):
    """Industry as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    ind_code: str
    industry_name: str
    sect_code: str


class BasicIndustryResponse(BaseModel):
    """Basic industry as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    basic_ind_code: str
    basic_industry_name: str
    definition: str | None
    ind_code: str


class DropdownDataResponse(BaseModel):
    """Single-call response for React 4-dropdown UI."""

    macro_economic_sectors: List[MacroEconomicSectorResponse]
    sectors: List[SectorResponse]
    industries: List[IndustryResponse]
    basic_industries: List[BasicIndustryResponse]


class StockByBasicIndustryItem(BaseModel):
    """Stock row returned for a basic industry code."""

    company_id: int | None
    company_name: str
    comments: str | None
    market_cap_category: str | None
    tech_risk: str | None
    fund_risk: str | None
    revenue_size: str | None


class StocksByBasicIndustryResponse(BaseModel):
    """Response envelope for stocks under a basic industry code."""

    basic_ind_code: str
    count: int
    data: List[StockByBasicIndustryItem]


class PaginatedStocksByBasicIndustryResponse(BaseModel):
    """Paginated response for stocks under a basic industry code."""

    basic_ind_code: str
    page: int
    page_size: int
    count: int
    total: int
    data: List[StockByBasicIndustryItem]


class CompanyClassificationUpdateRequest(BaseModel):
    """Payload for updating classification fields for a stock."""

    company_name: str
    basic_ind_code: str
    market_cap_category: Optional[str] = None
    tech_risk: Optional[str] = None
    fund_risk: Optional[str] = None
    revenue_size: Optional[str] = None
    comments: Optional[str] = None

    @field_validator("company_name", "basic_ind_code")
    @classmethod
    def non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("market_cap_category", "tech_risk", "fund_risk", "revenue_size", mode="before")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("comments", mode="before")
    @classmethod
    def strip_comments(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class CompanyClassificationUpdateResponse(BaseModel):
    """Updated stock classification row."""

    company_id: int
    company_name: str
    basic_ind_code: str
    market_cap_category: str | None
    tech_risk: str | None
    fund_risk: str | None
    revenue_size: str | None
    comments: str | None


class ListEnvelope(BaseModel):
    """Envelope for list endpoints: data + count (optional total)."""

    data: List
    count: int
    total: int | None = None
