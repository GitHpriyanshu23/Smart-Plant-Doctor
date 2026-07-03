import logging
import threading

import httpx
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User

logger = logging.getLogger("uvicorn.error")
settings = get_settings()

_jwks_cache: dict | None = None
_jwks_lock = threading.Lock()


def _fetch_jwks() -> dict:
    global _jwks_cache
    with _jwks_lock:
        if _jwks_cache is not None:
            return _jwks_cache
        url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        try:
            resp = httpx.get(url, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            logger.info("Fetched JWKS from Supabase (%d keys)", len(_jwks_cache.get("keys", [])))
        except Exception as e:
            logger.error("Failed to fetch JWKS: %s", e)
            _jwks_cache = {"keys": []}
        return _jwks_cache


def _get_signing_key(token: str) -> dict | None:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    alg = header.get("alg", "ES256")
    jwks = _fetch_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    if jwks.get("keys"):
        return jwks["keys"][0]
    return None


def verify_supabase_token(token: str) -> dict | None:
    if not settings.supabase_url:
        logger.warning("Supabase URL not configured")
        return None

    signing_key = _get_signing_key(token)
    if not signing_key:
        logger.warning("No matching signing key found in JWKS")
        return None

    alg = signing_key.get("alg", "ES256")

    try:
        return jwt.decode(
            token,
            signing_key,
            algorithms=[alg],
            audience="authenticated",
        )
    except JWTError as e:
        logger.warning("JWT verification failed (aud=authenticated): %s", e)
        try:
            return jwt.decode(
                token,
                signing_key,
                algorithms=[alg],
                options={"verify_aud": False},
            )
        except JWTError as e2:
            logger.warning("JWT verification (no aud) also failed: %s", e2)
            return None


def get_or_create_user_from_token(db: Session, token: str) -> User | None:
    payload = verify_supabase_token(token)
    if not payload:
        return None

    supabase_id = payload.get("sub")
    if not supabase_id:
        return None

    email = payload.get("email") or f"{supabase_id}@users.local"
    user = db.query(User).filter(User.supabase_id == supabase_id).first()
    if not user:
        user = User(supabase_id=supabase_id, email=email, password_hash=None)
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            user = db.query(User).filter(User.supabase_id == supabase_id).first()
            if not user:
                raise
    elif email and user.email != email:
        user.email = email
        db.commit()
        db.refresh(user)
    return user
