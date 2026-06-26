import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.routers import auth, care, chat, content, devices, diagnosis, plants, sensors
from app.seed import seed_species_profiles

logger = logging.getLogger("uvicorn.error")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Auth mode: %s | JWT secret loaded: %s | DB: %s",
        "supabase" if settings.use_supabase_auth else "legacy",
        bool(settings.supabase_jwt_secret),
        settings.database_url[:40] + "...",
    )
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_species_profiles(db)
    finally:
        db.close()
    uploads = Path(settings.uploads_dir)
    uploads.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.api_v1_prefix
app.include_router(auth.router, prefix=prefix)
app.include_router(plants.router, prefix=prefix)
app.include_router(devices.router, prefix=prefix)
app.include_router(sensors.router, prefix=prefix)
app.include_router(diagnosis.router, prefix=prefix)
app.include_router(care.router, prefix=prefix)
app.include_router(content.router, prefix=prefix)
app.include_router(chat.router, prefix=prefix)

if os.path.isdir(settings.uploads_dir):
    app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}
