import requests, json, os, sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def log(msg):
    print(f"[+] {msg}")

def create_recipient(name: str):
    resp = requests.post(f"{BASE_URL}/api/recipients", json={"display_name": name})
    resp.raise_for_status()
    data = resp.json()
    log(f"Created recipient: {data['id']}")
    return data['id']

def generate_keys(recipient_id: str):
    resp = requests.post(f"{BASE_URL}/api/recipients/{recipient_id}/keys")
    resp.raise_for_status()
    log("Generated PQC keys")

def upload_document(file_path: Path):
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/pdf")}
        resp = requests.post(f"{BASE_URL}/api/documents/upload", files=files)
    resp.raise_for_status()
    data = resp.json()
    log(f"Uploaded document: {data['id']}")
    return data['id']

def encrypt_document(document_id: str, recipient_id: str):
    payload = {"recipient_ids": [recipient_id]}
    resp = requests.post(f"{BASE_URL}/api/documents/{document_id}/encrypt", json=payload)
    resp.raise_for_status()
    log("Document encrypted and distributed")

def create_decryption_session(document_id: str, recipient_id: str):
    payload = {"document_id": document_id, "recipient_id": recipient_id}
    resp = requests.post(f"{BASE_URL}/api/decryption/sessions", json=payload)
    resp.raise_for_status()
    data = resp.json()
    log(f"Decryption session created: {data['session_id']}")
    return data['session_id']

def download_watermarked(session_id: str, out_path: Path):
    resp = requests.get(f"{BASE_URL}/api/decryption/sessions/{session_id}/download")
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    log(f"Watermarked PDF saved to {out_path}")

def main():
    # Create a tiny PDF file for testing
    test_pdf = Path("test_doc.pdf")
    if not test_pdf.exists():
        test_pdf.write_bytes(b"%PDF-1.4\n1 0 obj<<>>endobj\nxref\n0 2\n0000000000 65535 f \n0000000010 00000 n \ntrailer<< /Size 2 /Root 1 0 R >>\nstartxref\n20\n%%EOF")
        log("Created dummy PDF file")

    recipient_id = create_recipient("TestUser")
    generate_keys(recipient_id)
    document_id = upload_document(test_pdf)
    encrypt_document(document_id, recipient_id)
    session_id = create_decryption_session(document_id, recipient_id)
    download_watermarked(session_id, Path("watermarked_output.pdf"))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)
