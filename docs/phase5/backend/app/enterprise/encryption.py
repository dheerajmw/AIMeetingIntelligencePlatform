from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from ..config import settings


def encryption_enabled() -> bool:
    return bool(settings.encryption_key)


def _fernet() -> Fernet:
    if not settings.encryption_key:
        raise RuntimeError("ENCRYPTION_KEY not configured")
    raw = settings.encryption_key.strip()
    if len(raw) == 44 and raw.endswith("="):
        key = raw.encode("utf-8")
    else:
        digest = hashlib.sha256(raw.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_file_at_path(path: Path) -> None:
    data = path.read_bytes()
    token = _fernet().encrypt(data)
    path.write_bytes(token)


def decrypt_file_to_path(encrypted_path: Path, output_path: Path) -> None:
    token = encrypted_path.read_bytes()
    try:
        data = _fernet().decrypt(token)
    except InvalidToken as e:
        raise ValueError("Failed to decrypt upload (wrong ENCRYPTION_KEY?)") from e
    output_path.write_bytes(data)


def decrypt_upload_for_processing(upload_path: Path, meeting_id: int, encrypted: bool) -> Path:
    if not encrypted:
        return upload_path
    tmp = upload_path.parent / f".decrypt-{meeting_id}{upload_path.suffix}"
    decrypt_file_to_path(upload_path, tmp)
    return tmp


def cleanup_temp_decrypt(path: Path, upload_path: Path) -> None:
    if path != upload_path and path.exists():
        path.unlink(missing_ok=True)


def file_content_hash(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()
