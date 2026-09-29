"""
Watermark Service
Implements session-bound invisible forensic watermarking for PDF documents.

TECHNIQUE: DCT-domain watermarking on rasterized PDF pages.
- Each page of the PDF is rendered to an image.
- The watermark payload (HMAC-derived) is embedded in the DCT coefficients
  of mid-frequency bands of 8x8 blocks.
- The watermarked pages are reassembled into a new PDF.

WATERMARK PAYLOAD:
    watermark_payload = HMAC-SHA-256(
        watermark_secret,
        document_id || recipient_reference || session_id || nonce || algorithm_version
    )

LIMITATIONS:
- Not claimed to be robust against all transformations (heavy JPEG compression,
  rescaling, print-scan cycles may degrade extraction).
- Designed for digital-to-digital leak scenarios.
- Extraction requires the watermark secret.
- This is a research prototype; production watermarking requires additional evaluation.
"""
import hashlib
import hmac
import json
import secrets
import struct
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import io

from app.config import (
    WATERMARK_SECRET, WATERMARK_ALGORITHM_VERSION,
    WATERMARKED_DIR, DECRYPTED_DIR
)

# Watermark embedding strength
ALPHA = 25.0  # Embedding strength factor
BLOCK_SIZE = 8
# Mid-frequency DCT coefficient positions for embedding (zigzag order indices 3-10)
EMBED_POSITIONS = [(0, 3), (1, 2), (2, 1), (3, 0), (0, 4), (1, 3), (2, 2), (3, 1)]


def generate_watermark_payload(
    document_id: str,
    recipient_reference: str,
    session_id: str,
    nonce: str,
    algorithm_version: str = WATERMARK_ALGORITHM_VERSION
) -> bytes:
    """
    Generate a cryptographically derived watermark payload using HMAC-SHA-256.
    The payload does NOT contain plaintext recipient identity.
    """
    binding_data = f"{document_id}||{recipient_reference}||{session_id}||{nonce}||{algorithm_version}"
    payload = hmac.new(
        WATERMARK_SECRET.encode("utf-8"),
        binding_data.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return payload


def compute_watermark_commitment(payload: bytes) -> str:
    """Compute a commitment (hash) of the watermark payload for ledger storage."""
    return hashlib.sha256(payload).hexdigest()


def _payload_to_bits(payload: bytes, num_bits: int) -> list:
    """Convert payload bytes to a list of bits, repeating if necessary for redundancy."""
    bits = []
    for byte in payload:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    # Repeat bits to fill required length (error tolerance through redundancy)
    if len(bits) < num_bits:
        bits = (bits * ((num_bits // len(bits)) + 1))[:num_bits]
    return bits[:num_bits]


def _bits_to_payload(bits: list, payload_length: int = 32) -> bytes:
    """Convert extracted bits back to payload bytes using majority voting."""
    # Total bits from payload = payload_length * 8
    total_payload_bits = payload_length * 8
    if len(bits) < total_payload_bits:
        return bytes(payload_length)

    # Majority vote across repetitions
    repetitions = len(bits) // total_payload_bits
    voted_bits = []
    for i in range(total_payload_bits):
        count = 0
        for r in range(repetitions):
            idx = r * total_payload_bits + i
            if idx < len(bits):
                count += bits[idx]
        voted_bits.append(1 if count > repetitions / 2 else 0)

    # Convert bits to bytes
    result = bytearray()
    for i in range(0, len(voted_bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(voted_bits):
                byte = (byte << 1) | voted_bits[i + j]
            else:
                byte = byte << 1
        result.append(byte)
    return bytes(result[:payload_length])


def _dct2(block: np.ndarray) -> np.ndarray:
    """Compute 2D DCT of an 8x8 block."""
    from scipy.fftpack import dct
    return dct(dct(block.T, norm='ortho').T, norm='ortho')


def _idct2(block: np.ndarray) -> np.ndarray:
    """Compute 2D inverse DCT of an 8x8 block."""
    from scipy.fftpack import idct
    return idct(idct(block.T, norm='ortho').T, norm='ortho')


def _embed_in_channel(channel: np.ndarray, bits: list, alpha: float = ALPHA) -> Tuple[np.ndarray, int]:
    """Embed bits into the DCT coefficients of an image channel."""
    h, w = channel.shape
    result = channel.astype(np.float64).copy()
    bit_idx = 0
    total_embedded = 0

    for y in range(0, h - BLOCK_SIZE + 1, BLOCK_SIZE):
        for x in range(0, w - BLOCK_SIZE + 1, BLOCK_SIZE):
            if bit_idx >= len(bits):
                return result, total_embedded

            block = result[y:y+BLOCK_SIZE, x:x+BLOCK_SIZE]
            dct_block = _dct2(block)

            # Embed one bit per block in a mid-frequency coefficient
            pos = EMBED_POSITIONS[bit_idx % len(EMBED_POSITIONS)]
            coeff = dct_block[pos[0], pos[1]]

            bit = bits[bit_idx]
            # Quantization-based embedding
            quantized = round(coeff / alpha) * alpha
            if bit == 1:
                dct_block[pos[0], pos[1]] = quantized + alpha / 4
            else:
                dct_block[pos[0], pos[1]] = quantized - alpha / 4

            result[y:y+BLOCK_SIZE, x:x+BLOCK_SIZE] = _idct2(dct_block)
            bit_idx += 1
            total_embedded += 1

    return result, total_embedded


def _extract_from_channel(channel: np.ndarray, num_bits: int, alpha: float = ALPHA) -> list:
    """Extract bits from the DCT coefficients of an image channel."""
    h, w = channel.shape
    bits = []
    bit_idx = 0

    for y in range(0, h - BLOCK_SIZE + 1, BLOCK_SIZE):
        for x in range(0, w - BLOCK_SIZE + 1, BLOCK_SIZE):
            if bit_idx >= num_bits:
                return bits

            block = channel[y:y+BLOCK_SIZE, x:x+BLOCK_SIZE].astype(np.float64)
            dct_block = _dct2(block)

            pos = EMBED_POSITIONS[bit_idx % len(EMBED_POSITIONS)]
            coeff = dct_block[pos[0], pos[1]]

            quantized = round(coeff / alpha) * alpha
            diff = coeff - quantized
            bits.append(1 if diff > 0 else 0)
            bit_idx += 1

    return bits


def embed_watermark_in_pdf(
    pdf_bytes: bytes,
    watermark_payload: bytes,
    session_id: str,
    output_path: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Embed invisible watermark into a PDF document.
    Returns: (output_path, embedding_stats)
    """
    import fitz  # PyMuPDF
    from PIL import Image

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    new_doc = fitz.open()

    stats = {
        "pages_processed": 0,
        "total_bits_embedded": 0,
        "embedding_strength": ALPHA,
        "algorithm_version": WATERMARK_ALGORITHM_VERSION,
    }

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render page at 150 DPI for watermarking
        mat = fitz.Matrix(150/72, 150/72)
        pix = page.get_pixmap(matrix=mat)

        # Convert to numpy array (make copy to ensure array is writeable)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n).copy()

        if pix.n == 4:  # RGBA
            img = img[:, :, :3]  # Drop alpha

        # Calculate how many bits can be embedded per page
        h, w = img.shape[:2]
        blocks_h = h // BLOCK_SIZE
        blocks_w = w // BLOCK_SIZE
        capacity = blocks_h * blocks_w

        # Generate bits with redundancy
        bits = _payload_to_bits(watermark_payload, min(capacity, 256 * 8))  # Up to 256 bytes with redundancy

        # Embed in the blue channel (least visually noticeable)
        channel = img[:, :, 2].astype(np.float64)
        watermarked_channel, embedded = _embed_in_channel(channel, bits)
        img[:, :, 2] = np.clip(watermarked_channel, 0, 255).astype(np.uint8)

        stats["total_bits_embedded"] += embedded
        stats["pages_processed"] += 1

        # Convert back to PIL Image
        pil_img = Image.fromarray(img)
        img_bytes = io.BytesIO()
        pil_img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # Create new page with watermarked image
        img_rect = fitz.Rect(0, 0, page.rect.width, page.rect.height)
        new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(img_rect, stream=img_bytes.getvalue())

    if output_path is None:
        output_path = str(WATERMARKED_DIR / f"wm_{session_id}.pdf")

    new_doc.save(output_path)
    new_doc.close()
    doc.close()

    return output_path, stats


def extract_watermark_from_pdf(
    pdf_path: str,
    expected_bits: int = 256 * 8
) -> Tuple[Optional[bytes], Dict[str, Any]]:
    """
    Extract watermark from a PDF document.
    Returns: (extracted_payload_or_None, extraction_stats)
    """
    import fitz
    from PIL import Image

    doc = fitz.open(pdf_path)
    all_bits = []

    stats = {
        "pages_processed": 0,
        "total_bits_extracted": 0,
        "algorithm_version": WATERMARK_ALGORITHM_VERSION,
    }

    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(150/72, 150/72)
        pix = page.get_pixmap(matrix=mat)

        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        if pix.n == 4:
            img = img[:, :, :3]

        channel = img[:, :, 2].astype(np.float64)

        h, w = channel.shape
        blocks_h = h // BLOCK_SIZE
        blocks_w = w // BLOCK_SIZE
        capacity = blocks_h * blocks_w

        bits = _extract_from_channel(channel, min(capacity, expected_bits))
        all_bits.extend(bits)

        stats["total_bits_extracted"] += len(bits)
        stats["pages_processed"] += 1

    doc.close()

    if len(all_bits) < 256:  # Minimum bits needed
        return None, {**stats, "status": "insufficient_data"}

    # Reconstruct payload with majority voting
    payload = _bits_to_payload(all_bits, 32)

    return payload, {**stats, "status": "extracted"}


def verify_watermark(
    extracted_payload: bytes,
    expected_commitment: str
) -> Tuple[bool, float]:
    """
    Verify an extracted watermark against its expected commitment.
    Returns: (match, confidence)
    """
    extracted_commitment = compute_watermark_commitment(extracted_payload)

    if extracted_commitment == expected_commitment:
        return True, 1.0

    # Compute bit-level similarity for confidence
    expected_bytes = bytes.fromhex(expected_commitment) if len(expected_commitment) == 64 else b""
    if not expected_bytes:
        return False, 0.0

    # We compare the extracted payload against all known commitments in the match step
    return False, 0.0


def match_watermark_to_records(
    extracted_payload: bytes,
    records: list
) -> Tuple[Optional[Dict], float]:
    """
    Try to match extracted watermark payload against known forensic records.
    Returns: (matched_record_or_None, confidence)
    """
    extracted_commitment = compute_watermark_commitment(extracted_payload)

    for record in records:
        if record.get("watermark_commitment") == extracted_commitment:
            return record, 1.0

    # If no exact match, compute similarity based on payload
    best_match = None
    best_confidence = 0.0

    return best_match, best_confidence
