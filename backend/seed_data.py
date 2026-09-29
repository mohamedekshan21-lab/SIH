import requests, json, os
from pathlib import Path

BASE = 'http://127.0.0.1:8000'

def log(msg):
    print(f'[+] {msg}')

# Minimal but valid PDF
PDF_BYTES = (
    b'%PDF-1.4\n'
    b'1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj\n'
    b'2 0 obj<</Type /Pages /Kids [3 0 R] /Count 1>>endobj\n'
    b'3 0 obj<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]'
    b' /Contents 4 0 R /Resources<</Font<</F1<</Type /Font /Subtype /Type1'
    b' /BaseFont /Helvetica>>>>>>>>endobj\n'
    b'4 0 obj<</Length 44>>stream\n'
    b'BT /F1 12 Tf 100 700 Td (Classified Document) Tj ET\n'
    b'endstream\nendobj\n'
    b'xref\n0 5\n'
    b'0000000000 65535 f \n'
    b'0000000009 00000 n \n'
    b'0000000062 00000 n \n'
    b'0000000115 00000 n \n'
    b'0000000284 00000 n \n'
    b'trailer<</Size 5 /Root 1 0 R>>\nstartxref\n380\n%%EOF'
)

RECIPIENT_NAMES = ['Alice Chen', 'Bob Sharma', 'Carol Martinez', 'David Kim']
DOC_NAMES = [
    'classified_intel_brief.pdf',
    'operation_nightfall.pdf',
    'strategic_report_q4.pdf',
]

recipient_ids = []
doc_ids = []

log('=== Creating Recipients ===')
for name in RECIPIENT_NAMES:
    r = requests.post(f'{BASE}/api/recipients', json={'display_name': name})
    r.raise_for_status()
    rid = r.json()['id']
    recipient_ids.append(rid)
    log(f'  Created: {name} -> {rid[:8]}')
    r2 = requests.post(f'{BASE}/api/recipients/{rid}/keys')
    r2.raise_for_status()
    keys = r2.json()
    alg = keys.get('sig_algorithm', '?')
    kem = keys.get('kem_algorithm', '?')
    log(f'  Keys: {alg}, {kem}')

log('')
log('=== Uploading Documents ===')
for doc_name in DOC_NAMES:
    tmp = Path(doc_name)
    tmp.write_bytes(PDF_BYTES)
    with open(tmp, 'rb') as f:
        r = requests.post(
            f'{BASE}/api/documents/upload',
            files={'file': (doc_name, f, 'application/pdf')}
        )
    r.raise_for_status()
    doc_id = r.json()['id']
    doc_ids.append(doc_id)
    log(f'  Uploaded: {doc_name} -> {doc_id[:8]}')
    tmp.unlink()

log('')
log('=== Encrypting + Distributing ===')
# Doc0 -> Alice, Bob
r = requests.post(
    f'{BASE}/api/documents/{doc_ids[0]}/encrypt',
    json={'recipient_ids': [recipient_ids[0], recipient_ids[1]]}
)
r.raise_for_status()
log('  Doc0 (intel_brief) -> Alice, Bob')

# Doc1 -> Carol, David
r = requests.post(
    f'{BASE}/api/documents/{doc_ids[1]}/encrypt',
    json={'recipient_ids': [recipient_ids[2], recipient_ids[3]]}
)
r.raise_for_status()
log('  Doc1 (operation_nightfall) -> Carol, David')

# Doc2 -> all 4
r = requests.post(
    f'{BASE}/api/documents/{doc_ids[2]}/encrypt',
    json={'recipient_ids': recipient_ids}
)
r.raise_for_status()
log('  Doc2 (strategic_report_q4) -> all 4 recipients')

log('')
log('=== Creating Decryption Sessions ===')
pairs = [
    (doc_ids[0], recipient_ids[0], 'Alice', 'intel_brief'),
    (doc_ids[0], recipient_ids[1], 'Bob', 'intel_brief'),
    (doc_ids[1], recipient_ids[2], 'Carol', 'operation_nightfall'),
    (doc_ids[1], recipient_ids[3], 'David', 'operation_nightfall'),
    (doc_ids[2], recipient_ids[0], 'Alice', 'strategic_report'),
    (doc_ids[2], recipient_ids[2], 'Carol', 'strategic_report'),
    (doc_ids[2], recipient_ids[3], 'David', 'strategic_report'),
]

sessions = []
for doc_id, rec_id, rec_name, doc_label in pairs:
    r = requests.post(
        f'{BASE}/api/decryption/sessions',
        json={'document_id': doc_id, 'recipient_id': rec_id}
    )
    if r.status_code == 200:
        data = r.json()
        sid = data['session_id']
        wm = data.get('watermark_commitment', '')
        sessions.append({
            'session_id': sid,
            'watermark_commitment': wm,
            'recipient': rec_name,
            'doc': doc_label,
        })
        log(f'  OK: {rec_name} decrypted {doc_label} -> session {sid[:8]}')
    else:
        log(f'  FAIL: {rec_name} {doc_label}: {r.status_code} {r.text[:120]}')

log('')
log(f'=== Done: {len(sessions)}/{len(pairs)} sessions created ===')

# Print the watermark commitments for forensic testing
log('')
log('=== Watermark Commitments (for forensic testing) ===')
for s in sessions:
    log(f'  {s["recipient"]} / {s["doc"]}: commitment={s["watermark_commitment"][:24]}...')

# Save session info to a file for forensic test
with open('seed_sessions.json', 'w') as f:
    json.dump({
        'recipients': dict(zip(RECIPIENT_NAMES, recipient_ids)),
        'documents': dict(zip(DOC_NAMES, doc_ids)),
        'sessions': sessions,
    }, f, indent=2)
log('  Saved to seed_sessions.json')
