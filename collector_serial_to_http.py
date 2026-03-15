import argparse
import json
import serial
import requests
import serial.tools.list_ports
import time


def latest_port():
    for p in serial.tools.list_ports.comports():
        if "usbmodem" in p.device or "usbserial" in p.device:
            return p.device
    return None


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def ldr_to_lux(raw: float) -> float:
    # Rough linear map for dashboard trend visualization.
    return clamp((raw / 4095.0) * 1200.0, 0.0, 1200.0)


def raw_soil_to_percent(raw: float) -> float:
    # ESP32 ADC values usually rise as soil gets drier for many modules.
    wet_adc = 1200.0
    dry_adc = 3200.0
    pct = (dry_adc - raw) / (dry_adc - wet_adc) * 100.0
    return clamp(pct, 0.0, 100.0)


def parse_float_after_colon(line: str):
    if ":" not in line:
        return None
    try:
        return float(line.split(":", 1)[1].strip().split()[0])
    except Exception:
        return None


def normalize_payload(payload: dict, plant: str, default_ph: float):
    now_ts = int(time.time())
    normalized = {
        "ts": int(payload.get("ts", now_ts)),
        "plant": str(payload.get("plant", plant)),
        "temperature": float(payload["temperature"]),
        "humidity": float(payload["humidity"]),
        "light": float(payload["light"]),
        "soil_moisture": float(payload["soil_moisture"]),
        "ph": float(payload.get("ph", default_ph)),
    }
    return normalized


def main(port: str, baud: int, endpoint: str, token: str, plant: str, default_ph: float):
    ser = serial.Serial(port, baud, timeout=2)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    staged = {}
    while True:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue
        try:
            # Path 1: direct JSON line from firmware.
            payload = None
            if line.startswith("{") and line.endswith("}"):
                payload = normalize_payload(json.loads(line), plant, default_ph)

            # Path 2: parse current sketch's plain text output.
            if payload is None:
                if line.startswith("Temperature:"):
                    val = parse_float_after_colon(line)
                    if val is not None:
                        staged["temperature"] = val
                elif line.startswith("Humidity:"):
                    val = parse_float_after_colon(line)
                    if val is not None:
                        staged["humidity"] = val
                elif line.startswith("LDR Value:"):
                    val = parse_float_after_colon(line)
                    if val is not None:
                        staged["light"] = ldr_to_lux(val)
                elif line.startswith("Soil Moisture Value:"):
                    val = parse_float_after_colon(line)
                    if val is not None:
                        staged["soil_moisture"] = raw_soil_to_percent(val)

                needed = {"temperature", "humidity", "light", "soil_moisture"}
                if needed.issubset(staged.keys()):
                    payload = normalize_payload(staged, plant, default_ph)
                    staged = {}

            if payload is None:
                continue

            r = requests.post(endpoint, headers=headers, json=payload, timeout=3)
            if r.status_code != 200 or not r.json().get("ok"):
                print("POST failed", r.status_code, r.text)
        except Exception as e:
            # Print a short note and keep going
            print("skip line:", str(e))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Forward Arduino JSON lines over HTTP")
    ap.add_argument("--port", default=latest_port())
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--endpoint", required=True, help="http://<LaptopB-IP>:8000/ingest")
    ap.add_argument("--token", default="changeme")
    ap.add_argument("--plant", default="Money Plant", help="Plant name stored in DB (must match dashboard/alerts names)")
    ap.add_argument("--ph-default", type=float, default=6.5, help="Fallback pH when sensor is unavailable")
    args = ap.parse_args()
    if not args.port:
        raise SystemExit("No serial port found. Plug Arduino and try again.")
    main(args.port, args.baud, args.endpoint, args.token, args.plant, args.ph_default)




