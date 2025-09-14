"""
Encrypt .env file
Encrypts sensitive values in the .env file and creates a .env.encrypted file.

Author: HeadStart Development Team
Created: 2025-09-12
Purpose: To encrypt sensitive information in the .env file.
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

def encrypt_env_file():
    """Encrypts the .env file"""
    encryption_service = get_encryption_service()

    with open(".env", "r") as f_in, open(".env.encrypted", "w") as f_out:
        for line in f_in:
            line = line.strip()
            if not line or line.startswith("#"):
                f_out.write(line + "\n")
                continue

            key, value = line.split("=", 1)
            if key in SENSITIVE_KEYS:
                encrypted_value = encryption_service.encrypt(value)
                f_out.write(f"{key}={encrypted_value}\n")
            else:
                f_out.write(line + "\n")

if __name__ == "__main__":
    encrypt_env_file()
