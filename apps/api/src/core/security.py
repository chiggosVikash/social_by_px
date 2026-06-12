from cryptography.fernet import Fernet
from core.config import get_settings
import firebase_admin
from firebase_admin import auth, credentials

# Initialize Firebase Admin app if it hasn't been initialized
if not firebase_admin._apps:
    # Use default credentials (works if GOOGLE_APPLICATION_CREDENTIALS is set)
    # Alternatively, you can use a service account key path here.
    # We will initialize with default behavior.
    firebase_admin.initialize_app()

def get_fernet() -> Fernet:
    settings = get_settings()
    return Fernet(settings.ENCRYPTION_KEY.encode('utf-8'))

def encrypt_token(token: str) -> str:
    return get_fernet().encrypt(token.encode('utf-8')).decode('utf-8')

def decrypt_token(encrypted_token: str) -> str:
    return get_fernet().decrypt(encrypted_token.encode('utf-8')).decode('utf-8')

def verify_firebase_token(token: str) -> dict:
    """Verifies a Firebase ID token and returns the decoded token."""
    return auth.verify_id_token(token)

