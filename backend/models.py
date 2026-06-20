from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class LocationCache(Base):
    __tablename__ = "location_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query_hash = Column(String, unique=True, nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    address = Column(String)
    district = Column(String)
    state = Column(String)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)


class Airport(Base):
    __tablename__ = "airports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    city = Column(String)
    iata_code = Column(String)
    state = Column(String)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_operational = Column(Boolean, default=True)


class RailwayStation(Base):
    __tablename__ = "railway_stations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    station_name = Column(String, nullable=False)
    station_code = Column(String)
    state = Column(String)
    division = Column(String)
    zone = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)


class CensusData(Base):
    __tablename__ = "census_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    district_code = Column(String)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    total_population = Column(Integer)
    urban_population = Column(Integer)
    rural_population = Column(Integer)
    literacy_rate = Column(Float)
    sex_ratio = Column(Integer)
    workers_total = Column(Integer)


class CrimeData(Base):
    __tablename__ = "crime_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    year = Column(Integer, nullable=False)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    total_ipc_crimes = Column(Integer)
    crimes_per_lakh = Column(Float)
    property_crimes = Column(Integer)
    economic_offences = Column(Integer)


class MsmeData(Base):
    __tablename__ = "msme_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(String, nullable=False)
    district = Column(String, nullable=False)
    nic_code = Column(String)
    sector_name = Column(String)
    enterprise_count = Column(Integer)
    micro_count = Column(Integer)
    small_count = Column(Integer)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, default="anonymous")
    analysis_id = Column(String, nullable=True)  # LocationCache.query_hash
    business_type = Column(String, nullable=True)
    radius_km = Column(Float, nullable=True)
    location_query = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class ChatToolCall(Base):
    __tablename__ = "chat_tool_calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    message_id = Column(Integer, nullable=True)
    tool_name = Column(String, nullable=False)
    tool_input_json = Column(Text, nullable=True)
    tool_output_json = Column(Text, nullable=True)
    status = Column(String, default="success")
    created_at = Column(DateTime, server_default=func.now())
