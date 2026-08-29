from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import MANAGERS, REVIEWERS, CurrentUser, Db, require_roles
from app.db.session import SessionLocal
from app.models.entities import AnalysisJob, DamageAssessment, DisasterEvent, SatelliteImage
from app.models.enums import JobStatus
from app.schemas import AssessmentIn, AssessmentOut
from app.services.audit import audit
from app.services.jobs import run_job
from app.services.pagination import paginate

router = APIRouter(tags=["assessments"])


def _bg(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.get(AnalysisJob, job_id)
        if job:
            run_job(db, job)
    finally:
        db.close()


@router.get("/assessments", response_model=list[AssessmentOut])
def list_assessments(db: Db, user: CurrentUser, disaster_id: int | None = None, category: str = "", page: int = 1, page_size: int = 20):
    stmt = select(DamageAssessment).order_by(DamageAssessment.id.desc())
    if disaster_id:
        stmt = stmt.where(DamageAssessment.disaster_id == disaster_id)
    if category:
        stmt = stmt.where(DamageAssessment.category == category)
    items, _ = paginate(db, stmt, page, page_size)
    return items


@router.get("/assessments/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: int, db: Db, user: CurrentUser):
    row = db.get(DamageAssessment, assessment_id)
    if not row:
        raise HTTPException(404, "Assessment not found")
    return row


@router.post("/assessments/analyze", dependencies=[Depends(require_roles(*MANAGERS, *REVIEWERS))])
def trigger_analysis(payload: AssessmentIn, db: Db, actor: CurrentUser, background: BackgroundTasks):
    disaster = db.get(DisasterEvent, payload.disaster_id)
    if not disaster:
        raise HTTPException(404, "Disaster not found")
    before = db.get(SatelliteImage, payload.before_image_id) if payload.before_image_id else None
    after = db.get(SatelliteImage, payload.after_image_id) if payload.after_image_id else None
    job = AnalysisJob(
        job_type="damage_assessment",
        status=JobStatus.QUEUED.value,
        payload={
            "disaster_id": payload.disaster_id,
            "notes": payload.notes,
            "aoi": payload.aoi,
            "before_image_id": payload.before_image_id,
            "after_image_id": payload.after_image_id,
            "before_key": before.storage_key if before else None,
            "after_key": after.storage_key if after else None,
        },
        created_by_id=actor.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    audit(db, actor_id=actor.id, action="analyze", entity_type="assessment_job", entity_id=job.id)
    db.commit()
    background.add_task(_bg, job.id)
    return {"job_id": job.id, "status": job.status}


@router.get("/jobs/{job_id}")
def get_job(job_id: int, db: Db, user: CurrentUser):
    job = db.get(AnalysisJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"id": job.id, "status": job.status, "result": job.result, "error": job.error}
