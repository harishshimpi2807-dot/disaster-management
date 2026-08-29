from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.deps import CurrentUser, Db
from app.models.entities import EvidenceFile, SatelliteImage
from app.services.audit import audit
from app.services.storage import StorageService

router = APIRouter(tags=["files"])
storage = StorageService()


@router.post("/imagery")
def upload_imagery(
    db: Db,
    user: CurrentUser,
    file: UploadFile = File(...),
    disaster_id: int | None = Form(None),
    phase: str = Form("after"),
    sensor: str = Form(""),
    cloud_cover_pct: float | None = Form(None),
):
    key, ctype = storage.save_upload(file, "imagery")
    row = SatelliteImage(
        disaster_id=disaster_id,
        phase=phase,
        sensor=sensor,
        cloud_cover_pct=cloud_cover_pct,
        storage_key=key,
        original_filename=file.filename or "upload",
        content_type=ctype,
        uploaded_by_id=user.id,
        captured_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.flush()
    audit(db, actor_id=user.id, action="upload", entity_type="imagery", entity_id=row.id)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "storage_key": row.storage_key, "phase": row.phase, "filename": row.original_filename}


@router.get("/imagery")
def list_imagery(db: Db, user: CurrentUser, disaster_id: int | None = None):
    stmt = select(SatelliteImage).order_by(SatelliteImage.id.desc())
    if disaster_id:
        stmt = stmt.where(SatelliteImage.disaster_id == disaster_id)
    rows = db.scalars(stmt.limit(100)).all()
    return [{"id": r.id, "phase": r.phase, "filename": r.original_filename, "sensor": r.sensor, "disaster_id": r.disaster_id, "created_at": r.created_at} for r in rows]


@router.post("/evidence")
def upload_evidence(
    db: Db,
    user: CurrentUser,
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    entity_id: int = Form(...),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
):
    key, ctype = storage.save_upload(file, "evidence")
    row = EvidenceFile(
        entity_type=entity_type,
        entity_id=entity_id,
        storage_key=key,
        original_filename=file.filename or "upload",
        content_type=ctype,
        latitude=latitude,
        longitude=longitude,
        captured_at=datetime.now(timezone.utc),
        uploaded_by_id=user.id,
    )
    db.add(row)
    db.flush()
    audit(db, actor_id=user.id, action="upload", entity_type="evidence", entity_id=row.id)
    db.commit()
    return {"id": row.id, "filename": row.original_filename, "latitude": latitude, "longitude": longitude}


@router.get("/evidence")
def list_evidence(db: Db, user: CurrentUser, entity_type: str, entity_id: int):
    rows = db.scalars(select(EvidenceFile).where(EvidenceFile.entity_type == entity_type, EvidenceFile.entity_id == entity_id)).all()
    return [
        {
            "id": r.id,
            "filename": r.original_filename,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "captured_at": r.captured_at,
            "url": f"/api/v1/files/{r.id}",
        }
        for r in rows
    ]


@router.get("/files/{file_id}")
def download(file_id: int, db: Db, user: CurrentUser):
    row = db.get(EvidenceFile, file_id)
    if not row:
        img = db.get(SatelliteImage, file_id)
        if not img:
            raise HTTPException(404, "File not found")
        path = storage.path_for(img.storage_key)
        return FileResponse(path, media_type=img.content_type, filename=img.original_filename)
    path = storage.path_for(row.storage_key)
    return FileResponse(path, media_type=row.content_type, filename=row.original_filename)
