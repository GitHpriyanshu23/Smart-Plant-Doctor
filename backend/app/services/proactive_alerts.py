"""Rule-based proactive alerts evaluated on each ingest."""

from sqlalchemy.orm import Session

from app.models import Reading


def evaluate_proactive_alerts(db: Session, plant_id: int, reading: Reading) -> list[str]:
    alerts: list[str] = []
    recent = (
        db.query(Reading)
        .filter(Reading.plant_id == plant_id)
        .order_by(Reading.ts.desc())
        .limit(4)
        .all()
    )
    if len(recent) >= 3:
        drops = [recent[i].soil_moisture - recent[i + 1].soil_moisture for i in range(len(recent) - 1)]
        if all(d > 5 for d in drops):
            alerts.append("Water soon: soil moisture dropping quickly")

    if reading.humidity > 75 and reading.temperature > 26:
        alerts.append("Fungal disease risk elevated: warm and humid conditions")

    return alerts
