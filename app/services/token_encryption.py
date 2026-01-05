"""
Token encryption service
"""
from cryptography.fernet import Fernet
from app.config import settings
import base64
import hashlib


def get_encryption_key() -> bytes:
    """
    Get or generate encryption key from settings
    """
    if settings.token_encryption_key:
        # Use provided key, ensure it's properly formatted
        key = settings.token_encryption_key
        if isinstance(key, str):
            key = key.encode()
        # Derive a Fernet-compatible key from the provided key
        return base64.urlsafe_b64encode(hashlib.sha256(key).digest())
    else:
        # Generate a new key (in production, this should be stored)
        return Fernet.generate_key()


_fernet = Fernet(get_encryption_key())


def encrypt_token(token: str) -> str:
    """
    Encrypt a token for storage
    """
    if not token:
        return ""
    return _fernet.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a stored token
    """
    if not encrypted_token:
        return ""
    return _fernet.decrypt(encrypted_token.encode()).decode()

