from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import AuditLog, Notification


def audit(db: Session, *, actor_id: int | None, action: str, entity_type: str, entity_id: Any = "", detail: dict | None = None, ip: str = "") -> None:
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            detail=detail,
            ip_address=ip,
        )
    )


def notify(db: Session, *, user_id: int, title: str, body: str, link: str = "") -> None:
    db.add(Notification(user_id=user_id, title=title, body=body, link=link))
