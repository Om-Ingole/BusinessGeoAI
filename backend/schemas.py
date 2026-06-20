from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime


class AnalyzeRequest(BaseModel):
    query: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_km: float = Field(default=1.0, ge=0.5, le=5.0)
    business_type: Optional[str] = "retail"

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v):
        if v is not None and not (-90 <= v <= 90):
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("lon")
    @classmethod
    def validate_lon(cls, v):
        if v is not None and not (-180 <= v <= 180):
            raise ValueError("longitude must be between -180 and 180")
        return v


class LocationInfo(BaseModel):
    query: Optional[str] = None
    lat: float
    lon: float
    display_address: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None


class ScoreBreakdown(BaseModel):
    footfall_proxy: float = 5.0
    demographics: float = 5.0
    transport_access: float = 5.0
    poi_density: float = 5.0
    crime_safety: float = 5.0
    air_quality: float = 5.0
    business_density: float = 5.0
    growth_potential: float = 7.0


class PoiItem(BaseModel):
    id: Optional[str] = None
    provider: Optional[str] = None
    name: str
    lat: float
    lon: float
    distance_km: Optional[float] = None
    rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    business_status: Optional[str] = None
    address: Optional[str] = None
    google_maps_uri: Optional[str] = None
    types: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[dict] = None


class AqiData(BaseModel):
    station: Optional[str] = None
    city: Optional[str] = None
    pollutant_id: Optional[str] = None
    pollutant_avg: Optional[float] = None
    aqi_category: Optional[str] = None
    distance_km: Optional[float] = None
    error: Optional[str] = None


class DemographicsData(BaseModel):
    district: Optional[str] = None
    state: Optional[str] = None
    total_population: Optional[int] = None
    urban_population: Optional[int] = None
    rural_population: Optional[int] = None
    literacy_rate: Optional[float] = None
    sex_ratio: Optional[int] = None
    workers_total: Optional[int] = None
    urban_pct: Optional[float] = None


class CrimeRecord(BaseModel):
    year: int
    total_ipc_crimes: Optional[int] = None
    crimes_per_lakh: Optional[float] = None
    property_crimes: Optional[int] = None
    economic_offences: Optional[int] = None


class CrimeData(BaseModel):
    district: Optional[str] = None
    state: Optional[str] = None
    records: List[CrimeRecord] = Field(default_factory=list)
    latest_crimes_per_lakh: Optional[float] = None


class AirportInfo(BaseModel):
    name: str
    city: Optional[str] = None
    iata_code: Optional[str] = None
    state: Optional[str] = None
    distance_km: float


class RailwayInfo(BaseModel):
    station_name: str
    station_code: Optional[str] = None
    state: Optional[str] = None
    distance_km: float


class MsmeSector(BaseModel):
    sector_name: str
    nic_code: Optional[str] = None
    enterprise_count: int
    micro_count: Optional[int] = None
    small_count: Optional[int] = None


class FootfallProxy(BaseModel):
    poi_density_score: float
    total_amenities: int
    peak_hours_est: str = "6PM–9PM est."


class RiskItem(BaseModel):
    severity: str  # high / medium / low
    title: str
    evidence: str
    recommendation: str


class OpportunityItem(BaseModel):
    title: str
    evidence: str
    recommendation: str


class DataQuality(BaseModel):
    poi_provider: str = "osm"
    fallback_used: bool = False
    missing_sources: List[str] = Field(default_factory=list)


class AgentInsights(BaseModel):
    summary: str
    best_use_cases: List[str] = Field(default_factory=list)
    risks: List[RiskItem] = Field(default_factory=list)
    opportunities: List[OpportunityItem] = Field(default_factory=list)
    next_questions: List[str] = Field(default_factory=list)
    confidence: float = 0.5
    data_quality: Optional[DataQuality] = None


class AnalyzeResponse(BaseModel):
    location: LocationInfo
    viability_score: float
    score_breakdown: ScoreBreakdown
    data_confidence: float = 0.5
    demographics: Optional[DemographicsData] = None
    aqi: Optional[AqiData] = None
    crime: Optional[CrimeData] = None
    poi: Optional[dict] = None
    airports: List[AirportInfo] = Field(default_factory=list)
    nearest_railway: Optional[RailwayInfo] = None
    railway_stations: List[RailwayInfo] = Field(default_factory=list)
    msme_sectors: List[MsmeSector] = Field(default_factory=list)
    footfall_proxy: Optional[FootfallProxy] = None
    agent_insights: Optional[AgentInsights] = None
    provider: Optional[str] = None
    partial: bool = False
    warnings: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Chat schemas ──────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    analysis_id: Optional[str] = None
    user_id: Optional[str] = "anonymous"
    initial_context: Optional[str] = None


class CreateSessionResponse(BaseModel):
    session_id: str
    analysis_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessageRequest(BaseModel):
    session_id: str
    analysis_id: Optional[str] = None
    message: str
    current_report: Optional[dict] = None
    user_id: Optional[str] = "anonymous"


class ToolCallSummary(BaseModel):
    name: str
    status: str  # success / error / skipped


class ChatMessageResponse(BaseModel):
    message: str
    tool_calls: List[ToolCallSummary] = Field(default_factory=list)
    updated_report: Optional[dict] = None
    suggested_actions: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
