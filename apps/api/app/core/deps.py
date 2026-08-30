from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token, token_error
from app.db.session import get_db
from app.models.entities import User
from app.models.enums import Role

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

ROLE_HOME = {
    Role.SYSTEM_ADMIN.value: "/app/admin/users",
    Role.GOV_ADMIN.value: "/app",
    Role.FIELD_OFFICER.value: "/app/inspections",
    Role.AGRI_OFFICER.value: "/app/claims",
    Role.AUDITOR.value: "/app/anomalies",
}

# Login is removed from the frontend. Requests with no (or an invalid) bearer
# token fall back to this seeded account so RBAC checks and audit logging
# (actor_id) keep working unchanged everywhere CurrentUser is used.
DEFAULT_USER_EMAIL = "admin@sentinel.gov"


def get_current_user(token: Annotated[str | None, Depends(oauth2)], db: Annotated[Session, Depends(get_db)]) -> User:
    if token:
        try:
            payload = decode_token(token)
            sub = payload.get("sub")
        except token_error():
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
        user = db.get(User, int(sub)) if sub else None
        if user and user.is_active and not user.deleted_at:
            return user

    default_user = db.scalar(select(User).where(User.email == DEFAULT_USER_EMAIL, User.deleted_at.is_(None)))
    if not default_user or not default_user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No default account configured")
    return default_user


def require_roles(*roles: Role):
    allowed = {r.value for r in roles}

    def _inner(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this action")
        return user

    return _inner


CurrentUser = Annotated[User, Depends(get_current_user)]
Db = Annotated[Session, Depends(get_db)]

STAFF = (Role.SYSTEM_ADMIN, Role.GOV_ADMIN, Role.AGRI_OFFICER, Role.AUDITOR, Role.FIELD_OFFICER)
REVIEWERS = (Role.SYSTEM_ADMIN, Role.GOV_ADMIN, Role.AGRI_OFFICER, Role.AUDITOR)
MANAGERS = (Role.SYSTEM_ADMIN, Role.GOV_ADMIN)
ADMINS = (Role.SYSTEM_ADMIN,)