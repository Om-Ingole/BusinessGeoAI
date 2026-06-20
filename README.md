# GeoIQ India — Location Intelligence Platform

A free, open-source alternative to GeoIQ / Placer.ai built specifically for India. Enter any Indian address, pin code, or GPS coordinates to instantly generate a comprehensive 360° site analysis report — covering footfall proxies, demographics, air quality, crime statistics, nearby hospitals/schools/transport, airport distances, and top business sectors. No paid APIs. No Google Maps.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Screenshots / Layout](#screenshots--layout)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Installation & Setup](#installation--setup)
7. [Running the App](#running-the-app)
8. [How to Use](#how-to-use)
9. [Viability Score Explained](#viability-score-explained)
10. [Data Sources](#data-sources)
11. [API Reference](#api-reference)
12. [Environment Variables](#environment-variables)
13. [Adding Your Own CSV Data](#adding-your-own-csv-data)
14. [Known Limitations](#known-limitations)
15. [Extending the Platform](#extending-the-platform)

---

## What It Does

GeoIQ India gives you a **360° intelligence report for any location in India** in one click:

| Feature | What You Get |
|---|---|
| **Interactive Map** | Leaflet map with colour-coded POI markers — hospitals, schools, bus stops, railway stations, metro, offices, housing, pharmacies, banks, supermarkets |
| **Viability Score** | A weighted 0–10 composite score across 8 dimensions (footfall, transport, demographics, safety, air quality, business density, etc.) |
| **Live AQI** | Real-time air quality index from the nearest CPCB monitoring station via data.gov.in |
| **Crime Statistics** | NCRB district-level crime rate (per lakh population) with a 3-year trend bar chart |
| **Demographics** | Census population, urban/rural split, literacy rate, sex ratio, total workers |
| **Nearest Airports** | Up to 3 nearest airports with IATA codes and exact km distances (Haversine) |
| **Railway Stations** | Nearest 5 major railway stations with km distances |
| **MSME Business Sectors** | Top 8 business sectors in the district from UDYAM registration data |
| **Footfall Proxy** | OSM POI density score (0–100) as a footfall signal — no private data used |
| **Report Export** | Download the full analysis as JSON or print to PDF |
| **24hr Cache** | Repeat queries for the same location are served instantly from SQLite |

---

## Screenshots / Layout

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER:  GeoIQ India  [Search Bar — address / pin / lat,lon] [Export] │
├─────────────────┬───────────────────────────┬───────────────┤
│  LEFT PANEL     │  MAP (Leaflet)             │  RIGHT PANEL  │
│  - Viability    │  • Colour-coded POI markers│  - AQI gauge  │
│    Score gauge  │  • Radius circle overlay  │  - Crime chart│
│  - Footfall     │  • Popup cards on click   │  - Demographics│
│    proxy        │                           │  - Transport  │
│  - POI summary  │                           │    panel      │
│  - Airport list │                           │               │
├─────────────────┴───────────────────────────┴───────────────┤
│  BOTTOM:  MSME Business Sectors horizontal bar chart         │
└─────────────────────────────────────────────────────────────┘
```

**Map marker colours:**
- 🏥 Red — Hospitals & clinics
- 🏫 Blue — Schools, colleges, universities
- 🚌 Green — Bus stops
- 🚉 Orange — Railway stations
- 🚇 Purple — Metro stations
- 🏢 Violet — Corporate offices
- 🏠 Teal — Housing / apartments
- 💊 Pink — Pharmacies
- 🏦 Yellow — Banks & ATMs
- 🛒 Cyan — Supermarkets & malls

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| **Backend** | Python 3.11 + FastAPI | Async, auto-docs at `/docs` |
| **Frontend** | React 18 + Vite + TailwindCSS | HMR dev, utility-first CSS |
| **Map** | Leaflet.js via react-leaflet | Free, OpenStreetMap tiles, no API key |
| **Charts** | Recharts | Bar charts, pie charts, responsive |
| **Database** | SQLite + SQLAlchemy async + aiosqlite | Zero-config, file-based |
| **HTTP client** | httpx (async) | Concurrent external API calls |
| **Geocoding** | Nominatim (OpenStreetMap) | Free, no key, 1 req/sec limit |
| **POI** | Overpass API (OpenStreetMap) | Free, batched queries, 3 mirror failover |
| **AQI** | CPCB via data.gov.in | Free API key required |
| **Fonts** | Space Grotesk + Inter + JetBrains Mono | Via Google Fonts |

---

## Project Structure

```
location-intel/
│
├── backend/
│   ├── main.py                      # FastAPI app — CORS, lifespan, router registration
│   ├── database.py                  # SQLite engine + async session + init_db()
│   ├── models.py                    # SQLAlchemy ORM models
│   ├── schemas.py                   # Pydantic request/response schemas
│   ├── seed_data.py                 # Auto-seeds DB on startup with fallback data
│   ├── .env                         # Environment variables (API keys, DB URL)
│   ├── requirements.txt
│   │
│   ├── routers/
│   │   ├── location.py              # POST /api/analyze — core orchestration endpoint
│   │   ├── poi.py                   # GET /api/poi — raw POI query endpoint
│   │   ├── aqi.py                   # GET /api/aqi/{state} — AQI by state
│   │   └── airports.py              # GET /api/airports/nearest, /api/railway/nearest
│   │
│   ├── services/
│   │   ├── geocoder.py              # Nominatim geocoding + reverse geocoding
│   │   ├── overpass.py              # Overpass QL batched POI queries (3 mirrors)
│   │   ├── aqi_service.py           # CPCB data.gov.in AQI + nearest station
│   │   ├── static_data_service.py   # Airport, railway, census, crime, MSME queries
│   │   ├── cache_service.py         # SQLite 24hr cache (read/write/history)
│   │   └── score_service.py         # Viability score calculator (weighted 0–10)
│   │
│   ├── utils/
│   │   └── haversine.py             # Great-circle distance formula
│   │
│   └── data/                        # Optional: drop CSV files here to override fallback data
│       ├── railway_stations.csv
│       ├── airports.csv
│       ├── census_district.csv
│       ├── ncrb_crime.csv
│       └── msme_district.csv
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js               # Vite proxy: /api/* → http://localhost:8000
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── package.json
│   │
│   └── src/
│       ├── main.jsx                 # React root + Leaflet icon fix + QueryClient
│       ├── App.jsx                  # Main layout — header, panels, map, bottom row
│       ├── index.css                # CSS variables, Leaflet overrides, animations
│       │
│       ├── components/
│       │   ├── SearchBar.jsx        # Address / pin code / lat,lon input + radius picker
│       │   ├── MapView.jsx          # Leaflet map + POI markers + radius circle
│       │   ├── ScoreCard.jsx        # SVG arc gauge + dimension sub-score bars
│       │   ├── AqiWidget.jsx        # AQI value + gradient bar + category badge
│       │   ├── CrimeWidget.jsx      # Crime rate bar chart (3-year trend)
│       │   ├── DemographicsWidget.jsx  # Population pie + stat tiles
│       │   ├── TransportWidget.jsx  # Bus stops, railway, metro lists
│       │   ├── AirportWidget.jsx    # Nearest airports with IATA + distance
│       │   ├── MsmeWidget.jsx       # Horizontal bar chart — top business sectors
│       │   ├── PoiSummary.jsx       # POI count grid + nearest hospital callout
│       │   ├── FootfallWidget.jsx   # Footfall density score + total amenities
│       │   └── ReportExport.jsx     # JSON download + Print buttons
│       │
│       ├── hooks/
│       │   └── useLocationAnalysis.js  # React Query mutation for POST /api/analyze
│       │
│       └── utils/
│           ├── haversine.js         # Client-side distance utility
│           └── aqiColor.js          # AQI value → colour + label + Tailwind class
│
└── README.md
```

---

## Prerequisites

- **Python 3.11+** — `python --version`
- **Node.js 18+** — `node --version`
- **npm 9+** — `npm --version`
- Internet connection (for Nominatim, Overpass, and data.gov.in AQI API)

---

## Installation & Setup

### 1. Clone or download the project

```bash
cd D:\Agent-Projects        # or wherever you keep projects
# The project is already at: location-intel/
```

### 2. Backend setup

```bash
cd location-intel/backend

# Create a virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate           # Windows PowerShell / CMD
# source venv/bin/activate      # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

**Dependencies installed:**
- `fastapi` — web framework
- `uvicorn[standard]` — ASGI server
- `sqlalchemy[asyncio]` — async ORM
- `aiosqlite` — async SQLite driver
- `httpx` — async HTTP client
- `pydantic` — data validation
- `python-dotenv` — `.env` file loader
- `pandas` — CSV loading for seed data
- `alembic` — DB migrations (available but not required for basic run)

### 3. Frontend setup

```bash
cd location-intel/frontend
npm install
```

**Dependencies installed:**
- `react`, `react-dom` — UI framework
- `react-leaflet`, `leaflet` — interactive maps
- `recharts` — charts (bar, pie, responsive)
- `axios` — HTTP client
- `@tanstack/react-query` — server state management
- `tailwindcss`, `vite`, `@vitejs/plugin-react` — build tooling

### 4. (Optional) Get a free data.gov.in API key

The included demo key works but has low rate limits. For production use:

1. Go to [data.gov.in/user/register](https://data.gov.in/user/register)
2. Register for a free account
3. Copy your API key from your profile
4. Paste it into `backend/.env` as `DATA_GOV_API_KEY=your_key_here`

---

## Running the App

You need **two terminal windows** running simultaneously.

### Terminal 1 — Backend

```bash
cd location-intel/backend
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

uvicorn main:app --reload --port 8000
```

On first startup, the backend automatically:
- Creates the SQLite database (`location_intel.db`)
- Seeds it with 20 airports, 50 railway stations, 20 district census records, 16 crime records, 20 MSME sector entries

You should see:
```
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2 — Frontend

```bash
cd location-intel/frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

### Open the app

Navigate to **http://localhost:5173** in your browser.

---

## How to Use

### Searching a location

The search bar accepts three input formats:

| Format | Example |
|---|---|
| Full address | `Koregaon Park, Pune` |
| Locality + city | `Indiranagar, Bengaluru` |
| Pin code | `400050` |
| Landmark | `Connaught Place, New Delhi` |
| GPS coordinates | `18.5362, 73.8938` |

**Steps:**
1. Type an Indian address, pin code, or `lat, lon` in the search bar
2. Select the search radius from the dropdown (0.5 km / 1 km / 2 km / 5 km)
3. Click **Analyze**
4. Wait 15–30 seconds for the first query (subsequent queries for the same location are cached and return in under 1 second)

### Reading the dashboard

**Left panel — Score + POI summary**
- The SVG arc gauge shows the overall **Viability Score (0–10)**
  - Green (6.5–10): Good location
  - Amber (4–6.5): Average
  - Red (0–4): Poor
- Sub-score bars show each dimension's contribution
- The POI grid shows how many hospitals, schools, pharmacies, banks, bus stops, markets, offices, and housing complexes are within your chosen radius
- The nearest hospital callout appears below

**Map (centre)**
- Colour-coded markers for every POI category found within the radius
- A teal circle shows the exact search boundary
- A glowing teal dot marks your searched location
- Click any marker for a popup with the name, category, and distance

**Right panel — Live data widgets**
- **AQI widget** — Shows the nearest CPCB monitoring station's reading with a gradient bar and category label (Good / Satisfactory / Moderate / Poor / Very Poor / Severe)
- **Crime widget** — Bar chart of crimes per lakh population over the last 3 years for the matched district
- **Demographics widget** — Urban/rural pie chart, total population, literacy rate, sex ratio, total workers
- **Transport widget** — Lists the nearest bus stops, railway stations (from our 50-station database), and metro stations found in OSM

**Airport card (left panel)**
- Top 3 nearest airports with IATA codes and Haversine km distances

**Bottom row — MSME sectors**
- Horizontal bar chart showing the top business sectors (by enterprise count) in the district from UDYAM registration data

### Exporting results

- **Export JSON** — Downloads a full machine-readable report including all POI lists, scores, demographics, crime, AQI, airports, railway, and MSME data
- **Print** — Opens the browser print dialog; works well with "Save as PDF"

### Sample locations to try

The landing page shows 5 quick-select buttons:
- Koregaon Park, Pune
- Connaught Place, New Delhi
- Bandra West, Mumbai
- Indiranagar, Bengaluru
- T Nagar, Chennai

---

## Viability Score Explained

The overall score (0–10) is a **weighted average of 8 dimensions**, each scored independently:

| Dimension | Weight | How it's calculated |
|---|---|---|
| **Footfall Proxy** | 20% | Total OSM amenities in radius ÷ 5 (capped at 10) |
| **Transport Access** | 18% | Composite of bus stop count (40%) + nearest railway distance (60%) |
| **Demographics** | 15% | Literacy rate + urban percentage, each contributing up to 2.5 points |
| **POI Density** | 12% | Hospitals × 1.5 + Schools × 0.8 |
| **Crime Safety** | 12% | `10 − (crimes_per_lakh ÷ 50)`, inverted so lower crime = higher score |
| **Air Quality** | 10% | `10 − (AQI ÷ 40)`, inverted so cleaner air = higher score |
| **Business Density** | 8% | Total MSME enterprises in district ÷ 1000 (capped at 10) |
| **Growth Potential** | 5% | Static baseline of 7.0 for v1 (future: RERA + AMRUT signals) |

**Score interpretation:**

| Score | Meaning |
|---|---|
| 8.0 – 10.0 | Excellent — prime commercial / residential location |
| 6.5 – 7.9 | Good — well-served area with strong fundamentals |
| 4.0 – 6.4 | Average — adequate but with notable gaps |
| 0.0 – 3.9 | Poor — significant infrastructure or safety concerns |

---

## Data Sources

All data comes from **free, publicly accessible sources only**. No paid APIs are used.

### Live / API sources

| Data | Source | Notes |
|---|---|---|
| Geocoding | [Nominatim (OpenStreetMap)](https://nominatim.openstreetmap.org) | Free, no key, 1 req/sec rate limit |
| POI (hospitals, schools, transport, etc.) | [Overpass API (OpenStreetMap)](https://overpass-api.de) | Free, 3 mirror failover for reliability |
| Air Quality Index | [CPCB via data.gov.in](https://api.data.gov.in) | Free key required (demo key included) |

### Static / pre-seeded data

All static datasets are **baked into `seed_data.py`** as fallback data so the app works out of the box without any downloads. You can replace them with full CSVs for production use.

| Data | Records included | Source |
|---|---|---|
| Airports | 20 major airports (DEL, BOM, BLR, MAA, HYD, PNQ, AMD, JAI, CCU, COK, and 10 more) | AAI via data.gov.in |
| Railway stations | 50 major stations across India | Indian Railways via data.gov.in |
| Census demographics | 20 major districts (2011 Primary Census Abstract) | Census India via data.gov.in |
| Crime statistics | 16 district records, 2–3 years each (NCRB) | NCRB via data.gov.in |
| MSME business sectors | 20 district–sector entries (UDYAM) | Ministry of MSME via data.gov.in |

### AQI colour coding

| AQI Value | Category | Colour |
|---|---|---|
| 0 – 50 | Good | Green |
| 51 – 100 | Satisfactory | Lime |
| 101 – 200 | Moderate | Amber |
| 201 – 300 | Poor | Orange |
| 301 – 400 | Very Poor | Red |
| 400+ | Severe | Purple |

---

## API Reference

The FastAPI backend auto-generates interactive docs at **http://localhost:8000/docs**

### POST `/api/analyze`

The main endpoint. Accepts an address or coordinates and returns the full report.

**Request body:**
```json
{
  "query": "Koregaon Park, Pune",
  "radius_km": 1,
  "business_type": "retail"
}
```

Or with coordinates directly:
```json
{
  "lat": 18.5362,
  "lon": 73.8938,
  "radius_km": 2
}
```

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | if no lat/lon | — | Indian address, pin code, or place name |
| `lat` | float | if no query | — | Latitude |
| `lon` | float | if no query | — | Longitude |
| `radius_km` | float | no | 1.0 | Search radius: 0.5, 1, 2, or 5 |
| `business_type` | string | no | "retail" | For future use — retail, food, clinic, office |

**Response (abbreviated):**
```json
{
  "location": {
    "lat": 18.5362,
    "lon": 73.8938,
    "display_address": "Koregaon Park, Pune, Maharashtra",
    "district": "Pune",
    "state": "Maharashtra",
    "pin_code": "411001"
  },
  "viability_score": 7.1,
  "score_breakdown": {
    "footfall_proxy": 8.2,
    "transport_access": 5.2,
    "demographics": 9.2,
    "poi_density": 10.0,
    "crime_safety": 6.1,
    "air_quality": 5.0,
    "business_density": 10.0,
    "growth_potential": 7.0
  },
  "demographics": { "total_population": 9429408, "literacy_rate": 86.15, ... },
  "aqi": { "station": "Pune", "pollutant_avg": 85.0, "aqi_category": "Satisfactory", ... },
  "crime": { "latest_crimes_per_lakh": 195.0, "records": [...] },
  "poi": {
    "hospitals": [{ "name": "Ruby Hall Clinic", "distance_km": 0.4, ... }],
    "schools": [...],
    "bus_stops": [...],
    "railway": [...],
    "metro": [...],
    "corporates": [...],
    "housing": [...],
    "pharmacies": [...],
    "banks": [...],
    "supermarkets": [...]
  },
  "airports": [{ "name": "Pune Airport", "iata_code": "PNQ", "distance_km": 5.78 }],
  "nearest_railway": { "station_name": "Pune Junction", "distance_km": 2.22 },
  "railway_stations": [...],
  "msme_sectors": [{ "sector_name": "Retail Trade", "enterprise_count": 35000 }, ...],
  "footfall_proxy": { "poi_density_score": 82.0, "total_amenities": 41 },
  "generated_at": "2026-06-20T12:00:00Z"
}
```

### GET `/api/poi`

Fetch POI for a location without running the full analysis.

```
GET /api/poi?lat=18.5362&lon=73.8938&radius=1&types=hospitals,schools,bus_stops
```

| Param | Required | Description |
|---|---|---|
| `lat` | yes | Latitude |
| `lon` | yes | Longitude |
| `radius` | no (default 1) | Radius in km (0.5–5) |
| `types` | no | Comma-separated: hospitals, schools, bus_stops, railway, metro, corporates, housing, pharmacies, banks, supermarkets |

### GET `/api/aqi/{state}`

```
GET /api/aqi/Maharashtra?lat=18.5362&lon=73.8938
```

Returns the nearest CPCB monitoring station's AQI for the given state.

### GET `/api/airports/nearest`

```
GET /api/airports/nearest?lat=18.5362&lon=73.8938&limit=3
```

### GET `/api/railway/nearest`

```
GET /api/railway/nearest?lat=18.5362&lon=73.8938&limit=5
```

### GET `/api/reports/history`

Returns the last 20 analyzed locations from cache:
```
GET /api/reports/history
```

### GET `/health`

```
GET /health
→ { "status": "ok", "service": "India Location Intelligence API" }
```

---

## Environment Variables

Located at `backend/.env`:

```env
# AQI data from CPCB via data.gov.in
# Get your free key at: https://data.gov.in/user/register
DATA_GOV_API_KEY=579b464db66ec23bdd000001cdd3946e44ce4aab825uf591

# SQLite database file path (relative to backend/)
DATABASE_URL=sqlite+aiosqlite:///./location_intel.db

# Allowed frontend origins for CORS
CORS_ORIGINS=http://localhost:5173

# How long to cache analysis results
CACHE_TTL_HOURS=24
```

---

## Adding Your Own CSV Data

The app ships with fallback data covering 20 major Indian cities/districts. To get data for more districts, download CSVs from [data.gov.in](https://data.gov.in) and place them in `backend/data/`. The seed script will prefer CSV files over the hardcoded fallback.

### `backend/data/railway_stations.csv`

```csv
station_name,station_code,state,division,zone,latitude,longitude
New Delhi,NDLS,Delhi,Delhi,NR,28.6408,77.2219
```

Required columns: `station_name`, `state`, `latitude`, `longitude`
Optional: `station_code`, `division`, `zone`

Download from: [data.gov.in/catalog/railway-station](https://www.data.gov.in/catalog/railway-station)

### `backend/data/airports.csv`

```csv
name,city,iata_code,state,latitude,longitude,is_operational
Indira Gandhi International Airport,New Delhi,DEL,Delhi,28.5562,77.1000,True
```

Required columns: `name`, `latitude`, `longitude`
Optional: `city`, `iata_code`, `state`, `is_operational`

### `backend/data/census_district.csv`

```csv
state,district,total_population,urban_population,rural_population,literacy_rate,sex_ratio,workers_total
Maharashtra,Pune,9429408,7761886,1667522,86.15,915,3986000
```

Download from: [data.gov.in/catalog/census-india](https://www.data.gov.in/catalog/census-india)

### `backend/data/ncrb_crime.csv`

```csv
year,state,district,total_ipc_crimes,crimes_per_lakh,property_crimes,economic_offences
2022,Maharashtra,Pune,48000,195.0,15000,5000
```

Download from: [data.gov.in/keywords/NCRB](https://www.data.gov.in/keywords/NCRB)

### `backend/data/msme_district.csv`

```csv
state,district,nic_code,sector_name,enterprise_count,micro_count,small_count
Maharashtra,Pune,62,IT & Software,15200,12000,2800
```

Download from: [data.gov.in/catalog/udyam-registration-msme-registration](https://www.data.gov.in/catalog/udyam-registration-msme-registration)

**To reload after adding CSVs**, delete the existing database and restart:

```bash
# Windows
del backend\location_intel.db
uvicorn main:app --reload --port 8000

# macOS / Linux
rm backend/location_intel.db
uvicorn main:app --reload --port 8000
```

---

## Known Limitations

**Overpass API rate limits**
The free Overpass API enforces per-IP rate limits. The first analysis for a location may return incomplete POI results if Overpass throttles the requests (HTTP 429). The app uses 3 mirror servers and retry logic to mitigate this, but on heavy testing days (many requests from the same IP) some POI categories may return 0. Results are cached for 24 hours, so subsequent queries for the same location are always fast and complete.

**AQI station coverage**
Not every district has a CPCB monitoring station. The app finds the nearest station within the matched state. If the nearest station is far away, the AQI reading may not reflect local conditions.

**Census data is from 2011**
The demographic data is from India's most recent publicly available census. The 2021 census data was delayed; when released on data.gov.in, you can drop the updated CSV in `backend/data/`.

**District name matching is fuzzy**
The app matches district names from the geocoded address against the static datasets using a prefix match. For districts with unusual or long names, the match may fall back to the first record in the state.

**Nominatim rate limit**
Nominatim (OpenStreetMap's geocoder) enforces a strict 1 request/second limit. The app includes the required delay. Do not modify this delay or your IP may be temporarily blocked.

**No real footfall data**
The footfall proxy is based on OSM POI density — it correlates with activity but is not actual visit data. Google Maps Popular Times, Jio data, or mobile location data would provide actual footfall but are either paid or proprietary.

---

## Extending the Platform

The codebase is structured to make additions straightforward:

**Add a new data dimension:**
1. Create a service in `backend/services/`
2. Call it in `backend/routers/location.py` alongside the other `asyncio.gather()` calls
3. Add the result to the response dict
4. Create a new widget component in `frontend/src/components/`
5. Add it to `frontend/src/App.jsx`

**Add a new static dataset:**
1. Add a model in `backend/models.py`
2. Add seed data in `backend/seed_data.py`
3. Add a query function in `backend/services/static_data_service.py`

**Change the search radius options:**
Edit the `<select>` options in `frontend/src/components/SearchBar.jsx` and the `radius_km` field validator in `backend/schemas.py`.

**Change cache TTL:**
Set `CACHE_TTL_HOURS` in `backend/.env`.

**Use PostgreSQL instead of SQLite:**
Change `DATABASE_URL` in `.env` to a PostgreSQL connection string and install `asyncpg`:
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/geoiq
pip install asyncpg
```

**Deploy to production:**
- Backend: any Python host (Railway, Render, Fly.io, EC2) — set `CORS_ORIGINS` to your frontend domain
- Frontend: `npm run build` then deploy `dist/` to Vercel, Netlify, or Cloudflare Pages
- Database: switch to PostgreSQL for multi-instance deployments

---

## License

This project uses exclusively free and open data sources:
- OpenStreetMap data © OpenStreetMap contributors (ODbL)
- data.gov.in — Government of India Open Government Data Platform (NITI Aayog, NIC)
- CPCB air quality data — Central Pollution Control Board, India
- NCRB crime statistics — National Crime Records Bureau, India
- Census data — Office of the Registrar General & Census Commissioner, India
