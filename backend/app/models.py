import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CareEventType(str, enum.Enum):
    water = "water"
    fertilize = "fertilize"
    prune = "prune"
    repot = "repot"
    note = "note"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    supabase_id: Mapped[str | None] = mapped_column(String(36), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    plants: Mapped[list["Plant"]] = relationship(back_populates="user")
    devices: Mapped[list["Device"]] = relationship(back_populates="user")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), default="ESP32 Sensor")
    token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    setup_token_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    setup_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_claimed: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="devices")
    pots: Mapped[list["DevicePot"]] = relationship(back_populates="device")
    readings: Mapped[list["Reading"]] = relationship(back_populates="device")
    pending_commands: Mapped[list["DeviceCommand"]] = relationship(back_populates="device")


class DevicePot(Base):
    __tablename__ = "device_pots"
    __table_args__ = (UniqueConstraint("device_id", "pot_index", name="uq_device_pot"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    pot_index: Mapped[int] = mapped_column(Integer)
    plant_id: Mapped[int | None] = mapped_column(ForeignKey("plants.id"), nullable=True)

    device: Mapped["Device"] = relationship(back_populates="pots")
    plant: Mapped["Plant | None"] = relationship(back_populates="device_pot")


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    species: Mapped[str] = mapped_column(String(120))
    nickname: Mapped[str] = mapped_column(String(120))
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="plants")
    device_pot: Mapped["DevicePot | None"] = relationship(back_populates="plant", uselist=False)
    readings: Mapped[list["Reading"]] = relationship(back_populates="plant")
    diagnoses: Mapped[list["Diagnosis"]] = relationship(back_populates="plant")
    care_events: Mapped[list["CareEvent"]] = relationship(back_populates="plant")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    plant_id: Mapped[int | None] = mapped_column(ForeignKey("plants.id"), index=True, nullable=True)
    pot_index: Mapped[int] = mapped_column(Integer, default=0)
    ts: Mapped[int] = mapped_column(Integer, index=True)
    temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[float] = mapped_column(Float)
    light: Mapped[float] = mapped_column(Float)
    soil_moisture: Mapped[float] = mapped_column(Float)
    ph: Mapped[float] = mapped_column(Float, default=6.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    device: Mapped["Device"] = relationship(back_populates="readings")
    plant: Mapped["Plant | None"] = relationship(back_populates="readings")


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int | None] = mapped_column(ForeignKey("plants.id"), index=True, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    image_url: Mapped[str] = mapped_column(String(500))
    class_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    plant_species: Mapped[str | None] = mapped_column(String(120), nullable=True)
    disease: Mapped[str | None] = mapped_column(String(200), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="success")
    treatment_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    plant: Mapped["Plant | None"] = relationship(back_populates="diagnoses")


class CareEvent(Base):
    __tablename__ = "care_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), index=True)
    event_type: Mapped[CareEventType] = mapped_column(Enum(CareEventType))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    plant: Mapped["Plant"] = relationship(back_populates="care_events")


class SpeciesProfile(Base):
    __tablename__ = "species_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    species: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    thresholds: Mapped[dict] = mapped_column(JSON)
    care_guide: Mapped[str] = mapped_column(Text, default="")
    seasonal_tips: Mapped[str] = mapped_column(Text, default="")
    common_diseases: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class DiseaseReport(Base):
    __tablename__ = "disease_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    disease: Mapped[str] = mapped_column(String(200))
    species: Mapped[str | None] = mapped_column(String(120), nullable=True)
    geohash: Mapped[str] = mapped_column(String(12), index=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    action: Mapped[str] = mapped_column(String(50))
    pot_index: Mapped[int] = mapped_column(Integer, default=0)
    duration_sec: Mapped[int] = mapped_column(Integer, default=5)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    device: Mapped["Device"] = relationship(back_populates="pending_commands")
