# Stock Classification Backend

REST API that exposes endpoints by querying the database. Uses FastAPI, SQLAlchemy, and a structured logger.

## Setup

### 1. Virtual environment

```bash
cd stock-classification-backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Config

Copy env example and edit if needed:

```bash
cp .env.example .env
```

Defaults use SQLite (`sqlite:///./stock.db`). For PostgreSQL set:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/stock_db
```

(Then install: `pip install databases[postgresql] asyncpg` and switch engine to async if desired.)

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

## Project layout

- `app/` – application package  
  - `core/` – config (`config.py`), logger (`logger.py`)  
  - `database.py` – SQLAlchemy engine, session, `get_db_session`  
  - `models/` – SQLAlchemy models (e.g. `Stock`)  
  - `schemas/` – Pydantic request/response schemas  
  - `routers/` – REST routes (e.g. `/api/stocks`)  
  - `main.py` – FastAPI app and lifespan  

## REST endpoints

### Stocks (example)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stocks/` | List stocks (query params: `skip`, `limit`, `sector`, `symbol`) |
| GET | `/api/stocks/{id}` | Get one stock |
| POST | `/api/stocks/` | Create stock |
| PATCH | `/api/stocks/{id}` | Update stock |
| DELETE | `/api/stocks/{id}` | Delete stock |

### Classification (read-only, schema: classification)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/classification/dropdown-data` | All four lists in one response (for React 4-dropdown UI) |
| GET | `/api/classification/macro-economic-sectors` | List macro economic sectors |
| GET | `/api/classification/macro-economic-sectors/{mes_code}` | Get one by code |
| GET | `/api/classification/sectors` | List sectors (optional `?mes_code=`) |
| GET | `/api/classification/sectors/{sect_code}` | Get one by code |
| GET | `/api/classification/industries` | List industries (optional `?sect_code=`) |
| GET | `/api/classification/industries/{ind_code}` | Get one by code |
| GET | `/api/classification/basic-industries` | List basic industries (optional `?ind_code=`, `skip`, `limit`) |
| GET | `/api/classification/basic-industries/{basic_ind_code}` | Get one by code |

**Seed classification data** (from CSVs in `temp/`):

```bash
# From project root, after first run (tables created)
python -m scripts.seed_classification
```

Requires classification tables to exist (start the app once). Uses PostgreSQL schema `classification`; for SQLite the schema is handled by SQLAlchemy (see docs).

## Logger

Use the shared logger in your modules:

```python
from app.core.logger import get_logger

logger = get_logger(__name__)
logger.info("message")
```

Log level is controlled by `LOG_LEVEL` in `.env` (e.g. `DEBUG`, `INFO`).
