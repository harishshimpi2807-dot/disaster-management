from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token, token_error
from app.db.session import get_db
from app.models.entities import User
from app.models.enums import Role

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

ROLE_HOME = {
    Role.SYSTEM_ADMIN.value: "/app/admin/users",
    Role.GOV_ADMIN.value: "/app",
    Role.FIELD_OFFICER.value: "/app/inspections",
    Role.AGRI_OFFICER.value: "/app/claims",
    Role.AUDITOR.value: "/app/anomalies",
}


def get_current_user(token: Annotated[str, Depends(oauth2)], db: Annotated[Session, Depends(get_db)]) -> User:
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
    except token_error():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")
    user = db.get(User, int(sub)) if sub else None
    if not user or not user.is_active or user.deleted_at:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inactive account")
    return user


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
