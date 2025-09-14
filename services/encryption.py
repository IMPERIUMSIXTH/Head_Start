"""
Encryption Service
Service for encrypting and decrypting sensitive information

Author: HeadStart Development Team
Created: 2025-09-12
Purpose: Encryption and decryption of sensitive data using AES-GCM
"""

import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from config.settings import get_settings

class EncryptionService:
    """Encryption service using AES-GCM"""

    def __init__(self):
        settings = get_settings()
        key = base64.urlsafe_b64decode(settings.ENCRYPTION_KEY.encode())
        self.aesgcm = AESGCM(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext"""
        if not plaintext:
            return ""

        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        return f"{base64.urlsafe_b64encode(nonce).decode()}.{base64.urlsafe_b64encode(ciphertext).decode()}"

    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt ciphertext"""
        if not encrypted_text or "." not in encrypted_text:
            return ""

        nonce_str, ciphertext_str = encrypted_text.split(".", 1)
        nonce = base64.urlsafe_b64decode(nonce_str.encode())
        ciphertext = base64.urlsafe_b64decode(ciphertext_str.encode())

        try:
            decrypted_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted_bytes.decode()
        except Exception as e:
            # Handle decryption errors (e.g., invalid key, corrupted data)
            return ""

# Global encryption service instance
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """Get encryption service instance (singleton)"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
