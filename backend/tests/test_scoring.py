"""Tests for score_service including Google rating/review count signals."""
import pytest
from services import score_service


def test_score_returns_three_values(sample_poi, sample_demographics, sample_crime, sample_aqi, sample_msme):
    result = score_service.calculate_viability_score(
        poi=sample_poi,
        demographics=sample_demographics,
        crime=sample_crime,
        aqi=sample_aqi,
        nearest_railway={"station_name": "City", "distance_km": 2.0},
        msme_sectors=sample_msme,
    )
    assert len(result) == 3
    total, breakdown, confidence = result
    assert 0 <= total <= 10
    assert isinstance(breakdown, dict)
    assert 0 <= confidence <= 1


def test_empty_poi_gives_zero_footfall():
    score, breakdown, _ = score_service.calculate_viability_score(
        poi={}, demographics=None, crime=None, aqi=None,
        nearest_railway=None, msme_sectors=[],
    )
    assert breakdown["footfall_proxy"] == 0.0


def test_high_crime_lowers_score():
    high_crime = {"latest_crimes_per_lakh": 500.0}
    _, breakdown, _ = score_service.calculate_viability_score(
        poi={}, demographics=None, crime=high_crime, aqi=None,
        nearest_railway=None, msme_sectors=[],
    )
    assert breakdown["crime_safety"] == 0.0


def test_low_crime_raises_score():
    low_crime = {"latest_crimes_per_lakh": 50.0}
    _, breakdown, _ = score_service.calculate_viability_score(
        poi={}, demographics=None, crime=low_crime, aqi=None,
        nearest_railway=None, msme_sectors=[],
    )
    assert breakdown["crime_safety"] == 9.0


def test_good_aqi_raises_air_quality_score():
    good_aqi = {"pollutant_avg": 40.0, "aqi_category": "Good"}
    _, breakdown, _ = score_service.calculate_viability_score(
        poi={}, demographics=None, crime=None, aqi=good_aqi,
        nearest_railway=None, msme_sectors=[],
    )
    assert breakdown["air_quality"] == 9.0


def test_missing_data_reduces_confidence():
    _, _, confidence = score_service.calculate_viability_score(
        poi={}, demographics=None, crime=None, aqi=None,
        nearest_railway=None, msme_sectors=[],
        missing_sources=["demographics", "aqi", "crime", "msme"],
    )
    assert confidence < 0.7


def test_fallback_used_reduces_confidence():
    _, _, base_conf = score_service.calculate_viability_score(
        poi={}, demographics=None, crime=None, aqi=None,
        nearest_railway=None, msme_sectors=[], fallback_used=False,
    )
    _, _, fallback_conf = score_service.calculate_viability_score(
        poi={}, demographics=None, crime=None, aqi=None,
        nearest_railway=None, msme_sectors=[], fallback_used=True,
    )
    assert fallback_conf < base_conf


def test_google_rated_poi_boosts_business_density():
    google_poi = {
        "supermarkets": [
            {"name": "Big Bazaar", "provider": "google", "rating": 4.5,
             "business_status": "OPERATIONAL", "lat": 0, "lon": 0},
            {"name": "DMart", "provider": "google", "rating": 4.2,
             "business_status": "OPERATIONAL", "lat": 0, "lon": 0},
        ],
        "banks": [],
        "corporates": [
            {"name": "TCS", "provider": "google", "rating": 4.1,
             "business_status": "OPERATIONAL", "lat": 0, "lon": 0},
        ],
    }
    msme = [{"sector_name": "IT", "enterprise_count": 5000}]
    _, breakdown_with_google, _ = score_service.calculate_viability_score(
        poi=google_poi, demographics=None, crime=None, aqi=None,
        nearest_railway=None, msme_sectors=msme,
    )
    _, breakdown_no_poi, _ = score_service.calculate_viability_score(
        poi={}, demographics=None, crime=None, aqi=None,
        nearest_railway=None, msme_sectors=msme,
    )
    assert breakdown_with_google["business_density"] >= breakdown_no_poi["business_density"]


def test_cache_key_generation():
    from services.cache_service import make_hash
    h1 = make_hash(12.9716, 77.5946, 1.0)
    h2 = make_hash(12.9716, 77.5946, 1.0)
    h3 = make_hash(12.9716, 77.5946, 2.0)
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # SHA-256 hex


def test_cache_key_rounds_to_4_decimals():
    from services.cache_service import make_hash
    h1 = make_hash(12.97161, 77.59461, 1.0)
    h2 = make_hash(12.97162, 77.59462, 1.0)
    assert h1 == h2  # rounds to same 4dp
