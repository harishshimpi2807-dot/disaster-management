from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import select

from app.core.deps import ADMINS, CurrentUser, Db, require_roles
from app.models.entities import AuditLog, Dataset, Notification, NotificationRule, SystemSetting
from app.models.enums import Role
from app.schemas import RuleIn, SettingIn
from app.services.audit import audit
from app.services.pagination import paginate

router = APIRouter(tags=["admin"])


@router.get("/notifications")
def my_notes(db: Db, user: CurrentUser):
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.id.desc()).limit(50)).all()
    return [{"id": n.id, "title": n.title, "body": n.body, "link": n.link, "read": n.read, "created_at": n.created_at} for n in rows]


@router.post("/notifications/{nid}/read")
def read_note(nid: int, db: Db, user: CurrentUser):
    row = db.get(Notification, nid)
    if not row or row.user_id != user.id:
        raise HTTPException(404, "Notification not found")
    row.read = True
    db.commit()
    return {"ok": True}


@router.get("/audit")
def audit_logs(db: Db, user: CurrentUser, page: int = 1, page_size: int = 50, action: str = "", entity_type: str = ""):
    if user.role != Role.SYSTEM_ADMIN.value and user.role != Role.AUDITOR.value:
        raise HTTPException(403, "You do not have access to this action")
    stmt = select(AuditLog).order_by(AuditLog.id.desc())
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    items, total = paginate(db, stmt, page, page_size)
    return {
        "total": total,
        "items": [
            {
                "id": a.id,
                "actor_id": a.actor_id,
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "detail": a.detail,
                "created_at": a.created_at,
            }
            for a in items
        ],
    }


@router.get("/settings")
def list_settings(db: Db, user: CurrentUser):
    rows = db.scalars(select(SystemSetting)).all()
    return [{"key": s.key, "value": s.value} for s in rows]


@router.put("/settings", dependencies=[Depends(require_roles(*ADMINS))])
def put_setting(payload: SettingIn, db: Db, actor: CurrentUser):
    row = db.scalar(select(SystemSetting).where(SystemSetting.key == payload.key))
    if not row:
        row = SystemSetting(key=payload.key, value=payload.value)
        db.add(row)
    else:
        row.value = payload.value
    audit(db, actor_id=actor.id, action="update", entity_type="setting", entity_id=payload.key)
    db.commit()
    return {"key": payload.key, "value": payload.value}


@router.get("/notification-rules")
def rules(db: Db, user: CurrentUser):
    rows = db.scalars(select(NotificationRule)).all()
    return [{"id": r.id, "name": r.name, "event_type": r.event_type, "min_risk": r.min_risk, "channel": r.channel, "enabled": r.enabled} for r in rows]


@router.post("/notification-rules", dependencies=[Depends(require_roles(*ADMINS))])
def create_rule(payload: RuleIn, db: Db, actor: CurrentUser):
    row = NotificationRule(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name}


@router.get("/datasets")
def datasets(db: Db, user: CurrentUser):
    rows = db.scalars(select(Dataset)).all()
    return [{"id": d.id, "name": d.name, "kind": d.kind, "description": d.description, "created_at": d.created_at} for d in rows]


@router.post("/datasets", dependencies=[Depends(require_roles(*ADMINS))])
def create_dataset(db: Db, actor: CurrentUser, name: str, kind: str, description: str = ""):
    row = Dataset(name=name, kind=kind, description=description, created_by_id=actor.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name}


@router.get("/reports/export")
def export_report(db: Db, user: CurrentUser, kind: str = "anomalies"):
    if user.role not in {Role.SYSTEM_ADMIN.value, Role.GOV_ADMIN.value, Role.AUDITOR.value, Role.AGRI_OFFICER.value}:
        raise HTTPException(403, "You do not have access to this action")
    from app.models.entities import AnomalyAlert, DuplicateMatch, FundRequest, AgriculturalClaim

    lines = ["id,public_id,detail"]
    if kind == "anomalies":
        for a in db.scalars(select(AnomalyAlert)).all():
            lines.append(f"{a.id},{a.public_id},{a.risk_level}:{a.risk_score}")
    elif kind == "duplicates":
        for d in db.scalars(select(DuplicateMatch)).all():
            lines.append(f"{d.id},{d.public_id},{d.similarity}")
    elif kind == "funds":
        for r in db.scalars(select(FundRequest)).all():
            lines.append(f"{r.id},{r.public_id},{r.requested_amount}")
    elif kind == "claims":
        for c in db.scalars(select(AgriculturalClaim)).all():
            lines.append(f"{c.id},{c.public_id},{c.status}")
    else:
        raise HTTPException(400, "Unknown report kind")
    audit(db, actor_id=user.id, action="export", entity_type="report", entity_id=kind)
    db.commit()
    return PlainTextResponse("\n".join(lines), media_type="text/csv")
