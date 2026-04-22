"""
api/views/uploads.py  –  File upload/download for request attachments
Files are stored in uploads/ folder, NOT as base64 blobs in the database.
"""
import logging
import os
import uuid
import mimetypes
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import FileResponse

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
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


class UploadView(APIView):
    """POST /api/uploads/  –  Upload an attachment.
       Returns a file_id to store in the request record.
    """

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"detail": "No file provided. Send a multipart/form-data request with a 'file' field."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check MIME type
        mime = file.content_type or mimetypes.guess_type(file.name or "")[0] or ""
        if mime not in ALLOWED_MIME_TYPES:
            return Response(
                {"detail": f"File type '{mime}' not allowed. Allowed: PDF, DOC, DOCX, JPG, PNG."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Read and size-check
        data = file.read()
        if len(data) > MAX_FILE_SIZE:
            return Response({"detail": "File exceeds 2 MB limit."}, status=status.HTTP_400_BAD_REQUEST)

        # Save with a UUID filename to prevent collisions and path traversal
        ext     = Path(file.name or "file").suffix.lower()
        file_id = f"{uuid.uuid4().hex}{ext}"
        dest    = UPLOAD_DIR / file_id
        dest.write_bytes(data)

        logger.info("File uploaded: %s (%d bytes)", file_id, len(data))
        return Response({
            "file_id":   file_id,
            "filename":  file.name,
            "size":      len(data),
            "mime_type": mime,
        })


class DownloadView(APIView):
    """GET /api/uploads/<file_id>/  –  Download / view an uploaded attachment."""

    def get(self, request, file_id):
        # Prevent path traversal
        safe_id = Path(file_id).name
        path    = UPLOAD_DIR / safe_id

        if not path.exists():
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)

        mime, _ = mimetypes.guess_type(str(path))
        response = FileResponse(
            open(path, "rb"),
            content_type=mime or "application/octet-stream",
            as_attachment=False,
            filename=safe_id,
        )
        return response
