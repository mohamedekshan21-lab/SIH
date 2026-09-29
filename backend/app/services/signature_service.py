"""
Signature Service
Implements signed forensic records using ML-DSA post-quantum digital signatures.

Each decryption event produces a structured forensic record. The record is
canonically serialized (deterministic JSON), hashed, and signed by the
recipient's ML-DSA private key.

A digital signature provides cryptographic evidence that the holder of the
signing key signed the record. It does NOT prove that a specific person
physically operated the device. This distinction must be clearly communicated
in any forensic report.
"""
import json
import hashlib
from typing import Dict, Any, Tuple

from app.config import RECORD_VERSION
from app.services import pqc_service


def create_forensic_record(
    event_id: str,
    document_id: str,
    document_hash: str,
    recipient_reference: str,
    session_id: str,
    watermark_commitment: str,
    timestamp: str,
    watermark_algorithm_version: str,
    public_key_fingerprint: str,
) -> Dict[str, str]:
    """Create a structured forensic record."""
    return {
        "event_id": event_id,
        "document_id": document_id,
        "document_hash": document_hash,
        "recipient_id": recipient_reference,
        "session_id": session_id,
        "watermark_commitment": watermark_commitment,
        "timestamp": timestamp,
        "watermark_algorithm_version": watermark_algorithm_version,
        "public_key_fingerprint": public_key_fingerprint,
        "record_version": RECORD_VERSION,
    }


def canonical_serialize(record: Dict[str, str]) -> bytes:
    """
    Deterministic canonical serialization of a forensic record.
    Keys are sorted alphabetically, no whitespace, UTF-8 encoding.
    """
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def compute_record_hash(record: Dict[str, str]) -> str:
    """Compute SHA-256 hash of the canonical record."""
    canonical = canonical_serialize(record)
    return hashlib.sha256(canonical).hexdigest()


def sign_forensic_record(
    recipient_id: str,
    record: Dict[str, str]
) -> Tuple[str, str]:
    """
    Sign a forensic record using the recipient's ML-DSA private key.
    Returns: (signature_b64, canonical_record_hash)
    """
    canonical = canonical_serialize(record)
    record_hash = hashlib.sha256(canonical).hexdigest()
    signature = pqc_service.sign_message(recipient_id, canonical)
    return signature, record_hash


def verify_forensic_record(
    record: Dict[str, str],
    signature_b64: str,
    public_key_b64: str,
    expected_record_hash: str = None,
    algorithm: str = None,
) -> Dict[str, Any]:
    """
    Verify a signed forensic record.
    Returns a verification result dict.
    """
    result = {
        "record_hash_valid": False,
        "signature_valid": False,
        "record_integrity": False,
        "details": {},
    }

    # Verify canonical hash
    canonical = canonical_serialize(record)
    computed_hash = hashlib.sha256(canonical).hexdigest()
    result["details"]["computed_hash"] = computed_hash

    if expected_record_hash:
        result["record_hash_valid"] = (computed_hash == expected_record_hash)
        result["details"]["expected_hash"] = expected_record_hash
    else:
        result["record_hash_valid"] = True  # No expected hash to check

    # Verify signature
    try:
        sig_valid = pqc_service.verify_signature(public_key_b64, canonical, signature_b64, algorithm)
        result["signature_valid"] = sig_valid
    except Exception as e:
        result["signature_valid"] = False
        result["details"]["signature_error"] = str(e)

    # Overall integrity
    result["record_integrity"] = result["record_hash_valid"] and result["signature_valid"]

    return result
