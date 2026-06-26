import os
import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Diagnosis, Plant, User
from app.schemas import DiagnosisOut
from app.services.inference_service import run_diagnosis

router = APIRouter(prefix="/diagnose", tags=["diagnosis"])
settings = get_settings()


@router.post("", response_model=dict)
async def diagnose(
    file: UploadFile = File(...),
    plant_id: int | None = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if plant_id:
        plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user.id).first()
        if not plant:
            raise HTTPException(status_code=404, detail="Plant not found")

    uploads = Path(settings.uploads_dir)
    uploads.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "image.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = uploads / filename
    content = await file.read()
    dest.write_bytes(content)

    result = run_diagnosis(str(dest))

    image_url = f"/uploads/{filename}"
    diagnosis = Diagnosis(
        plant_id=plant_id,
        user_id=user.id,
        image_url=image_url,
        class_name=result.get("class_name"),
        plant_species=result.get("plant"),
        disease=result.get("disease"),
        confidence=result.get("confidence"),
        status=result.get("status", "success"),
        treatment_json=result.get("treatment"),
    )
    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)

    return {
        "diagnosis_id": diagnosis.id,
        "image_url": image_url,
        **result,
    }


@router.get("/history", response_model=list[DiagnosisOut])
def diagnosis_history(
    plant_id: int | None = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Diagnosis).filter(Diagnosis.user_id == user.id)
    if plant_id:
        q = q.filter(Diagnosis.plant_id == plant_id)
    return q.order_by(Diagnosis.created_at.desc()).limit(limit).all()


@router.get("/plants/{plant_id}/diagnoses", response_model=list[DiagnosisOut])
def plant_diagnoses(
    plant_id: int,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return (
        db.query(Diagnosis)
        .filter(Diagnosis.plant_id == plant_id)
        .order_by(Diagnosis.created_at.desc())
        .limit(limit)
        .all()
    )
