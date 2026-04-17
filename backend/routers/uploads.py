"""
routers/uploads.py  –  File upload/download for request attachments
Files are stored in uploads/ folder, NOT as base64 blobs in the database.
"""
import logging
import os
import uuid
import mimetypes
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from core.security import get_current_user

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}

router = APIRouter(
    prefix="/uploads",
    tags=["File Uploads"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """Upload an attachment. Returns a file_id to store in the request record."""
    # Check MIME type
    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{mime}' not allowed. Allowed: PDF, DOC, DOCX, JPG, PNG.",
        )

    # Read and size-check
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 2 MB limit.")

    # Save with a UUID filename to prevent collisions and path traversal
    ext      = Path(file.filename or "file").suffix.lower()
    file_id  = f"{uuid.uuid4().hex}{ext}"
    dest     = UPLOAD_DIR / file_id
    dest.write_bytes(data)

    logger.info("File uploaded: %s (%d bytes)", file_id, len(data))
    return {
        "file_id":   file_id,
        "filename":  file.filename,
        "size":      len(data),
        "mime_type": mime,
    }


@router.get("/{file_id}")
def download_file(file_id: str):
    """Download / view an uploaded attachment by its file_id."""
    # Prevent path traversal
    safe_id = Path(file_id).name
    path    = UPLOAD_DIR / safe_id

    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    mime, _ = mimetypes.guess_type(str(path))
    return FileResponse(
        path=str(path),
        media_type=mime or "application/octet-stream",
        filename=safe_id,
    )
