"""Shared fixtures for all backend tests."""
import os
import pytest
import pytest_asyncio

# Ensure no live Google/ADK calls in tests
os.environ.setdefault("GOOGLE_MAPS_API_KEY", "")
os.environ.setdefault("GOOGLE_GENAI_API_KEY", "")
os.environ.setdefault("DATA_GOV_API_KEY", "")
os.environ.setdefault("LOCATION_PROVIDER", "osm")
os.environ.setdefault("ADK_ENABLE_CHAT", "false")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_location_intel.db")

import pytest


@pytest.fixture
def sample_poi():
    return {
        "hospitals": [
            {"name": "City Hospital", "lat": 12.97, "lon": 77.59, "distance_km": 0.3, "provider": "osm", "tags": {}},
            {"name": "Apollo Clinic", "lat": 12.96, "lon": 77.60, "distance_km": 0.7, "provider": "osm", "tags": {}},
            {"name": "Manipal", "lat": 12.98, "lon": 77.58, "distance_km": 1.1, "provider": "osm", "tags": {}},
        ],
        "schools": [
            {"name": "DPS", "lat": 12.97, "lon": 77.60, "distance_km": 0.5, "provider": "osm", "tags": {}},
            {"name": "Kendriya", "lat": 12.96, "lon": 77.61, "distance_km": 0.8, "provider": "osm", "tags": {}},
        ],
        "bus_stops": [
            {"name": "MG Road", "lat": 12.97, "lon": 77.59, "distance_km": 0.1, "provider": "osm", "tags": {}},
        ] * 6,
        "pharmacies": [
            {"name": "MedPlus", "lat": 12.97, "lon": 77.59, "distance_km": 0.2, "provider": "osm", "tags": {}},
        ] * 4,
        "banks": [],
        "supermarkets": [],
        "metro": [],
        "railway": [],
        "housing": [],
        "corporates": [],
    }


@pytest.fixture
def sample_demographics():
    return {
        "district": "Bengaluru",
        "state": "Karnataka",
        "total_population": 9621551,
        "urban_population": 9621551,
        "rural_population": 0,
        "literacy_rate": 87.67,
        "sex_ratio": 908,
        "workers_total": 4200000,
        "urban_pct": 100.0,
    }


@pytest.fixture
def sample_crime():
    return {
        "district": "Bengaluru",
        "state": "Karnataka",
        "records": [
            {"year": 2022, "total_ipc_crimes": 42000, "crimes_per_lakh": 180.0,
             "property_crimes": 12000, "economic_offences": 4000},
        ],
        "latest_crimes_per_lakh": 180.0,
    }


@pytest.fixture
def sample_aqi():
    return {
        "station": "Silk Board",
        "city": "Bengaluru",
        "pollutant_id": "PM2.5",
        "pollutant_avg": 85.0,
        "aqi_category": "Satisfactory",
        "distance_km": 2.1,
    }


@pytest.fixture
def sample_msme():
    return [
        {"sector_name": "Retail Trade", "nic_code": "47", "enterprise_count": 35000},
        {"sector_name": "IT & Software", "nic_code": "62", "enterprise_count": 15000},
        {"sector_name": "Food Processing", "nic_code": "10", "enterprise_count": 8000},
    ]


@pytest.fixture
def sample_report(sample_poi, sample_demographics, sample_crime, sample_aqi, sample_msme):
    return {
        "location": {
            "query": "Indiranagar, Bengaluru",
            "lat": 12.9716,
            "lon": 77.5946,
            "display_address": "Indiranagar, Bengaluru, Karnataka",
            "district": "Bengaluru",
            "state": "Karnataka",
            "pin_code": "560038",
        },
        "viability_score": 7.1,
        "score_breakdown": {
            "footfall_proxy": 8.0,
            "transport_access": 6.5,
            "demographics": 9.5,
            "poi_density": 7.0,
            "crime_safety": 6.4,
            "air_quality": 7.9,
            "business_density": 8.0,
            "growth_potential": 7.0,
        },
        "data_confidence": 0.8,
        "poi": sample_poi,
        "demographics": sample_demographics,
        "crime": sample_crime,
        "aqi": sample_aqi,
        "airports": [{"name": "Kempegowda International", "iata_code": "BLR", "distance_km": 34.5}],
        "railway_stations": [{"station_name": "Bengaluru City", "distance_km": 4.2}],
        "nearest_railway": {"station_name": "Bengaluru City", "distance_km": 4.2},
        "msme_sectors": sample_msme,
        "footfall_proxy": {"poi_density_score": 80.0, "total_amenities": 40},
        "agent_insights": None,
        "provider": "osm",
        "partial": False,
        "warnings": [],
        "generated_at": "2026-06-20T12:00:00",
    }
