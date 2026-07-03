from pathlib import Path

from app.config import get_settings
from app.ml.inference import SmartPlantDoctor

settings = get_settings()
_model = None

_BUNDLED_MODEL = (
    Path(__file__).resolve().parent.parent / "ml" / "exports" / "smart_plant_doctor_model.pth"
)


def _model_path() -> Path:
    if settings.model_path:
        configured = Path(settings.model_path)
        if configured.is_file():
            return configured
    if _BUNDLED_MODEL.is_file():
        return _BUNDLED_MODEL
    repo_model = Path(__file__).resolve().parents[3] / "ai" / "exports" / "smart_plant_doctor_model.pth"
    if repo_model.is_file():
        return repo_model
    raise FileNotFoundError(
        f"Model weights not found. Checked {_BUNDLED_MODEL} and {repo_model}"
    )


def _get_model():
    global _model
    if _model is None:
        model_path = _model_path()
        _model = SmartPlantDoctor(model_path=str(model_path))
    return _model


def run_diagnosis(image_path: str) -> dict:
    model = _get_model()
    result = model.predict(image_path)

    if "error" in result:
        return {"status": "error", "message": result["error"], "confidence": 0}

    confidence = (result.get("confidence") or 0) / 100.0
    calibrated = confidence / max(settings.model_temperature, 0.01)

    if calibrated < settings.confidence_threshold:
        return {
            "status": "low_confidence",
            "message": "Try a clearer photo — ensure good lighting and focus on affected leaves.",
            "confidence": calibrated * 100,
            "plant": result.get("plant"),
            "disease": result.get("disease"),
            "class_name": result.get("class_name"),
        }

    return {
        "status": "success",
        "plant": result.get("plant"),
        "disease": result.get("disease"),
        "confidence": calibrated * 100,
        "class_name": result.get("class_name"),
        "treatment": result.get("treatment"),
        "output_format": result.get("output_format"),
    }
