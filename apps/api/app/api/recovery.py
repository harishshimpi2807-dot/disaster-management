from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import CurrentUser, Db
from app.models.entities import RecoveryRecord
from app.models.enums import RecoveryStatus
from app.schemas import RecoveryIn, RecoveryOut
from app.services.audit import audit, notify
from app.services.ids import public_id
from app.services.pagination import paginate

router = APIRouter(prefix="/recovery", tags=["recovery"])

LATER_PHASES = {"month_3", "month_6", "current"}


@router.get("", response_model=list[RecoveryOut])
def list_recovery(
    db: Db,
    user: CurrentUser,
    disaster_id: int | None = None,
    state: str = "",
    district: str = "",
    status: str = "",
    category: str = "",
    phase: str = "",
    page: int = 1,
    page_size: int = 40,
):
    stmt = select(RecoveryRecord).order_by(RecoveryRecord.observed_on.desc())
    if disaster_id:
        stmt = stmt.where(RecoveryRecord.disaster_id == disaster_id)
    if state:
        stmt = stmt.where(RecoveryRecord.state.ilike(state))
    if district:
        stmt = stmt.where(RecoveryRecord.district.ilike(district))
    if status:
        stmt = stmt.where(RecoveryRecord.status == status)
    if category:
        stmt = stmt.where(RecoveryRecord.category == category)
    if phase:
        stmt = stmt.where(RecoveryRecord.phase == phase)
    items, _ = paginate(db, stmt, page, page_size)
    return items


@router.get("/alerts/delayed")
def delayed_alerts(db: Db, user: CurrentUser):
    rows = db.scalars(select(RecoveryRecord).where(RecoveryRecord.status == RecoveryStatus.DELAYED.value)).all()
    return [
        {
            "id": r.id,
            "public_id": r.public_id,
            "disaster_id": r.disaster_id,
            "category": r.category,
            "locality": r.locality or r.district,
            "recovery_pct": r.recovery_pct,
            "recovery_score": r.recovery_score,
            "phase": r.phase,
            "status": r.status,
        }
        for r in rows
    ]


@router.post("", response_model=RecoveryOut)
def create_recovery(payload: RecoveryIn, db: Db, actor: CurrentUser):
    status = payload.status
    if payload.recovery_pct < 35 and payload.phase in LATER_PHASES:
        status = RecoveryStatus.DELAYED.value
    score = round(payload.recovery_pct * 0.9 + (10 if status == RecoveryStatus.RESTORED.value else 0), 1)
    data = payload.model_dump()
    data["status"] = status
    row = RecoveryRecord(public_id=public_id("RCV"), recovery_score=min(100, score), **data)
    db.add(row)
    db.flush()
    if status == RecoveryStatus.DELAYED.value:
        notify(
            db,
            user_id=actor.id,
            title="Delayed recovery alert",
            body=f"{row.public_id} ({row.category} in {row.district}) is behind expected recovery.",
            link="/app/recovery",
        )
    audit(db, actor_id=actor.id, action="create", entity_type="recovery", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row
