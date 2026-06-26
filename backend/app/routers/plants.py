from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import DevicePot, Plant, User
from app.schemas import PlantCreate, PlantOut, PlantUpdate

router = APIRouter(prefix="/plants", tags=["plants"])


def _link_device_pot(db: Session, plant: Plant, device_id: int | None, pot_index: int | None):
    if device_id is None:
        return
    pot = (
        db.query(DevicePot)
        .filter(DevicePot.device_id == device_id, DevicePot.pot_index == (pot_index or 0))
        .first()
    )
    if not pot:
        pot = DevicePot(device_id=device_id, pot_index=pot_index or 0, plant_id=plant.id)
        db.add(pot)
    else:
        pot.plant_id = plant.id
    plant.device_id = device_id


@router.get("", response_model=list[PlantOut])
def list_plants(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Plant).filter(Plant.user_id == user.id).order_by(Plant.id).all()


@router.post("", response_model=PlantOut, status_code=201)
def create_plant(payload: PlantCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plant = Plant(user_id=user.id, species=payload.species, nickname=payload.nickname, device_id=payload.device_id)
    db.add(plant)
    db.flush()
    _link_device_pot(db, plant, payload.device_id, payload.pot_index)
    db.commit()
    db.refresh(plant)
    return plant


@router.get("/{plant_id}", response_model=PlantOut)
def get_plant(plant_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


@router.patch("/{plant_id}", response_model=PlantOut)
def update_plant(
    plant_id: int,
    payload: PlantUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    if payload.species is not None:
        plant.species = payload.species
    if payload.nickname is not None:
        plant.nickname = payload.nickname
    if payload.device_id is not None:
        _link_device_pot(db, plant, payload.device_id, payload.pot_index)
    db.commit()
    db.refresh(plant)
    return plant


@router.delete("/{plant_id}", status_code=204)
def delete_plant(plant_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plant = db.query(Plant).filter(Plant.id == plant_id, Plant.user_id == user.id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Plant not found")
    db.delete(plant)
    db.commit()
