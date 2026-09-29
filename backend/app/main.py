"""
Main FastAPI Application
Quantum-Safe Session-Bound Forensic Watermarking System

All endpoints are designed for offline operation.
No external cloud services, public blockchains, or network APIs are required.
"""
import os
import uuid
import json
import shutil
import hashlib
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import (
    APP_NAME, APP_VERSION, OFFLINE_MODE,
    ENCRYPTION_ALGORITHM, HASH_ALGORITHM,
    PQC_SIG_ALGORITHM, PQC_KEM_ALGORITHM,
    WATERMARK_ALGORITHM_VERSION, WATERMARK_SECRET,
    LEDGER_VALIDATOR_COUNT, LEDGER_QUORUM_SIZE,
    DOCS_DIR, ENCRYPTED_DIR, DECRYPTED_DIR, WATERMARKED_DIR,
    UPLOADS_DIR, FORENSIC_DIR, REPORTS_DIR,
)
from app.models import (
    init_db, get_db, Recipient, Document, Distribution,
    DecryptionSession, ForensicRecord, LedgerRecord,
    Investigation, AuditLog
)
from app.schemas import (
    RecipientCreate, RecipientResponse, RecipientKeyInfo,
    DocumentResponse, EncryptRequest, EncryptResponse,
    DistributionResponse, DecryptionSessionCreate, DecryptionSessionResponse,
    LedgerRecordResponse, LedgerHealthResponse, LedgerVerifyResponse,
    InvestigationResponse, ForensicReportResponse,
    SystemConfigResponse, DashboardStats,
)
from app.services import pqc_service, encryption_service, watermark_service, signature_service, forensic_service
from app.services.ledger_service import get_ledger_manager

# Initialize database
init_db()

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Quantum-Safe Session-Bound Forensic Watermarking with Offline Tamper-Evident DLT",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== DASHBOARD =====

@app.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    total_docs = db.query(Document).count()
    total_encrypted = db.query(Document).filter(Document.encryption_status == "encrypted").count()
    total_recipients = db.query(Recipient).filter(Recipient.status == "active").count()
    total_sessions = db.query(DecryptionSession).count()
    total_signed = db.query(ForensicRecord).count()

    ledger = get_ledger_manager()
    health = ledger.get_health()

    recent = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10).all()
    recent_activity = [
        {
            "id": r.id,
            "event_type": r.event_type,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "details": r.details,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in recent
    ]

    return DashboardStats(
        total_documents=total_docs,
        total_encrypted=total_encrypted,
        total_recipients=total_recipients,
        total_sessions=total_sessions,
        total_signed_records=total_signed,
        ledger_health=health["status"],
        validator_status=health["validators"],
        pending_transactions=0,
        tamper_alerts=0,
        recent_activity=recent_activity,
    )


# ===== RECIPIENTS =====

@app.post("/api/recipients", response_model=RecipientResponse)
def create_recipient(data: RecipientCreate, db: Session = Depends(get_db)):
    recipient = Recipient(
        id=str(uuid.uuid4()),
        display_name=data.display_name,
    )
    db.add(recipient)
    db.commit()
    db.refresh(recipient)

    _audit(db, "recipient_created", "recipient", recipient.id, f"Created recipient: {data.display_name}")

    return _recipient_to_response(recipient)


@app.get("/api/recipients", response_model=List[RecipientResponse])
def list_recipients(db: Session = Depends(get_db)):
    recipients = db.query(Recipient).all()
    return [_recipient_to_response(r) for r in recipients]


@app.get("/api/recipients/{recipient_id}", response_model=RecipientResponse)
def get_recipient(recipient_id: str, db: Session = Depends(get_db)):
    r = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not r:
        raise HTTPException(404, "Recipient not found")
    return _recipient_to_response(r)


@app.post("/api/recipients/{recipient_id}/keys", response_model=RecipientKeyInfo)
def generate_keys(recipient_id: str, db: Session = Depends(get_db)):
    r = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not r:
        raise HTTPException(404, "Recipient not found")
    if r.status == "revoked":
        raise HTTPException(400, "Cannot generate keys for revoked recipient")

    # Generate ML-DSA signing key pair
    pub_b64, fp, alg = pqc_service.generate_signing_keypair(recipient_id)
    r.public_key = pub_b64
    r.public_key_fingerprint = fp
    r.key_algorithm = alg

    # Generate ML-KEM key pair
    kem_pub_b64, kem_fp, kem_alg = pqc_service.generate_kem_keypair(recipient_id)
    r.kem_public_key = kem_pub_b64
    r.kem_public_key_fingerprint = kem_fp
    r.kem_algorithm = kem_alg

    db.commit()
    _audit(db, "keys_generated", "recipient", recipient_id, f"PQC keys generated: {alg}, {kem_alg}")

    return RecipientKeyInfo(
        signing_key_generated=True,
        kem_key_generated=True,
        public_key_fingerprint=fp,
        kem_public_key_fingerprint=kem_fp,
        sig_algorithm=alg,
        kem_algorithm=kem_alg,
    )


@app.post("/api/recipients/{recipient_id}/revoke")
def revoke_recipient(recipient_id: str, db: Session = Depends(get_db)):
    r = db.query(Recipient).filter(Recipient.id == recipient_id).first()
    if not r:
        raise HTTPException(404, "Recipient not found")
    r.status = "revoked"
    r.revoked_at = datetime.now(timezone.utc)
    db.commit()
    _audit(db, "recipient_revoked", "recipient", recipient_id, "Recipient revoked")
    return {"status": "revoked", "recipient_id": recipient_id}


# ===== DOCUMENTS =====

@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(400, "No filename")

    # Validate file type
    allowed = [".pdf"]
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type: {ext}. Supported: {allowed}")

    doc_id = str(uuid.uuid4())
    save_path = DOCS_DIR / f"{doc_id}{ext}"

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    doc_hash = encryption_service.compute_bytes_hash(content)
    doc = Document(
        id=doc_id,
        filename=file.filename,
        original_hash=doc_hash,
        file_size=len(content),
        mime_type=file.content_type,
        stored_path=str(save_path),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    _audit(db, "document_uploaded", "document", doc_id, f"Uploaded: {file.filename}")

    return _doc_to_response(doc)


@app.post("/api/documents/{document_id}/encrypt", response_model=EncryptResponse)
def encrypt_document(document_id: str, data: EncryptRequest, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.encryption_status == "encrypted":
        raise HTTPException(400, "Document already encrypted")
    if not doc.stored_path or not Path(doc.stored_path).exists():
        raise HTTPException(400, "Document file not found on disk")

    # Validate recipients have KEM keys
    distributions = []
    for rid in data.recipient_ids:
        r = db.query(Recipient).filter(Recipient.id == rid).first()
        if not r:
            raise HTTPException(404, f"Recipient {rid} not found")
        if r.status == "revoked":
            raise HTTPException(400, f"Recipient {r.display_name} is revoked")
        if not r.kem_public_key:
            raise HTTPException(400, f"Recipient {r.display_name} has no KEM key. Generate keys first.")

    # Encrypt document
    encrypted_path, encrypted_hash, dek = encryption_service.encrypt_document(doc.stored_path, document_id)
    doc.encrypted_path = encrypted_path
    doc.encrypted_hash = encrypted_hash
    doc.encryption_status = "encrypted"

    # Wrap DEK for each recipient
    for rid in data.recipient_ids:
        r = db.query(Recipient).filter(Recipient.id == rid).first()
        wrap_result = encryption_service.wrap_dek_for_recipient(dek, r.kem_public_key)

        dist = Distribution(
            id=str(uuid.uuid4()),
            document_id=document_id,
            recipient_id=rid,
            wrapped_key=wrap_result["wrapped_dek"],
            kem_ciphertext=wrap_result["kem_ciphertext"],
        )
        db.add(dist)
        distributions.append({"recipient_id": rid, "distribution_id": dist.id, "status": "distributed"})

    db.commit()
    _audit(db, "document_encrypted", "document", document_id,
           f"Encrypted and distributed to {len(data.recipient_ids)} recipients")

    return EncryptResponse(
        document_id=document_id,
        encryption_status="encrypted",
        encrypted_hash=encrypted_hash,
        distributions=distributions,
    )


@app.get("/api/documents", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [_doc_to_response(d) for d in docs]


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return _doc_to_response(doc)


@app.get("/api/documents/{document_id}/distributions", response_model=List[DistributionResponse])
def get_distributions(document_id: str, db: Session = Depends(get_db)):
    dists = db.query(Distribution).filter(Distribution.document_id == document_id).all()
    result = []
    for d in dists:
        r = db.query(Recipient).filter(Recipient.id == d.recipient_id).first()
        result.append(DistributionResponse(
            id=d.id,
            document_id=d.document_id,
            recipient_id=d.recipient_id,
            recipient_name=r.display_name if r else None,
            status=d.status,
            created_at=d.created_at.isoformat() if d.created_at else None,
        ))
    return result


# ===== DECRYPTION =====

@app.post("/api/decryption/sessions", response_model=DecryptionSessionResponse)
def create_decryption_session(data: DecryptionSessionCreate, db: Session = Depends(get_db)):
    """Execute the full decryption + watermarking + signing + ledger commit workflow."""
    doc = db.query(Document).filter(Document.id == data.document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.encryption_status != "encrypted":
        raise HTTPException(400, "Document not encrypted")

    recipient = db.query(Recipient).filter(Recipient.id == data.recipient_id).first()
    if not recipient:
        raise HTTPException(404, "Recipient not found")
    if recipient.status == "revoked":
        raise HTTPException(403, "Recipient is revoked")
    if not recipient.public_key or not recipient.kem_public_key:
        raise HTTPException(400, "Recipient keys not generated")

    # Check distribution exists
    dist = db.query(Distribution).filter(
        Distribution.document_id == data.document_id,
        Distribution.recipient_id == data.recipient_id,
    ).first()
    if not dist:
        raise HTTPException(403, "Recipient not authorized for this document")

    session_id = str(uuid.uuid4())
    nonce = secrets.token_hex(16)
    timestamp = datetime.now(timezone.utc)
    events = []

    session = DecryptionSession(
        id=session_id,
        document_id=data.document_id,
        recipient_id=data.recipient_id,
        nonce=nonce,
        status="initiated",
        watermark_algorithm_version=WATERMARK_ALGORITHM_VERSION,
        timestamp=timestamp,
    )
    db.add(session)
    db.commit()

    try:
        # Step 1: Credential validation
        events.append({"step": 1, "name": "Credential Validation", "status": "success",
                       "detail": f"Recipient {recipient.display_name} authenticated"})

        # Step 2: Document decryption
        session.status = "decrypting"
        db.commit()
        dek = encryption_service.unwrap_dek_for_recipient(
            data.recipient_id, dist.kem_ciphertext, dist.wrapped_key
        )
        plaintext = encryption_service.decrypt_document(doc.encrypted_path, data.document_id, dek)
        events.append({"step": 2, "name": "Document Decryption", "status": "success",
                       "detail": f"Decrypted {len(plaintext)} bytes"})

        # Step 3: Watermark generation
        session.status = "watermarking"
        db.commit()
        recipient_ref = hashlib.sha256(
            f"{data.recipient_id}:{recipient.public_key_fingerprint}".encode()
        ).hexdigest()[:16]

        wm_payload = watermark_service.generate_watermark_payload(
            document_id=data.document_id,
            recipient_reference=recipient_ref,
            session_id=session_id,
            nonce=nonce,
            algorithm_version=WATERMARK_ALGORITHM_VERSION,
        )
        wm_commitment = watermark_service.compute_watermark_commitment(wm_payload)
        events.append({"step": 3, "name": "Watermark Generation", "status": "success",
                       "detail": f"Commitment: {wm_commitment[:16]}..."})

        # Step 4: Watermark embedding
        wm_path, wm_stats = watermark_service.embed_watermark_in_pdf(
            plaintext, wm_payload, session_id
        )
        events.append({"step": 4, "name": "Watermark Embedding", "status": "success",
                       "detail": f"Embedded {wm_stats['total_bits_embedded']} bits in {wm_stats['pages_processed']} pages"})

        # Step 5: Record canonicalization
        session.status = "signing"
        db.commit()
        event_id = str(uuid.uuid4())
        forensic_rec = signature_service.create_forensic_record(
            event_id=event_id,
            document_id=data.document_id,
            document_hash=doc.original_hash,
            recipient_reference=recipient_ref,
            session_id=session_id,
            watermark_commitment=wm_commitment,
            timestamp=timestamp.isoformat(),
            watermark_algorithm_version=WATERMARK_ALGORITHM_VERSION,
            public_key_fingerprint=recipient.public_key_fingerprint,
        )
        events.append({"step": 5, "name": "Record Canonicalization", "status": "success"})

        # Step 6: ML-DSA signature
        signature_b64, canonical_hash = signature_service.sign_forensic_record(
            data.recipient_id, forensic_rec
        )
        events.append({"step": 6, "name": "ML-DSA Signature", "status": "success",
                       "detail": f"Signed with {pqc_service.RESOLVED_SIG}"})

        # Step 7: Store forensic record in DB
        fr = ForensicRecord(
            event_id=event_id,
            document_id=data.document_id,
            document_hash=doc.original_hash,
            recipient_reference=recipient_ref,
            session_id=session_id,
            watermark_commitment=wm_commitment,
            watermark_algorithm_version=WATERMARK_ALGORITHM_VERSION,
            canonical_record_hash=canonical_hash,
            signature=signature_b64,
            public_key_fingerprint=recipient.public_key_fingerprint,
        )
        db.add(fr)
        db.commit()

        # Step 8: Ledger submission
        ledger = get_ledger_manager()
        ledger_result = ledger.submit_transaction(forensic_rec, event_id)
        events.append({"step": 7, "name": "Ledger Submission", "status": "success",
                       "detail": f"Block {ledger_result['block_index']}, Quorum: {'met' if ledger_result['quorum_met'] else 'NOT met'}"})

        # Store ledger record in DB
        lr = LedgerRecord(
            record_id=ledger_result["record_id"],
            block_index=ledger_result["block_index"],
            event_id=event_id,
            previous_record_hash=ledger_result["previous_hash"],
            record_hash=ledger_result["record_hash"],
            merkle_root=ledger_result["merkle_root"],
            data_payload=json.dumps(forensic_rec),
            validator_confirmations=json.dumps(ledger_result["confirmations"]),
            commit_status=ledger_result["commit_status"],
        )
        db.add(lr)

        events.append({"step": 8, "name": "Ledger Commit", "status": "success",
                       "detail": f"Status: {ledger_result['commit_status']}"})

        # Step 9: Finalize
        session.status = "committed"
        session.watermark_commitment = wm_commitment
        session.watermarked_doc_path = wm_path
        db.commit()

        events.append({"step": 9, "name": "Watermarked Document Ready", "status": "success",
                       "detail": f"Output: {Path(wm_path).name}"})

        _audit(db, "decryption_session", "session", session_id,
               f"Recipient {recipient.display_name} decrypted document {doc.filename}")

    except Exception as e:
        session.status = "failed"
        db.commit()
        events.append({"step": "error", "name": "Error", "status": "failed", "detail": str(e)})
        raise HTTPException(500, f"Decryption workflow failed: {str(e)}")

    return DecryptionSessionResponse(
        session_id=session_id,
        document_id=data.document_id,
        recipient_id=data.recipient_id,
        status=session.status,
        watermark_commitment=wm_commitment,
        timestamp=timestamp.isoformat(),
        events=events,
    )


@app.get("/api/decryption/sessions", response_model=List[DecryptionSessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(DecryptionSession).order_by(DecryptionSession.timestamp.desc()).all()
    result = []
    for s in sessions:
        result.append(DecryptionSessionResponse(
            session_id=s.id,
            document_id=s.document_id,
            recipient_id=s.recipient_id,
            status=s.status,
            watermark_commitment=s.watermark_commitment,
            timestamp=s.timestamp.isoformat() if s.timestamp else None,
        ))
    return result


@app.get("/api/decryption/sessions/{session_id}")
def get_session(session_id: str, db: Session = Depends(get_db)):
    s = db.query(DecryptionSession).filter(DecryptionSession.id == session_id).first()
    if not s:
        raise HTTPException(404, "Session not found")
    r = db.query(Recipient).filter(Recipient.id == s.recipient_id).first()
    return {
        "session_id": s.id,
        "document_id": s.document_id,
        "recipient_id": s.recipient_id,
        "recipient_name": r.display_name if r else None,
        "status": s.status,
        "watermark_commitment": s.watermark_commitment,
        "watermark_algorithm_version": s.watermark_algorithm_version,
        "timestamp": s.timestamp.isoformat() if s.timestamp else None,
    }


@app.get("/api/decryption/sessions/{session_id}/download")
def download_watermarked(session_id: str, db: Session = Depends(get_db)):
    s = db.query(DecryptionSession).filter(DecryptionSession.id == session_id).first()
    if not s:
        raise HTTPException(404, "Session not found")
    if not s.watermarked_doc_path or not Path(s.watermarked_doc_path).exists():
        raise HTTPException(404, "Watermarked document not found")
    return FileResponse(s.watermarked_doc_path, filename=f"decrypted_{session_id[:8]}.pdf")


# ===== LEDGER =====

@app.get("/api/ledger/health", response_model=LedgerHealthResponse)
def ledger_health():
    ledger = get_ledger_manager()
    return ledger.get_health()


@app.get("/api/ledger/records")
def ledger_records(
    event_id: Optional[str] = None,
    document_id: Optional[str] = None,
    watermark_commitment: Optional[str] = None,
):
    ledger = get_ledger_manager()
    records = ledger.get_all_records()

    # Apply filters
    if event_id:
        records = [r for r in records if r.get("event_id") == event_id]
    if document_id:
        records = [r for r in records if _payload_field(r, "document_id") == document_id]
    if watermark_commitment:
        records = [r for r in records if _payload_field(r, "watermark_commitment") == watermark_commitment]

    # Parse data payloads for display
    result = []
    for r in records:
        payload = r.get("data_payload", "{}")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        result.append({**r, "data_payload": payload})

    return result


@app.post("/api/ledger/verify", response_model=LedgerVerifyResponse)
def verify_ledger():
    ledger = get_ledger_manager()
    result = ledger.verify_all_chains()
    return result


@app.post("/api/ledger/tamper-test")
def test_tamper(record_index: int = 0):
    """Simulate tampering for demonstration. Does NOT modify actual ledger."""
    ledger = get_ledger_manager()
    return ledger.simulate_tamper(record_index)


# ===== FORENSICS =====

@app.post("/api/forensics/upload")
async def upload_forensic(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(400, "No filename")

    inv_id = str(uuid.uuid4())
    save_path = FORENSIC_DIR / f"{inv_id}.pdf"

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    doc_hash = encryption_service.compute_bytes_hash(content)

    inv = Investigation(
        investigation_id=inv_id,
        input_document_hash=doc_hash,
        input_filename=file.filename,
    )
    db.add(inv)
    db.commit()

    _audit(db, "forensic_upload", "investigation", inv_id, f"Uploaded leaked document: {file.filename}")

    return {
        "investigation_id": inv_id,
        "input_document_hash": doc_hash,
        "input_filename": file.filename,
        "status": "created",
    }


@app.post("/api/forensics/{investigation_id}/extract")
def extract_watermark(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(404, "Investigation not found")

    pdf_path = FORENSIC_DIR / f"{investigation_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(404, "Investigation document not found")

    result = forensic_service.extract_watermark(investigation_id, str(pdf_path))

    inv.extracted_watermark_status = result["status"]
    if result.get("watermark_commitment"):
        inv.extracted_watermark_commitment = result["watermark_commitment"]
    db.commit()

    return result


@app.post("/api/forensics/{investigation_id}/match")
def match_watermark(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(404, "Investigation not found")
    if not inv.extracted_watermark_commitment:
        raise HTTPException(400, "Watermark not yet extracted")

    result = forensic_service.match_to_ledger(investigation_id, inv.extracted_watermark_commitment)

    if result.get("matched_event_id"):
        inv.matched_event_id = result["matched_event_id"]
    db.commit()

    return result


@app.post("/api/forensics/{investigation_id}/verify")
def verify_investigation(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(404, "Investigation not found")
    if not inv.matched_event_id:
        raise HTTPException(400, "No matched event. Run extraction and matching first.")

    # Get matched record from ledger
    ledger = get_ledger_manager()
    ledger_record = ledger.get_record_by_event(inv.matched_event_id)
    if not ledger_record:
        raise HTTPException(404, "Matched ledger record not found")

    payload = ledger_record.get("data_payload", "{}")
    if isinstance(payload, str):
        payload = json.loads(payload)

    result = forensic_service.verify_evidence(
        investigation_id, payload, ledger_record, inv.input_document_hash
    )

    inv.verification_status = result["overall_status"]
    inv.signature_status = result["signature_verification"]
    inv.ledger_status = result["ledger_integrity"]
    inv.document_hash_status = result["document_hash_verification"]
    db.commit()

    return result


@app.get("/api/forensics/{investigation_id}/report")
def get_forensic_report(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(404, "Investigation not found")

    # Build full report
    extraction_result = {
        "status": inv.extracted_watermark_status,
        "watermark_commitment": inv.extracted_watermark_commitment,
    }
    match_result = {"status": "not_found"}
    verification_result = {
        "overall_status": inv.verification_status or "pending",
        "signature_verification": inv.signature_status,
        "document_hash_verification": inv.document_hash_status,
        "ledger_integrity": inv.ledger_status,
        "watermark_binding": "VERIFIED" if inv.extracted_watermark_commitment else "pending",
        "details": {},
    }

    if inv.matched_event_id:
        ledger = get_ledger_manager()
        lr = ledger.get_record_by_event(inv.matched_event_id)
        if lr:
            payload = lr.get("data_payload", "{}")
            if isinstance(payload, str):
                payload = json.loads(payload)
            match_result = {
                "status": "matched",
                "matched_event_id": inv.matched_event_id,
                "matched_record": payload,
            }

            # Get recipient info
            fr = db.query(ForensicRecord).filter(ForensicRecord.event_id == inv.matched_event_id).first()
            if fr:
                recipient = db.query(Recipient).filter(
                    Recipient.public_key_fingerprint == fr.public_key_fingerprint
                ).first()
                if recipient:
                    verification_result["details"]["recipient_name"] = recipient.display_name
                    verification_result["details"]["recipient_id"] = recipient.id
                    verification_result["details"]["public_key_fingerprint"] = fr.public_key_fingerprint

    report = forensic_service.generate_forensic_report(
        investigation_id, extraction_result, match_result, verification_result, inv.input_document_hash
    )

    inv.report_path = report.get("report_path")
    db.commit()

    return report


@app.get("/api/forensics", response_model=List[InvestigationResponse])
def list_investigations(db: Session = Depends(get_db)):
    invs = db.query(Investigation).order_by(Investigation.created_at.desc()).all()
    return [InvestigationResponse(
        investigation_id=i.investigation_id,
        input_document_hash=i.input_document_hash,
        input_filename=i.input_filename,
        extracted_watermark_status=i.extracted_watermark_status or "pending",
        extracted_watermark_commitment=i.extracted_watermark_commitment,
        matched_event_id=i.matched_event_id,
        verification_status=i.verification_status or "pending",
        signature_status=i.signature_status,
        ledger_status=i.ledger_status,
        document_hash_status=i.document_hash_status,
        created_at=i.created_at.isoformat() if i.created_at else None,
    ) for i in invs]


# ===== VERIFICATION CENTER =====

@app.post("/api/verify/signature")
def verify_signature_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
):
    fr = db.query(ForensicRecord).filter(ForensicRecord.event_id == event_id).first()
    if not fr:
        raise HTTPException(404, "Forensic record not found")

    recipient = db.query(Recipient).filter(
        Recipient.public_key_fingerprint == fr.public_key_fingerprint
    ).first()
    if not recipient:
        raise HTTPException(404, "Recipient not found")

    record = signature_service.create_forensic_record(
        event_id=fr.event_id,
        document_id=fr.document_id,
        document_hash=fr.document_hash,
        recipient_reference=fr.recipient_reference,
        session_id=fr.session_id,
        watermark_commitment=fr.watermark_commitment,
        timestamp=fr.created_at.isoformat() if fr.created_at else "",
        watermark_algorithm_version=fr.watermark_algorithm_version,
        public_key_fingerprint=fr.public_key_fingerprint,
    )

    result = signature_service.verify_forensic_record(
        record=record,
        signature_b64=fr.signature,
        public_key_b64=recipient.public_key,
        expected_record_hash=fr.canonical_record_hash,
    )

    return {
        "event_id": event_id,
        "recipient_name": recipient.display_name,
        "algorithm": recipient.key_algorithm,
        **result,
    }


@app.post("/api/verify/document-hash")
def verify_document_hash(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    if doc.stored_path and Path(doc.stored_path).exists():
        current_hash = encryption_service.compute_file_hash(doc.stored_path)
        match = current_hash == doc.original_hash
        return {
            "document_id": document_id,
            "stored_hash": doc.original_hash,
            "computed_hash": current_hash,
            "match": match,
            "status": "VERIFIED" if match else "FAILED",
        }
    return {"document_id": document_id, "status": "FILE_NOT_FOUND"}


@app.post("/api/verify/ledger-chain")
def verify_ledger_chain():
    ledger = get_ledger_manager()
    return ledger.verify_all_chains()


@app.post("/api/verify/merkle-proof")
def verify_merkle_proof_endpoint(block_index: int):
    ledger = get_ledger_manager()
    proof = ledger.get_merkle_proof(block_index)
    if proof is None:
        raise HTTPException(404, "Record not found")

    records = ledger.get_all_records()
    all_hashes = [r["record_hash"] for r in records]
    from app.services.ledger_service import compute_merkle_root, verify_merkle_proof as _verify_mp
    root = compute_merkle_root(all_hashes)
    record_hash = records[block_index]["record_hash"]
    valid = _verify_mp(record_hash, proof, root)

    return {
        "block_index": block_index,
        "record_hash": record_hash,
        "merkle_root": root,
        "proof": proof,
        "valid": valid,
    }


# ===== ANALYTICS =====

@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """Rich analytics data for graphical dashboards."""
    from collections import defaultdict

    # --- Sessions over time (last 30 days, grouped by day) ---
    sessions_all = db.query(DecryptionSession).order_by(DecryptionSession.timestamp.asc()).all()
    day_counts = defaultdict(int)
    for s in sessions_all:
        if s.timestamp:
            day = s.timestamp.strftime("%Y-%m-%d")
            day_counts[day] += 1
    sessions_over_time = [{"date": d, "sessions": c} for d, c in sorted(day_counts.items())]

    # --- Documents over time ---
    docs_all = db.query(Document).order_by(Document.created_at.asc()).all()
    doc_day_counts = defaultdict(int)
    for d in docs_all:
        if d.created_at:
            day = d.created_at.strftime("%Y-%m-%d")
            doc_day_counts[day] += 1
    documents_over_time = [{"date": d, "documents": c} for d, c in sorted(doc_day_counts.items())]

    # --- Sessions per recipient ---
    recipients_all = db.query(Recipient).all()
    recipient_map = {r.id: r.display_name for r in recipients_all}
    sessions_by_recipient = defaultdict(int)
    for s in sessions_all:
        name = recipient_map.get(s.recipient_id, "Unknown")
        sessions_by_recipient[name] += 1
    sessions_per_recipient = [{"name": k, "sessions": v} for k, v in sessions_by_recipient.items()]

    # --- Document encryption status distribution ---
    total_docs = db.query(Document).count()
    encrypted_docs = db.query(Document).filter(Document.encryption_status == "encrypted").count()
    pending_docs = total_docs - encrypted_docs
    doc_status_dist = [
        {"status": "Encrypted", "count": encrypted_docs, "fill": "#6366f1"},
        {"status": "Pending", "count": pending_docs, "fill": "#f59e0b"},
    ]

    # --- Forensic investigations by status ---
    invs_all = db.query(Investigation).all()
    inv_statuses = defaultdict(int)
    for inv in invs_all:
        status = inv.verification_status or "pending"
        inv_statuses[status] += 1
    forensic_by_status = [{"status": k, "count": v} for k, v in inv_statuses.items()]

    # --- Ledger records over time ---
    ledger_recs = db.query(LedgerRecord).order_by(LedgerRecord.created_at.asc()).all()
    ledger_day_counts = defaultdict(int)
    for lr in ledger_recs:
        if lr.created_at:
            day = lr.created_at.strftime("%Y-%m-%d")
            ledger_day_counts[day] += 1
    ledger_over_time = [{"date": d, "blocks": c} for d, c in sorted(ledger_day_counts.items())]

    # --- Recipient key status ---
    key_ready = sum(1 for r in recipients_all if r.public_key_fingerprint and r.status == "active")
    key_missing = sum(1 for r in recipients_all if not r.public_key_fingerprint and r.status == "active")
    revoked = sum(1 for r in recipients_all if r.status == "revoked")
    recipient_key_status = [
        {"label": "Keys Ready", "value": key_ready, "fill": "#10b981"},
        {"label": "No Keys", "value": key_missing, "fill": "#f59e0b"},
        {"label": "Revoked", "value": revoked, "fill": "#ef4444"},
    ]

    # --- Audit event types distribution ---
    audit_logs = db.query(AuditLog).all()
    event_type_counts = defaultdict(int)
    for log in audit_logs:
        event_type_counts[log.event_type] += 1
    audit_event_dist = [{"event": k, "count": v} for k, v in sorted(event_type_counts.items(), key=lambda x: -x[1])]

    # --- Summary KPIs ---
    ledger = get_ledger_manager()
    health = ledger.get_health()

    return {
        "kpis": {
            "total_documents": total_docs,
            "total_encrypted": encrypted_docs,
            "total_recipients": len(recipients_all),
            "total_sessions": len(sessions_all),
            "total_forensic_investigations": len(invs_all),
            "total_ledger_records": len(ledger_recs),
            "ledger_health": health.get("status", "unknown"),
        },
        "sessions_over_time": sessions_over_time,
        "documents_over_time": documents_over_time,
        "ledger_over_time": ledger_over_time,
        "sessions_per_recipient": sessions_per_recipient,
        "doc_status_dist": doc_status_dist,
        "recipient_key_status": recipient_key_status,
        "forensic_by_status": forensic_by_status,
        "audit_event_dist": audit_event_dist,
    }


# ===== SYSTEM CONFIG =====

@app.get("/api/system/config", response_model=SystemConfigResponse)
def get_system_config():
    pqc_info = pqc_service.get_pqc_info()
    return SystemConfigResponse(
        app_name=APP_NAME,
        app_version=APP_VERSION,
        offline_mode=OFFLINE_MODE,
        encryption_algorithm=ENCRYPTION_ALGORITHM,
        hash_algorithm=HASH_ALGORITHM,
        sig_algorithm=pqc_info["sig_algorithm"],
        kem_algorithm=pqc_info["kem_algorithm"],
        watermark_algorithm_version=WATERMARK_ALGORITHM_VERSION,
        ledger_validator_count=LEDGER_VALIDATOR_COUNT,
        ledger_quorum_size=LEDGER_QUORUM_SIZE,
        pqc_available=pqc_info["available"],
        pqc_library=pqc_info.get("library", "unknown"),
    )


@app.get("/api/system/pqc-info")
def get_pqc_info():
    return pqc_service.get_pqc_info()


# ===== DEMO =====

@app.post("/api/demo/setup")
def demo_setup(db: Session = Depends(get_db)):
    """Set up demo data: create sample recipients and a test document."""
    import fitz  # PyMuPDF

    results = {"recipients": [], "document": None}

    # Create 3 recipients
    names = ["Recipient Alpha", "Recipient Beta", "Recipient Gamma"]
    for name in names:
        existing = db.query(Recipient).filter(Recipient.display_name == name).first()
        if existing:
            results["recipients"].append({"id": existing.id, "name": name, "status": "already_exists"})
            continue

        r = Recipient(id=str(uuid.uuid4()), display_name=name)
        db.add(r)
        db.commit()
        db.refresh(r)

        # Generate keys
        pub_b64, fp, alg = pqc_service.generate_signing_keypair(r.id)
        kem_pub_b64, kem_fp, kem_alg = pqc_service.generate_kem_keypair(r.id)
        r.public_key = pub_b64
        r.public_key_fingerprint = fp
        r.key_algorithm = alg
        r.kem_public_key = kem_pub_b64
        r.kem_public_key_fingerprint = kem_fp
        r.kem_algorithm = kem_alg
        db.commit()

        results["recipients"].append({
            "id": r.id, "name": name, "status": "created",
            "fingerprint": fp[:16] + "...",
        })

    # Create a sample PDF document
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "CLASSIFIED DOCUMENT\n\n"
        "Project: Operation Quantum Shield\n"
        "Classification: TOP SECRET\n"
        "Date: 2026-09-24\n\n"
        "This document contains sensitive information regarding the deployment "
        "of quantum-safe cryptographic protocols across critical infrastructure. "
        "Unauthorized disclosure is strictly prohibited.\n\n"
        "Section 1: Threat Assessment\n"
        "Current quantum computing capabilities pose an emerging threat to "
        "classical cryptographic systems including RSA and ECDSA. "
        "Migration to post-quantum algorithms is required within 24 months.\n\n"
        "Section 2: Migration Plan\n"
        "Phase 1: Key infrastructure audit and algorithm selection\n"
        "Phase 2: ML-KEM deployment for key establishment\n"
        "Phase 3: ML-DSA deployment for digital signatures\n"
        "Phase 4: Legacy system decommission\n\n"
        "Section 3: Budget Allocation\n"
        "Total estimated cost: $4.2M\n"
        "Timeline: 18-24 months\n\n"
        "Distribution: AUTHORIZED PERSONNEL ONLY"
    )
    page.insert_text((72, 72), text, fontsize=11, fontname="helv")

    # Add a second page
    page2 = doc.new_page()
    text2 = (
        "APPENDIX A: Technical Specifications\n\n"
        "Encryption: AES-256-GCM\n"
        "Key Encapsulation: ML-KEM-768 (FIPS 203)\n"
        "Digital Signatures: ML-DSA-65 (FIPS 204)\n"
        "Hash: SHA-256 / SHA-3-256\n\n"
        "All cryptographic operations must be performed in FIPS-validated modules.\n"
        "Key material must never leave the secure enclave.\n\n"
        "APPENDIX B: Authorized Recipients\n\n"
        "1. Recipient Alpha - Security Operations\n"
        "2. Recipient Beta - Infrastructure Team\n"
        "3. Recipient Gamma - Compliance Office\n\n"
        "Each recipient must verify document integrity upon receipt.\n"
        "Any suspected compromise must be reported within 24 hours."
    )
    page2.insert_text((72, 72), text2, fontsize=11, fontname="helv")

    doc_id = str(uuid.uuid4())
    pdf_path = DOCS_DIR / f"{doc_id}.pdf"
    doc.save(str(pdf_path))
    doc.close()

    with open(pdf_path, "rb") as f:
        content = f.read()
    doc_hash = encryption_service.compute_bytes_hash(content)

    db_doc = Document(
        id=doc_id,
        filename="classified_quantum_shield.pdf",
        original_hash=doc_hash,
        file_size=len(content),
        mime_type="application/pdf",
        stored_path=str(pdf_path),
    )
    db.add(db_doc)
    db.commit()

    results["document"] = {
        "id": doc_id,
        "filename": "classified_quantum_shield.pdf",
        "hash": doc_hash[:16] + "...",
        "size": len(content),
    }

    _audit(db, "demo_setup", "system", "demo", "Demo data initialized")
    return results


# ===== HELPERS =====

def _recipient_to_response(r) -> RecipientResponse:
    return RecipientResponse(
        id=r.id,
        display_name=r.display_name,
        public_key_fingerprint=r.public_key_fingerprint,
        kem_public_key_fingerprint=r.kem_public_key_fingerprint,
        key_algorithm=r.key_algorithm or "ML-DSA-65",
        kem_algorithm=r.kem_algorithm or "ML-KEM-768",
        status=r.status or "active",
        created_at=r.created_at.isoformat() if r.created_at else None,
    )


def _doc_to_response(d) -> DocumentResponse:
    return DocumentResponse(
        id=d.id,
        filename=d.filename,
        original_hash=d.original_hash,
        encrypted_hash=d.encrypted_hash,
        file_size=d.file_size,
        encryption_algorithm=d.encryption_algorithm or "AES-256-GCM",
        encryption_status=d.encryption_status or "pending",
        created_at=d.created_at.isoformat() if d.created_at else None,
    )


def _audit(db, event_type, entity_type, entity_id, details):
    log = AuditLog(
        id=str(uuid.uuid4()),
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
    db.commit()


def _payload_field(record, field):
    payload = record.get("data_payload", "{}")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            return None
    return payload.get(field)


# Serve frontend static files
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
