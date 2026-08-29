from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.deps import ADMINS, CurrentUser, Db, require_roles
from app.core.security import hash_password
from app.models.entities import User
from app.models.enums import Role
from app.schemas import UserCreate, UserOut, UserUpdate
from app.services.audit import audit
from app.services.pagination import paginate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Db, user: CurrentUser, page: int = 1, page_size: int = 50, q: str = "", role: str = ""):
    if user.role not in {Role.SYSTEM_ADMIN.value, Role.GOV_ADMIN.value}:
        raise HTTPException(403, "You do not have access to this action")
    stmt = select(User).where(User.deleted_at.is_(None)).order_by(User.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((User.email.ilike(like)) | (User.full_name.ilike(like)))
    if role:
        stmt = stmt.where(User.role == role)
    items, _ = paginate(db, stmt, page, page_size)
    return items


@router.post("", response_model=UserOut, dependencies=[Depends(require_roles(*ADMINS))])
def create_user(payload: UserCreate, db: Db, actor: CurrentUser):
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(409, "Email already registered")
    if payload.role not in {r.value for r in Role}:
        raise HTTPException(400, "Unknown role")
    row = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        agency=payload.agency,
        district=payload.district,
    )
    db.add(row)
    db.flush()
    audit(db, actor_id=actor.id, action="create", entity_type="user", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{user_id}", response_model=UserOut, dependencies=[Depends(require_roles(*ADMINS))])
def update_user(user_id: int, payload: UserUpdate, db: Db, actor: CurrentUser):
    row = db.get(User, user_id)
    if not row or row.deleted_at:
        raise HTTPException(404, "User not found")
    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        row.hashed_password = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(row, k, v)
    audit(db, actor_id=actor.id, action="update", entity_type="user", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return row
