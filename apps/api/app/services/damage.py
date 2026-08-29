from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.ai.providers import get_change_detection, get_damage_classifier
from app.models.entities import DamageAssessment, DisasterEvent
from app.services.ids import public_id


class DamageAssessmentService:
    """Orchestrates change detection + classification.

    Swap providers via CHANGE_DETECTION_URL / DAMAGE_CLASSIFIER_URL.
    This class must not approve claims or funds.
    """

    def analyse(
        self,
        db: Session,
        *,
        disaster: DisasterEvent,
        job_id: int,
        created_by_id: int,
        aoi: dict[str, Any] | None,
        notes: str,
        before_image_id: int | None,
        after_image_id: int | None,
        before_key: str | None,
        after_key: str | None,
    ) -> dict[str, Any]:
        change = get_change_detection().detect(
            before_key=before_key,
            after_key=after_key,
            aoi=aoi or disaster.boundary,
            disaster_type=disaster.disaster_type,
        )
        classes = get_damage_classifier().classify(
            disaster_type=disaster.disaster_type,
            aoi=aoi or disaster.boundary,
        )
        created: list[int] = []
        for item in classes:
            row = DamageAssessment(
                public_id=public_id("DAS"),
                disaster_id=disaster.id,
                category=item["category"],
                severity=item["severity"],
                estimated_area_ha=item["estimated_area_ha"],
                confidence=round(item["confidence"] * change["confidence"], 3),
                geometry=aoi or disaster.boundary,
                notes=notes or change["notes"],
                before_image_id=before_image_id,
                after_image_id=after_image_id,
                job_id=job_id,
                analyzed_at=datetime.now(timezone.utc),
                created_by_id=created_by_id,
            )
            db.add(row)
            db.flush()
            created.append(row.id)
        return {"change": change, "assessment_ids": created}
