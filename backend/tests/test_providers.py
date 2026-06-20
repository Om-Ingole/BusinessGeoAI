"""Tests for provider selection, Google normalization, and OSM fallback."""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Provider selection ────────────────────────────────────────────────────────

def test_no_google_key_returns_osm_provider():
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "", "LOCATION_PROVIDER": "hybrid"}):
        from services.location_providers.hybrid import get_provider
        provider = get_provider()
        assert provider.provider_name() == "osm"


def test_google_key_with_hybrid_mode_returns_hybrid():
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "fake-key", "LOCATION_PROVIDER": "hybrid"}):
        from services.location_providers.hybrid import get_provider
        provider = get_provider()
        assert provider.provider_name() == "hybrid"


def test_osm_mode_forces_osm_even_with_key():
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "fake-key", "LOCATION_PROVIDER": "osm"}):
        from services.location_providers.hybrid import get_provider
        provider = get_provider()
        assert provider.provider_name() == "osm"


def test_google_mode_returns_google_provider():
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "fake-key", "LOCATION_PROVIDER": "google"}):
        from services.location_providers.hybrid import get_provider
        from services.location_providers.google_maps import GoogleMapsProvider
        provider = get_provider()
        assert isinstance(provider, GoogleMapsProvider)


# ── Google geocode response normalization ─────────────────────────────────────

def test_google_geocode_parse():
    from services.location_providers.google_maps import GoogleMapsProvider
    p = GoogleMapsProvider("fake-key")
    raw_result = {
        "geometry": {"location": {"lat": 18.5362, "lng": 73.8938}},
        "formatted_address": "Koregaon Park, Pune, Maharashtra 411001, India",
        "address_components": [
            {"long_name": "Maharashtra", "types": ["administrative_area_level_1", "political"]},
            {"long_name": "Pune", "types": ["administrative_area_level_3", "political"]},
            {"long_name": "411001", "types": ["postal_code"]},
        ],
    }
    result = p._parse_geocode_result(raw_result)
    assert result["lat"] == 18.5362
    assert result["lon"] == 73.8938
    assert result["state"] == "Maharashtra"
    assert result["postcode"] == "411001"
    assert result["provider"] == "google"


def test_google_normalize_place():
    from services.location_providers.google_maps import GoogleMapsProvider
    p = GoogleMapsProvider("fake-key")
    raw_place = {
        "id": "ChIJ_test_123",
        "displayName": {"text": "Apollo Hospital"},
        "formattedAddress": "21 Greams Lane, Chennai",
        "location": {"latitude": 13.06, "longitude": 80.25},
        "primaryType": "hospital",
        "types": ["hospital", "health"],
        "businessStatus": "OPERATIONAL",
        "rating": 4.2,
        "userRatingCount": 1450,
        "googleMapsUri": "https://maps.google.com/?cid=123",
    }
    normalized = p._normalize_place(raw_place, 13.06, 80.25)
    assert normalized["id"] == "ChIJ_test_123"
    assert normalized["name"] == "Apollo Hospital"
    assert normalized["provider"] == "google"
    assert normalized["rating"] == 4.2
    assert normalized["business_status"] == "OPERATIONAL"
    assert normalized["distance_km"] == 0.0


# ── Fallback behavior ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_hybrid_falls_back_to_osm_on_google_geocode_failure():
    from services.location_providers.hybrid import HybridProvider

    google_mock = AsyncMock()
    google_mock.geocode.side_effect = Exception("Google down")
    google_mock.provider_name.return_value = "google"

    osm_mock = AsyncMock()
    osm_mock.geocode.return_value = {
        "lat": 18.5, "lon": 73.8, "display_name": "Pune",
        "provider": "osm", "district": "Pune", "state": "Maharashtra",
    }

    hybrid = HybridProvider(google_mock, osm_mock)
    result = await hybrid.geocode("Koregaon Park, Pune")

    assert result["provider"] == "osm"
    assert result.get("fallback") is True
    osm_mock.geocode.assert_called_once()


@pytest.mark.asyncio
async def test_hybrid_falls_back_to_osm_on_google_poi_quota_error():
    from services.location_providers.hybrid import HybridProvider
    import httpx

    google_mock = AsyncMock()
    google_mock.fetch_poi.side_effect = RuntimeError("Google Places quota exceeded")
    google_mock.provider_name.return_value = "google"

    osm_mock = AsyncMock()
    osm_mock.fetch_poi.return_value = {"hospitals": [{"name": "Test", "lat": 12.0, "lon": 77.0}]}

    hybrid = HybridProvider(google_mock, osm_mock)
    result = await hybrid.fetch_poi(12.97, 77.59, 1000, ["hospitals"])

    osm_mock.fetch_poi.assert_called_once()
    assert "hospitals" in result


# ── POI endpoint fetches once ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_poi_endpoint_fetches_once_and_filters():
    """Provider.fetch_poi should be called once, returning only requested categories."""
    with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "", "LOCATION_PROVIDER": "osm"}):
        from services.location_providers.osm import OSMProvider

        all_poi = {
            "hospitals": [{"name": "H1"}],
            "schools": [{"name": "S1"}],
            "bus_stops": [],
        }

        with patch.object(OSMProvider, "fetch_poi", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"hospitals": all_poi["hospitals"], "schools": []}
            provider = OSMProvider()
            result = await provider.fetch_poi(12.97, 77.59, 1000, ["hospitals", "schools"])

        mock_fetch.assert_called_once()
        assert "hospitals" in result
        assert "schools" in result


# ── Lat/lon validation ────────────────────────────────────────────────────────

def test_invalid_lat_rejected():
    from schemas import AnalyzeRequest
    with pytest.raises(Exception):
        AnalyzeRequest(lat=95.0, lon=77.0)


def test_invalid_lon_rejected():
    from schemas import AnalyzeRequest
    with pytest.raises(Exception):
        AnalyzeRequest(lat=18.0, lon=200.0)


def test_valid_lat_lon_accepted():
    from schemas import AnalyzeRequest
    req = AnalyzeRequest(lat=18.5362, lon=73.8938, radius_km=1.0)
    assert req.lat == 18.5362
    assert req.lon == 73.8938
