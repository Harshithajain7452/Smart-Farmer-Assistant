"""Input validation + secure file upload helpers."""
import os
import re
import uuid

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
PHONE_RE = re.compile(r"^[6-9]\d{9}$")            # Indian mobile numbers
NAME_RE = re.compile(r"^[A-Za-z\u0900-\u0D7F .'-]{2,120}$")

# Magic-byte signatures accepted for uploaded images.
IMAGE_SIGNATURES = (
    b"\xff\xd8\xff",              # JPEG
    b"\x89PNG\r\n\x1a\n",         # PNG
    b"RIFF",                      # WEBP container
)


def is_valid_email(value: str) -> bool:
    return bool(value and EMAIL_RE.match(value.strip()))


def is_valid_phone(value: str) -> bool:
    return bool(value and PHONE_RE.match(value.strip()))


def is_valid_name(value: str) -> bool:
    return bool(value and NAME_RE.match(value.strip()))


def password_issues(password: str) -> list:
    """Return a list of human-readable password policy violations."""
    issues = []
    if len(password or "") < 8:
        issues.append("at least 8 characters")
    if not re.search(r"[A-Za-z]", password or ""):
        issues.append("one letter")
    if not re.search(r"\d", password or ""):
        issues.append("one number")
    return issues


def clean_text(value: str, max_len: int = 500) -> str:
    """Strip control characters and clamp length (defence against injection/XSS)."""
    if not value:
        return ""
    value = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    return value.strip()[:max_len]


def to_float(value, default=0.0, minimum=None, maximum=None) -> float:
    """Coerce user input to a bounded float."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        num = max(minimum, num)
    if maximum is not None:
        num = min(maximum, num)
    return num


def allowed_image(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def save_upload(file: FileStorage, subfolder: str) -> str:
    """
    Securely persist an uploaded image.

    * random UUID filename (no user-controlled paths)
    * extension whitelist + magic-byte sniffing
    * stored outside the templates tree, served through a controlled route

    Returns the relative path (``subfolder/filename``).
    """
    if not file or not file.filename:
        raise ValueError("No file selected.")
    if not allowed_image(file.filename):
        raise ValueError("Only PNG, JPG or WEBP images are allowed.")

    head = file.stream.read(12)
    file.stream.seek(0)
    if not any(head.startswith(sig) for sig in IMAGE_SIGNATURES):
        raise ValueError("The uploaded file is not a valid image.")

    ext = secure_filename(file.filename).rsplit(".", 1)[-1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, name))
    return f"{subfolder}/{name}"
