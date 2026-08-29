from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select

from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.assessments import router as assessments_router
from app.api.auth import router as auth_router
from app.api.claims import router as claims_router
from app.api.disasters import router as disasters_router
from app.api.files import router as files_router
from app.api.funds import router as funds_router
from app.api.gis import router as gis_router
from app.api.inspections import router as inspections_router
from app.api.recovery import router as recovery_router
from app.api.risk import router as risk_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.db.session import Base, SessionLocal, engine
from app.models import entities as _entities  # noqa: F401
from app.models.entities import User
from app.seed import seed_if_empty

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


def init_db() -> None:
    Path("data").mkdir(exist_ok=True)
    Path(settings.storage_local_path).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.scalar(select(User).limit(1)) is None:
            seed_if_empty(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Evidence-based disaster intelligence. AI recommends; authorised humans decide.",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exc(_, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "error": True})


@app.exception_handler(Exception)
async def unhandled(_, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "error": True})


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


prefix = "/api/v1"
for r in (
    auth_router,
    users_router,
    disasters_router,
    assessments_router,
    claims_router,
    funds_router,
    risk_router,
    inspections_router,
    recovery_router,
    gis_router,
    analytics_router,
    files_router,
    admin_router,
):
    app.include_router(r, prefix=prefix)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}
