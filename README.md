# BusinessGeo AI — Location Intelligence Platform

AI-powered location intelligence for business decisions. Enter any Indian address, pin code, landmark, or GPS coordinates to instantly generate a 360° site analysis — covering footfall signals, nearby businesses, transport access, air quality, crime, demographics, and AI recommendations. Powered by Google Maps Platform + OpenStreetMap, with a built-in Gemini-powered chat assistant.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [UI Layout](#ui-layout)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Prerequisites](#prerequisites)
6. [Installation & Setup](#installation--setup)
7. [Running the App](#running-the-app)
8. [How to Use](#how-to-use)
9. [Google Maps Platform Setup](#google-maps-platform-setup)
10. [AI Chat Setup (BusinessGeo Assistant)](#ai-chat-setup-businessgeo-assistant)
11. [Viability Score Explained](#viability-score-explained)
12. [Data Sources](#data-sources)
13. [API Reference](#api-reference)
14. [Environment Variables](#environment-variables)
15. [Adding Your Own CSV Data](#adding-your-own-csv-data)
16. [Known Limitations](#known-limitations)
17. [Extending the Platform](#extending-the-platform)

---

## What It Does

BusinessGeo AI gives you a **360° intelligence report for any location in India** in one search:

| Feature | What You Get |
|---|---|
| **Interactive Map** | Leaflet map with color-coded circular POI markers, category filter chips, and detailed popups (name, provider, rating, address, Google Maps link) |
| **Viability Score** | Animated 0–10 composite score across 8 dimensions with confidence rating and band label (Excellent / Good / Average / Poor) |
| **AI Insights** | Deterministic risk/opportunity analysis — rules fire on AQI, crime, transport, POI mix, and demographics; no LLM required |
| **BusinessGeo Assistant** | Gemini-powered chat: ask about the location, compare areas, evaluate business fit, find competitors, check transit access |
| **Google Places Data** | Ratings, review counts, business status, and Google Maps links when a Google Maps API key is configured |
| **Live AQI** | Real-time air quality from the nearest CPCB monitoring station via data.gov.in |
| **Crime Statistics** | NCRB district-level crime rate (per lakh population) with color-coded severity band |
| **Demographics** | Census population, urban %, literacy rate, sex ratio, total workers |
| **Transport Access** | Bus stops, metro stations, nearest railway station distance |
| **Nearest Airports** | Up to 3 airports with IATA codes and exact km distances |
| **MSME Business Sectors** | Top business sectors in the district from UDYAM registration data |
| **Business Type Filter** | Select Retail, Cafe, Clinic, etc. to tailor the analysis context |
| **Report Export** | Download as `businessgeo-report-{location}-{date}.json` or print to PDF |
| **24hr Cache** | Repeat queries for the same location are served instantly from SQLite |

---

## UI Layout

BusinessGeo AI uses a three-panel dashboard:

```
┌──────────────────────────────────────────────────────────────────────┐
│ HEADER                                                               │
│ [BusinessGeo AI]  [Search bar]  [Radius]  [Business Type]           │
│                                           [Export]  [Provider badge] │
├──────────────────┬──────────────────────────────┬───────────────────┤
│ LEFT PANEL       │ CENTER MAP                    │ RIGHT PANEL       │
│                  │                               │                   │
│ Viability Score  │  Interactive Leaflet map      │ BusinessGeo       │
│ (animated, 0-10) │                               │ Assistant (chat)  │
│ Score breakdown  │  Color-coded POI markers      │                   │
│                  │  Category filter chips        │ AQI               │
│ AI Insights      │  (top-right, toggleable)      │ Crime Safety      │
│ - Summary        │                               │ Demographics      │
│ - Best Fit       │  Pulsing center marker        │ Transport         │
│ - Opportunities  │                               │ Airports          │
│ - Risks          │  Toolbar: radius / places /   │ MSME Sectors      │
│                  │  provider badge (bottom)      │                   │
│ POI Summary      │                               │                   │
│ Footfall Score   │                               │                   │
└──────────────────┴──────────────────────────────┴───────────────────┘
```

**Map marker colors:** Red (hospitals) · Orange (pharmacies) · Blue (schools) · Purple (banks) · Cyan (transit) · Yellow-green (supermarkets) · Amber (corporates) · Slate (housing)

Clicking a marker shows: name, category, provider badge (Google/OSM), distance, star rating + review count (Google only), business status, address, and a Google Maps deep link.

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| **Backend** | Python 3.11 + FastAPI | Async, auto-docs at `/docs` |
| **Frontend** | React 18 + Vite + TailwindCSS | HMR dev, utility-first CSS |
| **Icons** | lucide-react | Clean SVG icons throughout |
| **Map** | Leaflet.js via react-leaflet | OSM tiles, no API key needed |
| **Database** | SQLite + SQLAlchemy async + aiosqlite | Zero-config, file-based |
| **HTTP client** | httpx (async) | Concurrent external API calls |
| **Geocoding** | Nominatim (OSM) or Google Geocoding API | Hybrid fallback chain |
| **POI** | Overpass API (OSM) or Google Places API (New) | Concurrent batched queries |
| **AI Chat** | Google ADK + Gemini (`gemini-2.0-flash`) | Optional; returns 503 if unconfigured |
| **AQI** | CPCB via data.gov.in | Free API key required |

---

## Project Structure

```
BusinessGeoAI/
│
├── backend/
│   ├── main.py                          # FastAPI app, CORS, lifespan, router registration
│   ├── database.py                      # SQLite engine + async session
│   ├── models.py                        # ORM: LocationCache, ChatSession, ChatMessage, ChatToolCall
│   ├── schemas.py                       # Pydantic v2 request/response schemas
│   ├── seed_data.py                     # Auto-seeds DB on startup
│   ├── .env.example                     # Template — copy to .env and fill keys
│   ├── requirements.txt
│   │
│   ├── routers/
│   │   ├── location.py                  # POST /api/analyze
│   │   ├── poi.py                       # GET /api/poi
│   │   ├── aqi.py                       # GET /api/aqi/{state}
│   │   ├── airports.py                  # GET /api/airports/nearest, /api/railway/nearest
│   │   └── chat.py                      # POST /api/chat/session, /api/chat/message
│   │
│   ├── services/
│   │   ├── analysis_service.py          # Core orchestration — 7 concurrent tasks
│   │   ├── agent_service.py             # Deterministic insights (no LLM required)
│   │   ├── score_service.py             # Returns (score, breakdown, data_confidence)
│   │   ├── cache_service.py             # SQLite 24hr cache
│   │   ├── aqi_service.py               # CPCB AQI
│   │   ├── geocoder.py                  # Nominatim
│   │   ├── overpass.py                  # Overpass QL, 3 mirrors, concurrent batches
│   │   ├── static_data_service.py       # Airports, railway, census, crime, MSME
│   │   └── location_providers/
│   │       ├── base.py                  # Abstract provider interface
│   │       ├── osm.py                   # Nominatim + Overpass (always available)
│   │       ├── google_maps.py           # Google Geocoding + Places API (New) + Routes
│   │       └── hybrid.py               # Google-first, OSM fallback
│   │
│   ├── agents/
│   │   ├── location_agent.py            # ADK Runner singleton (lazy init)
│   │   ├── tools.py                     # 6 ADK tools: analyze, compare, business_fit, etc.
│   │   └── session_store.py             # SQLite chat session metadata
│   │
│   ├── utils/haversine.py
│   └── tests/
│       ├── conftest.py
│       ├── test_providers.py
│       ├── test_scoring.py
│       ├── test_insights.py
│       └── test_chat.py
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js                   # Proxy: /api/* → http://127.0.0.1:8000
│   ├── tailwind.config.js               # CSS variable-mapped color tokens
│   ├── package.json
│   │
│   └── src/
│       ├── App.jsx                      # 3-panel layout, businessType state, chat update handler
│       ├── index.css                    # Design-system CSS vars (navy/teal palette)
│       │
│       ├── components/
│       │   ├── Header.jsx               # Brand, search, radius, business type, provider badge
│       │   ├── SearchBar.jsx
│       │   ├── MapView.jsx              # Leaflet map, circular markers, filter chips, popups
│       │   ├── ScoreCard.jsx            # Animated count-up score, breakdown bars
│       │   ├── AgentInsightsWidget.jsx  # AI summary, best fit, opportunities, risks
│       │   ├── ChatPanel.jsx            # BusinessGeo Assistant (lazy-loaded)
│       │   ├── WidgetCard.jsx           # Shared card shell for all right-panel widgets
│       │   ├── AqiWidget.jsx
│       │   ├── CrimeWidget.jsx
│       │   ├── DemographicsWidget.jsx
│       │   ├── TransportWidget.jsx
│       │   ├── AirportWidget.jsx
│       │   ├── MsmeWidget.jsx
│       │   ├── FootfallWidget.jsx
│       │   ├── PoiSummary.jsx
│       │   ├── ReportExport.jsx
│       │   └── AnalysisProgress.jsx     # Step-by-step loading with progress bar
│       │
│       ├── hooks/
│       │   ├── useLocationAnalysis.js   # React Query mutation for POST /api/analyze
│       │   └── useChat.js               # Chat session state (create, send, reset)
│       │
│       └── utils/
│           ├── haversine.js
│           └── aqiColor.js
│
└── README.md
```

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm 9+**
- Internet connection (Nominatim, Overpass, optionally Google APIs)

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone git@github.com:Om-Ingole/BusinessGeoAI.git
cd BusinessGeoAI
```

### 2. Backend setup

```bash
cd backend

python -m venv venv
.\venv\Scripts\Activate.ps1      # Windows PowerShell
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt

copy .env.example .env           # Windows
# cp .env.example .env           # macOS / Linux
```

Edit `backend/.env` and add your keys (see [Environment Variables](#environment-variables)).

### 3. Frontend setup

```bash
cd frontend
npm install
```

---

## Running the App

Open **two terminals**.

**Terminal 1 — Backend:**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

On first start the backend creates `location_intel.db` and seeds it with airports, railway stations, census, crime, and MSME data. API docs: **http://localhost:8000/docs**

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev
```

Open **http://localhost:5173**.

> **Windows note:** The Vite proxy targets `127.0.0.1` (not `localhost`) to avoid IPv6 resolution issues.

---

## How to Use

The search bar accepts addresses, landmarks, pin codes, or `lat, lon` coordinates.

1. Type a location and press **Analyze**
2. A step-by-step progress screen shows what's happening (geocoding → POI fetch → AQI → score → insights)
3. The 3-panel dashboard loads

**Sample locations** on the empty state (click to auto-search):
- Koregaon Park, Pune
- Connaught Place, New Delhi
- Bandra West, Mumbai
- Indiranagar, Bengaluru
- T Nagar, Chennai

**Export:** Click **Export JSON** in the header to download `businessgeo-report-{location}-{date}.json`, or **Print** for PDF.

---

## Google Maps Platform Setup

By default the app works entirely with OpenStreetMap — no key needed.

To add Google Places ratings, review counts, business status, and more accurate geocoding:

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project
2. Enable: **Geocoding API**, **Places API (New)**, **Routes API**
3. Create an API key and add to `backend/.env`:

```env
GOOGLE_MAPS_API_KEY=your_key_here
LOCATION_PROVIDER=hybrid
```

The `hybrid` provider uses Google for geocoding and most POI categories, and always falls back to OSM on quota errors or for housing.

> **Security:** The Google Maps key never reaches the browser. All calls are backend-only.

---

## AI Chat Setup (BusinessGeo Assistant)

The chat uses Google ADK with Gemini to answer questions, compare locations, and evaluate business fit.

1. Get a free key at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Install the ADK package: `pip install google-adk`
3. Add to `backend/.env`:

```env
GOOGLE_GENAI_API_KEY=your_key_here
GOOGLE_ADK_MODEL=gemini-2.0-flash
```

4. Restart the backend

**Chat tools available:**

| Tool | What it does |
|---|---|
| `analyze_location_tool` | Runs a fresh analysis and updates the dashboard |
| `get_cached_report_tool` | Retrieves a previous analysis by ID |
| `compare_locations_tool` | Compares 2–4 locations side by side |
| `business_fit_tool` | Evaluates fit for a specific business type |
| `nearby_competition_tool` | Searches for nearby competitors (needs Google Maps key) |
| `route_access_tool` | Travel times to key destinations |

**Example questions:** "Is this good for a cafe?" · "Compare Bandra and Koregaon Park" · "What are the top risks?" · "Find nearby pharmacies" · "Explain the viability score"

To disable chat: `ADK_ENABLE_CHAT=false` — endpoints return 503.

---

## Viability Score Explained

Weighted average of 8 dimensions (0–10 each):

| Dimension | Weight | Basis |
|---|---|---|
| Footfall Proxy | 20% | Total POI count; Google rating volume adds bonus |
| Transport Access | 18% | Bus stop count + nearest railway distance |
| Demographics | 15% | Literacy rate + urban percentage |
| POI Density | 12% | Hospitals × 1.5 + Schools × 0.8 |
| Crime Safety | 12% | Inverted crimes-per-lakh |
| Air Quality | 10% | Inverted AQI |
| Business Density | 8% | MSME enterprise count + Google OPERATIONAL bonus |
| Growth Potential | 5% | Static 7.0 baseline (v1) |

**Data confidence** is shown alongside the score — reduced when OSM fallback is used or sources are missing.

| Score | Label |
|---|---|
| 8.5 – 10.0 | Excellent |
| 7.0 – 8.4 | Good |
| 5.0 – 6.9 | Average |
| 0.0 – 4.9 | Poor |

---

## Data Sources

**Live APIs:** Nominatim / Google Geocoding · Overpass / Google Places API (New) · CPCB AQI via data.gov.in · Google Routes API (optional)

**Static / seeded:** 20 airports · 50 railway stations · 20 districts census (2011) · 16 districts crime (NCRB) · 20 MSME sector entries

---

## API Reference

Interactive docs at **http://localhost:8000/docs**

### POST `/api/analyze`
Main endpoint. Accepts address or coordinates, returns full report including `viability_score`, `score_breakdown`, `data_confidence`, `agent_insights`, `poi`, `demographics`, `aqi`, `crime`, `airports`, `msme_sectors`, `provider`, `partial`, `warnings[]`.

### POST `/api/chat/session`
Creates an ADK chat session. Returns `session_id`.

### POST `/api/chat/message`
Sends a message to the assistant. Returns `message`, `tool_calls`, `updated_report` (if chat triggered a new analysis), `suggested_actions`, `warnings`.

### GET `/api/chat/session/{session_id}/history`
### GET `/api/poi` · GET `/api/aqi/{state}` · GET `/api/airports/nearest` · GET `/api/railway/nearest`
### GET `/api/reports/history` · GET `/health`

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env`:

| Variable | Default | Purpose |
|---|---|---|
| `DATA_GOV_API_KEY` | — | CPCB AQI via data.gov.in |
| `DATABASE_URL` | `sqlite+aiosqlite:///./location_intel.db` | SQLite path |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origins |
| `CACHE_TTL_HOURS` | `24` | Analysis cache TTL |
| `GOOGLE_MAPS_API_KEY` | — | Google geocoding + Places + Routes |
| `LOCATION_PROVIDER` | `hybrid` | `osm` / `google` / `hybrid` |
| `GOOGLE_GENAI_API_KEY` | — | BusinessGeo Assistant (Gemini) |
| `GOOGLE_ADK_MODEL` | `gemini-2.0-flash` | Gemini model for chat |
| `ADK_ENABLE_CHAT` | `true` | Set `false` to disable chat endpoints |

> **Security:** Never put Google or Gemini keys in frontend Vite env vars — all calls are backend-only.

---

## Adding Your Own CSV Data

Drop CSV files in `backend/data/` to override the seeded fallback. Delete `location_intel.db` and restart to reload.

| File | Required columns |
|---|---|
| `railway_stations.csv` | `station_name`, `state`, `latitude`, `longitude` |
| `airports.csv` | `name`, `latitude`, `longitude` |
| `census_district.csv` | `state`, `district`, `total_population`, `literacy_rate`, `sex_ratio` |
| `ncrb_crime.csv` | `year`, `state`, `district`, `total_ipc_crimes`, `crimes_per_lakh` |
| `msme_district.csv` | `state`, `district`, `sector_name`, `enterprise_count` |

Reset DB: `Remove-Item backend\location_intel.db` then restart uvicorn.

---

## Known Limitations

- **Overpass rate limits** — Heavy testing from one IP may cause partial POI results; results are cached for 24h
- **AQI station coverage** — Not every district has a CPCB station nearby
- **Census 2011** — 2021 census not yet fully available on data.gov.in
- **District name matching** — Fuzzy prefix match; unusual district names may fall back to first state record
- **Nominatim 1 req/sec** — Do not remove the sleep in `geocoder.py`
- **ADK sessions are in-memory** — Chat context resets on backend restart; message history in SQLite is preserved
- **No real footfall data** — Footfall proxy is POI density, not actual visit data

---

## Extending the Platform

**Add a new data dimension:**
1. Add a service in `backend/services/`
2. Add it to `asyncio.gather()` in `backend/services/analysis_service.py`
3. Add field to `backend/schemas.py` `AnalyzeResponse`
4. Create a widget in `frontend/src/components/` using `WidgetCard`
5. Wire it into `frontend/src/App.jsx`

**Change cache TTL:** Set `CACHE_TTL_HOURS` in `.env`

**Use PostgreSQL:** Change `DATABASE_URL` to `postgresql+asyncpg://...` and `pip install asyncpg`

**Deploy:**
- Backend: Railway, Render, Fly.io, or any Python host — set `CORS_ORIGINS` to your frontend domain
- Frontend: `npm run build` → deploy `dist/` to Vercel, Netlify, or Cloudflare Pages

---

## License

Uses exclusively free and open data sources:
- OpenStreetMap © OpenStreetMap contributors (ODbL)
- data.gov.in — Government of India Open Government Data Platform
- CPCB air quality — Central Pollution Control Board, India
- NCRB crime statistics — National Crime Records Bureau, India
- Census data — Office of the Registrar General & Census Commissioner, India
