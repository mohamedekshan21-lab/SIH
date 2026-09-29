"""
Encryption Service
Implements document encryption using AES-256-GCM with envelope encryption.
Key wrapping uses ML-KEM for post-quantum key establishment.

DESIGN:
- A random 256-bit Document Encryption Key (DEK) is generated per document.
- The document is encrypted with AES-256-GCM using the DEK.
- For each recipient, the DEK is wrapped using ML-KEM key encapsulation:
  - A shared secret is encapsulated with the recipient's ML-KEM public key.
  - The shared secret is used to derive a Key Wrapping Key (KWK).
  - The DEK is encrypted (wrapped) with AES-256-GCM using the KWK.

LIMITATIONS:
- This is an envelope-encryption distribution model, not a fully secure broadcast encryption scheme.
- Each recipient has an independently encapsulated copy of the DEK.
- Security depends on the strength of ML-KEM and AES-256-GCM.
"""
import os
import base64
import hashlib
import secrets
import json
from pathlib import Path
from typing import Tuple, Dict, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config import DOCS_DIR, ENCRYPTED_DIR, DECRYPTED_DIR
from app.services import pqc_service


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_bytes_hash(data: bytes) -> str:
    """Compute SHA-256 hash of bytes."""
    return hashlib.sha256(data).hexdigest()


def _generate_dek() -> bytes:
    """Generate a random 256-bit Document Encryption Key."""
    return secrets.token_bytes(32)


def _derive_wrapping_key(shared_secret: bytes, context: bytes = b"DEK-WRAP") -> bytes:
    """Derive a wrapping key from KEM shared secret using HKDF."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=context,
    )
    return hkdf.derive(shared_secret)


def encrypt_document(file_path: str, document_id: str) -> Tuple[str, str, bytes]:
    """
    Encrypt a document with AES-256-GCM.
    Returns: (encrypted_file_path, encrypted_hash, dek)
    The DEK must be securely wrapped for each recipient separately.
    """
    with open(file_path, "rb") as f:
        plaintext = f.read()

    dek = _generate_dek()
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(dek)
    ciphertext = aesgcm.encrypt(nonce, plaintext, document_id.encode("utf-8"))

    # Store: nonce || ciphertext
    encrypted_data = nonce + ciphertext
    encrypted_path = str(ENCRYPTED_DIR / f"{document_id}.enc")
    with open(encrypted_path, "wb") as f:
        f.write(encrypted_data)

    encrypted_hash = compute_bytes_hash(encrypted_data)
    return encrypted_path, encrypted_hash, dek


def wrap_dek_for_recipient(dek: bytes, recipient_kem_public_key_b64: str) -> Dict[str, str]:
    """
    Wrap the DEK for a specific recipient using ML-KEM.
    Returns dict with kem_ciphertext and wrapped_dek (both base64).
    """
    # Encapsulate shared secret with recipient's KEM public key
    shared_secret, kem_ciphertext_b64 = pqc_service.kem_encapsulate(recipient_kem_public_key_b64)

    # Derive wrapping key from shared secret
    wrapping_key = _derive_wrapping_key(shared_secret)

    # Wrap the DEK with AES-256-GCM
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(wrapping_key)
    wrapped = aesgcm.encrypt(nonce, dek, b"DEK-ENVELOPE")

    return {
        "kem_ciphertext": kem_ciphertext_b64,
        "wrapped_dek": base64.b64encode(nonce + wrapped).decode(),
    }


def unwrap_dek_for_recipient(recipient_id: str, kem_ciphertext_b64: str, wrapped_dek_b64: str) -> bytes:
    """
    Unwrap the DEK using recipient's ML-KEM private key.
    Returns the DEK bytes.
    """
    # Decapsulate shared secret
    shared_secret = pqc_service.kem_decapsulate(recipient_id, kem_ciphertext_b64)

    # Derive wrapping key
    wrapping_key = _derive_wrapping_key(shared_secret)

    # Unwrap the DEK
    wrapped_data = base64.b64decode(wrapped_dek_b64)
    nonce = wrapped_data[:12]
    ciphertext = wrapped_data[12:]
    aesgcm = AESGCM(wrapping_key)
    dek = aesgcm.decrypt(nonce, ciphertext, b"DEK-ENVELOPE")
    return dek


def decrypt_document(encrypted_path: str, document_id: str, dek: bytes) -> bytes:
    """
    Decrypt a document using the DEK.
    Returns plaintext bytes.
    """
    with open(encrypted_path, "rb") as f:
        encrypted_data = f.read()

    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    aesgcm = AESGCM(dek)
    plaintext = aesgcm.decrypt(nonce, ciphertext, document_id.encode("utf-8"))
    return plaintext
