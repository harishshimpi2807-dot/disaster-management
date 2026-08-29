from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.deps import CurrentUser, Db
from app.core.security import create_access_token, verify_password
from app.models.entities import User
from app.schemas import LoginIn, TokenOut, UserOut
from app.services.audit import audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue(db: Db, request: Request, email: str, password: str) -> TokenOut:
    user = db.scalar(select(User).where(User.email == email.lower(), User.deleted_at.is_(None)))
    if not user or not verify_password(password, user.hashed_password) or not user.is_active:
        raise HTTPException(401, "Incorrect email or password")
    token = create_access_token(str(user.id), {"role": user.role})
    audit(db, actor_id=user.id, action="login", entity_type="user", entity_id=user.id, ip=request.client.host if request.client else "")
    db.commit()
    return TokenOut(access_token=token, role=user.role, full_name=user.full_name, user_id=user.id)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Db, request: Request):
    return _issue(db, request, payload.email, payload.password)


@router.post("/token", response_model=TokenOut)
def token(db: Db, request: Request, form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return _issue(db, request, form.username, form.password)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


@router.post("/logout")
def logout(user: CurrentUser, db: Db, request: Request):
    audit(db, actor_id=user.id, action="logout", entity_type="user", entity_id=user.id, ip=request.client.host if request.client else "")
    db.commit()
    return {"ok": True}
