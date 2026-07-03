import json
import logging
import time
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
settings = get_settings()

# Matches ESP32 firmware virtual pins in sensors data/src/main.cpp
NUMERIC_PINS = ("v0", "v1", "v2", "v3")
STATUS_PIN = "v4"


def _api_base() -> str:
    return settings.blynk_server.rstrip("/")


def _token() -> str:
    token = (settings.blynk_auth_token or "").strip()
    if not token:
        raise ValueError("Blynk is not configured")
    return token


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


async def _fetch_pin_raw(client: httpx.AsyncClient, pin: str) -> str:
    # Blynk expects `...&v0` style query params (pin name as key).
    url = f"{_api_base()}/external/api/get?token={_token()}&{pin}"
    resp = await client.get(url, timeout=15)
    if resp.status_code >= 400:
        logger.error("Blynk pin %s failed: %s %s", pin, resp.status_code, resp.text[:200])
        resp.raise_for_status()
    return resp.text.strip()


async def is_hardware_connected() -> bool:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"{_api_base()}/external/api/isHardwareConnected?token={_token()}"
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text.strip().lower() == "true"
    except Exception as exc:
        logger.warning("Blynk connectivity check failed: %s", exc)
        return False


async def fetch_live_snapshot() -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=15) as client:
        values: dict[str, str] = {}
        for pin in (*NUMERIC_PINS, STATUS_PIN):
            values[pin] = await _fetch_pin_raw(client, pin)

    try:
        temperature = float(values["v0"])
        humidity = float(values["v1"])
        soil_raw = float(values["v2"])
        light_raw = float(values["v3"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Unexpected Blynk numeric response: {values}") from exc

    soil_status = soil_label_from_status(values.get(STATUS_PIN, soil_label_from_raw(soil_raw)))
    now = int(time.time())
    return {
        "id": 0,
        "pot_index": 0,
        "ts": now,
        "temperature": temperature,
        "humidity": humidity,
        "soil_moisture": soil_raw,
        "light": light_raw,
        "soil_status": soil_status,
        "ph": 6.5,
    }


async def _fetch_pin_history(client: httpx.AsyncClient, pin: str, from_ms: int, to_ms: int) -> list[tuple[int, float]]:
    url = f"{_api_base()}/external/api/data/get"
    resp = await client.get(
        url,
        params={
            "token": _token(),
            "pin": pin,
            "from": from_ms,
            "to": to_ms,
        },
        timeout=15,
    )
    if resp.status_code >= 400:
        logger.warning("Blynk history %s failed: %s", pin, resp.status_code)
        return []

    text = resp.text.strip()
    if not text:
        return []

    try:
        rows = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse Blynk history for %s: %s", pin, text[:120])
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
    async with httpx.AsyncClient(timeout=15) as client:
        for pin in NUMERIC_PINS:
            try:
                histories[pin] = await _fetch_pin_history(client, pin, from_ms, now_ms)
            except Exception as exc:
                logger.warning("Blynk history fetch failed for %s: %s", pin, exc)
                histories[pin] = []

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
            if idx < len(series):
                return float(series[idx][1])
            return float(series[-1][1])

        readings.append(
            {
                "id": idx + 1,
                "pot_index": 0,
                "ts": ts,
                "temperature": temperature,
                "humidity": nearest("v1", live["humidity"]),
                "soil_moisture": nearest("v2", live["soil_moisture"]),
                "light": nearest("v3", live["light"]),
                "soil_status": soil_label_from_raw(nearest("v2", live["soil_moisture"])),
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
