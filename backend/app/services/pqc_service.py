"""
Post-Quantum Cryptography Service
Implements ML-DSA (FIPS 204) digital signatures and ML-KEM (FIPS 203) key encapsulation
using Python's `cryptography` library (v50+).

ML-DSA-65 is used for digital signatures (NIST FIPS 204, security level 3).
ML-KEM-768 is used for key encapsulation (NIST FIPS 203, security level 3).

LIMITATIONS (Prototype):
- Private keys stored in encrypted local files (AES-256-GCM + PBKDF2), not hardware-backed.
- Production deployment requires HSM or equivalent protected key storage.
- The keystore password is demo-only; production must use strong, unique passwords.
"""
import base64
import hashlib
import json
import secrets
from pathlib import Path
from typing import Tuple, Dict, Any

from cryptography.hazmat.primitives.asymmetric import mldsa, mlkem
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, PublicFormat, NoEncryption,
    load_der_private_key, load_der_public_key,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import KEYS_DIR, PQC_SIG_ALGORITHM, PQC_KEM_ALGORITHM, KEYSTORE_PASSWORD

RESOLVED_SIG = "ML-DSA-65"
RESOLVED_KEM = "ML-KEM-768"


def is_pqc_available() -> bool:
    return True


def get_pqc_info() -> Dict[str, Any]:
    return {
        "available": True,
        "sig_algorithm": RESOLVED_SIG,
        "kem_algorithm": RESOLVED_KEM,
        "library": "cryptography 50.0.1",
        "sig_mechanisms": ["ML-DSA-44", "ML-DSA-65", "ML-DSA-87"],
        "kem_mechanisms": ["ML-KEM-768", "ML-KEM-1024"],
    }


def _derive_keystore_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000)
    return kdf.derive(password.encode("utf-8"))


def _encrypt_private_key(private_key_bytes: bytes, password: str) -> Dict[str, str]:
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    key = _derive_keystore_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, private_key_bytes, None)
    return {
        "salt": base64.b64encode(salt).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
    }


def _decrypt_private_key(encrypted: Dict[str, str], password: str) -> bytes:
    salt = base64.b64decode(encrypted["salt"])
    nonce = base64.b64decode(encrypted["nonce"])
    ct = base64.b64decode(encrypted["ciphertext"])
    key = _derive_keystore_key(password, salt)
    return AESGCM(key).decrypt(nonce, ct, None)


def fingerprint(public_key_bytes: bytes) -> str:
    return hashlib.sha256(public_key_bytes).hexdigest()


def generate_signing_keypair(recipient_id: str) -> Tuple[str, str, str]:
    """Generate ML-DSA-65 signing key pair. Returns (pub_b64, fingerprint, algorithm)."""
    private_key = mldsa.MLDSA65PrivateKey.generate()
    public_key = private_key.public_key()

    pub_raw = public_key.public_bytes_raw()
    priv_der = private_key.private_bytes(Encoding.DER, PrivateFormat.PKCS8, NoEncryption())

    pub_b64 = base64.b64encode(pub_raw).decode()
    fp = fingerprint(pub_raw)

    encrypted = _encrypt_private_key(priv_der, KEYSTORE_PASSWORD)
    keystore_path = KEYS_DIR / f"{recipient_id}_sig.json"
    with open(keystore_path, "w") as f:
        json.dump({
            "recipient_id": recipient_id,
            "algorithm": RESOLVED_SIG,
            "key_type": "signing",
            "public_key": pub_b64,
            "fingerprint": fp,
            "encrypted_private_key": encrypted,
            "key_format": "DER_PKCS8",
        }, f, indent=2)

    return pub_b64, fp, RESOLVED_SIG


def generate_kem_keypair(recipient_id: str) -> Tuple[str, str, str]:
    """Generate ML-KEM-768 key pair. Returns (pub_b64, fingerprint, algorithm)."""
    private_key = mlkem.MLKEM768PrivateKey.generate()
    public_key = private_key.public_key()

    pub_der = public_key.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
    priv_der = private_key.private_bytes(Encoding.DER, PrivateFormat.PKCS8, NoEncryption())

    pub_b64 = base64.b64encode(pub_der).decode()
    fp = fingerprint(pub_der)

    encrypted = _encrypt_private_key(priv_der, KEYSTORE_PASSWORD)
    keystore_path = KEYS_DIR / f"{recipient_id}_kem.json"
    with open(keystore_path, "w") as f:
        json.dump({
            "recipient_id": recipient_id,
            "algorithm": RESOLVED_KEM,
            "key_type": "kem",
            "public_key": pub_b64,
            "fingerprint": fp,
            "encrypted_private_key": encrypted,
            "key_format": "DER_PKCS8",
        }, f, indent=2)

    return pub_b64, fp, RESOLVED_KEM


def _load_signing_private_key(recipient_id: str):
    keystore_path = KEYS_DIR / f"{recipient_id}_sig.json"
    if not keystore_path.exists():
        raise FileNotFoundError(f"Signing key not found for recipient {recipient_id}")
    with open(keystore_path) as f:
        keydata = json.load(f)
    priv_der = _decrypt_private_key(keydata["encrypted_private_key"], KEYSTORE_PASSWORD)
    return load_der_private_key(priv_der, None)


def _load_kem_private_key(recipient_id: str):
    keystore_path = KEYS_DIR / f"{recipient_id}_kem.json"
    if not keystore_path.exists():
        raise FileNotFoundError(f"KEM key not found for recipient {recipient_id}")
    with open(keystore_path) as f:
        keydata = json.load(f)
    priv_der = _decrypt_private_key(keydata["encrypted_private_key"], KEYSTORE_PASSWORD)
    return load_der_private_key(priv_der, None)


def sign_message(recipient_id: str, message: bytes) -> str:
    """Sign a message using ML-DSA-65. Returns base64 signature."""
    private_key = _load_signing_private_key(recipient_id)
    sig = private_key.sign(message)
    return base64.b64encode(sig).decode()


def verify_signature(public_key_b64: str, message: bytes, signature_b64: str, algorithm: str = None) -> bool:
    """Verify an ML-DSA-65 signature using the raw public key."""
    pub_raw = base64.b64decode(public_key_b64)
    sig = base64.b64decode(signature_b64)
    # Reconstruct public key from raw bytes
    public_key = mldsa.MLDSA65PublicKey.from_public_bytes(pub_raw)
    try:
        public_key.verify(sig, message)
        return True
    except Exception:
        return False


def kem_encapsulate(recipient_public_key_b64: str) -> Tuple[bytes, str]:
    """Encapsulate shared secret with ML-KEM-768. Returns (shared_secret, ciphertext_b64)."""
    pub_der = base64.b64decode(recipient_public_key_b64)
    public_key = load_der_public_key(pub_der)
    shared_secret, ciphertext = public_key.encapsulate()
    return shared_secret, base64.b64encode(ciphertext).decode()


def kem_decapsulate(recipient_id: str, ciphertext_b64: str) -> bytes:
    """Decapsulate shared secret with recipient's ML-KEM-768 private key."""
    private_key = _load_kem_private_key(recipient_id)
    ciphertext = base64.b64decode(ciphertext_b64)
    return private_key.decapsulate(ciphertext)
