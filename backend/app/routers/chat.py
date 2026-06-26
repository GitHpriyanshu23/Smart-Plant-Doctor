from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import CareEvent, Diagnosis, Plant, Reading, SpeciesProfile, User
from app.schemas import ChatRequest, ChatResponse
from app.services.llm_service import get_chat_reply, stream_chat_reply

router = APIRouter(prefix="/chat", tags=["chat"])


def _build_context(db: Session, user: User, plant_id: int | None) -> str:
    if not plant_id:
        return (
            "General plant care query — no specific plant selected. "
            "The user may ask about any plant species, disease, watering, or care topic."
        )

    plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")

    reading = db.query(Reading).filter(Reading.plant_id == plant_id).order_by(Reading.ts.desc()).first()
    diagnosis = (
        db.query(Diagnosis)
        .filter(Diagnosis.plant_id == plant_id, Diagnosis.status == "success")
        .order_by(Diagnosis.created_at.desc())
        .first()
    )
    care = db.query(CareEvent).filter(CareEvent.plant_id == plant_id).order_by(CareEvent.created_at.desc()).limit(3).all()
    profile = db.query(SpeciesProfile).filter(SpeciesProfile.species == plant.species).first()

    parts = [
        f"Plant: {plant.nickname} ({plant.species})",
    ]
    if reading:
        parts.append(
            f"Current readings: temp {reading.temperature}°C, humidity {reading.humidity}%, "
            f"soil {reading.soil_moisture}%, light {reading.light} lux, pH {reading.ph}"
        )
    if diagnosis:
        parts.append(
            f"Last diagnosis: {diagnosis.disease} ({diagnosis.confidence:.1f}%) on {diagnosis.created_at.date()}"
        )
    if care:
        parts.append("Recent care: " + ", ".join(f"{c.event_type.value} on {c.created_at.date()}" for c in care))
    if profile and profile.care_guide:
        parts.append(f"Care guide excerpt: {profile.care_guide[:500]}")

    return "\n".join(parts)


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    context = _build_context(db, user, payload.plant_id)
    reply = get_chat_reply(context, payload.message)
    return ChatResponse(reply=reply)


@router.post("/stream")
def chat_stream(payload: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    context = _build_context(db, user, payload.plant_id)

    def generate():
        for chunk in stream_chat_reply(context, payload.message):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")
