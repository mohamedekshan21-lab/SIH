"""
Database Models
SQLAlchemy ORM models for the Quantum-Safe Forensic Watermarking System.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, DateTime, Integer, Float,
    ForeignKey, Boolean, LargeBinary, Index, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from app.config import DATABASE_URL

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(String, primary_key=True, default=generate_uuid)
    display_name = Column(String(255), nullable=False)
    public_key = Column(Text, nullable=True)  # Base64-encoded PQC public key
    public_key_fingerprint = Column(String(64), nullable=True)
    kem_public_key = Column(Text, nullable=True)  # Base64-encoded KEM public key
    kem_public_key_fingerprint = Column(String(64), nullable=True)
    key_algorithm = Column(String(50), default="ML-DSA-65")
    kem_algorithm = Column(String(50), default="ML-KEM-768")
    status = Column(String(20), default="active")  # active, revoked, suspended
    created_at = Column(DateTime, default=utcnow)
    revoked_at = Column(DateTime, nullable=True)

    distributions = relationship("Distribution", back_populates="recipient")
    sessions = relationship("DecryptionSession", back_populates="recipient")

    __table_args__ = (
        Index("idx_recipient_fingerprint", "public_key_fingerprint"),
        Index("idx_recipient_status", "status"),
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String(512), nullable=False)
    original_hash = Column(String(64), nullable=False)  # SHA-256 of original
    encrypted_hash = Column(String(64), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    encryption_algorithm = Column(String(50), default="AES-256-GCM")
    encryption_status = Column(String(20), default="pending")  # pending, encrypted, failed
    stored_path = Column(Text, nullable=True)
    encrypted_path = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    distributions = relationship("Distribution", back_populates="document")
    sessions = relationship("DecryptionSession", back_populates="document")

    __table_args__ = (
        Index("idx_document_hash", "original_hash"),
    )


class Distribution(Base):
    __tablename__ = "distributions"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    recipient_id = Column(String, ForeignKey("recipients.id"), nullable=False)
    wrapped_key = Column(Text, nullable=True)  # Encrypted DEK for this recipient
    kem_ciphertext = Column(Text, nullable=True)  # KEM encapsulation ciphertext
    status = Column(String(20), default="distributed")  # distributed, revoked
    created_at = Column(DateTime, default=utcnow)

    document = relationship("Document", back_populates="distributions")
    recipient = relationship("Recipient", back_populates="distributions")

    __table_args__ = (
        Index("idx_dist_document", "document_id"),
        Index("idx_dist_recipient", "recipient_id"),
    )


class DecryptionSession(Base):
    __tablename__ = "decryption_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    recipient_id = Column(String, ForeignKey("recipients.id"), nullable=False)
    nonce = Column(String(64), nullable=True)
    status = Column(String(20), default="initiated")  # initiated, decrypting, watermarking, signing, committed, failed
    watermark_algorithm_version = Column(String(50), nullable=True)
    watermark_commitment = Column(String(64), nullable=True)
    watermarked_doc_path = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utcnow)

    document = relationship("Document", back_populates="sessions")
    recipient = relationship("Recipient", back_populates="sessions")

    __table_args__ = (
        Index("idx_session_document", "document_id"),
        Index("idx_session_recipient", "recipient_id"),
        Index("idx_session_watermark", "watermark_commitment"),
    )


class ForensicRecord(Base):
    __tablename__ = "forensic_records"

    event_id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, nullable=False)
    document_hash = Column(String(64), nullable=False)
    recipient_reference = Column(String, nullable=False)  # Privacy-preserving ref
    session_id = Column(String, nullable=False)
    watermark_commitment = Column(String(64), nullable=False)
    watermark_algorithm_version = Column(String(50), nullable=False)
    canonical_record_hash = Column(String(64), nullable=False)
    signature = Column(Text, nullable=False)  # Base64 ML-DSA signature
    public_key_fingerprint = Column(String(64), nullable=False)
    record_version = Column(String(10), default="1.0")
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_fr_document", "document_id"),
        Index("idx_fr_watermark", "watermark_commitment"),
        Index("idx_fr_session", "session_id"),
        Index("idx_fr_recipient", "recipient_reference"),
    )


class LedgerRecord(Base):
    __tablename__ = "ledger_records"

    record_id = Column(String, primary_key=True, default=generate_uuid)
    block_index = Column(Integer, nullable=False)
    event_id = Column(String, nullable=False)
    previous_record_hash = Column(String(64), nullable=False)
    record_hash = Column(String(64), nullable=False)
    merkle_root = Column(String(64), nullable=True)
    data_payload = Column(Text, nullable=False)  # JSON of the forensic record
    validator_confirmations = Column(Text, nullable=True)  # JSON list of validator sigs
    commit_status = Column(String(20), default="pending")  # pending, committed, rejected
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_ledger_block", "block_index"),
        Index("idx_ledger_event", "event_id"),
        Index("idx_ledger_hash", "record_hash"),
    )


class LedgerValidator(Base):
    __tablename__ = "ledger_validators"

    node_id = Column(String, primary_key=True)
    node_name = Column(String(100), nullable=False)
    status = Column(String(20), default="active")  # active, offline, compromised
    last_block_index = Column(Integer, default=0)
    last_seen = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)


class Investigation(Base):
    __tablename__ = "investigations"

    investigation_id = Column(String, primary_key=True, default=generate_uuid)
    input_document_hash = Column(String(64), nullable=True)
    input_filename = Column(String(512), nullable=True)
    extracted_watermark_status = Column(String(20), default="pending")  # pending, extracted, failed, not_found
    extracted_watermark_commitment = Column(String(64), nullable=True)
    matched_event_id = Column(String, nullable=True)
    verification_status = Column(String(20), default="pending")  # pending, verified, failed, incomplete
    signature_status = Column(String(20), nullable=True)
    ledger_status = Column(String(20), nullable=True)
    document_hash_status = Column(String(20), nullable=True)
    attribution_conclusion = Column(Text, nullable=True)
    report_path = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_inv_hash", "input_document_hash"),
        Index("idx_inv_event", "matched_event_id"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utcnow)


# Database engine and session
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
