import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from database import init_db
from routers import location, poi, aqi, airports
from routers import chat as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from seed_data import seed_if_empty
    await seed_if_empty()
    yield


app = FastAPI(
    title="India Location Intelligence API",
    version="2.0.0",
    description="360° site analysis for any Indian location — with Google Maps + ADK chat",
    lifespan=lifespan,
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(location.router, prefix="/api", tags=["analysis"])
app.include_router(poi.router, prefix="/api", tags=["poi"])
app.include_router(aqi.router, prefix="/api", tags=["aqi"])
app.include_router(airports.router, prefix="/api", tags=["transport"])
app.include_router(chat_router.router, prefix="/api", tags=["chat"])


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "India Location Intelligence API",
        "version": "2.0.0",
        "chat_enabled": os.getenv("ADK_ENABLE_CHAT", "true").lower() == "true",
        "location_provider": os.getenv("LOCATION_PROVIDER", "hybrid"),
        "google_maps": bool(os.getenv("GOOGLE_MAPS_API_KEY")),
    }
