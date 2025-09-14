"""
Decrypt .env.encrypted file
Decrypts the .env.encrypted file and creates a .env file.

Author: HeadStart Development Team
Created: 2025-09-12
Purpose: To decrypt the .env.encrypted file.
"""

import os
from services.encryption import get_encryption_service

SENSITIVE_KEYS = [
    "OPENAI_API_KEY",
    "GPT_API_KEY",
    "YOUTUBE_API_KEY",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GITHUB_CLIENT_ID",
    "GITHUB_CLIENT_SECRET",
    "JWT_SECRET",
    "DATABASE_URL",
    "REDIS_URL",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
]

def decrypt_env_file():
    """Decrypts the .env.encrypted file"""
    encryption_service = get_encryption_service()

    with open(".env.encrypted", "r") as f_in, open(".env", "w") as f_out:
        for line in f_in:
            line = line.strip()
            if not line or line.startswith("#"):
                f_out.write(line + "\n")
                continue

            key, value = line.split("=", 1)
            if key in SENSITIVE_KEYS:
                decrypted_value = encryption_service.decrypt(value)
                f_out.write(f"{key}={decrypted_value}\n")
            else:
                f_out.write(line + "\n")

if __name__ == "__main__":
    decrypt_env_file()
