import json
import logging
import time
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
settings = get_settings()

# Matches ESP32 firmware virtual pins in sensors data/src/main.cpp
BLYNK_PINS = ("v0", "v1", "v2", "v3", "v4")


def _api_base() -> str:
    return settings.blynk_server.rstrip("/")


def _parse_values(raw: str, count: int) -> list[str]:
    text = raw.strip()
    if not text:
        return []
    if "\n" in text:
        parts = [p.strip() for p in text.splitlines() if p.strip()]
    else:
        parts = text.split()
    if len(parts) >= count:
        return parts[:count]
    return parts


def soil_label_from_raw(raw: float) -> str:
    if raw < 1500:
        return "Wet"
    if raw < 2500:
        return "Moist"
    return "Dry"


def soil_label_from_status(status: str) -> str:
    lowered = status.lower()
    if "wet" in lowered:
        return "Wet"
    if "moist" in lowered:
        return "Moist"
    if "dry" in lowered:
        return "Dry"
    return status.strip() or "Unknown"


async def _blynk_get(path: str, params: dict[str, Any]) -> str:
    if not settings.blynk_auth_token:
        raise ValueError("Blynk is not configured")

    url = f"{_api_base()}{path}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.text


async def is_hardware_connected() -> bool:
    try:
        raw = await _blynk_get(
            "/external/api/isHardwareConnected",
            {"token": settings.blynk_auth_token},
        )
        return raw.strip().lower() == "true"
    except Exception as exc:
        logger.warning("Blynk connectivity check failed: %s", exc)
        return False


async def fetch_live_snapshot() -> dict[str, Any]:
    params: list[tuple[str, str]] = [("token", settings.blynk_auth_token)]
    for pin in BLYNK_PINS:
        params.append((pin, ""))

    url = f"{_api_base()}/external/api/get"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        raw = resp.text
    values = _parse_values(raw, 5)
    if len(values) < 4:
        raise ValueError("Unexpected Blynk response")

    temperature = float(values[0])
    humidity = float(values[1])
    soil_raw = float(values[2])
    light_raw = float(values[3])
    soil_status = values[4] if len(values) > 4 else soil_label_from_raw(soil_raw)

    now = int(time.time())
    return {
        "id": 0,
        "pot_index": 0,
        "ts": now,
        "temperature": temperature,
        "humidity": humidity,
        "soil_moisture": soil_raw,
        "light": light_raw,
        "soil_status": soil_label_from_status(soil_status),
        "ph": 6.5,
    }


async def _fetch_pin_history(pin: str, from_ms: int, to_ms: int) -> list[tuple[int, float]]:
    raw = await _blynk_get(
        "/external/api/data/get",
        {
            "token": settings.blynk_auth_token,
            "pin": pin,
            "from": from_ms,
            "to": to_ms,
        },
    )
    text = raw.strip()
    if not text:
        return []
    try:
        rows = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse Blynk history for %s", pin)
        return []

    parsed: list[tuple[int, float]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 2:
            continue
        ts_ms, value = row[0], row[1]
        try:
            parsed.append((int(ts_ms), float(value)))
        except (TypeError, ValueError):
            continue
    return parsed


async def fetch_readings(hours: int = 1) -> dict[str, Any]:
    connected = await is_hardware_connected()
    live = await fetch_live_snapshot()

    now_ms = int(time.time() * 1000)
    from_ms = now_ms - hours * 60 * 60 * 1000

    histories: dict[str, list[tuple[int, float]]] = {}
    for pin in ("v0", "v1", "v2", "v3"):
        try:
            histories[pin] = await _fetch_pin_history(pin, from_ms, now_ms)
        except Exception as exc:
            logger.warning("Blynk history fetch failed for %s: %s", pin, exc)
            histories[pin] = []

    # Bucket by 30-second intervals using v0 timestamps as the anchor series.
    anchor = histories.get("v0") or []
    if not anchor:
        return {
            "connected": connected,
            "source": "blynk",
            "latest": live,
            "readings": [live],
        }

    readings: list[dict[str, Any]] = []
    for idx, (ts_ms, temperature) in enumerate(anchor):
        ts = int(ts_ms / 1000)

        def nearest(pin: str, default: float) -> float:
            series = histories.get(pin, [])
            if not series:
                return default
            # histories are time-ordered; use same index when possible
            if idx < len(series):
                return float(series[idx][1])
            return float(series[-1][1])

        humidity = nearest("v1", live["humidity"])
        soil_raw = nearest("v2", live["soil_moisture"])
        light_raw = nearest("v3", live["light"])
        readings.append(
            {
                "id": idx + 1,
                "pot_index": 0,
                "ts": ts,
                "temperature": temperature,
                "humidity": humidity,
                "soil_moisture": soil_raw,
                "light": light_raw,
                "soil_status": soil_label_from_raw(soil_raw),
                "ph": 6.5,
            }
        )

    readings.sort(key=lambda item: item["ts"], reverse=True)
    latest = readings[0] if readings else live
    latest["soil_status"] = live["soil_status"]

    return {
        "connected": connected,
        "source": "blynk",
        "latest": latest,
        "readings": readings,
    }
