from cryptography.fernet import Fernet
from core.config import get_settings

def get_fernet() -> Fernet:
    settings = get_settings()
    return Fernet(settings.ENCRYPTION_KEY.encode('utf-8'))

def encrypt_token(token: str) -> str:
    return get_fernet().encrypt(token.encode('utf-8')).decode('utf-8')

def decrypt_token(encrypted_token: str) -> str:
    return get_fernet().decrypt(encrypted_token.encode('utf-8')).decode('utf-8')
