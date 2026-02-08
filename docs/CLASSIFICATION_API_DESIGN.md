# Classification API – Design (schema: classification)

## 1. Schema overview

Four tables in hierarchy (parent → child):

| Table                     | PK / Code       | Name column              | Parent FK   | Rows (from CSVs) |
|---------------------------|-----------------|--------------------------|-------------|-------------------|
| **macro_economic_sectors**| `mes_code`      | `macro_economic_sector`   | —           | 12                |
| **sectors**              | `sect_code`     | `sector_name`            | `mes_code`  | 23                |
| **industries**            | `ind_code`      | `industry_name`          | `sect_code`| 61                |
| **basic_industries**      | `basic_ind_code`| `basic_industry_name`    | `ind_code`  | 198               |

**Relationship chain:**  
`macro_economic_sectors` → `sectors` → `industries` → `basic_industries`

---

## 2. Exposing the code (primary key) in the response

**Recommendation: Yes, expose the code in the response.**

- These codes (`mes_code`, `sect_code`, `ind_code`, `basic_ind_code`) are **business keys**, not internal surrogate IDs. They are stable, human-readable, and already used in the hierarchy (e.g. `sect_code` in industries).
- The **React UI needs the code** to:
  - Know which option the user selected (e.g. `IN01` for “Commodities”).
  - Filter the next dropdown (e.g. sectors where `mes_code = IN01`).
  - Submit the final “classified stock” with the four codes.
- Hiding the code would force the UI to use something else (e.g. internal DB id), which adds complexity and doesn’t add security for this read-only reference data.

**When to avoid exposing a key:** If you had a surrogate auto-increment `id` used only internally, you could omit it from the public API and expose only the business code. Here the code *is* the primary and business identifier, so exposing it is the right choice.

---

## 3. One API vs four APIs for the 4 dropdowns (React UI)

**Recommendation: Prefer one API that returns all data needed for the four cascading dropdowns.**

| Approach | Pros | Cons |
|----------|------|------|
| **Four separate APIs** | Small per-call payloads; load children only when parent is selected. | 4 round-trips (or 1 + 3 on user interaction); loading state for each dropdown; more frontend logic. |
| **One “dropdown data” API** | **Single backend call**; no loading between dropdowns; frontend filters client-side; simpler React state; works offline after first load. | Slightly larger initial payload (~300 small objects), which is negligible. |

For a page with four cascading dropdowns (Macro → Sector → Industry → Basic industry), **one API** keeps the UI simple: one fetch on mount, store the result, then derive each dropdown’s options from the selected parent (all client-side).

**Proposed endpoint for the UI:**

- **`GET /api/classification/dropdown-data`**  
  Returns all four lists in one response (flat structure). The UI uses the **code** in each item to filter and to submit the final classification.

Optional: keep the four granular endpoints for deep links, admin tools, or when you need only one level.

---

## 4. API base and resource naming

- **Base path:** `/api/classification`
- **Resource paths (plural, kebab-case):**
  - `macro-economic-sectors`
  - `sectors`
  - `industries`
  - `basic-industries`
- **Dropdown UI:** `GET /api/classification/dropdown-data` (see §5.0 and §6.0)

---

## 5. Endpoints

### 5.0 Dropdown data (single call for React 4-dropdown UI)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/classification/dropdown-data` | Returns all four lists in one response for populating the four cascading dropdowns. |

No query params. Response shape: flat object with four arrays (see §6.0).

---

### 5.1 Macro Economic Sectors

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/classification/macro-economic-sectors` | List all macro economic sectors |
| GET | `/api/classification/macro-economic-sectors/{mes_code}` | Get one by `mes_code` |

### 5.2 Sectors

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/classification/sectors` | List all sectors (optional filter by `mes_code`) |
| GET | `/api/classification/sectors/{sect_code}` | Get one by `sect_code` |

**Query (optional):** `mes_code` – filter sectors by parent macro economic sector.

### 5.3 Industries

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/classification/industries` | List all industries (optional filter by `sect_code`) |
| GET | `/api/classification/industries/{ind_code}` | Get one by `ind_code` |

**Query (optional):** `sect_code` – filter industries by parent sector.

### 5.4 Basic Industries

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/classification/basic-industries` | List all basic industries (optional filter by `ind_code`) |
| GET | `/api/classification/basic-industries/{basic_ind_code}` | Get one by `basic_ind_code` |

**Query (optional):** `ind_code` – filter basic industries by parent industry.

### 5.5 Pagination (optional, same for list endpoints)

- `skip` (default 0), `limit` (default 50, max 200) for list endpoints.

---

## 6. Sample requests and responses

### 6.0 Dropdown data (single call for React UI)

**Request:**

```http
GET /api/classification/dropdown-data
```

**Response:** `200 OK`

```json
{
  "macro_economic_sectors": [
    { "mes_code": "IN01", "macro_economic_sector": "Commodities" },
    { "mes_code": "IN02", "macro_economic_sector": "Consumer Discretionary" }
  ],
  "sectors": [
    { "sect_code": "IN0101", "sector_name": "Chemicals", "mes_code": "IN01" },
    { "sect_code": "IN0102", "sector_name": "Construction Materials", "mes_code": "IN01" }
  ],
  "industries": [
    { "ind_code": "IN010101", "industry_name": "Chemicals & Petrochemicals", "sect_code": "IN0101" },
    { "ind_code": "IN010102", "industry_name": "Fertilizers & Agrochemicals", "sect_code": "IN0101" }
  ],
  "basic_industries": [
    {
      "basic_ind_code": "IN010101001",
      "basic_industry_name": "Commodity Chemicals",
      "definition": "Manufacturers of basic and industrial chemicals...",
      "ind_code": "IN010101"
    }
  ]
}
```

**React usage:** On mount, call this once and store the result. For each dropdown:
- **Dropdown 1:** options = `macro_economic_sectors`; value = `mes_code`; label = `macro_economic_sector`.
- **Dropdown 2:** options = `sectors.filter(s => s.mes_code === selectedMesCode)`; value = `sect_code`; label = `sector_name`.
- **Dropdown 3:** options = `industries.filter(i => i.sect_code === selectedSectCode)`; value = `ind_code`; label = `industry_name`.
- **Dropdown 4:** options = `basic_industries.filter(b => b.ind_code === selectedIndCode)`; value = `basic_ind_code`; label = `basic_industry_name`.

Submit the classified stock with the four selected codes (e.g. `mes_code`, `sect_code`, `ind_code`, `basic_ind_code`).

---

### 6.1 Macro Economic Sectors

**Request:** list all

```http
GET /api/classification/macro-economic-sectors
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "mes_code": "IN01",
      "macro_economic_sector": "Commodities"
    },
    {
      "mes_code": "IN02",
      "macro_economic_sector": "Consumer Discretionary"
    }
  ],
  "count": 12
}
```

**Request:** get one by code

```http
GET /api/classification/macro-economic-sectors/IN01
```

**Response:** `200 OK`

```json
{
  "mes_code": "IN01",
  "macro_economic_sector": "Commodities"
}
```

**Response:** `404 Not Found` (invalid code)

```json
{
  "detail": "Macro economic sector not found"
}
```

---

### 6.2 Sectors

**Request:** list all

```http
GET /api/classification/sectors
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "sect_code": "IN0101",
      "sector_name": "Chemicals",
      "mes_code": "IN01"
    },
    {
      "sect_code": "IN0102",
      "sector_name": "Construction Materials",
      "mes_code": "IN01"
    }
  ],
  "count": 23
}
```

**Request:** list sectors for a macro economic sector

```http
GET /api/classification/sectors?mes_code=IN01
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "sect_code": "IN0101",
      "sector_name": "Chemicals",
      "mes_code": "IN01"
    },
    {
      "sect_code": "IN0102",
      "sector_name": "Construction Materials",
      "mes_code": "IN01"
    },
    {
      "sect_code": "IN0103",
      "sector_name": "Metals & Mining",
      "mes_code": "IN01"
    },
    {
      "sect_code": "IN0104",
      "sector_name": "Forest Materials",
      "mes_code": "IN01"
    }
  ],
  "count": 4
}
```

**Request:** get one by code

```http
GET /api/classification/sectors/IN0101
```

**Response:** `200 OK`

```json
{
  "sect_code": "IN0101",
  "sector_name": "Chemicals",
  "mes_code": "IN01"
}
```

---

### 6.3 Industries

**Request:** list all

```http
GET /api/classification/industries
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "ind_code": "IN010101",
      "industry_name": "Chemicals & Petrochemicals",
      "sect_code": "IN0101"
    },
    {
      "ind_code": "IN010102",
      "industry_name": "Fertilizers & Agrochemicals",
      "sect_code": "IN0101"
    }
  ],
  "count": 61
}
```

**Request:** list industries for a sector

```http
GET /api/classification/industries?sect_code=IN0101
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "ind_code": "IN010101",
      "industry_name": "Chemicals & Petrochemicals",
      "sect_code": "IN0101"
    },
    {
      "ind_code": "IN010102",
      "industry_name": "Fertilizers & Agrochemicals",
      "sect_code": "IN0101"
    }
  ],
  "count": 2
}
```

**Request:** get one by code

```http
GET /api/classification/industries/IN010101
```

**Response:** `200 OK`

```json
{
  "ind_code": "IN010101",
  "industry_name": "Chemicals & Petrochemicals",
  "sect_code": "IN0101"
}
```

---

### 6.4 Basic Industries

**Request:** list all (with optional pagination)

```http
GET /api/classification/basic-industries?skip=0&limit=10
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "basic_ind_code": "IN010101001",
      "basic_industry_name": "Commodity Chemicals",
      "definition": "Manufacturers of basic and industrial chemicals like synthetic fibres, films, organic and inorganic chemicals etc.",
      "ind_code": "IN010101"
    },
    {
      "basic_ind_code": "IN010101002",
      "basic_industry_name": "Specialty Chemicals",
      "definition": "Manufacturers of chemicals used in the manufacture of a variety of products, like fine chemicals, additives, advanced polymers, explosives, adhesives, printing inks, sealants, dyes, pigments, coatings etc.",
      "ind_code": "IN010101"
    }
  ],
  "count": 10,
  "total": 198
}
```

**Request:** list basic industries for an industry

```http
GET /api/classification/basic-industries?ind_code=IN010101
```

**Response:** `200 OK`

```json
{
  "data": [
    {
      "basic_ind_code": "IN010101001",
      "basic_industry_name": "Commodity Chemicals",
      "definition": "Manufacturers of basic and industrial chemicals like synthetic fibres, films, organic and inorganic chemicals etc.",
      "ind_code": "IN010101"
    },
    {
      "basic_ind_code": "IN010101002",
      "basic_industry_name": "Specialty Chemicals",
      "definition": "Manufacturers of chemicals used in the manufacture of a variety of products...",
      "ind_code": "IN010101"
    }
  ],
  "count": 9,
  "total": 9
}
```

**Request:** get one by code

```http
GET /api/classification/basic-industries/IN010101001
```

**Response:** `200 OK`

```json
{
  "basic_ind_code": "IN010101001",
  "basic_industry_name": "Commodity Chemicals",
  "definition": "Manufacturers of basic and industrial chemicals like synthetic fibres, films, organic and inorganic chemicals etc.",
  "ind_code": "IN010101"
}
```

---

## 7. Response envelope (list endpoints)

For **list** endpoints, use a consistent envelope:

| Field   | Type   | Description |
|---------|--------|-------------|
| `data`  | array  | List of items for the resource |
| `count` | number | Number of items in `data` (after filters and pagination) |
| `total` | number | (Optional) Total matching items before pagination; useful for basic-industries |

For **get-by-code** endpoints, return the single object directly (no `data` wrapper).

---

## 8. Error responses

| Status | When |
|--------|------|
| 400 | Invalid query (e.g. invalid code format). |
| 404 | Resource not found for the given code. |
| 500 | Server error (body: `{"detail": "..."}`). |

---

## 9. Optional: hierarchical response

If you want “drill-down” in one call, we can add an optional query param (e.g. `embed=children`) or dedicated endpoints:

- **Example:** `GET /api/classification/macro-economic-sectors/IN01?embed=sectors`  
  → returns macro sector IN01 plus nested list of its sectors.

- **Example:** `GET /api/classification/industries/IN010101?embed=basic_industries`  
  → returns industry IN010101 plus nested list of basic industries.

This can be added in a second phase after the flat design above is implemented.

---

## 10. Summary

| Resource / use case   | Endpoint / path                                                       | Notes |
|------------------------|-----------------------------------------------------------------------|-------|
| **Dropdown UI (single call)** | `GET /api/classification/dropdown-data`                               | Returns all four lists; React populates 4 cascading dropdowns from one response. |
| Macro economic sectors | List: `GET /api/classification/macro-economic-sectors`; get: `.../{mes_code}` | — |
| Sectors                | List: `GET /api/classification/sectors`; get: `.../{sect_code}`      | Filter: `mes_code` |
| Industries             | List: `GET /api/classification/industries`; get: `.../{ind_code}`     | Filter: `sect_code` |
| Basic industries       | List: `GET /api/classification/basic-industries`; get: `.../{basic_ind_code}` | Filter: `ind_code` |

All tables live in schema **classification**. No create/update/delete in this design; read-only API. Exposing the **code** in responses is recommended (see §2). Once you confirm this design, we can implement it in code.
