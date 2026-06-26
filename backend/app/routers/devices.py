import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Device, DeviceCommand, DevicePot, User
from app.schemas import (
    DeviceClaimRequest,
    DeviceClaimResponse,
    DeviceCommandOut,
    DeviceCommandRequest,
    DeviceOut,
    DeviceRegisterResponse,
)
from app.security import generate_token, hash_token

router = APIRouter(prefix="/devices", tags=["devices"])
settings = get_settings()


@router.post("/register", response_model=DeviceRegisterResponse)
def register_device(
    name: str = "ESP32 Sensor",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    setup_token = generate_token()
    device = Device(
        user_id=user.id,
        name=name,
        setup_token_hash=hash_token(setup_token),
        setup_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        is_claimed=False,
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    qr_payload = json.dumps(
        {
            "setup_token": setup_token,
            "api_url": settings.public_api_url,
            "device_id": device.id,
        }
    )
    claim_url = f"{settings.public_api_url}{settings.api_v1_prefix}/devices/claim"
    return DeviceRegisterResponse(
        device_id=device.id,
        setup_token=setup_token,
        qr_payload=qr_payload,
        claim_url=claim_url,
    )


@router.post("/claim", response_model=DeviceClaimResponse)
def claim_device(payload: DeviceClaimRequest, db: Session = Depends(get_db)):
    token_hash = hash_token(payload.setup_token)
    device = db.query(Device).filter(Device.setup_token_hash == token_hash).first()
    if not device:
        raise HTTPException(status_code=404, detail="Invalid setup token")
    if device.setup_expires_at and device.setup_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Setup token expired")
    if device.is_claimed:
        raise HTTPException(status_code=400, detail="Device already claimed")

    device_token = generate_token()
    device.token_hash = hash_token(device_token)
    device.setup_token_hash = None
    device.is_claimed = True
    device.firmware_version = payload.firmware_version
    device.last_seen = datetime.now(timezone.utc)
    if not device.pots:
        for i in range(4):
            db.add(DevicePot(device_id=device.id, pot_index=i))
    db.commit()

    ingest_url = f"{settings.public_api_url}{settings.api_v1_prefix}/ingest"
    return DeviceClaimResponse(device_token=device_token, ingest_url=ingest_url, device_id=device.id)


@router.get("", response_model=list[DeviceOut])
def list_devices(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Device).filter(Device.user_id == user.id).order_by(Device.id).all()


@router.post("/{device_id}/commands", response_model=DeviceCommandOut)
def create_command(
    device_id: int,
    payload: DeviceCommandRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = db.query(Device).filter(Device.id == device_id, Device.user_id == user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    cmd = DeviceCommand(
        device_id=device.id,
        action=payload.action,
        pot_index=payload.pot_index,
        duration_sec=payload.duration_sec,
    )
    db.add(cmd)
    db.commit()
    db.refresh(cmd)
    return cmd


