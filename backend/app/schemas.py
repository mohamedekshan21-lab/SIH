"""
Pydantic Schemas for API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# === Recipient ===

class RecipientCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)

class RecipientResponse(BaseModel):
    id: str
    display_name: str
    public_key_fingerprint: Optional[str] = None
    kem_public_key_fingerprint: Optional[str] = None
    key_algorithm: str = "ML-DSA-65"
    kem_algorithm: str = "ML-KEM-768"
    status: str = "active"
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

class RecipientKeyInfo(BaseModel):
    signing_key_generated: bool
    kem_key_generated: bool
    public_key_fingerprint: Optional[str] = None
    kem_public_key_fingerprint: Optional[str] = None
    sig_algorithm: str = "ML-DSA-65"
    kem_algorithm: str = "ML-KEM-768"


# === Document ===

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_hash: str
    encrypted_hash: Optional[str] = None
    file_size: Optional[int] = None
    encryption_algorithm: str
    encryption_status: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

class EncryptRequest(BaseModel):
    recipient_ids: List[str]

class EncryptResponse(BaseModel):
    document_id: str
    encryption_status: str
    encrypted_hash: Optional[str] = None
    distributions: List[Dict[str, str]] = []


# === Distribution ===

class DistributionResponse(BaseModel):
    id: str
    document_id: str
    recipient_id: str
    recipient_name: Optional[str] = None
    status: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


# === Decryption ===

class DecryptionSessionCreate(BaseModel):
    document_id: str
    recipient_id: str

class DecryptionSessionResponse(BaseModel):
    session_id: str
    document_id: str
    recipient_id: str
    status: str
    watermark_commitment: Optional[str] = None
    timestamp: Optional[str] = None
    events: List[Dict[str, Any]] = []


# === Ledger ===

class LedgerRecordResponse(BaseModel):
    record_id: str
    block_index: int
    event_id: str
    record_hash: str
    previous_record_hash: str
    merkle_root: Optional[str] = None
    commit_status: str
    created_at: Optional[str] = None
    data_payload: Optional[Dict[str, Any]] = None

class LedgerHealthResponse(BaseModel):
    status: str
    validator_count: int
    quorum_size: int
    total_records: int
    chain_valid: bool
    nodes_consistent: bool
    merkle_root: Optional[str] = None
    validators: List[Dict[str, Any]] = []

class LedgerVerifyResponse(BaseModel):
    overall_valid: bool
    consistent: bool
    validators: Dict[str, Any] = {}
    total_records: int


# === Forensic ===

class InvestigationResponse(BaseModel):
    investigation_id: str
    input_document_hash: Optional[str] = None
    input_filename: Optional[str] = None
    extracted_watermark_status: str = "pending"
    extracted_watermark_commitment: Optional[str] = None
    matched_event_id: Optional[str] = None
    verification_status: str = "pending"
    signature_status: Optional[str] = None
    ledger_status: Optional[str] = None
    document_hash_status: Optional[str] = None
    attribution_conclusion: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

class ForensicReportResponse(BaseModel):
    report_id: str
    investigation_id: str
    generated_at: str
    evidence_summary: Dict[str, Any]
    verification_results: Dict[str, Any]
    attribution: Dict[str, Any]
    limitations: List[str]


# === System ===

class SystemConfigResponse(BaseModel):
    app_name: str
    app_version: str
    offline_mode: bool
    encryption_algorithm: str
    hash_algorithm: str
    sig_algorithm: str
    kem_algorithm: str
    watermark_algorithm_version: str
    ledger_validator_count: int
    ledger_quorum_size: int
    pqc_available: bool
    pqc_library: str
    supported_formats: List[str] = ["PDF"]

class DashboardStats(BaseModel):
    total_documents: int = 0
    total_encrypted: int = 0
    total_recipients: int = 0
    total_sessions: int = 0
    total_signed_records: int = 0
    ledger_health: str = "unknown"
    validator_status: List[Dict[str, Any]] = []
    pending_transactions: int = 0
    tamper_alerts: int = 0
    recent_activity: List[Dict[str, Any]] = []
