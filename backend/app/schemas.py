from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PlantCreate(BaseModel):
    species: str
    nickname: str
    device_id: int | None = None
    pot_index: int | None = None


class PlantUpdate(BaseModel):
    species: str | None = None
    nickname: str | None = None
    device_id: int | None = None
    pot_index: int | None = None


class PlantOut(BaseModel):
    id: int
    species: str
    nickname: str
    device_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReadingOut(BaseModel):
    id: int
    plant_id: int | None
    pot_index: int
    ts: int
    temperature: float
    humidity: float
    light: float
    soil_moisture: float
    ph: float
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestReadingItem(BaseModel):
    pot_index: int = 0
    ts: int
    temperature: float
    humidity: float
    light: float
    soil_moisture: float
    ph: float = 6.5


class IngestPayload(BaseModel):
    readings: list[IngestReadingItem]


class DeviceRegisterResponse(BaseModel):
    device_id: int
    setup_token: str
    qr_payload: str
    claim_url: str


class DeviceClaimRequest(BaseModel):
    setup_token: str
    firmware_version: str | None = None


class DeviceClaimResponse(BaseModel):
    device_token: str
    ingest_url: str
    device_id: int


class DeviceOut(BaseModel):
    id: int
    name: str
    is_claimed: bool
    last_seen: datetime | None
    firmware_version: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceCommandRequest(BaseModel):
    action: str
    pot_index: int = 0
    duration_sec: int = 5


class DeviceCommandOut(BaseModel):
    id: int
    action: str
    pot_index: int
    duration_sec: int
    status: str

    model_config = {"from_attributes": True}


class DiagnosisOut(BaseModel):
    id: int
    plant_id: int | None
    image_url: str
    class_name: str | None
    plant_species: str | None
    disease: str | None
    confidence: float | None
    status: str
    treatment_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CareEventCreate(BaseModel):
    event_type: str
    notes: str | None = None


class CareEventOut(BaseModel):
    id: int
    plant_id: int
    event_type: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SpeciesProfileOut(BaseModel):
    id: int
    species: str
    thresholds: dict
    care_guide: str
    seasonal_tips: str
    common_diseases: dict | None

    model_config = {"from_attributes": True}


class DiseaseReportCreate(BaseModel):
    disease: str
    species: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    region: str | None = None


class DiseaseMapPoint(BaseModel):
    geohash: str
    region: str | None
    disease: str
    count: int


class ChatRequest(BaseModel):
    plant_id: int | None = None
    message: str


class ChatResponse(BaseModel):
    reply: str
