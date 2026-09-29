"""
Application Configuration
Centralized configuration for the Quantum-Safe Forensic Watermarking System.
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KEYS_DIR = DATA_DIR / "keys"
DOCS_DIR = DATA_DIR / "documents"
ENCRYPTED_DIR = DATA_DIR / "encrypted"
DECRYPTED_DIR = DATA_DIR / "decrypted"
WATERMARKED_DIR = DATA_DIR / "watermarked"
LEDGER_DIR = DATA_DIR / "ledger"
FORENSIC_DIR = DATA_DIR / "forensic"
REPORTS_DIR = DATA_DIR / "reports"
UPLOADS_DIR = DATA_DIR / "uploads"

# Create all directories
for d in [DATA_DIR, KEYS_DIR, DOCS_DIR, ENCRYPTED_DIR, DECRYPTED_DIR,
          WATERMARKED_DIR, LEDGER_DIR, FORENSIC_DIR, REPORTS_DIR, UPLOADS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = f"sqlite:///{DATA_DIR / 'qsfw.db'}"

# Cryptography Configuration
ENCRYPTION_ALGORITHM = "AES-256-GCM"
HASH_ALGORITHM = "SHA-256"
PQC_SIG_ALGORITHM = "ML-DSA-65"  # NIST FIPS 204 (Dilithium3)
PQC_KEM_ALGORITHM = "ML-KEM-768"  # NIST FIPS 203 (Kyber768)

# Watermark Configuration
WATERMARK_ALGORITHM_VERSION = "QSFW-WM-v1.0"
WATERMARK_SECRET_KEY_ENV = "QSFW_WATERMARK_SECRET"
WATERMARK_SECRET = os.environ.get(WATERMARK_SECRET_KEY_ENV, "DEMO-ONLY-WATERMARK-SECRET-KEY-DO-NOT-USE-IN-PRODUCTION")

# Ledger Configuration
LEDGER_VALIDATOR_COUNT = 3
LEDGER_QUORUM_SIZE = 2  # Minimum validators for commit
LEDGER_BLOCK_SIZE = 10  # Records per block

# Keystore Configuration
KEYSTORE_PASSWORD_ENV = "QSFW_KEYSTORE_PASSWORD"
KEYSTORE_PASSWORD = os.environ.get(KEYSTORE_PASSWORD_ENV, "DEMO-ONLY-KEYSTORE-PASSWORD")

# Application
APP_VERSION = "1.0.0-prototype"
APP_NAME = "Quantum-Safe Forensic Watermarking System"
OFFLINE_MODE = True

# Record Version
RECORD_VERSION = "1.0"
