from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import MANAGERS, CurrentUser, Db, require_roles
from app.models.entities import AgriculturalClaim, AnomalyAlert, DamageAssessment, DuplicateMatch, FieldInspection
from app.models.enums import InspectionStatus, Role
from app.schemas import InspectionIn, InspectionOut, InspectionUpdate
from app.services.audit import audit, notify
from app.services.ids import public_id
from app.services.pagination import paginate

router = APIRouter(prefix="/inspections", tags=["inspections"])


@router.get("", response_model=list[InspectionOut])
def list_inspections(db: Db, user: CurrentUser, status: str = "", page: int = 1, page_size: int = 20):
    stmt = select(FieldInspection).order_by(FieldInspection.id.desc())
    if user.role == Role.FIELD_OFFICER.value:
        stmt = stmt.where(FieldInspection.assigned_to_id == user.id)
    if status:
        stmt = stmt.where(FieldInspection.status == status)
    items, _ = paginate(db, stmt, page, page_size)
    return items


@router.get("/{iid}")
def get_inspection(iid: int, db: Db, user: CurrentUser):
    row = db.get(FieldInspection, iid)
    if not row:
        raise HTTPException(404, "Inspection not found")
    if user.role == Role.FIELD_OFFICER.value and row.assigned_to_id != user.id:
        raise HTTPException(403, "Not assigned to you")
    context: dict = {}
    if row.case_type == "claim":
        claim = db.get(AgriculturalClaim, row.case_id)
        if claim:
            context["claim"] = {
                "public_id": claim.public_id,
                "reported_damage_pct": claim.reported_damage_pct,
                "estimated_damage_pct": claim.estimated_damage_pct,
                "status": claim.status,
                "recommendation": claim.recommendation,
            }
    elif row.case_type == "assessment":
        a = db.get(DamageAssessment, row.case_id)
        if a:
            context["assessment"] = {
                "public_id": a.public_id,
                "category": a.category,
                "estimated_area_ha": a.estimated_area_ha,
                "confidence": a.confidence,
            }
    alerts = db.scalars(select(AnomalyAlert).where(AnomalyAlert.entity_id == row.case_id)).all()
    dupes = db.scalars(
        select(DuplicateMatch).where((DuplicateMatch.left_id == row.case_id) | (DuplicateMatch.right_id == row.case_id))
    ).all()
    return {
        **InspectionOut.model_validate(row).model_dump(),
        "context": context,
        "anomaly_alerts": [{"public_id": a.public_id, "risk_level": a.risk_level, "risk_score": a.risk_score, "reasons": a.reasons} for a in alerts],
        "potential_duplicates": [{"public_id": d.public_id, "similarity": d.similarity, "matching_factors": d.matching_factors} for d in dupes],
    }


@router.post("", response_model=InspectionOut)
def assign(payload: InspectionIn, db: Db, actor: CurrentUser):
    if actor.role not in {r.value for r in MANAGERS} and actor.role != "agri_officer":
        raise HTTPException(403, "You do not have access to this action")
    row = FieldInspection(public_id=public_id("INS"), assigned_by_id=actor.id, **payload.model_dump())
    db.add(row)
    db.flush()
    notify(db, user_id=payload.assigned_to_id, title="Field verification assigned", body=f"{row.public_id} requires on-site verification.", link=f"/app/inspections/{row.id}")
    audit(db, actor_id=actor.id, action="assign", entity_type="inspection", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{iid}", response_model=InspectionOut)
def update(iid: int, payload: InspectionUpdate, db: Db, user: CurrentUser):
    row = db.get(FieldInspection, iid)
    if not row:
        raise HTTPException(404, "Inspection not found")
    if user.role == Role.FIELD_OFFICER.value and row.assigned_to_id != user.id:
        raise HTTPException(403, "Not assigned to you")
    data = payload.model_dump(exclude_unset=True)
    if data.get("status") == InspectionStatus.ARRIVED.value and not row.arrived_at:
        row.arrived_at = datetime.now(timezone.utc)
    if data.get("status") in {InspectionStatus.SUBMITTED.value, InspectionStatus.READY_FOR_REVIEW.value}:
        row.submitted_at = datetime.now(timezone.utc)
    for k, v in data.items():
        setattr(row, k, v)
    audit(db, actor_id=user.id, action="update", entity_type="inspection", entity_id=row.id, detail={"status": row.status})
    db.commit()
    db.refresh(row)
    return row
