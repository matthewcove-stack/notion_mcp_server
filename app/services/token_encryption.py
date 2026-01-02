"""
Token encryption utilities using Fernet
"""
from cryptography.fernet import Fernet
from typing import Optional
import structlog

from app.config import settings

logger = structlog.get_logger()


class TokenEncryption:
    """Handle encryption/decryption of OAuth tokens"""
    
    def __init__(self):
        if not settings.TOKEN_ENCRYPTION_KEY:
            raise ValueError("TOKEN_ENCRYPTION_KEY must be set")
        
        try:
            self.cipher = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())
        except Exception as e:
            logger.error("token_encryption_init_failed", error=str(e))
            raise ValueError(f"Invalid TOKEN_ENCRYPTION_KEY: {e}")
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a token"""
        if not plaintext:
            return ""
        try:
            encrypted = self.cipher.encrypt(plaintext.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error("token_encryption_failed", error=str(e))
            raise ValueError(f"Failed to encrypt token: {e}")
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a token"""
        if not ciphertext:
            return ""
        try:
            decrypted = self.cipher.decrypt(ciphertext.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error("token_decryption_failed", error=str(e))
            raise ValueError(f"Failed to decrypt token: {e}")


# Singleton instance
_token_encryption: Optional[TokenEncryption] = None


def get_token_encryption() -> TokenEncryption:
    """Get or create token encryption instance"""
    global _token_encryption
    if _token_encryption is None:
        _token_encryption = TokenEncryption()
    return _token_encryption

