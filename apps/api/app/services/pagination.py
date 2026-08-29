from typing import Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


class Page(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


def page_params(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    return {"page": page, "page_size": page_size}


def paginate(db: Session, stmt: Select, page: int, page_size: int) -> tuple[Sequence, int]:
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return items, int(total)
