from cryptography.fernet import Fernet
from src.core.config import get_settings

settings = get_settings()
fernet = Fernet(settings.ENCRYPTION_KEY.encode('utf-8'))

def encrypt_token(token: str) -> str:
    return fernet.encrypt(token.encode('utf-8')).decode('utf-8')

def decrypt_token(encrypted_token: str) -> str:
    return fernet.decrypt(encrypted_token.encode('utf-8')).decode('utf-8')
