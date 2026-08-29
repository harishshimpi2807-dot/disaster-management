from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings

ALLOWED = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
    "application/geo+json": ".geojson",
    "application/json": ".json",
}
MAX_BYTES = 25 * 1024 * 1024


class StorageService:
    def __init__(self) -> None:
        s = get_settings()
        self.root = Path(s.storage_local_path).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save_upload(self, file: UploadFile, prefix: str) -> tuple[str, str]:
        content_type = (file.content_type or "").split(";")[0].strip().lower()
        if content_type not in ALLOWED:
            raise HTTPException(415, "Unsupported file type. Use JPEG, PNG, WebP, PDF, or GeoJSON.")
        data = file.file.read()
        if len(data) > MAX_BYTES:
            raise HTTPException(413, "File exceeds 25 MB limit.")
        if content_type.startswith("image/"):
            try:
                Image.open(__import__("io").BytesIO(data)).verify()
            except (UnidentifiedImageError, OSError):
                raise HTTPException(400, "Image could not be validated.")
        ext = ALLOWED[content_type]
        key = f"{prefix}/{uuid4().hex}{ext}"
        dest = self.root / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return key, content_type

    def path_for(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not str(path).startswith(str(self.root)):
            raise HTTPException(400, "Invalid storage key")
        return path
