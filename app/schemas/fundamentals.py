"""Pydantic schemas for fundamentals API."""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict


class PeerYearsResponse(BaseModel):
    """Available financial years for a basic industry peer group."""

    basic_ind_code: str
    years: List[str]
    default_year: str


class PeerRow(BaseModel):
    """Single stock row in the peer comparison table."""

    model_config = ConfigDict(from_attributes=True)

    stock_id: int
    stock_name: Optional[str]
    financial_year: Optional[int]
    financial_date: Optional[str]

    # Size
    total_revenue: Optional[float]
    net_income: Optional[float]
    ebitda: Optional[float]
    free_cash_flow: Optional[float]

    # Per share
    diluted_eps: Optional[float]
    book_value_per_share: Optional[float]
    fcf_per_share: Optional[float]

    # Growth
    revenue_growth_pct: Optional[float]
    net_income_growth_pct: Optional[float]
    eps_growth_pct: Optional[float]
    ebitda_growth_pct: Optional[float]
    fcf_growth_pct: Optional[float]

    # Profitability
    gross_margin_pct: Optional[float]
    operating_margin_pct: Optional[float]
    ebitda_margin_pct: Optional[float]
    net_margin_pct: Optional[float]
    roa_pct: Optional[float]
    roe_pct: Optional[float]
    roic_pct: Optional[float]
    roce_pct: Optional[float]

    # Efficiency
    receivables_turnover_x: Optional[float]
    inventory_turnover_x: Optional[float]
    payables_turnover_x: Optional[float]

    # Leverage
    debt_to_equity_x: Optional[float]
    debt_to_assets_pct: Optional[float]
    net_debt_to_ebitda_x: Optional[float]
    interest_coverage_x: Optional[float]

    # Liquidity
    current_ratio_x: Optional[float]
    quick_ratio_x: Optional[float]

    # Cash flow quality
    cash_flow_to_net_income_x: Optional[float]
    free_cash_flow_margin_pct: Optional[float]
    capex_intensity_pct: Optional[float]
    cash_change: Optional[float]

    # Data quality
    has_balance_sheet: Optional[bool]
    has_cashflow: Optional[bool]


class PeersResponse(BaseModel):
    """Paginated peer comparison response."""

    basic_ind_code: str
    financial_year: int
    page: int
    page_size: int
    total: int
    sort_by: str
    sort_dir: str
    rows: List[PeerRow]
