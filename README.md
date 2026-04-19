# Stock Classification Backend

REST API for stock classification and fundamentals. Built with FastAPI, async SQLAlchemy, and PostgreSQL.

## Setup

### 1. Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Config

```bash
cp .env.example .env
```

Set the database URL in `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/stock_db
```

### 4. Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## Project layout

```
app/
  core/         config.py, logger.py
  models/       SQLAlchemy ORM models
  schemas/      Pydantic request/response schemas
  services/     DB query logic
  routers/      FastAPI route handlers
  database.py   engine, session, init_db
  main.py       app factory, lifespan, middleware
docs/           design docs
scripts/        seed scripts
```

---

## API Reference

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |

---

### Classification — reference data (read-only)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/classification/dropdown-data` | All four hierarchy lists in one call (for cascading dropdowns) |
| GET | `/api/classification/macro-economic-sectors` | List all macro economic sectors |
| GET | `/api/classification/macro-economic-sectors/{mes_code}` | Get one macro economic sector |
| GET | `/api/classification/sectors` | List sectors (`?mes_code=` to filter) |
| GET | `/api/classification/sectors/{sect_code}` | Get one sector |
| GET | `/api/classification/industries` | List industries (`?sect_code=` to filter) |
| GET | `/api/classification/industries/{ind_code}` | Get one industry |
| GET | `/api/classification/basic-industries` | List basic industries (`?ind_code=`, `?skip=`, `?limit=`) |
| GET | `/api/classification/basic-industries/{basic_ind_code}` | Get one basic industry |
| GET | `/api/classification/stocks` | Stocks for a basic industry code (`?basic_ind_code=`) — active only |
| GET | `/api/classification/stocks/paginated` | Paginated version (`?basic_ind_code=`, `?page=`, `?page_size=`) |
| PUT | `/api/classification/stocks/{company_id}` | Update `basic_ind_code` and `market_cap_category` for a stock |

---

### Stocks — identity and classification detail

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stocks/` | Paginated stock list. Filters: `?is_active=`, `?basic_ind_code=`, `?exchange=`, `?market_cap_category=` |
| GET | `/api/stocks/unclassified` | All stocks not yet in `company_classification` |
| GET | `/api/stocks/{stock_id}` | Full stock detail — ticker + classification info (active or inactive) |
| POST | `/api/stocks/{stock_id}/classify` | Classify a stock (insert into `company_classification`) |

**POST `/api/stocks/{stock_id}/classify` payload:**
```json
{
  "company_name": "XYZ LTD",
  "basic_ind_code": "IN040101001",
  "market_cap_category": "SMALL"
}
```
Returns `201` on success, `409` if already classified.

---

### Profiles — qualitative stock data

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/profiles/{stock_id}` | Full profile for a stock (active or inactive) |
| PATCH | `/api/profiles/{stock_id}` | Partial update — send only fields to change |

**PATCH `/api/profiles/{stock_id}` patchable fields:**
`associated_brands`, `business_group`, `information`, `risk_level`, `location`,
`ownership_type`, `keynotes`, `clients`, `parent_companies`, `subsidiaries`,
`products`, `index_stock`, `cutting_edge_products`

`ownership_type` must be one of: `GOVT_CONTROLLED`, `JOINT_VENTURE`, `PRIVATE`, `PSU`

---

### Fundamentals — annual financial data

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/fundamentals/peer-years` | Available financial years for a basic industry (`?basic_ind_code=`) — active stocks only |
| GET | `/api/fundamentals/peers` | Paginated peer comparison table (`?basic_ind_code=`, `?financial_year=`, `?page=`, `?page_size=`, `?sort_by=`, `?sort_dir=`) — active stocks only |
| GET | `/api/fundamentals/stock/{stock_id}` | All annual fundamentals for a single stock, newest year first |

**`/api/fundamentals/peers` sort options:**
`total_revenue`, `net_income`, `ebitda`, `free_cash_flow`, `diluted_eps`,
`book_value_per_share`, `fcf_per_share`, `revenue_growth_pct`, `net_income_growth_pct`,
`eps_growth_pct`, `ebitda_growth_pct`, `fcf_growth_pct`, `gross_margin_pct`,
`operating_margin_pct`, `ebitda_margin_pct`, `net_margin_pct`, `roa_pct`, `roe_pct`,
`roic_pct`, `roce_pct`, `receivables_turnover_x`, `inventory_turnover_x`,
`payables_turnover_x`, `debt_to_equity_x`, `debt_to_assets_pct`, `net_debt_to_ebitda_x`,
`interest_coverage_x`, `current_ratio_x`, `quick_ratio_x`, `cash_flow_to_net_income_x`,
`free_cash_flow_margin_pct`, `capex_intensity_pct`, `cash_change`

---

## Logger

```python
from app.core.logger import get_logger
logger = get_logger(__name__)
logger.info("message")
```

Log level set via `LOG_LEVEL` in `.env` (`DEBUG`, `INFO`, etc.)
