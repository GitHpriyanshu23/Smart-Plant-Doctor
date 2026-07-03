import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_user_from_token_string
from app.models import Device, DevicePot, Plant, Reading, User
from app.schemas import BlynkReadingsResponse, DeviceCommandOut, IngestPayload, ReadingOut
from app.security import hash_token
from app.services.blynk_service import fetch_readings as fetch_blynk_readings
from app.services.proactive_alerts import evaluate_proactive_alerts
from app.ws_manager import ws_manager

router = APIRouter(tags=["sensors"])
logger = logging.getLogger("uvicorn.error")


@router.get("/sensors/blynk/readings", response_model=BlynkReadingsResponse)
async def get_blynk_readings(
    hours: int = Query(default=1, ge=1, le=24),
    _user: User = Depends(get_current_user),
):
    try:
        payload = await fetch_blynk_readings(hours=hours)
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Blynk readings fetch failed")
        raise HTTPException(status_code=502, detail="Failed to fetch Blynk sensor data") from exc


def _get_device_from_token(authorization: str, db: Session) -> Device:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")
    token = authorization.removeprefix("Bearer ").strip()
    device = db.query(Device).filter(Device.token_hash == hash_token(token), Device.is_claimed == True).first()
    if not device:
        raise HTTPException(status_code=401, detail="unauthorized")
    return device


@router.post("/ingest")
async def ingest(
    payload: IngestPayload,
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
):
    device = _get_device_from_token(authorization, db)
    device.last_seen = datetime.now(timezone.utc)

    pot_map = {p.pot_index: p.plant_id for p in device.pots}
    inserted: list[Reading] = []

    for item in payload.readings:
        plant_id = pot_map.get(item.pot_index)
        reading = Reading(
            device_id=device.id,
            plant_id=plant_id,
            pot_index=item.pot_index,
            ts=item.ts,
            temperature=item.temperature,
            humidity=item.humidity,
            light=item.light,
            soil_moisture=item.soil_moisture,
            ph=item.ph,
        )
        db.add(reading)
        inserted.append(reading)

    db.commit()

    for reading in inserted:
        db.refresh(reading)
        if reading.plant_id:
            data = {
                "id": reading.id,
                "plant_id": reading.plant_id,
                "pot_index": reading.pot_index,
                "ts": reading.ts,
                "temperature": reading.temperature,
                "humidity": reading.humidity,
                "light": reading.light,
                "soil_moisture": reading.soil_moisture,
                "ph": reading.ph,
            }
            await ws_manager.broadcast(reading.plant_id, data)
            evaluate_proactive_alerts(db, reading.plant_id, reading)

    return {"ok": True, "count": len(inserted)}


@router.get("/plants/{plant_id}/readings", response_model=list[ReadingOut])
def get_readings(
    plant_id: int,
    limit: int = Query(default=500, le=2000),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return (
        db.query(Reading)
        .filter(Reading.plant_id == plant_id)
        .order_by(Reading.ts.desc())
        .limit(limit)
        .all()
    )


@router.get("/plants/{plant_id}/readings/latest", response_model=ReadingOut | None)
def get_latest_reading(
    plant_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return db.query(Reading).filter(Reading.plant_id == plant_id).order_by(Reading.ts.desc()).first()


@router.websocket("/ws/plants/{plant_id}")
async def plant_websocket(plant_id: int, websocket: WebSocket, token: str = Query(...)):
    db = next(get_db())
    try:
        user = get_user_from_token_string(db, token)
        if not user:
            await websocket.close(code=4401)
            return
        plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user.id).first()
        if not plant:
            await websocket.close(code=4404)
            return
    finally:
        db.close()

    await ws_manager.connect(plant_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(plant_id, websocket)


@router.get("/devices/{device_id}/commands/pending", response_model=list[DeviceCommandOut])
def device_pending_commands(
    device_id: int,
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
):
    device = _get_device_from_token(authorization, db)
    if device.id != device_id:
        raise HTTPException(status_code=403, detail="forbidden")
    from app.models import DeviceCommand

    cmds = (
        db.query(DeviceCommand)
        .filter(DeviceCommand.device_id == device_id, DeviceCommand.status == "pending")
        .order_by(DeviceCommand.id)
        .all()
    )
    for cmd in cmds:
        cmd.status = "sent"
    db.commit()
    return cmds
