"""Pydantic schemas for classification API (read-only)."""

from typing import List

from pydantic import BaseModel, ConfigDict


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


class StocksByBasicIndustryResponse(BaseModel):
    """Response envelope for stocks under a basic industry code."""

    basic_ind_code: str
    count: int
    data: List[StockByBasicIndustryItem]


class ListEnvelope(BaseModel):
    """Envelope for list endpoints: data + count (optional total)."""

    data: List
    count: int
    total: int | None = None
