import logging
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.routers import auth, care, chat, content, devices, diagnosis, plants, sensors
from app.seed import seed_species_profiles

logger = logging.getLogger("uvicorn.error")
settings = get_settings()

DEFAULT_ORIGINS = {
    "http://localhost:5173",
    "http://localhost:3000",
    "https://smart-plant-dr.vercel.app",
}
VERCEL_ORIGIN_RE = re.compile(r"^https://[\w-]+\.vercel\.app$")


def is_allowed_origin(origin: str | None) -> bool:
    if not origin:
        return False
    if origin in DEFAULT_ORIGINS or origin in settings.cors_origin_list:
        return True
    return bool(VERCEL_ORIGIN_RE.fullmatch(origin))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Auth mode: %s | JWT secret loaded: %s | Supabase URL: %s | DB: %s | CORS env: %s | Blynk: %s",
        "supabase" if settings.use_supabase_auth else "legacy",
        bool(settings.supabase_jwt_secret),
        settings.supabase_url or "(missing)",
        settings.database_url[:40] + "...",
        settings.cors_origin_list,
        bool(settings.blynk_auth_token),
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


@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    allowed = is_allowed_origin(origin)

    if request.method == "OPTIONS":
        if not allowed:
            return Response(status_code=400, content="CORS origin not allowed")
        requested_headers = request.headers.get("Access-Control-Request-Headers", "Authorization, Content-Type")
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin or "",
                "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": requested_headers,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "600",
                "Vary": "Origin",
            },
        )

    response = await call_next(request)
    if allowed and origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    return response


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
