from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import REVIEWERS, CurrentUser, Db, require_roles
from app.models.entities import AnomalyAlert, DuplicateMatch
from app.services.audit import audit
from app.services.pagination import paginate

router = APIRouter(tags=["risk"])


@router.get("/anomalies")
def list_anomalies(db: Db, user: CurrentUser, risk_level: str = "", entity_type: str = "", page: int = 1, page_size: int = 20):
    stmt = select(AnomalyAlert).order_by(AnomalyAlert.risk_score.desc())
    if risk_level:
        stmt = stmt.where(AnomalyAlert.risk_level == risk_level)
    if entity_type:
        stmt = stmt.where(AnomalyAlert.entity_type == entity_type)
    items, _ = paginate(db, stmt, page, page_size)
    return [
        {
            "id": a.id,
            "public_id": a.public_id,
            "disaster_id": a.disaster_id,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "risk_level": a.risk_level,
            "risk_score": a.risk_score,
            "reasons": a.reasons,
            "recommended_action": a.recommended_action,
            "geometry": a.geometry,
            "status": a.status,
            "created_at": a.created_at,
        }
        for a in items
    ]


@router.patch("/anomalies/{aid}")
def update_anomaly(aid: int, db: Db, actor: CurrentUser, status: str = "reviewed"):
    row = db.get(AnomalyAlert, aid)
    if not row:
        raise HTTPException(404, "Alert not found")
    row.status = status
    audit(db, actor_id=actor.id, action="update", entity_type="anomaly", entity_id=row.id)
    db.commit()
    return {"id": row.id, "status": row.status}


@router.get("/duplicates")
def list_dupes(db: Db, user: CurrentUser, review_status: str = "", page: int = 1, page_size: int = 20):
    stmt = select(DuplicateMatch).order_by(DuplicateMatch.similarity.desc())
    if review_status:
        stmt = stmt.where(DuplicateMatch.review_status == review_status)
    items, _ = paginate(db, stmt, page, page_size)
    return [
        {
            "id": d.id,
            "public_id": d.public_id,
            "left_type": d.left_type,
            "left_id": d.left_id,
            "right_type": d.right_type,
            "right_id": d.right_id,
            "similarity": d.similarity,
            "matching_factors": d.matching_factors,
            "review_status": d.review_status,
            "created_at": d.created_at,
        }
        for d in items
    ]


@router.patch("/duplicates/{did}")
def update_dupe(did: int, db: Db, actor: CurrentUser, review_status: str):
    row = db.get(DuplicateMatch, did)
    if not row:
        raise HTTPException(404, "Record not found")
    row.review_status = review_status
    audit(db, actor_id=actor.id, action="update", entity_type="duplicate", entity_id=row.id)
    db.commit()
    return {"id": row.id, "review_status": row.review_status}
