"""Store announcement attachments under the existing /uploads static mount."""
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024
UPLOAD_ROOT = Path(__file__).resolve().parents[4] / "uploads" / "notifications"


def save_attachment(upload, root=None):
    root = Path(root) if root is not None else UPLOAD_ROOT
    filename = (upload.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".jpg", ".jpeg", ".png"}:
        raise HTTPException(422, "Attachment must be a PDF, JPEG or PNG file")
    content = upload.file.read(MAX_ATTACHMENT_BYTES + 1)
    if not content:
        raise HTTPException(422, "Attachment is empty")
    if len(content) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(413, "Attachment must not exceed 5 MB")
    signatures = {".pdf": b"%PDF-", ".png": b"\x89PNG\r\n\x1a\n", ".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff"}
    if not content.startswith(signatures[extension]):
        raise HTTPException(422, "Attachment content does not match its file type")
    root.mkdir(parents=True, exist_ok=True)
    path = root / (uuid4().hex + extension)
    try:
        with path.open("xb") as destination:
            destination.write(content)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return filename[:255], "/uploads/notifications/" + path.name, path
