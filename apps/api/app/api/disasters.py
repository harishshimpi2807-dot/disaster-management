from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select

from app.core.deps import MANAGERS, CurrentUser, Db, require_roles
from app.db.session import utcnow
from app.models.entities import (
    AgriculturalClaim,
    AnomalyAlert,
    DamageAssessment,
    DisasterEvent,
    FieldInspection,
    FundAllocation,
    FundRequest,
    RecoveryRecord,
    SatelliteImage,
)
from app.models.enums import DisasterType, LifecycleStatus, Severity
from app.schemas import DisasterIn, DisasterOut
from app.services.audit import audit
from app.services.ids import public_id
from app.services.pagination import paginate

router = APIRouter(prefix="/disasters", tags=["disasters"])


@router.get("", response_model=list[DisasterOut])
def list_disasters(
    db: Db,
    user: CurrentUser,
    q: str = "",
    disaster_type: str = "",
    status: str = "",
    state: str = "",
    severity: str = "",
    page: int = 1,
    page_size: int = 20,
):
    stmt = select(DisasterEvent).where(DisasterEvent.deleted_at.is_(None)).order_by(DisasterEvent.start_date.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(DisasterEvent.name.ilike(like), DisasterEvent.public_id.ilike(like), DisasterEvent.district.ilike(like)))
    if disaster_type:
        stmt = stmt.where(DisasterEvent.disaster_type == disaster_type)
    if status:
        stmt = stmt.where(DisasterEvent.status == status)
    if state:
        stmt = stmt.where(DisasterEvent.state.ilike(state))
    if severity:
        stmt = stmt.where(DisasterEvent.severity == severity)
    items, _ = paginate(db, stmt, page, page_size)
    return items


@router.get("/{disaster_id}", response_model=DisasterOut)
def get_disaster(disaster_id: int, db: Db, user: CurrentUser):
    row = db.get(DisasterEvent, disaster_id)
    if not row or row.deleted_at:
        raise HTTPException(404, "Disaster not found")
    return row


@router.post("", response_model=DisasterOut, dependencies=[Depends(require_roles(*MANAGERS))])
def create_disaster(payload: DisasterIn, db: Db, actor: CurrentUser):
    _validate(payload)
    row = DisasterEvent(public_id=public_id("DSE"), created_by_id=actor.id, **payload.model_dump())
    db.add(row)
    db.flush()
    audit(db, actor_id=actor.id, action="create", entity_type="disaster", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{disaster_id}", response_model=DisasterOut, dependencies=[Depends(require_roles(*MANAGERS))])
def update_disaster(disaster_id: int, payload: DisasterIn, db: Db, actor: CurrentUser):
    row = db.get(DisasterEvent, disaster_id)
    if not row or row.deleted_at:
        raise HTTPException(404, "Disaster not found")
    _validate(payload)
    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    audit(db, actor_id=actor.id, action="update", entity_type="disaster", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{disaster_id}", dependencies=[Depends(require_roles(*MANAGERS))])
def archive_disaster(disaster_id: int, db: Db, actor: CurrentUser):
    row = db.get(DisasterEvent, disaster_id)
    if not row or row.deleted_at:
        raise HTTPException(404, "Disaster not found")
    row.deleted_at = utcnow()
    row.status = LifecycleStatus.CLOSED.value
    audit(db, actor_id=actor.id, action="archive", entity_type="disaster", entity_id=row.id)
    db.commit()
    return {"ok": True, "public_id": row.public_id}


@router.get("/{disaster_id}/dossier")
def disaster_dossier(disaster_id: int, db: Db, user: CurrentUser):
    row = db.get(DisasterEvent, disaster_id)
    if not row or row.deleted_at:
        raise HTTPException(404, "Disaster not found")
    assessments = db.scalars(select(DamageAssessment).where(DamageAssessment.disaster_id == row.id)).all()
    claims = db.scalars(select(AgriculturalClaim).where(AgriculturalClaim.disaster_id == row.id)).all()
    funds = db.scalars(select(FundRequest).where(FundRequest.disaster_id == row.id)).all()
    allocs = db.scalars(select(FundAllocation).where(FundAllocation.disaster_id == row.id)).all()
    recs = db.scalars(select(RecoveryRecord).where(RecoveryRecord.disaster_id == row.id)).all()
    ins = db.scalars(select(FieldInspection).where(FieldInspection.disaster_id == row.id)).all()
    alerts = db.scalars(select(AnomalyAlert).where(AnomalyAlert.disaster_id == row.id)).all()
    images = db.scalars(select(SatelliteImage).where(SatelliteImage.disaster_id == row.id)).all()
    return {
        "disaster": DisasterOut.model_validate(row).model_dump(),
        "assessments": [{"id": a.id, "public_id": a.public_id, "category": a.category, "severity": a.severity, "estimated_area_ha": a.estimated_area_ha, "confidence": a.confidence} for a in assessments],
        "claims": [{"id": c.id, "public_id": c.public_id, "status": c.status, "reported_damage_pct": c.reported_damage_pct, "estimated_damage_pct": c.estimated_damage_pct} for c in claims],
        "fund_requests": [{"id": f.id, "public_id": f.public_id, "department": f.department, "requested_amount": f.requested_amount, "status": f.status} for f in funds],
        "allocations": [{"id": a.id, "public_id": a.public_id, "purpose": a.purpose, "status": a.status, "observed_progress_pct": a.observed_progress_pct, "planned_progress_pct": a.planned_progress_pct} for a in allocs],
        "recovery": [{"id": r.id, "public_id": r.public_id, "category": r.category, "phase": r.phase, "recovery_pct": r.recovery_pct, "status": r.status} for r in recs],
        "inspections": [{"id": i.id, "public_id": i.public_id, "status": i.status, "case_type": i.case_type} for i in ins],
        "anomalies": [{"id": a.id, "public_id": a.public_id, "risk_level": a.risk_level, "risk_score": a.risk_score} for a in alerts],
        "imagery": [{"id": i.id, "phase": i.phase, "filename": i.original_filename} for i in images],
    }


def _validate(payload: DisasterIn) -> None:
    if payload.disaster_type not in {t.value for t in DisasterType}:
        raise HTTPException(400, "Invalid disaster type")
    if payload.severity not in {s.value for s in Severity}:
        raise HTTPException(400, "Invalid severity")
    if payload.status not in {s.value for s in LifecycleStatus}:
        raise HTTPException(400, "Invalid status")
