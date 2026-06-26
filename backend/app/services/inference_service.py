import sys
from pathlib import Path

from app.config import get_settings

settings = get_settings()
_model = None


def _get_model():
    global _model
    if _model is None:
        ai_root = Path(__file__).resolve().parents[3] / "ai"
        sys.path.insert(0, str(ai_root))
        from inference import SmartPlantDoctor

        model_path = ai_root / "exports" / "smart_plant_doctor_model.pth"
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
