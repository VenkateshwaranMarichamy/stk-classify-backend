"""Pydantic schemas for fundamentals API."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ── Financials ───────────────────────────────────────────────────────────────

class PeerYearItem(BaseModel):
    """A single available year + period type for a peer group."""

    financial_year: int
    period_type: Optional[str]


class PeerYearsResponse(BaseModel):
    """Available financial years for a basic industry peer group."""

    basic_ind_code: str
    years: List[PeerYearItem]
    default_year: int
    default_period_type: str


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


class StockFundamentalsResponse(BaseModel):
    """All annual fundamentals for a single stock."""

    stock_id: int
    stock_name: Optional[str]
    count: int
    rows: List[PeerRow]


class PeersResponse(BaseModel):
    """Paginated peer comparison response."""

    basic_ind_code: str
    financial_year: int
    period_type: str
    page: int
    page_size: int
    total: int
    sort_by: str
    sort_dir: str
    rows: List[PeerRow]


# ── Valuation ────────────────────────────────────────────────────────────────

class ValuationYearsResponse(BaseModel):
    """Available financial years for valuation data (plain list — no period_type)."""

    basic_ind_code: str
    years: List[str]
    default_year: str


class ValuationRow(BaseModel):
    """Single stock row in the valuation metrics table."""

    stock_id: int
    stock: Optional[str]
    financial_year: Optional[int]
    financial_date: Optional[str]

    # Pricing
    current_price: Optional[float]
    market_cap: Optional[float]
    enterprise_value: Optional[float]

    # Multiples
    trailing_pe: Optional[float]
    forward_pe: Optional[float]
    peg_ratio: Optional[float]
    price_to_sales: Optional[float]
    price_to_book: Optional[float]
    enterprise_to_revenue: Optional[float]
    enterprise_to_ebitda: Optional[float]

    # Per share
    trailing_eps: Optional[float]
    forward_eps: Optional[float]
    book_value: Optional[float]
    total_cash_per_share: Optional[float]

    # Ratios
    current_ratio: Optional[float]
    quick_ratio: Optional[float]
    debt_to_equity: Optional[float]
    return_on_assets: Optional[float]
    return_on_equity: Optional[float]

    # Dividends
    dividend_yield: Optional[float]
    payout_ratio: Optional[float]

    # Shares
    shares_outstanding: Optional[float]
    float_shares: Optional[float]
    held_percent_insiders: Optional[float]
    held_percent_institutions: Optional[float]


class ValuationPeersResponse(BaseModel):
    """Paginated valuation peer comparison response."""

    basic_ind_code: str
    financial_year: int
    page: int
    page_size: int
    total: int
    sort_by: str
    sort_dir: str
    rows: List[ValuationRow]


class StockValuationResponse(BaseModel):
    """All annual valuation metrics for a single stock."""

    stock_id: int
    stock: Optional[str]
    count: int
    rows: List[ValuationRow]
