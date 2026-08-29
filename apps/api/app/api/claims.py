from __future__ import annotations

import hashlib
from datetime import date

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import REVIEWERS, CurrentUser, Db, require_roles
from app.models.entities import AgriculturalClaim, AnomalyAlert, DisasterEvent, DuplicateMatch, FieldInspection
from app.models.enums import ClaimStatus, DuplicateReviewStatus
from app.schemas import ClaimIn, ClaimOut
from app.services.anomaly import evaluate_claim_or_request
from app.services.audit import audit, notify
from app.services.duplicates import similarity
from app.services.geo import centroid
from app.services.ids import public_id
from app.services.pagination import paginate

router = APIRouter(prefix="/claims", tags=["claims"])


def _estimate(ref: str, reported: float) -> tuple[float, float]:
    h = int(hashlib.sha256(ref.encode()).hexdigest()[:4], 16)
    est = round(20 + (h % 70) + (reported * 0.05), 1)
    est = min(98.0, max(5.0, est))
    conf = round(0.55 + (h % 40) / 100, 3)
    return est, conf


def _status(diff: float) -> str:
    if diff < 8:
        return ClaimStatus.CONSISTENT.value
    if diff < 18:
        return ClaimStatus.MINOR_DISCREPANCY.value
    if diff < 35:
        return ClaimStatus.REQUIRES_VERIFICATION.value
    return ClaimStatus.HIGH_ANOMALY_RISK.value


def _recommend(status: str) -> str:
    return {
        ClaimStatus.CONSISTENT.value: "Reported loss is aligned with the remote-sensing estimate. Continue documentary review. Do not treat this as an approval.",
        ClaimStatus.MINOR_DISCREPANCY.value: "Minor gap versus estimate. Request clarification from the submitting office.",
        ClaimStatus.REQUIRES_VERIFICATION.value: "Assign human field verification before any financial recommendation.",
        ClaimStatus.HIGH_ANOMALY_RISK.value: "High anomaly risk. Escalate for independent verification. This is not a finding of fraud.",
    }[status]


@router.get("", response_model=list[ClaimOut])
def list_claims(db: Db, user: CurrentUser, disaster_id: int | None = None, status: str = "", q: str = "", page: int = 1, page_size: int = 20):
    stmt = select(AgriculturalClaim).order_by(AgriculturalClaim.id.desc())
    if disaster_id:
        stmt = stmt.where(AgriculturalClaim.disaster_id == disaster_id)
    if status:
        stmt = stmt.where(AgriculturalClaim.status == status)
    if q:
        stmt = stmt.where(AgriculturalClaim.farmer_reference.ilike(f"%{q}%"))
    items, _ = paginate(db, stmt, page, page_size)
    return items


@router.get("/{claim_id}", response_model=ClaimOut)
def get_claim(claim_id: int, db: Db, user: CurrentUser):
    row = db.get(AgriculturalClaim, claim_id)
    if not row:
        raise HTTPException(404, "Claim not found")
    return row


@router.post("/{claim_id}/request-verification")
def request_verification(claim_id: int, db: Db, actor: CurrentUser, assigned_to_id: int | None = None):
    row = db.get(AgriculturalClaim, claim_id)
    if not row:
        raise HTTPException(404, "Claim not found")
    row.status = ClaimStatus.REQUIRES_VERIFICATION.value
    row.recommendation = _recommend(ClaimStatus.REQUIRES_VERIFICATION.value)
    officer = assigned_to_id
    if not officer:
        from app.models.entities import User
        from app.models.enums import Role

        field = db.scalar(select(User).where(User.role == Role.FIELD_OFFICER.value, User.is_active.is_(True)))
        officer = field.id if field else actor.id
    ins = FieldInspection(
        public_id=public_id("INS"),
        disaster_id=row.disaster_id,
        case_type="claim",
        case_id=row.id,
        assigned_to_id=officer,
        assigned_by_id=actor.id,
        status="assigned",
        required_actions=f"Verify crop-loss case {row.public_id}. Compare reported {row.reported_damage_pct}% with estimate {row.estimated_damage_pct}%.",
        location=row.field_boundary,
    )
    db.add(ins)
    db.flush()
    notify(db, user_id=officer, title="Field verification requested", body=f"{row.public_id} requires on-site verification.", link=f"/app/inspections/{ins.id}")
    audit(db, actor_id=actor.id, action="request_verification", entity_type="claim", entity_id=row.id)
    db.commit()
    db.refresh(ins)
    return {"inspection_id": ins.id, "public_id": ins.public_id, "claim_status": row.status}


@router.post("", response_model=ClaimOut)
def create_claim(payload: ClaimIn, db: Db, actor: CurrentUser):
    disaster = db.get(DisasterEvent, payload.disaster_id)
    if not disaster:
        raise HTTPException(404, "Disaster not found")
    est, conf = _estimate(payload.farmer_reference, payload.reported_damage_pct)
    diff = round(abs(payload.reported_damage_pct - est), 1)
    status = _status(diff)
    row = AgriculturalClaim(
        public_id=public_id("CLM"),
        estimated_damage_pct=est,
        confidence=conf,
        difference_pct=diff,
        status=status,
        recommendation=_recommend(status),
        created_by_id=actor.id,
        **payload.model_dump(),
    )
    db.add(row)
    db.flush()
    _flag(db, disaster, row, actor.id)
    _dupes(db, row)
    audit(db, actor_id=actor.id, action="create", entity_type="claim", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row


def _flag(db, disaster: DisasterEvent, row: AgriculturalClaim, actor_id: int) -> None:
    c = centroid(row.field_boundary)
    nearby = 0
    if c:
        others = db.scalars(select(AgriculturalClaim).where(AgriculturalClaim.disaster_id == row.disaster_id)).all()
        nearby = max(0, len(others) - 1)
    result = evaluate_claim_or_request(
        reported=row.reported_damage_pct,
        estimated=row.estimated_damage_pct,
        amount=None,
        incident=row.incident_date,
        disaster_start=disaster.start_date,
        disaster_end=disaster.end_date,
        geometry=row.field_boundary,
        disaster_boundary=disaster.boundary,
        nearby_count=nearby,
    )
    if result["risk_level"] in {"medium", "high", "critical"}:
        alert = AnomalyAlert(
            public_id=public_id("ANM"),
            disaster_id=disaster.id,
            entity_type="claim",
            entity_id=row.id,
            risk_level=result["risk_level"],
            risk_score=result["risk_score"],
            reasons=result["reasons"],
            recommended_action=result["recommended_action"],
            geometry=row.field_boundary,
        )
        db.add(alert)
        notify(
            db,
            user_id=actor_id,
            title="Anomaly risk flagged on crop-loss case",
            body=f"{row.public_id}: {result['risk_level']} risk. Human review required.",
            link=f"/app/claims/{row.id}",
        )


def _dupes(db, row: AgriculturalClaim) -> None:
    others = db.scalars(select(AgriculturalClaim).where(AgriculturalClaim.id != row.id, AgriculturalClaim.disaster_id == row.disaster_id)).all()
    for other in others:
        score, factors = similarity(
            a_geo=row.field_boundary,
            b_geo=other.field_boundary,
            a_disaster=row.disaster_id,
            b_disaster=other.disaster_id,
            a_cat="agricultural_fields",
            b_cat="agricultural_fields",
            a_ref=row.farmer_reference,
            b_ref=other.farmer_reference,
            a_date=row.incident_date,
            b_date=other.incident_date,
        )
        if score >= 55:
            db.add(
                DuplicateMatch(
                    public_id=public_id("DUP"),
                    left_type="claim",
                    left_id=row.id,
                    right_type="claim",
                    right_id=other.id,
                    similarity=score,
                    matching_factors=factors,
                    review_status=DuplicateReviewStatus.OPEN.value,
                )
            )
