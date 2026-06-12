"""Firebase Admin SDK initialization and token verification.

# [SOLID: SRP] — Extracted from security.py; single reason to change: Firebase config.
"""
import logging
from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials

from core.config import get_settings

logger = logging.getLogger(__name__)

# [DRY] — Centralised app root; avoids fragile parents[N] in multiple files
APP_ROOT = Path(__file__).resolve().parents[2]


def init_firebase() -> None:
    """Initialize the Firebase Admin SDK if not already initialized.

    Loads credentials from the path configured in FIREBASE_CREDENTIALS_PATH.
    Falls back to Application Default Credentials if the file is absent.
    """
    if firebase_admin._apps:
        return

    settings = get_settings()
    cred_path = _resolve_credentials_path(settings.FIREBASE_CREDENTIALS_PATH)

    if cred_path and cred_path.is_file():
        try:
            cred = credentials.Certificate(str(cred_path))
            firebase_admin.initialize_app(cred)
            logger.info(
                "Firebase Admin initialized with credentials from %s", cred_path
            )
        except (ValueError, KeyError, FileNotFoundError) as exc:
            # [DEFENSIVE] — Clear error if the JSON is malformed or missing keys
            logger.error(
                "Failed to load Firebase credentials from %s: %s", cred_path, exc
            )
            raise
    else:
        firebase_admin.initialize_app()
        logger.info(
            "Firebase Admin initialized with Application Default Credentials"
        )


def verify_firebase_token(token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims."""
    return auth.verify_id_token(token)


def _resolve_credentials_path(raw_path: str) -> Path | None:
    """Resolve a credentials path, checking relative to APP_ROOT."""
    path = Path(raw_path)
    if path.is_absolute():
        return path if path.exists() else None

    resolved = APP_ROOT / path
    return resolved if resolved.exists() else None
