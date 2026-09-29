# ROLE: SENIOR SECURITY ARCHITECT, POST-QUANTUM CRYPTOGRAPHY ENGINEER & FULL-STACK DEVELOPER

You are an expert software architect and implementation engineer. Your task is to design and BUILD a complete, working, research-oriented prototype for the following problem:

# PROJECT TITLE

**Quantum-Safe Session-Bound Forensic Watermarking with an Offline, Tamper-Evident Distributed Ledger**

## 1. PROJECT OBJECTIVE

Develop an end-to-end secure document distribution and forensic attribution system that solves the problem of identifying the specific recipient and decryption session responsible for a leaked document when the same encrypted document is distributed to multiple authorized recipients.

The system must implement a novel, research-oriented approach that combines:

1. Broadcast encryption with individual recipient decryption.
2. Session-specific invisible forensic watermarking.
3. Recipient-bound post-quantum digital signatures.
4. Offline and air-gapped identity and key management.
5. An offline tamper-evident distributed ledger.
6. Cryptographic forensic watermark extraction and verification.

The prototype must be FUNCTIONAL, DEMONSTRABLE, SECURITY-CONSCIOUS, and visually professional.

Do not build only a landing page or a static UI. Implement the actual end-to-end workflow using real cryptographic libraries, real document processing, real watermark embedding and extraction, and a local ledger.

If a production-grade security guarantee cannot be established, clearly identify the limitation and demonstrate the implemented mechanism honestly.

---

# 2. PROBLEM STATEMENT

Sensitive documents are distributed using a broadcast-encrypt, individually-decrypt model.

A sender encrypts a document once and distributes it to multiple authorized recipients. Each recipient decrypts the document independently using their credentials.

The decrypted documents are visually identical. If one copy leaks, every recipient who could decrypt it is an equally plausible suspect.

Traditional safeguards do not fully solve the attribution problem:

* Server-side access logs may be modified by privileged administrators.
* Static watermarks may be identical across recipients.
* A watermark generated before distribution cannot distinguish individual decryption sessions.
* Centralized audit storage introduces a single point of trust or compromise.

The system must generate a unique, invisible forensic watermark at the moment of decryption and cryptographically associate the decryption event with the recipient's identity and session.

A forensic investigator must be able to extract the watermark from a leaked document and verify the associated recipient, event record, signature, and ledger evidence.

---

# 3. CORE FUNCTIONAL REQUIREMENTS

Implement ALL of the following requirements.

## A. Document Encryption and Distribution

1. Sender uploads a supported document.
2. Generate a document identifier and cryptographic hash.
3. Encrypt the document using a modern authenticated encryption algorithm.
4. Create a document distribution record.
5. Register authorized recipients in the local identity system.
6. Distribute the encrypted document to the authorized recipients.
7. Ensure the encrypted document is shared without creating recipient-specific static plaintext copies.

Use an appropriate envelope encryption design:

* Random symmetric document encryption key.
* Authenticated encryption using AES-256-GCM or an approved alternative.
* Recipient-specific key wrapping or key encapsulation.
* Post-quantum key establishment using a NIST-standardized KEM where supported.

Important:
Do not claim that the implementation is a fully secure broadcast encryption scheme if it is only a prototype envelope-encryption distribution model. Clearly document the chosen construction and limitations.

## B. Recipient Identity and Key Management

Implement a local, offline identity system.

Each recipient must have:

* Unique recipient ID.
* Display name.
* Local identity metadata.
* Post-quantum key pair for digital signatures.
* Post-quantum key establishment credentials, where applicable.
* Public key fingerprint.
* Key creation timestamp.
* Key status and revocation state.

Use NIST-standardized post-quantum algorithms:

### Key establishment

* ML-KEM, standardized by NIST FIPS 203.

### Digital signatures

* ML-DSA, standardized by NIST FIPS 204.
* Optionally support SLH-DSA (FIPS 205) as a configurable alternative if library support is available.

Use a well-maintained cryptographic library with verified API support.

Do not invent cryptographic algorithms.
Do not implement cryptographic primitives manually.
Do not claim that a custom signature construction is post-quantum secure.

All private keys must remain within the local offline environment.

For the prototype:

* Store private keys in an encrypted local keystore.
* Require a local unlock mechanism.
* Use a clear demo-only key protection strategy.
* Do not store private keys in frontend source code, browser local storage, or plaintext database fields.
* Document that a production deployment requires hardware-backed or equivalent protected key storage.

## C. Unique Session-Bound Invisible Forensic Watermark

This is the CORE INNOVATION of the project.

At the moment an authorized recipient decrypts a document, generate a unique forensic watermark tied to the specific decryption event.

The watermark must include or be cryptographically derived from:

* Document ID.
* Recipient ID or a privacy-preserving recipient reference.
* Unique decryption session ID.
* Cryptographically secure random nonce.
* Decryption timestamp.
* Version of the watermark algorithm.
* Optional ledger record identifier.
* Integrity-protected binding data.

IMPORTANT PRIVACY AND SECURITY DESIGN:

Do not blindly embed plaintext recipient identity, private information, or secret cryptographic keys inside the watermark.

Use a cryptographically derived watermark payload, for example:

watermark_payload =
HMAC-SHA-256(
watermark_secret,
document_id || recipient_reference || session_id || nonce || algorithm_version
)

The exact design may be improved if justified.

The system must provide a way for the forensic verifier to resolve the watermark to a ledger record without exposing sensitive recipient information directly in the document.

### Watermark Requirements

* Invisible or visually imperceptible under normal viewing.
* Unique for every authorized decryption session.
* Resistant to ordinary document handling and supported transformations.
* Extractable using a documented extraction process.
* Bound to the intended document.
* Integrity-protected against unauthorized modification.
* Detectable with a confidence or integrity result.
* Designed to minimize false positives and false attribution.

Do not claim that any watermark is perfectly invisible or impossible to remove.
Do not claim robustness against every transformation.
Document supported file types, transformations, and limitations.

---

# 4. NOVELTY TO IMPLEMENT

Implement a meaningful system-level novelty rather than merely combining existing technologies.

## PROPOSED NOVELTY

### "Quantum-Safe Session-Bound Forensic Attribution with Cryptographically Linked Watermark and Offline DLT Evidence"

Design and implement the following integrated approach:

### Novelty 1: Session-Specific Watermark Derivation

Every decryption session creates a unique watermark using cryptographically secure random material and recipient/session binding.

The same source document can produce different forensic fingerprints for different recipients and different decryption sessions.

Two sessions involving the same recipient must not automatically produce the same watermark.

### Novelty 2: Recipient-Bound Post-Quantum Authorization Evidence

Each decryption event produces a structured forensic record.

The recipient signs the record using their own ML-DSA private key.

The signature must be verified using the registered public key.

IMPORTANT:
A digital signature provides cryptographic evidence that the holder of the signing key signed the record. It does not, by itself, prove that the person physically operated the device or that a recipient cannot deny all involvement. Explain this distinction in the documentation.

### Novelty 3: Cryptographic Binding Between Watermark and Ledger Record

The watermark and the signed decryption record must be cryptographically linked.

The ledger record should contain:

* Event ID.
* Document hash.
* Document ID.
* Recipient ID or protected recipient reference.
* Session ID or a privacy-preserving session reference.
* Watermark commitment/hash.
* Watermark algorithm version.
* Decryption timestamp.
* Public key fingerprint.
* Digital signature.
* Previous ledger state reference or transaction reference.
* Record hash.

Do not store a private key in the ledger.

Design the system so that the watermark can be matched to the ledger record using an authenticated or integrity-protected mechanism.

### Novelty 4: Offline, Tamper-Evident Multi-Node Ledger

Implement an offline ledger that provides tamper evidence and distributed record validation.

Use a local permissioned DLT design with multiple independent validator nodes or logically separated validator processes.

Potential prototype implementation:

* Python-based local ledger service.
* SQLite or an equivalent embedded database for persistence.
* Hash-linked ledger records.
* Merkle tree or Merkle accumulator for record integrity.
* Signed transactions.
* Validator quorum or configurable multi-node commit policy.
* Local node identities.
* Ledger snapshots.
* Verification of chain integrity.
* Detection of unauthorized record alteration or deletion.

For a stronger research prototype, implement a small permissioned ledger with multiple local nodes and a documented consensus mechanism, such as a quorum-based validation protocol.

Do not describe a simple hash chain as a complete blockchain consensus system.
Do not claim Byzantine fault tolerance unless an actual, tested BFT protocol is implemented.
Do not claim immutability in the absolute physical sense; demonstrate tamper evidence, append-only behavior, and recovery or detection controls.

### Novelty 5: Offline Forensic Verification

An investigator must be able to:

1. Import a leaked document.
2. Extract the embedded forensic watermark.
3. Validate extraction integrity and confidence.
4. Search the local ledger.
5. Locate the corresponding signed decryption record.
6. Verify the recipient's public key and ML-DSA signature.
7. Verify the document hash and event binding.
8. Verify the ledger's hash links and Merkle evidence.
9. Generate a forensic verification report.

The report must clearly separate:

* Successfully verified evidence.
* Unverified or missing evidence.
* Watermark extraction confidence.
* Cryptographic signature verification.
* Ledger integrity verification.
* Attribution limitations.

---

# 5. DOCUMENT FORMAT AND WATERMARK IMPLEMENTATION

Support a practical document format for the prototype.

Choose an initial format based on implementation reliability, such as PDF.

If PDF watermarking is selected:

* Implement invisible or visually imperceptible forensic embedding.
* Use a documented embedding method.
* Ensure extraction is performed by the corresponding algorithm.
* Preserve readability and normal viewing.
* Evaluate behavior under supported transformations.

Potential approaches to investigate:

1. Frequency-domain watermarking, such as DCT/DWT-based techniques for rasterized document pages.
2. Robust image watermarking for rendered page content.
3. A carefully documented PDF-compatible embedding strategy.
4. Error-correcting codes and redundancy for improved extraction reliability.

Choose a method that can be implemented and tested locally.

Do not simply add visible text, a QR code, or a normal PDF metadata field and call it an invisible forensic watermark.

If the selected method has robustness limitations, display them in the application and documentation.

### Document Handling

* Preserve the original document securely.
* Create a decrypted, watermarked output copy.
* Avoid exposing the watermark payload in the user interface.
* Store document hashes and version identifiers.
* Support test documents generated locally.
* Validate that the decrypted document remains usable.

If fully robust PDF watermarking is impractical within the development environment, implement the strongest reliable prototype supported by the available libraries and explicitly mark unsupported properties.

---

# 6. DIGITAL SIGNATURE AND FORENSIC RECORD DESIGN

Implement a signed decryption record using ML-DSA.

Example logical record:

{
"event_id": "...",
"document_id": "...",
"document_hash": "...",
"recipient_id": "...",
"session_id": "...",
"watermark_commitment": "...",
"timestamp": "...",
"watermark_algorithm_version": "...",
"public_key_fingerprint": "...",
"record_version": "1.0"
}

The canonical record must be serialized deterministically before signing.

Implement:

1. Canonical record serialization.
2. Record hash generation.
3. ML-DSA digital signature generation.
4. Signature verification.
5. Public key fingerprint verification.
6. Record-to-watermark cryptographic binding.
7. Record-to-document binding.

Use secure random generation for session nonces and event identifiers.

Avoid signing an ambiguous JSON representation. Define a canonical serialization method and test that the same record produces the same signing bytes.

The verifier must detect:

* Modified fields.
* Invalid signatures.
* Wrong public keys.
* Incorrect document hashes.
* Invalid watermark commitments.
* Missing ledger evidence.

---

# 7. OFFLINE LEDGER ARCHITECTURE

Build a fully local, offline ledger.

The application must not depend on:

* Public blockchain networks.
* Cloud KMS.
* Cloud storage.
* External authentication services.
* Internet-based APIs.
* External hosted databases.

### Suggested Local Architecture

Node A:

* Ledger validator.
* Local persistent storage.
* Transaction validation.

Node B:

* Independent validator.
* Local ledger replica.
* Signature and transaction checks.

Node C:

* Independent validator.
* Local ledger replica.
* Integrity and quorum checks.

The nodes may run as separate local processes or containers.

Implement a configurable ledger commit policy, such as:

* A defined number of validators must accept a transaction.
* Valid transactions are appended to the local ledger.
* Replicas maintain consistent ledger state.
* Invalid or conflicting transactions are rejected.
* A validator disagreement is displayed rather than silently ignored.

If a multi-node consensus protocol is too complex for the initial prototype, create a modular architecture with a clearly documented simplified quorum mechanism and identify the limitations.

### Ledger Features

* Append-only transaction processing.
* Hash-linked blocks or records.
* Merkle root generation.
* Local validator signatures.
* Ledger replication.
* Chain integrity validation.
* Tamper detection.
* Ledger export and import.
* Offline forensic lookup.
* Audit history.
* Recovery and integrity check tools.

The UI must clearly show whether the ledger is:

* Healthy.
* Tampered.
* Incomplete.
* Out of sync.
* Awaiting validator confirmation.

---

# 8. APPLICATION ARCHITECTURE

Use a modular architecture with clear separation of concerns.

## Recommended Technology Stack

### Frontend

Choose a modern, maintainable stack:

* React.
* TypeScript.
* Vite.
* Tailwind CSS.
* shadcn/ui or another polished local component system.
* Lucide icons.
* Recharts or a suitable charting library for local dashboard visualizations.

### Backend

Choose a robust local backend:

* Python.
* FastAPI.
* Pydantic.
* SQLAlchemy or an appropriate persistence layer.

### Cryptography

* Open Quantum Safe liboqs or another properly supported library for post-quantum cryptography.
* A maintained Python-compatible binding where available.
* ML-KEM.
* ML-DSA.
* AES-256-GCM or another appropriate authenticated encryption scheme.
* SHA-256/SHA-3 as appropriate.
* Secure random generation.

Before implementation, verify the installed library's supported algorithm names, APIs, and version. Do not assume that every Python package exposes the same cryptographic interface.

### Watermarking

* OpenCV.
* NumPy.
* Pillow.
* PyMuPDF or another appropriate PDF library.
* Additional signal-processing libraries if necessary.

### Local Storage

* SQLite.
* Encrypted local keystore.
* Local document storage.
* Ledger persistence.
* Audit event storage.

### Deployment

* Fully local execution.
* Docker Compose for local service isolation, if useful.
* No external cloud dependency.
* No public blockchain dependency.
* No external network requirement after installation and dependency preparation.

The system should be capable of running in an air-gapped environment after all required dependencies and models/packages have been provisioned locally.

---

# 9. USER INTERFACE — PREMIUM SECURITY OPERATIONS DASHBOARD

The user interface is a major requirement.

Create a visually polished, professional, research-grade cybersecurity application.

Do not create a generic admin dashboard with random cards.

The UI must look like a real secure document forensic platform suitable for:

* Research demonstrations.
* University project presentations.
* Security architecture reviews.
* Hackathon demonstrations.
* Technical evaluation by judges.

## Design Language

Theme:

* Modern cybersecurity operations center.
* Dark mode as the primary theme.
* Optional light mode.
* Professional typography.
* Subtle blue/cyan or neutral security-oriented accents.
* High contrast and accessible text.
* Minimal unnecessary decoration.
* Clear information hierarchy.

Do not overuse glowing effects, animated backgrounds, or excessive gradients.
Do not use stock images.
Do not use fake security metrics.
Do not use excessive text blocks.
Prioritize clarity, usability, and visual consistency.

## Main Navigation

Implement the following pages:

### 1. Overview Dashboard

Display:

* Total encrypted documents.
* Total authorized recipients.
* Total decryption sessions.
* Total signed records.
* Ledger health.
* Validator status.
* Pending ledger transactions.
* Tamper alerts.
* Recent decryption activity.

Include a simple architecture/status visualization showing:

Document → Decryption → Watermark → Signature → Ledger → Verification

All displayed statistics must come from actual local application data.

### 2. Secure Document Distribution

Features:

* Upload a document.
* Show document name and cryptographic hash.
* Encrypt the document.
* Select authorized recipients.
* Show distribution status.
* Display encryption details.
* Show the document's distribution history.

### 3. Recipient Management

Features:

* Create local recipients.
* Generate or import authorized public keys.
* Generate local post-quantum signing keys.
* Display public key fingerprints.
* Show key status.
* Display revocation status.
* Manage recipient access.
* Use a secure local key-management workflow.

Never display private keys by default.

### 4. Recipient Decryption Workspace

Features:

* Select an authorized encrypted document.
* Authenticate or unlock the recipient's local credentials.
* Start a decryption session.
* Generate the session-bound watermark.
* Create the signed decryption record.
* Commit the record to the offline ledger.
* Display successful completion status.
* Provide the watermarked decrypted document as a local output.

Display a clear event timeline:

1. Credential validation.
2. Document decryption.
3. Watermark generation.
4. Watermark embedding.
5. Record canonicalization.
6. ML-DSA signature generation.
7. Ledger submission.
8. Ledger commit confirmation.
9. Watermarked document ready.

Do not reveal secret watermark payloads or private keys in the normal UI.

### 5. Ledger Explorer

Features:

* View ledger blocks/records.
* Search by event ID.
* Search by document ID.
* Search by recipient reference.
* Search by watermark commitment.
* View transaction details.
* View Merkle roots.
* View validator confirmations.
* Verify chain integrity.
* Display tamper alerts.
* Export a local evidence package.

### 6. Forensic Investigation Workspace

This is the MOST IMPORTANT DEMONSTRATION PAGE.

The investigator should be able to:

1. Upload a leaked document.
2. Start watermark extraction.
3. Display extraction status.
4. Display watermark integrity and confidence.
5. Match the extracted watermark to the ledger.
6. Display the matching event.
7. Verify the digital signature.
8. Verify the document hash.
9. Verify ledger and Merkle evidence.
10. Generate a forensic report.

Use a professional investigation result layout:

* Investigation ID.
* Input document hash.
* Watermark extraction status.
* Matching record status.
* Recipient reference.
* Decryption event timestamp.
* Public key fingerprint.
* Signature verification result.
* Ledger integrity result.
* Evidence consistency result.
* Attribution conclusion with limitations.

Do not claim attribution when the evidence does not verify successfully.

Use distinct statuses:

* VERIFIED.
* FAILED.
* INCOMPLETE.
* NOT FOUND.
* REQUIRES REVIEW.

### 7. Cryptographic Verification Center

Implement a dedicated verification interface for:

* ML-DSA signatures.
* Document hashes.
* Watermark commitments.
* Merkle proofs.
* Ledger chain integrity.
* Validator signatures, where implemented.

Provide a detailed but readable verification report.

### 8. System Configuration

Show:

* Offline mode.
* Cryptographic algorithm configuration.
* Watermark algorithm version.
* Ledger configuration.
* Validator count.
* Local database status.
* Key storage status.
* Supported file formats.
* Application version.

Clearly display that the system is designed for offline operation.

---

# 10. END-TO-END DEMONSTRATION SCENARIO

Implement a built-in demo mode using locally generated test data.

The demo must show a realistic workflow:

### Step 1 — Register Recipients

Create at least three local recipients:

* Recipient Alpha.
* Recipient Beta.
* Recipient Gamma.

Generate independent post-quantum key pairs for each recipient.

### Step 2 — Upload and Encrypt Document

Create or upload a sample sensitive document.

Encrypt the document once.

Register the authorized recipients.

### Step 3 — Decryption by Multiple Recipients

Perform independent decryption sessions:

* Alpha decrypts the document.
* Beta decrypts the document.
* Gamma decrypts the document.

Each session must produce:

* A distinct session ID.
* A distinct watermark.
* A signed event record.
* A ledger transaction.

### Step 4 — Compare Output Documents

Demonstrate:

* All decrypted documents are visually identical or within the supported visual tolerance.
* Their cryptographic files or embedded forensic data differ.
* Watermark extraction distinguishes the session-specific outputs.

Do not state that documents are byte-identical if watermarking modifies their underlying binary representation.

### Step 5 — Simulate a Leak

Select one watermarked document and copy it to a separate local investigation input.

Do not assume the application can identify an arbitrary document unless a watermark is actually embedded and the extraction algorithm succeeds.

### Step 6 — Investigate the Leak

Upload the leaked document to the Forensic Investigation Workspace.

The system must:

* Extract the watermark.
* Match the watermark to the local ledger.
* Verify the signature.
* Verify the document hash.
* Verify the ledger evidence.
* Display the associated recipient reference and decryption event.

### Step 7 — Demonstrate Tamper Detection

Create a controlled test:

1. Modify a ledger record or a signed record in a test copy of the local ledger.
2. Run integrity verification.
3. Detect the alteration.
4. Display the failed verification result.
5. Explain why the original signed record cannot be accepted after modification.

Do not modify the production evidence store destructively.
Use a disposable test dataset or a dedicated tampering simulation.

### Step 8 — Demonstrate Invalid Signature Detection

Create a test with a modified record or incorrect public key.

Show:

* Signature verification failure.
* Evidence inconsistency.
* Appropriate UI status.

### Step 9 — Generate Forensic Report

Generate a professional local report containing:

* Case ID.
* Evidence file hash.
* Extracted watermark identifier or commitment.
* Matching ledger event.
* Signature verification.
* Ledger integrity checks.
* Verification timestamps.
* Limitations.
* System version.
* Evidence status.

---

# 11. SECURITY REQUIREMENTS

Implement security controls throughout the application.

### Cryptography

* Use standardized, supported algorithms.
* Use secure randomness.
* Use authenticated encryption.
* Verify digital signatures before accepting attribution evidence.
* Protect private keys.
* Avoid hardcoded production secrets.
* Avoid custom cryptographic primitives.
* Use domain separation or explicit record context where appropriate.
* Validate all cryptographic inputs.

### Authentication and Authorization

* Require local recipient authentication before decryption.
* Prevent unauthorized recipient access.
* Separate investigator permissions from recipient permissions.
* Require authorization for ledger administrative operations.
* Avoid relying only on frontend access control.
* Enforce permissions in backend endpoints.

### Offline Operation

The application must operate without network connectivity after dependencies are provisioned.

Implement:

* Local authentication.
* Local key management.
* Local document storage.
* Local cryptographic operations.
* Local ledger.
* Local forensic verification.
* Local report generation.

Include an offline mode indicator and ensure that external network calls are not necessary for the primary workflow.

### Evidence Integrity

* Hash input documents.
* Maintain canonical signed records.
* Validate ledger records.
* Verify signatures.
* Detect tampering.
* Record evidence version and algorithm version.
* Maintain clear provenance of forensic reports.

---

# 12. API AND BACKEND DESIGN

Create well-organized backend modules and API endpoints.

Suggested modules:

backend/
app/
main.py
config.py
api/
models/
schemas/
services/
crypto_service.py
pqc_service.py
encryption_service.py
watermark_service.py
signature_service.py
ledger_service.py
forensic_service.py
identity_service.py
report_service.py
storage/
security/
tests/

Suggested API categories:

### Identity

* POST /api/recipients
* GET /api/recipients
* GET /api/recipients/{recipient_id}
* POST /api/recipients/{recipient_id}/keys
* POST /api/recipients/{recipient_id}/revoke

### Documents

* POST /api/documents/upload
* POST /api/documents/{document_id}/encrypt
* GET /api/documents
* GET /api/documents/{document_id}

### Distribution

* POST /api/distributions
* GET /api/distributions/{distribution_id}

### Decryption

* POST /api/decryption/sessions
* POST /api/decryption/sessions/{session_id}/execute
* GET /api/decryption/sessions/{session_id}

### Ledger

* POST /api/ledger/transactions
* GET /api/ledger/records
* GET /api/ledger/records/{event_id}
* POST /api/ledger/verify
* GET /api/ledger/health

### Forensics

* POST /api/forensics/upload
* POST /api/forensics/{investigation_id}/extract
* POST /api/forensics/{investigation_id}/match
* POST /api/forensics/{investigation_id}/verify
* GET /api/forensics/{investigation_id}/report

Adapt these endpoints to the actual implementation.

Use typed schemas, validation, error handling, and clear API documentation.

---

# 13. DATA MODEL

Create appropriate database models.

At minimum:

### Recipient

* id
* display_name
* public_key
* public_key_fingerprint
* key_algorithm
* status
* created_at

### Document

* id
* filename
* original_hash
* encrypted_hash
* encryption_algorithm
* created_at

### Distribution

* id
* document_id
* recipient_id
* wrapped_key_or_kem_metadata
* status
* created_at

### DecryptionSession

* id
* document_id
* recipient_id
* nonce_reference
* status
* timestamp
* watermark_algorithm_version

### ForensicRecord

* event_id
* document_id
* document_hash
* recipient_reference
* session_id
* watermark_commitment
* canonical_record_hash
* signature
* public_key_fingerprint
* created_at

### LedgerRecord

* record_id
* event_id
* previous_record_hash
* record_hash
* merkle_root
* validator_confirmations
* commit_status
* created_at

### Investigation

* investigation_id
* input_document_hash
* extracted_watermark_status
* matched_event_id
* verification_status
* report_path
* created_at

Use foreign keys, indexes, and uniqueness constraints where appropriate.

---

# 14. ERROR HANDLING AND EDGE CASES

Implement and test:

* Unauthorized decryption attempt.
* Missing recipient key.
* Revoked recipient.
* Invalid encrypted document.
* Unsupported file format.
* Watermark extraction failure.
* Watermark not found.
* Multiple possible watermark matches.
* Invalid digital signature.
* Modified signed record.
* Ledger record missing.
* Ledger inconsistency.
* Validator disagreement.
* Duplicate event submission.
* Interrupted ledger commit.
* Corrupted local database.
* Missing local cryptographic dependency.
* Offline environment with no network access.

Display useful error messages and do not expose sensitive cryptographic material.

---

# 15. TESTING AND VALIDATION

Create a comprehensive automated test suite.

## Unit Tests

Test:

* Hash generation.
* Canonical serialization.
* ML-KEM integration.
* ML-DSA key generation.
* ML-DSA signature generation and verification.
* Encryption and decryption.
* Watermark generation.
* Watermark embedding.
* Watermark extraction.
* Watermark commitment matching.
* Ledger hash linking.
* Merkle tree generation and verification.
* Tamper detection.

## Integration Tests

Test:

* Recipient registration → key generation.
* Document upload → encryption.
* Encryption → recipient decryption.
* Decryption → watermark generation.
* Watermark → signed forensic record.
* Signed record → ledger commit.
* Leaked document → extraction → lookup → verification.
* Tampered record → verification failure.

## Security and Negative Tests

Include:

* Invalid signature.
* Wrong public key.
* Altered document.
* Altered watermark payload or commitment.
* Modified ledger record.
* Unauthorized access.
* Duplicate event.
* Missing ledger evidence.

## Demo Acceptance Criteria

The demo must successfully show:

1. A document encrypted once.
2. At least three recipients with independent credentials.
3. Multiple decryption sessions.
4. Unique watermarks for each session.
5. Signed records using ML-DSA.
6. Ledger commits in a local environment.
7. Successful forensic extraction from a supported output.
8. Cryptographic verification.
9. Tamper detection.
10. Offline operation without external services.

Measure watermark performance on a generated test corpus where feasible:

* Extraction success rate.
* False-positive behavior.
* Visual quality or document fidelity.
* Behavior after supported transformations.
* Processing time.
* Signature verification time.
* Ledger commit time.

Do not fabricate performance numbers. Generate and display measured results only.

---

# 16. RESEARCH CONTRIBUTION AND DOCUMENTATION

Create a dedicated documentation section explaining:

### Research Problem

Why conventional identical watermarking and access logs are insufficient for multi-recipient attribution.

### Proposed Method

Session-specific watermarking linked to a signed decryption record and offline tamper-evident ledger.

### Novelty

Explain the system-level integration and any genuinely new algorithmic or architectural contribution. Do not claim that combining established technologies is automatically a new cryptographic primitive or proven academic novelty.

### Threat Model

Discuss:

* Malicious recipient.
* Compromised recipient device.
* Malicious administrator.
* Ledger tampering.
* Signature forgery attempt.
* Watermark removal.
* Document transformation.
* Collusion between recipients.
* Key compromise.
* Unauthorized decryption.

### Security Assumptions

Document what must be trusted:

* Local private-key protection.
* Trusted software execution environment.
* Watermark extraction reliability.
* Local identity binding.
* Ledger validator assumptions.
* Secure key provisioning.

### Limitations

Clearly document:

* Watermark robustness limitations.
* PDF transformation limitations.
* Key compromise implications.
* Offline multi-node availability.
* Metadata leakage.
* Attribution versus legal proof.
* Prototype limitations.
* Dependence on cryptographic library support.

### Research Evaluation

Generate a structured evaluation plan with measurable metrics and comparison baselines:

* Static watermark baseline.
* Session-bound watermark without ledger.
* Session-bound watermark with signed records.
* Session-bound watermark with signed records and ledger.

Do not invent experimental results. Provide executable tests and report actual measurements.

---

# 17. PROJECT STRUCTURE

Organize the repository professionally.

Suggested structure:

project-root/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── types/
│   └── package.json
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
├── ledger/
│   ├── node_a/
│   ├── node_b/
│   ├── node_c/
│   └── README.md
│
├── crypto/
│   ├── key_management/
│   ├── signatures/
│   └── encryption/
│
├── watermark/
│   ├── embedding/
│   ├── extraction/
│   └── evaluation/
│
├── demo/
│   ├── sample_documents/
│   ├── scripts/
│   └── test_data/
│
├── docs/
│   ├── architecture.md
│   ├── threat_model.md
│   ├── security.md
│   ├── novelty.md
│   └── deployment.md
│
├── tests/
├── docker-compose.yml
├── README.md
└── .env.example

Adapt the structure to the actual architecture.

---

# 18. IMPLEMENTATION PROCESS

Follow this workflow:

## PHASE 1 — Analyze and Plan

Before writing significant code:

1. Inspect the development environment.
2. Check available cryptographic libraries and versions.
3. Verify ML-KEM and ML-DSA API availability.
4. Choose a supported watermarking approach.
5. Design the local ledger architecture.
6. Create an architecture document.
7. Identify implementation limitations.
8. Define the minimum working prototype.

Do not spend the entire task writing a plan without implementing the system.

## PHASE 2 — Build the Backend

Implement:

* Local identity management.
* Key management.
* Document encryption.
* Recipient decryption.
* Watermark generation and embedding.
* Digital signatures.
* Ledger services.
* Forensic extraction and verification.
* Persistence.
* APIs.

## PHASE 3 — Build the Frontend

Implement the polished dashboard and all required workflows.

Ensure every button performs a real backend operation.
Do not use fake success messages for unimplemented functionality.
Use loading, success, warning, and failure states.

## PHASE 4 — Integrate

Connect the frontend to the backend.

Test the full workflow.

Resolve integration issues.

## PHASE 5 — Testing

Run unit tests, integration tests, negative tests, and the end-to-end demo.

Fix actual errors rather than hiding them.

## PHASE 6 — Improve the UI

Ensure:

* Professional visual consistency.
* Clear typography.
* Responsive layout.
* Useful tables.
* Meaningful status indicators.
* Good empty states.
* No excessive text.
* No unnecessary visual clutter.

## PHASE 7 — Document and Demonstrate

Create:

* README.
* Setup instructions.
* Architecture diagram.
* Threat model.
* Novelty explanation.
* API documentation.
* Offline deployment guide.
* Testing results.
* Demo instructions.
* Known limitations.

---

# 19. IMPORTANT IMPLEMENTATION RULES

1. BUILD THE ACTUAL WORKING SYSTEM, NOT JUST A VISUAL MOCKUP.
2. Do not use fake cryptographic signatures.
3. Do not claim ML-DSA if a classical signature is used instead.
4. Do not use SHA-256 alone as a substitute for post-quantum signatures.
5. Do not claim an ordinary hash chain is a complete permissioned blockchain.
6. Do not claim absolute immutability without a justified threat model and actual protections.
7. Do not embed plaintext sensitive recipient data in the watermark.
8. Do not expose private keys in the frontend.
9. Do not rely on cloud KMS or public blockchain networks.
10. Do not fabricate benchmark results.
11. Do not hide failed cryptographic verification.
12. Do not claim successful watermark extraction unless the extraction is actually verified.
13. Do not claim legal attribution solely from the presence of a watermark.
14. Use deterministic canonical serialization for signed records.
15. Make the system modular so cryptography, watermarking, and ledger components can be independently tested.
16. Keep the entire primary workflow executable offline.
17. Make the application visually impressive, clean, and suitable for a technical presentation.
18. Prefer working, verifiable functionality over excessive features.
19. If a requirement is not fully implementable, provide the closest honest prototype, document the gap, and do not silently substitute a weaker mechanism.
20. Do not use a custom cryptographic algorithm as a replacement for standardized cryptography.

---

# 20. FINAL DELIVERABLE

At the end of implementation, provide:

1. A fully functional local application.
2. A polished frontend dashboard.
3. Working backend APIs.
4. A local identity and key-management system.
5. A working encryption and decryption flow.
6. Session-bound watermark generation.
7. Watermark embedding and extraction.
8. ML-DSA signed decryption records.
9. Offline tamper-evident ledger.
10. Ledger integrity verification.
11. Forensic investigation workflow.
12. Tamper-detection demonstration.
13. Automated tests.
14. Architecture documentation.
15. Threat model.
16. Novelty and research contribution documentation.
17. Offline setup and deployment instructions.
18. A complete demo scenario using at least three recipients.

The application must demonstrate the following final workflow:

**Encrypt Document → Distribute to Recipients → Decrypt → Generate Unique Watermark → Sign Event with ML-DSA → Commit to Offline DLT → Leak Investigation → Extract Watermark → Match Ledger → Verify Signature → Produce Cryptographically Verifiable Forensic Record**

Begin by analyzing the project and development environment, then implement the highest-priority working end-to-end path. Continue with the remaining features, testing, and UI refinement.

Prioritize real functionality, security transparency, modular architecture, and professional presentation quality.
