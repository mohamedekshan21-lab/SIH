const API = import.meta.env.VITE_API_BASE_URL || '/api';

async function request(url, options = {}) {
  const res = await fetch(`${API}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

async function upload(url, file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API}${url}`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export const api = {
  // Dashboard
  getDashboard: () => request('/dashboard'),

  // Recipients
  getRecipients: () => request('/recipients'),
  getRecipient: (id) => request(`/recipients/${id}`),
  createRecipient: (data) => request('/recipients', { method: 'POST', body: JSON.stringify(data) }),
  generateKeys: (id) => request(`/recipients/${id}/keys`, { method: 'POST' }),
  revokeRecipient: (id) => request(`/recipients/${id}/revoke`, { method: 'POST' }),

  // Documents
  getDocuments: () => request('/documents'),
  getDocument: (id) => request(`/documents/${id}`),
  uploadDocument: (file) => upload('/documents/upload', file),
  encryptDocument: (id, recipientIds) => request(`/documents/${id}/encrypt`, {
    method: 'POST', body: JSON.stringify({ recipient_ids: recipientIds }),
  }),
  getDistributions: (id) => request(`/documents/${id}/distributions`),

  // Decryption
  createSession: (data) => request('/decryption/sessions', {
    method: 'POST', body: JSON.stringify(data),
  }),
  getSessions: () => request('/decryption/sessions'),
  getSession: (id) => request(`/decryption/sessions/${id}`),

  // Ledger
  getLedgerHealth: () => request('/ledger/health'),
  getLedgerRecords: (params) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/ledger/records${qs ? '?' + qs : ''}`);
  },
  verifyLedger: () => request('/ledger/verify', { method: 'POST' }),
  tamperTest: (idx) => request(`/ledger/tamper-test?record_index=${idx}`, { method: 'POST' }),

  // Forensics
  uploadForensic: (file) => upload('/forensics/upload', file),
  extractWatermark: (id) => request(`/forensics/${id}/extract`, { method: 'POST' }),
  matchWatermark: (id) => request(`/forensics/${id}/match`, { method: 'POST' }),
  verifyInvestigation: (id) => request(`/forensics/${id}/verify`, { method: 'POST' }),
  getForensicReport: (id) => request(`/forensics/${id}/report`),
  getInvestigations: () => request('/forensics'),

  // Verification
  verifySignature: (eventId) => request(`/verify/signature?event_id=${eventId}`, { method: 'POST' }),
  verifyDocHash: (docId) => request(`/verify/document-hash?document_id=${docId}`, { method: 'POST' }),
  verifyChain: () => request('/verify/ledger-chain', { method: 'POST' }),
  verifyMerkle: (idx) => request(`/verify/merkle-proof?block_index=${idx}`, { method: 'POST' }),

  // System
  getConfig: () => request('/system/config'),
  getPqcInfo: () => request('/system/pqc-info'),

  // Analytics
  getAnalytics: () => request('/analytics'),

  // Demo
  setupDemo: () => request('/demo/setup', { method: 'POST' }),
};
