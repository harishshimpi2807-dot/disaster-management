from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.session import utcnow
from app.models.entities import AnalysisJob, DisasterEvent
from app.models.enums import JobStatus
from app.services.damage import DamageAssessmentService


def run_job(db: Session, job: AnalysisJob) -> None:
    job.status = JobStatus.RUNNING.value
    job.started_at = utcnow()
    db.commit()
    try:
        if job.job_type == "damage_assessment":
            payload = job.payload or {}
            disaster = db.get(DisasterEvent, payload["disaster_id"])
            if not disaster:
                raise ValueError("Disaster not found")
            job.result = DamageAssessmentService().analyse(
                db,
                disaster=disaster,
                job_id=job.id,
                created_by_id=job.created_by_id,
                aoi=payload.get("aoi"),
                notes=payload.get("notes") or "",
                before_image_id=payload.get("before_image_id"),
                after_image_id=payload.get("after_image_id"),
                before_key=payload.get("before_key"),
                after_key=payload.get("after_key"),
            )
        else:
            job.result = {"ok": True}
        job.status = JobStatus.COMPLETED.value
        job.finished_at = utcnow()
    except Exception as exc:  # noqa: BLE001 — persist failure for operators
        job.status = JobStatus.FAILED.value
        job.error = str(exc)
        job.finished_at = utcnow()
    db.commit()
