import os
import sys
import json
import requests
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

BASE_URL = "http://127.0.0.1:8000/api"

# Directory for test documents
OUT_DIR = Path("d:/SIH/test_documents")
OUT_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = OUT_DIR / "CONFIDENTIAL_PROJECT_CYGNUS.pdf"
WATERMARKED_PATH = OUT_DIR / "LEAKED_CYGNUS_WATERMARKED.pdf"
TEXT_PATH = OUT_DIR / "CONFIDENTIAL_PROJECT_CYGNUS.txt"

def generate_pdf(file_path: Path):
    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=letter,
        rightMargin=45, leftMargin=45,
        topMargin=45, bottomMargin=45
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
        spaceAfter=15
    )

    banner_style = ParagraphStyle(
        'ClassBanner',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#dc2626'),
        alignment=1,
        spaceAfter=12
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        textColor=colors.HexColor('#334155'),
        spaceAfter=10
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569')
    )

    story = []

    # Classification Banner
    story.append(Paragraph("&#9632; TOP SECRET // CONTROLLED FORENSIC SPECIFICATION // NOFORN &#9632;", banner_style))
    story.append(Spacer(1, 10))

    # Title
    story.append(Paragraph("PROJECT CYGNUS: QUANTUM-SAFE FORENSIC WATERMARKING SPECIFICATION", title_style))
    story.append(Spacer(1, 10))

    # Metadata Table
    table_data = [
        [Paragraph("DOCUMENT ID:", meta_style), Paragraph("CYGNUS-2026-ALPHA-09", body_style)],
        [Paragraph("SECURITY CLEARANCE:", meta_style), Paragraph("LEVEL 5 (POST-QUANTUM CELL)", body_style)],
        [Paragraph("CRYPTOGRAPHIC SUITE:", meta_style), Paragraph("ML-KEM-768 &amp; ML-DSA-65 (NIST FIPS 203/204)", body_style)],
        [Paragraph("DISPOSITION:", meta_style), Paragraph("FORENSIC VERIFICATION REFERENCE DATASET", body_style)],
    ]
    t = Table(table_data, colWidths=[160, 360])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 18))

    # Document Body
    story.append(Paragraph("<b>1. OPERATIONAL OBJECTIVE</b>", ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#0f172a'))))
    story.append(Paragraph(
        "This controlled document serves as the benchmark forensic test payload for the Quantum-Safe Forensic "
        "Watermarking System (QSFW). It is distributed under an air-gapped broadcast model where recipient "
        "decryption dynamically embeds a session-unique, imperceptible forensic watermark bound to post-quantum "
        "digital signatures.",
        body_style
    ))

    story.append(Paragraph("<b>2. FORENSIC ATTRIBUTION GUARANTEE</b>", ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#0f172a'))))
    story.append(Paragraph(
        "Each authorized recipient decrypting this document produces an independent tamper-evident block "
        "committed to the distributed offline ledger. If this document is exfiltrated, photographed, or copied, "
        "the extraction pipeline will isolate the watermark pattern and cross-reference the canonical ledger "
        "records to establish non-repudiable legal attribution.",
        body_style
    ))

    story.append(Paragraph("<b>3. CRYPTOGRAPHIC VERIFICATION PROOFS</b>", ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#0f172a'))))
    story.append(Paragraph(
        "Integrity can be independently verified via the Cryptographic Verification Center using Document Hash "
        "validation, ML-DSA post-quantum signature verification, Merkle tree inclusion proofs, and ledger chain "
        "cross-validation.",
        body_style
    ))

    story.append(Spacer(1, 20))
    story.append(Paragraph("&#9632; END OF CLASSIFIED CYGNUS SPECIFICATION &#9632;", banner_style))

    doc.build(story)
    print(f"[+] Generated PDF: {file_path}")

def generate_txt(file_path: Path):
    text_content = """TOP SECRET // CONTROLLED FORENSIC SPECIFICATION // NOFORN

PROJECT CYGNUS: QUANTUM-SAFE FORENSIC WATERMARKING SPECIFICATION
================================================================
Document Reference: CYGNUS-2026-ALPHA-09
Security Classification: LEVEL 5 (POST-QUANTUM CELL)
Cryptographic Suite: ML-KEM-768 / ML-DSA-65 (NIST FIPS 203/204)
Disposition: FORENSIC VERIFICATION REFERENCE DATASET

1. OPERATIONAL OBJECTIVE
This controlled document serves as the benchmark forensic test payload for the
Quantum-Safe Forensic Watermarking System (QSFW). Recipient decryption dynamically
embeds a session-unique, imperceptible forensic watermark bound to post-quantum signatures.

2. FORENSIC ATTRIBUTION GUARANTEE
Each authorized recipient decrypting this document produces an independent tamper-evident block
committed to the distributed offline ledger. In the event of unauthorized leak or exfiltration,
the extraction pipeline isolates the watermark pattern and establishes cryptographic attribution.

3. CRYPTOGRAPHIC VERIFICATION PROOFS
Integrity can be verified via:
- Document SHA-256 Hash Binding
- ML-DSA Post-Quantum Digital Signature Verification
- Merkle Path Inclusion Proof
- Multi-node Distributed Ledger Consistency

[END OF CLASSIFIED CYGNUS TEST DOCUMENT]
"""
    file_path.write_text(text_content, encoding='utf-8')
    print(f"[+] Generated Plaintext: {file_path}")

def main():
    print("=" * 60)
    print("CREATING DUMMY TEST DOCUMENT & RUNNING FULL VERIFICATION FLOW")
    print("=" * 60)

    # 1. Generate files
    generate_pdf(PDF_PATH)
    generate_txt(TEXT_PATH)

    # 2. Check if backend is alive
    try:
        r = requests.get(f"{BASE_URL}/dashboard")
        r.raise_for_status()
        print("[+] Backend is online and healthy.")
    except Exception as e:
        print(f"[-] Backend connection error: {e}")
        sys.exit(1)

    # 3. Create or find recipient
    rec_name = "Agent Evelyn Reed (Special Inspector)"
    rec_id = None
    all_recs = requests.get(f"{BASE_URL}/recipients").json()
    for rec in all_recs:
        if rec.get("display_name") == rec_name:
            rec_id = rec["id"]
            print(f"[+] Found existing recipient: {rec_name} ({rec_id})")
            break

    if not rec_id:
        r = requests.post(f"{BASE_URL}/recipients", json={"display_name": rec_name})
        r.raise_for_status()
        rec_id = r.json()["id"]
        print(f"[+] Created recipient: {rec_name} ({rec_id})")
        r_keys = requests.post(f"{BASE_URL}/recipients/{rec_id}/keys")
        r_keys.raise_for_status()
        print(f"[+] Generated PQC keys (ML-KEM / ML-DSA)")

    # 4. Upload document
    with open(PDF_PATH, "rb") as f:
        r = requests.post(f"{BASE_URL}/documents/upload", files={"file": (PDF_PATH.name, f, "application/pdf")})
        r.raise_for_status()
        doc_data = r.json()
        doc_id = doc_data["id"]
        original_hash = doc_data["original_hash"]
        print(f"[+] Uploaded document: {PDF_PATH.name}")
        print(f"    Document ID   : {doc_id}")
        print(f"    Original Hash : {original_hash}")

    # 5. Encrypt document for recipient
    r = requests.post(f"{BASE_URL}/documents/{doc_id}/encrypt", json={"recipient_ids": [rec_id]})
    r.raise_for_status()
    print(f"[+] Document encrypted and distributed with ML-KEM-768 ciphertext")

    # 6. Execute Decryption Session (Generates Watermark, ML-DSA Signature, and Ledger Block)
    r = requests.post(f"{BASE_URL}/decryption/sessions", json={"document_id": doc_id, "recipient_id": rec_id})
    r.raise_for_status()
    session_data = r.json()
    session_id = session_data["session_id"]
    event_id = session_data.get("event_id", "")
    wm_commitment = session_data.get("watermark_commitment", "")
    print(f"[+] Decryption session executed successfully:")
    print(f"    Session ID    : {session_id}")
    print(f"    Event ID      : {event_id}")
    print(f"    WM Commitment : {wm_commitment}")

    # 7. Download Watermarked Decrypted Document (for forensic test)
    r = requests.get(f"{BASE_URL}/decryption/sessions/{session_id}/download")
    r.raise_for_status()
    WATERMARKED_PATH.write_bytes(r.content)
    print(f"[+] Saved forensically watermarked document to:")
    print(f"    {WATERMARKED_PATH} ({len(r.content)} bytes)")

    # 8. Find block index in ledger records
    r_ledger = requests.get(f"{BASE_URL}/ledger/records").json()
    block_index = 0
    for idx, blk in enumerate(r_ledger):
        payload = blk.get("data_payload", {})
        if isinstance(payload, str):
            try: payload = json.loads(payload)
            except: payload = {}
        if payload.get("session_id") == session_id or (event_id and blk.get("event_id") == event_id):
            block_index = blk.get("block_index", idx)
            if not event_id:
                event_id = blk.get("event_id", "")
            print(f"[+] Committed Ledger Block #{block_index} (Record Hash: {blk.get('record_hash')}, Event ID: {event_id})")
            break

    # 9. Test Verification Center Endpoints directly
    print("\n" + "=" * 60)
    print("VERIFYING TEST DATA VIA VERIFICATION CENTER ENDPOINTS")
    print("=" * 60)

    # 9a. Document Hash
    v_doc = requests.post(f"{BASE_URL}/verify/document-hash?document_id={doc_id}").json()
    print(f"[OK] Document Hash Verification : {v_doc.get('status')} (match={v_doc.get('match')})")

    # 9b. Signature Verification
    if event_id:
        v_sig = requests.post(f"{BASE_URL}/verify/signature?event_id={event_id}").json()
        print(f"[OK] ML-DSA Signature Verification: signature_valid={v_sig.get('signature_valid')}, hash_valid={v_sig.get('hash_valid')}")
    else:
        print("[!] No event_id returned, skipping direct signature check.")

    # 9c. Ledger Chain
    v_chain = requests.post(f"{BASE_URL}/verify/ledger-chain").json()
    print(f"[OK] Ledger Chain Verification  : valid={v_chain.get('valid')}, consistent={v_chain.get('consistent')}")

    # 9d. Merkle Proof
    v_merkle = requests.post(f"{BASE_URL}/verify/merkle-proof?block_index={block_index}").json()
    print(f"[OK] Merkle Proof Verification  : valid={v_merkle.get('valid')}")

    # 10. Save verification bundle file for user reference
    info_bundle = {
        "document_name": PDF_PATH.name,
        "pdf_path": str(PDF_PATH),
        "text_path": str(TEXT_PATH),
        "watermarked_leaked_path": str(WATERMARKED_PATH),
        "document_id": doc_id,
        "event_id": event_id,
        "block_index": block_index,
        "session_id": session_id,
        "watermark_commitment": wm_commitment,
        "recipient_name": rec_name,
        "recipient_id": rec_id,
    }
    info_json_path = OUT_DIR / "verification_test_bundle.json"
    info_json_path.write_text(json.dumps(info_bundle, indent=2), encoding='utf-8')
    print(f"\n[+] Saved test bundle info to: {info_json_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
