from __future__ import annotations

from datetime import date
from typing import Any

from app.models.enums import RiskLevel
from app.services.geo import centroid, haversine_km, point_in_geojson


def _level(score: float) -> str:
    if score >= 85:
        return RiskLevel.CRITICAL.value
    if score >= 65:
        return RiskLevel.HIGH.value
    if score >= 40:
        return RiskLevel.MEDIUM.value
    return RiskLevel.LOW.value


def evaluate_claim_or_request(
    *,
    reported: float,
    estimated: float | None,
    amount: float | None,
    incident: date | None,
    disaster_start: date | None,
    disaster_end: date | None,
    geometry: dict[str, Any] | None,
    disaster_boundary: dict[str, Any] | None,
    nearby_count: int = 0,
    median_amount: float | None = None,
) -> dict[str, Any]:
    """Anomaly *risk* only. Never labels a person or organisation as fraudulent."""
    reasons: list[str] = []
    score = 8.0

    if estimated is not None:
        delta = abs(reported - estimated)
        if delta >= 40:
            score += 38
            reasons.append("Significant difference between reported damage and remote-sensing estimate")
        elif delta >= 20:
            score += 22
            reasons.append("Notable difference between reported damage and remote-sensing estimate")
        elif delta >= 10:
            score += 10
            reasons.append("Moderate difference between reported and estimated damage")

    if incident and disaster_start and incident < disaster_start:
        score += 28
        reasons.append("Incident date is before the recorded disaster start")
    if incident and disaster_end and incident > disaster_end:
        score += 18
        reasons.append("Incident date is after the recorded disaster end")

    c = centroid(geometry)
    if c and disaster_boundary and not point_in_geojson(c, disaster_boundary):
        # still allow near-boundary
        bc = centroid(disaster_boundary)
        if not bc or haversine_km(c, bc) > 25:
            score += 32
            reasons.append("Reported location sits outside the recorded affected-area boundary")

    if nearby_count >= 8:
        score += 16
        reasons.append("Abnormal concentration of similar records in the same locality")
    elif nearby_count >= 4:
        score += 8
        reasons.append("Elevated concentration of similar records nearby")

    if amount is not None and median_amount and median_amount > 0:
        ratio = amount / median_amount
        if ratio >= 4:
            score += 24
            reasons.append("Requested amount is unusually high versus similar records")
        elif ratio >= 2.5:
            score += 12
            reasons.append("Requested amount is elevated versus similar records")

    score = min(99.0, round(score, 1))
    level = _level(score)
    action = {
        RiskLevel.CRITICAL.value: "Prioritise independent field verification and senior review before any financial decision.",
        RiskLevel.HIGH.value: "Assign field verification and retain the case in the review queue.",
        RiskLevel.MEDIUM.value: "Request additional evidence and a second officer review.",
        RiskLevel.LOW.value: "Continue routine documentary review.",
    }[level]
    return {"risk_score": score, "risk_level": level, "reasons": reasons or ["No elevated anomaly patterns detected"], "recommended_action": action}
