from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import DiseaseReport, SpeciesProfile, User
from app.schemas import DiseaseMapPoint, DiseaseReportCreate, SpeciesProfileOut
from app.services.geohash_util import encode as geohash_encode

router = APIRouter(tags=["content"])


def _bucket_geohash(lat: float, lng: float, precision: int = 4) -> str:
    return geohash_encode(lat, lng, precision=precision)


@router.get("/encyclopedia", response_model=list[SpeciesProfileOut])
def list_species(db: Session = Depends(get_db)):
    return db.query(SpeciesProfile).order_by(SpeciesProfile.species).all()


@router.get("/encyclopedia/{species}", response_model=SpeciesProfileOut)
def get_species(species: str, db: Session = Depends(get_db)):
    profile = db.query(SpeciesProfile).filter(SpeciesProfile.species == species).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Species not found")
    return profile


@router.post("/disease-reports", status_code=201)
def create_disease_report(
    payload: DiseaseReportCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    gh = "unknown"
    if payload.latitude is not None and payload.longitude is not None:
        gh = _bucket_geohash(payload.latitude, payload.longitude)
    report = DiseaseReport(
        user_id=None,
        disease=payload.disease,
        species=payload.species,
        geohash=gh,
        region=payload.region,
    )
    db.add(report)
    db.commit()
    return {"ok": True}


@router.get("/disease-map", response_model=list[DiseaseMapPoint])
def disease_map(region: str | None = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(
        DiseaseReport.geohash,
        DiseaseReport.region,
        DiseaseReport.disease,
        func.count(DiseaseReport.id).label("count"),
    ).group_by(DiseaseReport.geohash, DiseaseReport.region, DiseaseReport.disease)
    if region:
        q = q.filter(DiseaseReport.region == region)
    rows = q.all()
    return [
        DiseaseMapPoint(geohash=r.geohash, region=r.region, disease=r.disease, count=r.count)
        for r in rows
    ]
