from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.deps import CurrentUser, Db
from app.models.entities import (
    AgriculturalClaim,
    AnomalyAlert,
    DamageAssessment,
    DisasterEvent,
    DuplicateMatch,
    FundAllocation,
    FundRequest,
    RecoveryRecord,
)
from app.models.enums import AllocationStatus, DuplicateReviewStatus, InspectionStatus
from app.models.entities import FieldInspection

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def overview(db: Db, user: CurrentUser):
    disasters = db.scalars(select(DisasterEvent).where(DisasterEvent.deleted_at.is_(None))).all()
    assessments = db.scalars(select(DamageAssessment)).all()
    claims = db.scalars(select(AgriculturalClaim)).all()
    alerts = db.scalars(select(AnomalyAlert)).all()
    dupes = db.scalars(select(DuplicateMatch)).all()
    reqs = db.scalars(select(FundRequest)).all()
    allocs = db.scalars(select(FundAllocation)).all()
    recs = db.scalars(select(RecoveryRecord)).all()
    delayed_insp = db.scalars(select(FieldInspection).where(FieldInspection.status == InspectionStatus.ASSIGNED.value)).all()

    area = sum(a.estimated_area_ha for a in assessments)
    rec_pct = round(sum(r.recovery_pct for r in recs) / len(recs), 1) if recs else 0
    delayed_rec = [r for r in recs if r.status == "delayed"]
    verify_claims = [c for c in claims if c.status in {"requires_verification", "high_anomaly_risk"}]
    high_anom = [a for a in alerts if a.risk_level in {"high", "critical"}]
    open_dupes = [d for d in dupes if d.review_status == DuplicateReviewStatus.OPEN.value]

    by_type: dict[str, int] = {}
    for d in disasters:
        by_type[d.disaster_type] = by_type.get(d.disaster_type, 0) + 1

    timeline = [
        {"date": str(d.start_date), "name": d.name, "severity": d.severity, "type": d.disaster_type}
        for d in sorted(disasters, key=lambda x: x.start_date)
    ]

    return {
        "total_disasters": len(disasters),
        "total_affected_area_ha": round(area, 1),
        "estimated_damage_records": len(assessments),
        "claims_requiring_verification": len(verify_claims),
        "high_risk_anomalies": len(high_anom),
        "potential_duplicates": len(open_dupes),
        "funds_requested": round(sum(r.requested_amount for r in reqs), 2),
        "funds_allocated": round(sum(a.amount for a in allocs), 2),
        "funds_monitored": round(sum(a.amount for a in allocs), 2),
        "recovery_percentage": rec_pct,
        "delayed_recovery_locations": len(delayed_rec),
        "open_inspections": len(delayed_insp),
        "delayed_allocations": len([a for a in allocs if a.status == AllocationStatus.DELAYED.value]),
        "disasters_by_type": by_type,
        "timeline": timeline,
        "recovery_by_category": _group(recs),
        "anomaly_by_level": _count(alerts, "risk_level"),
    }


def _group(recs):
    out: dict[str, list[float]] = {}
    for r in recs:
        out.setdefault(r.category, []).append(r.recovery_pct)
    return {k: round(sum(v) / len(v), 1) for k, v in out.items()}


def _count(items, attr):
    out: dict[str, int] = {}
    for i in items:
        k = getattr(i, attr)
        out[k] = out.get(k, 0) + 1
    return out
