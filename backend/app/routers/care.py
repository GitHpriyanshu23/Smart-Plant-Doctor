from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import CareEvent, CareEventType, Plant, User
from app.schemas import CareEventCreate, CareEventOut

router = APIRouter(prefix="/plants", tags=["care"])


@router.post("/{plant_id}/care-events", response_model=CareEventOut, status_code=201)
def create_care_event(
    plant_id: int,
    payload: CareEventCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    try:
        event_type = CareEventType(payload.event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid event type")
    event = CareEvent(plant_id=plant_id, event_type=event_type, notes=payload.notes)
    db.add(event)
    db.commit()
    db.refresh(event)
    return CareEventOut(
        id=event.id,
        plant_id=event.plant_id,
        event_type=event.event_type.value,
        notes=event.notes,
        created_at=event.created_at,
    )


@router.get("/{plant_id}/care-events", response_model=list[CareEventOut])
def list_care_events(
    plant_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    events = db.query(CareEvent).filter(CareEvent.plant_id == plant_id).order_by(CareEvent.created_at.desc()).all()
    return [
        CareEventOut(
            id=e.id,
            plant_id=e.plant_id,
            event_type=e.event_type.value,
            notes=e.notes,
            created_at=e.created_at,
        )
        for e in events
    ]
