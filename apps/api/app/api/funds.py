from statistics import median

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import MANAGERS, CurrentUser, Db, require_roles
from app.models.entities import AnomalyAlert, DisasterEvent, DuplicateMatch, FundAllocation, FundRequest
from app.models.enums import AllocationStatus, DuplicateReviewStatus, FundStatus
from app.schemas import AllocationIn, AllocationOut, FundRequestIn, FundRequestOut
from app.services.anomaly import evaluate_claim_or_request
from app.services.audit import audit, notify
from app.services.duplicates import similarity
from app.services.ids import public_id
from app.services.pagination import paginate

router = APIRouter(tags=["funds"])


def _fund_status(consistency: float) -> str:
    if consistency >= 75:
        return FundStatus.CONSISTENT_WITH_EVIDENCE.value
    if consistency >= 45:
        return FundStatus.REQUIRES_ADDITIONAL_VERIFICATION.value
    return FundStatus.SIGNIFICANT_DISCREPANCY_DETECTED.value


@router.get("/fund-requests", response_model=list[FundRequestOut])
def list_requests(db: Db, user: CurrentUser, disaster_id: int | None = None, status: str = "", page: int = 1, page_size: int = 20):
    stmt = select(FundRequest).order_by(FundRequest.id.desc())
    if disaster_id:
        stmt = stmt.where(FundRequest.disaster_id == disaster_id)
    if status:
        stmt = stmt.where(FundRequest.status == status)
    items, _ = paginate(db, stmt, page, page_size)
    return items


@router.get("/fund-requests/{rid}", response_model=FundRequestOut)
def get_request(rid: int, db: Db, user: CurrentUser):
    row = db.get(FundRequest, rid)
    if not row:
        raise HTTPException(404, "Fund request not found")
    return row


@router.post("/fund-requests", response_model=FundRequestOut)
def create_request(payload: FundRequestIn, db: Db, actor: CurrentUser):
    disaster = db.get(DisasterEvent, payload.disaster_id)
    if not disaster:
        raise HTTPException(404, "Disaster not found")
    amounts = [r.requested_amount for r in db.scalars(select(FundRequest)).all()]
    med = median(amounts) if amounts else payload.requested_amount
    # Consistency: inverse of anomaly score later
    result = evaluate_claim_or_request(
        reported=70,
        estimated=55,
        amount=payload.requested_amount,
        incident=disaster.start_date,
        disaster_start=disaster.start_date,
        disaster_end=disaster.end_date,
        geometry=payload.geometry,
        disaster_boundary=disaster.boundary,
        nearby_count=len(amounts),
        median_amount=med,
    )
    consistency = round(max(5.0, 100 - result["risk_score"]), 1)
    status = _fund_status(consistency)
    rec = {
        FundStatus.CONSISTENT_WITH_EVIDENCE.value: "Geospatial evidence is broadly consistent with the reported requirement. Human officials remain the decision-makers.",
        FundStatus.REQUIRES_ADDITIONAL_VERIFICATION.value: "Evidence is incomplete or mixed. Request field verification before a funding recommendation.",
        FundStatus.SIGNIFICANT_DISCREPANCY_DETECTED.value: "Reported requirement diverges from available evidence. Escalate for independent review. This is not an accusation.",
    }[status]
    row = FundRequest(
        public_id=public_id("FND"),
        evidence_consistency=consistency,
        confidence=round(0.6 + (consistency / 400), 3),
        recommendation=rec,
        status=status,
        created_by_id=actor.id,
        **payload.model_dump(),
    )
    db.add(row)
    db.flush()
    if result["risk_level"] in {"medium", "high", "critical"}:
        db.add(
            AnomalyAlert(
                public_id=public_id("ANM"),
                disaster_id=disaster.id,
                entity_type="fund_request",
                entity_id=row.id,
                risk_level=result["risk_level"],
                risk_score=result["risk_score"],
                reasons=result["reasons"],
                recommended_action=result["recommended_action"],
                geometry=payload.geometry,
            )
        )
        notify(db, user_id=actor.id, title="Anomaly risk on fund requirement", body=f"{row.public_id} needs human review.", link=f"/app/funds/requests/{row.id}")
    others = db.scalars(select(FundRequest).where(FundRequest.id != row.id)).all()
    for other in others:
        score, factors = similarity(
            a_geo=row.geometry,
            b_geo=other.geometry,
            a_disaster=row.disaster_id,
            b_disaster=other.disaster_id,
            a_cat=row.damage_category,
            b_cat=other.damage_category,
            a_ref=row.department,
            b_ref=other.department,
            a_date=disaster.start_date,
            b_date=disaster.start_date,
        )
        if score >= 58:
            db.add(
                DuplicateMatch(
                    public_id=public_id("DUP"),
                    left_type="fund_request",
                    left_id=row.id,
                    right_type="fund_request",
                    right_id=other.id,
                    similarity=score,
                    matching_factors=factors,
                    review_status=DuplicateReviewStatus.OPEN.value,
                )
            )
    audit(db, actor_id=actor.id, action="create", entity_type="fund_request", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row


@router.get("/fund-allocations", response_model=list[AllocationOut])
def list_alloc(db: Db, user: CurrentUser, disaster_id: int | None = None, status: str = "", page: int = 1, page_size: int = 20):
    stmt = select(FundAllocation).order_by(FundAllocation.id.desc())
    if disaster_id:
        stmt = stmt.where(FundAllocation.disaster_id == disaster_id)
    if status:
        stmt = stmt.where(FundAllocation.status == status)
    items, _ = paginate(db, stmt, page, page_size)
    return items


@router.get("/fund-allocations/{aid}", response_model=AllocationOut)
def get_alloc(aid: int, db: Db, user: CurrentUser):
    row = db.get(FundAllocation, aid)
    if not row:
        raise HTTPException(404, "Allocation not found")
    return row


@router.post("/fund-allocations", response_model=AllocationOut)
def create_alloc(payload: AllocationIn, db: Db, actor: CurrentUser):
    if payload.status not in {s.value for s in AllocationStatus}:
        raise HTTPException(400, "Invalid status")
    if payload.observed_progress_pct + 15 < payload.planned_progress_pct:
        payload.status = AllocationStatus.DELAYED.value
    row = FundAllocation(public_id=public_id("ALC"), created_by_id=actor.id, **payload.model_dump())
    db.add(row)
    db.flush()
    if row.status == AllocationStatus.DELAYED.value:
        notify(db, user_id=actor.id, title="Delayed progress on allocation", body=f"{row.public_id} is behind planned progress.", link=f"/app/funds/allocations/{row.id}")
    audit(db, actor_id=actor.id, action="create", entity_type="allocation", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/fund-allocations/{aid}", response_model=AllocationOut)
def update_alloc(aid: int, payload: AllocationIn, db: Db, actor: CurrentUser):
    row = db.get(FundAllocation, aid)
    if not row:
        raise HTTPException(404, "Allocation not found")
    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    if row.observed_progress_pct + 15 < row.planned_progress_pct:
        row.status = AllocationStatus.DELAYED.value
    audit(db, actor_id=actor.id, action="update", entity_type="allocation", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row
