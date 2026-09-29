import { useState, useEffect, useCallback } from 'react';
import { Shield, LayoutDashboard, FileText, Users, KeyRound, Search, Database, Settings, ChevronRight, Upload, Lock, Unlock, Eye, CheckCircle2, XCircle, AlertTriangle, Clock, Activity, FileSearch, ShieldCheck, Loader2, Download, Trash2, RefreshCw, Play, Plus, ArrowRight, Hash, Fingerprint, Server, Zap, AlertOctagon, Info, BookOpen, TrendingUp, BarChart2, PieChart as PieIcon } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart, Line,
  AreaChart, Area,
  BarChart, Bar,
  PieChart, Pie, Cell, Tooltip as ReTooltip, Legend,
  XAxis, YAxis, CartesianGrid,
  RadialBarChart, RadialBar,
} from 'recharts';
import './index.css';
import { api } from './services/api.js';
import Analytics from './Analytics.jsx';

// ===== TOAST SYSTEM =====
let toastId = 0;
function useToasts() {
  const [toasts, setToasts] = useState([]);
  const add = useCallback((msg, type = 'info') => {
    const id = ++toastId;
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  }, []);
  return { toasts, success: m => add(m, 'success'), error: m => add(m, 'error'), info: m => add(m, 'info') };
}

function Toasts({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          {t.type === 'success' ? <CheckCircle2 size={16} /> : t.type === 'error' ? <XCircle size={16} /> : <Info size={16} />}
          {t.msg}
        </div>
      ))}
    </div>
  );
}

// ===== SIDEBAR =====
const NAV = [
  { id: 'dashboard', label: 'Overview', icon: LayoutDashboard, section: 'OPERATIONS' },
  { id: 'documents', label: 'Document Distribution', icon: FileText, section: 'OPERATIONS' },
  { id: 'recipients', label: 'Recipient Management', icon: Users, section: 'OPERATIONS' },
  { id: 'decryption', label: 'Decryption Workspace', icon: Unlock, section: 'OPERATIONS' },
  { id: 'ledger', label: 'Ledger Explorer', icon: Database, section: 'FORENSICS' },
  { id: 'forensics', label: 'Forensic Investigation', icon: FileSearch, section: 'FORENSICS' },
  { id: 'verification', label: 'Verification Center', icon: ShieldCheck, section: 'FORENSICS' },
  { id: 'analytics', label: 'Analytics & Trends', icon: TrendingUp, section: 'ANALYTICS' },
  { id: 'config', label: 'System Configuration', icon: Settings, section: 'SYSTEM' },
];

function Sidebar({ page, setPage }) {
  let lastSection = '';
  return (
    <nav className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <div className="logo-icon"><Shield size={20} color="#0a0e1a" /></div>
          <div className="logo-text">
            <h1>QSFW System</h1>
            <span>Quantum-Safe Forensics</span>
          </div>
        </div>
      </div>
      <div className="sidebar-nav">
        {NAV.map(n => {
          const showSection = n.section !== lastSection;
          lastSection = n.section;
          return (
            <div key={n.id}>
              {showSection && <div className="nav-section-label">{n.section}</div>}
              <div className={`nav-item ${page === n.id ? 'active' : ''}`} onClick={() => setPage(n.id)}>
                <n.icon className="nav-icon" size={18} />
                {n.label}
              </div>
            </div>
          );
        })}
      </div>
      <div className="sidebar-footer">
        <div className="offline-badge">
          <div className="offline-dot" />
          AIR-GAPPED · OFFLINE MODE
        </div>
      </div>
    </nav>
  );
}

// ===== DASHBOARD =====
function Dashboard({ toast }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = () => { setLoading(true); api.getDashboard().then(setStats).catch(e => toast.error(e.message)).finally(() => setLoading(false)); };
  useEffect(load, []);

  if (loading) return <Loading />;

  const s = stats || {};
  return (
    <>
      <div className="page-header">
        <h2>Security Operations Dashboard</h2>
        <p>Quantum-Safe Forensic Watermarking System — Real-time operational overview</p>
      </div>
      <div className="page-body">
        <div className="stats-grid">
          <StatCard icon={FileText} color="blue" value={s.total_documents} label="Total Documents" />
          <StatCard icon={Lock} color="purple" value={s.total_encrypted} label="Encrypted" />
          <StatCard icon={Users} color="green" value={s.total_recipients} label="Recipients" />
          <StatCard icon={KeyRound} color="blue" value={s.total_sessions} label="Decryption Sessions" />
          <StatCard icon={Fingerprint} color="purple" value={s.total_signed_records} label="Signed Records" />
          <StatCard icon={Database} color={s.ledger_health === 'healthy' ? 'green' : 'red'} value={s.ledger_health?.toUpperCase()} label="Ledger Health" />
        </div>

        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header"><div className="card-title"><Activity size={16} /> System Architecture Flow</div></div>
          <div className="flow-diagram">
            {['Document Upload', 'AES-256-GCM Encryption', 'ML-KEM Distribution', 'Recipient Decryption', 'Session Watermark', 'ML-DSA Signature', 'Ledger Commit', 'Forensic Verification'].map((step, i, a) => (
              <span key={step}>
                <span className="flow-step"><Zap size={12} />{step}</span>
                {i < a.length - 1 && <span className="flow-arrow"> → </span>}
              </span>
            ))}
          </div>
        </div>

        <div className="grid-2">
          <div className="card">
            <div className="card-header"><div className="card-title"><Server size={16} /> Validator Status</div></div>
            <div className="card-body">
              {(s.validator_status || []).map(v => (
                <div key={v.node_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                  <span>{v.node_name}</span>
                  <span className="badge badge-success">{v.status}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <div className="card-header"><div className="card-title"><Clock size={16} /> Recent Activity</div></div>
            <div className="card-body">
              {(s.recent_activity || []).length === 0 ? <p style={{ color: 'var(--text-muted)' }}>No activity yet. Run the demo setup to get started.</p> : null}
              {(s.recent_activity || []).slice(0, 5).map(a => (
                <div key={a.id} style={{ padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: 12 }}>
                  <span className="badge badge-info" style={{ marginRight: 8 }}>{a.event_type}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{a.details}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <button className="btn btn-primary btn-lg" onClick={() => {
            toast.info('Setting up demo data...');
            api.setupDemo().then(() => { toast.success('Demo data initialized!'); load(); }).catch(e => toast.error(e.message));
          }}>
            <Play size={18} /> Initialize Demo Data
          </button>
        </div>
      </div>
    </>
  );
}

function StatCard({ icon: Icon, color, value, label }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}><Icon size={20} /></div>
      <div className="stat-value">{value ?? 0}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

// ===== DOCUMENTS =====
function Documents({ toast }) {
  const [docs, setDocs] = useState([]);
  const [recipients, setRecipients] = useState([]);
  const [selRecipients, setSelRecipients] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([api.getDocuments(), api.getRecipients()])
      .then(([d, r]) => { setDocs(d); setRecipients(r); })
      .catch(e => toast.error(e.message))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      toast.info(`Uploading ${file.name}...`);
      await api.uploadDocument(file);
      toast.success('Document uploaded');
      load();
    } catch (e) { toast.error(e.message); }
  };

  const handleEncrypt = async (docId) => {
    if (selRecipients.length === 0) return toast.error('Select at least one recipient');
    try {
      toast.info('Encrypting and distributing...');
      await api.encryptDocument(docId, selRecipients);
      toast.success('Document encrypted & distributed!');
      setSelRecipients([]);
      load();
    } catch (e) { toast.error(e.message); }
  };

  if (loading) return <Loading />;

  return (
    <>
      <div className="page-header">
        <h2>Secure Document Distribution</h2>
        <p>Upload, encrypt, and distribute documents to authorized recipients</p>
      </div>
      <div className="page-body">
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header"><div className="card-title"><Upload size={16} /> Upload Document</div></div>
          <label className="file-drop">
            <Upload className="file-drop-icon" size={48} />
            <div className="file-drop-text">Click to upload a PDF document</div>
            <div className="file-drop-hint">Supported: .pdf</div>
            <input type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} />
          </label>
        </div>

        {docs.length > 0 && (
          <div className="card">
            <div className="card-header"><div className="card-title"><FileText size={16} /> Documents</div></div>
            <div className="table-container">
              <table>
                <thead><tr><th>Filename</th><th>Hash</th><th>Status</th><th>Size</th><th>Actions</th></tr></thead>
                <tbody>
                  {docs.map(d => (
                    <tr key={d.id}>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{d.filename}</td>
                      <td><span className="hash-display">{d.original_hash?.slice(0, 16)}...</span></td>
                      <td><span className={`badge ${d.encryption_status === 'encrypted' ? 'badge-success' : 'badge-warning'}`}>{d.encryption_status}</span></td>
                      <td>{d.file_size ? `${(d.file_size / 1024).toFixed(1)} KB` : '-'}</td>
                      <td>
                        {d.encryption_status !== 'encrypted' && (
                          <div>
                            <div style={{ marginBottom: 8 }}>
                              <div className="select-chips">
                                {recipients.filter(r => r.status === 'active' && r.public_key_fingerprint).map(r => (
                                  <span key={r.id} className={`chip ${selRecipients.includes(r.id) ? 'selected' : ''}`}
                                    onClick={() => setSelRecipients(s => s.includes(r.id) ? s.filter(x => x !== r.id) : [...s, r.id])}>
                                    {r.display_name}
                                  </span>
                                ))}
                              </div>
                            </div>
                            <button className="btn btn-primary btn-sm" onClick={() => handleEncrypt(d.id)}><Lock size={14} /> Encrypt & Distribute</button>
                          </div>
                        )}
                        {d.encryption_status === 'encrypted' && <span className="badge badge-success"><CheckCircle2 size={12} /> Distributed</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {docs.length === 0 && (
          <div className="empty-state">
            <FileText className="empty-state-icon" size={56} />
            <h3>No Documents Yet</h3>
            <p>Upload a PDF document to get started with the encryption workflow.</p>
          </div>
        )}
      </div>
    </>
  );
}

// ===== RECIPIENTS =====
function Recipients({ toast }) {
  const [recipients, setRecipients] = useState([]);
  const [newName, setNewName] = useState('');
  const [loading, setLoading] = useState(true);

  const load = () => { setLoading(true); api.getRecipients().then(setRecipients).catch(e => toast.error(e.message)).finally(() => setLoading(false)); };
  useEffect(load, []);

  const create = async () => {
    if (!newName.trim()) return;
    try {
      await api.createRecipient({ display_name: newName.trim() });
      toast.success(`Created ${newName}`);
      setNewName('');
      load();
    } catch (e) { toast.error(e.message); }
  };

  const genKeys = async (id, name) => {
    try {
      toast.info(`Generating PQC keys for ${name}...`);
      const r = await api.generateKeys(id);
      toast.success(`Keys generated: ${r.sig_algorithm}, ${r.kem_algorithm}`);
      load();
    } catch (e) { toast.error(e.message); }
  };

  const revoke = async (id) => {
    try {
      await api.revokeRecipient(id);
      toast.success('Recipient revoked');
      load();
    } catch (e) { toast.error(e.message); }
  };

  if (loading) return <Loading />;

  return (
    <>
      <div className="page-header">
        <h2>Recipient Management</h2>
        <p>Manage identities, generate post-quantum cryptographic keys, and control access</p>
      </div>
      <div className="page-body">
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header"><div className="card-title"><Plus size={16} /> Create Recipient</div></div>
          <div style={{ display: 'flex', gap: 12 }}>
            <input className="input" placeholder="Recipient display name" value={newName} onChange={e => setNewName(e.target.value)} onKeyDown={e => e.key === 'Enter' && create()} />
            <button className="btn btn-primary" onClick={create}><Plus size={16} /> Create</button>
          </div>
        </div>

        {recipients.length > 0 && (
          <div className="card">
            <div className="card-header"><div className="card-title"><Users size={16} /> Recipients ({recipients.length})</div></div>
            <div className="table-container">
              <table>
                <thead><tr><th>Name</th><th>Signing Key</th><th>KEM Key</th><th>Algorithm</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                  {recipients.map(r => (
                    <tr key={r.id}>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{r.display_name}</td>
                      <td>{r.public_key_fingerprint ? <span className="hash-display">{r.public_key_fingerprint.slice(0, 12)}...</span> : <span className="badge badge-warning">None</span>}</td>
                      <td>{r.kem_public_key_fingerprint ? <span className="hash-display">{r.kem_public_key_fingerprint.slice(0, 12)}...</span> : <span className="badge badge-warning">None</span>}</td>
                      <td><span style={{ fontSize: 12, color: 'var(--accent-primary)' }}>{r.key_algorithm}</span></td>
                      <td><span className={`badge ${r.status === 'active' ? 'badge-success' : 'badge-error'}`}>{r.status}</span></td>
                      <td style={{ display: 'flex', gap: 6 }}>
                        {!r.public_key_fingerprint && r.status === 'active' && (
                          <button className="btn btn-primary btn-sm" onClick={() => genKeys(r.id, r.display_name)}><KeyRound size={14} /> Gen Keys</button>
                        )}
                        {r.status === 'active' && (
                          <button className="btn btn-danger btn-sm" onClick={() => revoke(r.id)}><XCircle size={14} /> Revoke</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

// ===== DECRYPTION WORKSPACE =====
function Decryption({ toast }) {
  const [docs, setDocs] = useState([]);
  const [recipients, setRecipients] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [selDoc, setSelDoc] = useState('');
  const [selRecip, setSelRecip] = useState('');
  const [events, setEvents] = useState([]);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([api.getDocuments(), api.getRecipients(), api.getSessions()])
      .then(([d, r, s]) => { setDocs(d.filter(x => x.encryption_status === 'encrypted')); setRecipients(r.filter(x => x.status === 'active')); setSessions(s); })
      .catch(e => toast.error(e.message))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const decrypt = async () => {
    if (!selDoc || !selRecip) return toast.error('Select a document and recipient');
    setRunning(true);
    setEvents([]);
    try {
      toast.info('Starting decryption session...');
      const result = await api.createSession({ document_id: selDoc, recipient_id: selRecip });
      setEvents(result.events || []);
      toast.success(`Session complete! Status: ${result.status}`);
      load();
    } catch (e) {
      toast.error(e.message);
    }
    setRunning(false);
  };

  if (loading) return <Loading />;

  return (
    <>
      <div className="page-header">
        <h2>Recipient Decryption Workspace</h2>
        <p>Decrypt documents, generate session-bound watermarks, sign records with ML-DSA</p>
      </div>
      <div className="page-body">
        <div className="grid-2" style={{ marginBottom: 24 }}>
          <div className="card">
            <div className="card-header"><div className="card-title"><Unlock size={16} /> New Decryption Session</div></div>
            <div className="input-group">
              <label className="input-label">Select Encrypted Document</label>
              <select className="input" value={selDoc} onChange={e => setSelDoc(e.target.value)}>
                <option value="">-- Select document --</option>
                {docs.map(d => <option key={d.id} value={d.id}>{d.filename}</option>)}
              </select>
            </div>
            <div className="input-group">
              <label className="input-label">Select Recipient</label>
              <select className="input" value={selRecip} onChange={e => setSelRecip(e.target.value)}>
                <option value="">-- Select recipient --</option>
                {recipients.filter(r => r.public_key_fingerprint).map(r => <option key={r.id} value={r.id}>{r.display_name}</option>)}
              </select>
            </div>
            <button className="btn btn-primary btn-lg" disabled={running} onClick={decrypt} style={{ width: '100%', justifyContent: 'center' }}>
              {running ? <><Loader2 size={18} className="spinner" /> Processing...</> : <><Play size={18} /> Execute Decryption Session</>}
            </button>
          </div>
          <div className="card">
            <div className="card-header"><div className="card-title"><Activity size={16} /> Session Event Timeline</div></div>
            {events.length === 0 && <div style={{ color: 'var(--text-muted)', fontSize: 13, padding: 16 }}>Start a decryption session to see the event timeline.</div>}
            <div className="timeline">
              {events.map((ev, i) => (
                <div className="timeline-item" key={i}>
                  <div className={`timeline-dot ${ev.status === 'success' ? 'success' : ev.status === 'failed' ? 'error' : 'pending'}`} />
                  <div className="timeline-title">Step {ev.step}: {ev.name}</div>
                  <div className="timeline-detail">{ev.detail || ev.status}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {sessions.length > 0 && (
          <div className="card">
            <div className="card-header"><div className="card-title"><Clock size={16} /> Previous Sessions ({sessions.length})</div></div>
            <div className="table-container">
              <table>
                <thead><tr><th>Session ID</th><th>Document</th><th>Recipient</th><th>Status</th><th>Watermark</th><th>Timestamp</th></tr></thead>
                <tbody>
                  {sessions.map(s => (
                    <tr key={s.session_id}>
                      <td><span className="hash-display">{s.session_id.slice(0, 8)}...</span></td>
                      <td><span className="hash-display">{s.document_id.slice(0, 8)}...</span></td>
                      <td>{s.recipient_id.slice(0, 8)}...</td>
                      <td><span className={`badge ${s.status === 'committed' ? 'badge-success' : 'badge-warning'}`}>{s.status}</span></td>
                      <td>{s.watermark_commitment ? <span className="hash-display">{s.watermark_commitment.slice(0, 12)}...</span> : '-'}</td>
                      <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{s.timestamp ? new Date(s.timestamp).toLocaleString() : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

// ===== LEDGER EXPLORER =====
function Ledger({ toast }) {
  const [health, setHealth] = useState(null);
  const [records, setRecords] = useState([]);
  const [searchField, setSearchField] = useState('');
  const [searchValue, setSearchValue] = useState('');
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([api.getLedgerHealth(), api.getLedgerRecords({})])
      .then(([h, r]) => { setHealth(h); setRecords(r); })
      .catch(e => toast.error(e.message))
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const search = async () => {
    if (!searchValue) return load();
    try {
      const params = {};
      params[searchField || 'event_id'] = searchValue;
      const r = await api.getLedgerRecords(params);
      setRecords(r);
    } catch (e) { toast.error(e.message); }
  };

  const verify = async () => {
    try {
      const r = await api.verifyLedger();
      toast[r.overall_valid ? 'success' : 'error'](`Chain: ${r.overall_valid ? 'VALID' : 'INVALID'}, Consistent: ${r.consistent}`);
    } catch (e) { toast.error(e.message); }
  };

  const tamperTest = async () => {
    if (records.length === 0) return toast.error('No records to test');
    try {
      const r = await api.tamperTest(0);
      toast[r.tamper_detected ? 'success' : 'error'](r.message);
    } catch (e) { toast.error(e.message); }
  };

  if (loading) return <Loading />;

  return (
    <>
      <div className="page-header">
        <h2>Ledger Explorer</h2>
        <p>Browse, search, and verify the offline tamper-evident distributed ledger</p>
      </div>
      <div className="page-body">
        {health && (
          <div className="stats-grid" style={{ marginBottom: 24 }}>
            <StatCard icon={Database} color={health.status === 'healthy' ? 'green' : 'red'} value={health.status?.toUpperCase()} label="Ledger Status" />
            <StatCard icon={Server} color="blue" value={health.validator_count} label="Validators" />
            <StatCard icon={Hash} color="purple" value={health.total_records} label="Total Records" />
            <StatCard icon={CheckCircle2} color="green" value={health.chain_valid ? 'YES' : 'NO'} label="Chain Valid" />
          </div>
        )}

        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">
            <div className="card-title"><Search size={16} /> Search Records</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-success btn-sm" onClick={verify}><ShieldCheck size={14} /> Verify Chain</button>
              <button className="btn btn-danger btn-sm" onClick={tamperTest}><AlertOctagon size={14} /> Tamper Test</button>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <select className="input" style={{ maxWidth: 200 }} value={searchField} onChange={e => setSearchField(e.target.value)}>
              <option value="event_id">Event ID</option>
              <option value="document_id">Document ID</option>
              <option value="watermark_commitment">Watermark</option>
            </select>
            <input className="input" placeholder="Search value..." value={searchValue} onChange={e => setSearchValue(e.target.value)} onKeyDown={e => e.key === 'Enter' && search()} />
            <button className="btn btn-primary btn-sm" onClick={search}><Search size={14} /></button>
            <button className="btn btn-secondary btn-sm" onClick={() => { setSearchValue(''); load(); }}><RefreshCw size={14} /></button>
          </div>
        </div>

        {records.length > 0 && (
          <div className="card">
            <div className="card-header"><div className="card-title"><Database size={16} /> Ledger Records ({records.length})</div></div>
            <div className="table-container">
              <table>
                <thead><tr><th>Block</th><th>Event ID</th><th>Record Hash</th><th>Previous Hash</th><th>Status</th><th>Timestamp</th></tr></thead>
                <tbody>
                  {records.map((r, i) => (
                    <tr key={i}>
                      <td style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>#{r.block_index}</td>
                      <td><span className="hash-display">{r.event_id?.slice(0, 12)}...</span></td>
                      <td><span className="hash-display">{r.record_hash?.slice(0, 12)}...</span></td>
                      <td><span className="hash-display">{r.previous_record_hash?.slice(0, 12)}...</span></td>
                      <td><span className="badge badge-success">{r.commit_status || 'committed'}</span></td>
                      <td style={{ fontSize: 12 }}>{r.created_at ? new Date(r.created_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {records.length === 0 && <div className="empty-state"><Database className="empty-state-icon" size={56} /><h3>Ledger Empty</h3><p>Run decryption sessions to add records to the ledger.</p></div>}

        {health && health.merkle_root && (
          <div className="card" style={{ marginTop: 24 }}>
            <div className="card-header"><div className="card-title"><Hash size={16} /> Merkle Root</div></div>
            <div className="hash-display" style={{ padding: 12 }}>{health.merkle_root}</div>
          </div>
        )}
      </div>
    </>
  );
}

// ===== FORENSIC INVESTIGATION =====
function Forensics({ toast }) {
  const [invs, setInvs] = useState([]);
  const [current, setCurrent] = useState(null);
  const [extraction, setExtraction] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [verification, setVerification] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const load = () => { setLoading(true); api.getInvestigations().then(setInvs).catch(e => toast.error(e.message)).finally(() => setLoading(false)); };
  useEffect(load, []);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      toast.info('Uploading leaked document...');
      const r = await api.uploadForensic(file);
      setCurrent(r);
      toast.success('Document uploaded for investigation');
      load();
    } catch (e) { toast.error(e.message); }
  };

  const runFullInvestigation = async () => {
    if (!current) return;
    setRunning(true);
    try {
      // Step 1: Extract
      toast.info('Step 1: Extracting watermark...');
      const ext = await api.extractWatermark(current.investigation_id);
      setExtraction(ext);
      if (ext.status !== 'extracted') { toast.error('Watermark extraction failed'); setRunning(false); return; }

      // Step 2: Match
      toast.info('Step 2: Matching to ledger...');
      const match = await api.matchWatermark(current.investigation_id);
      setMatchResult(match);
      if (match.status !== 'matched') { toast.error('No matching ledger record found'); setRunning(false); return; }

      // Step 3: Verify
      toast.info('Step 3: Verifying evidence...');
      const ver = await api.verifyInvestigation(current.investigation_id);
      setVerification(ver);

      // Step 4: Report
      toast.info('Step 4: Generating report...');
      const rep = await api.getForensicReport(current.investigation_id);
      setReport(rep);

      toast.success('Investigation complete!');
      load();
    } catch (e) { toast.error(e.message); }
    setRunning(false);
  };

  if (loading) return <Loading />;

  return (
    <>
      <div className="page-header">
        <h2>Forensic Investigation Workspace</h2>
        <p>Upload leaked documents, extract watermarks, match to ledger, and verify attribution</p>
      </div>
      <div className="page-body">
        <div className="grid-2" style={{ marginBottom: 24 }}>
          <div className="card">
            <div className="card-header"><div className="card-title"><Upload size={16} /> Upload Leaked Document</div></div>
            <label className="file-drop" style={{ padding: 24 }}>
              <FileSearch className="file-drop-icon" size={40} />
              <div className="file-drop-text">Upload suspected leaked PDF</div>
              <div className="file-drop-hint">The system will extract and match the embedded watermark</div>
              <input type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} />
            </label>
            {current && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Investigation ID</div>
                <div className="hash-display">{current.investigation_id}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>Document Hash</div>
                <div className="hash-display">{current.input_document_hash}</div>
                <button className="btn btn-primary" style={{ marginTop: 16, width: '100%', justifyContent: 'center' }} disabled={running} onClick={runFullInvestigation}>
                  {running ? <><Loader2 size={16} /> Running Investigation...</> : <><Play size={16} /> Run Full Investigation</>}
                </button>
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-header"><div className="card-title"><Activity size={16} /> Investigation Progress</div></div>
            <div className="timeline">
              <TimelineStep name="Document Upload" status={current ? 'success' : 'pending'} detail={current?.input_filename} />
              <TimelineStep name="Watermark Extraction" status={extraction?.status === 'extracted' ? 'success' : extraction?.status === 'failed' ? 'error' : 'pending'}
                detail={extraction?.watermark_commitment ? `Commitment: ${extraction.watermark_commitment.slice(0, 16)}...` : null} />
              <TimelineStep name="Ledger Match" status={matchResult?.status === 'matched' ? 'success' : matchResult?.status === 'not_found' ? 'error' : 'pending'}
                detail={matchResult?.matched_event_id ? `Event: ${matchResult.matched_event_id.slice(0, 12)}...` : null} />
              <TimelineStep name="Evidence Verification" status={verification?.overall_status === 'VERIFIED' ? 'success' : verification?.overall_status === 'FAILED' ? 'error' : 'pending'} />
              <TimelineStep name="Report Generation" status={report ? 'success' : 'pending'} />
            </div>
          </div>
        </div>

        {verification && (
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header"><div className="card-title"><ShieldCheck size={16} /> Verification Results</div></div>
            <div className="verification-grid">
              <VerificationItem label="ML-DSA Signature" status={verification.signature_verification} />
              <VerificationItem label="Document Hash Binding" status={verification.document_hash_verification} />
              <VerificationItem label="Ledger Integrity" status={verification.ledger_integrity} />
              <VerificationItem label="Watermark Binding" status={verification.watermark_binding} />
            </div>
            <div style={{ marginTop: 16, padding: 16, background: verification.overall_status === 'VERIFIED' ? 'var(--success-bg)' : 'var(--error-bg)', borderRadius: 'var(--radius-md)', border: `1px solid ${verification.overall_status === 'VERIFIED' ? 'var(--success-border)' : 'var(--error-border)'}` }}>
              <div style={{ fontSize: 18, fontWeight: 800, color: verification.overall_status === 'VERIFIED' ? 'var(--success)' : 'var(--error)' }}>
                {verification.overall_status === 'VERIFIED' ? <><CheckCircle2 size={20} /> ATTRIBUTION VERIFIED</> : <><XCircle size={20} /> {verification.overall_status}</>}
              </div>
              {verification.details?.recipient_name && <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>Attributed to: <strong>{verification.details.recipient_name}</strong></div>}
            </div>
          </div>
        )}

        {report && (
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header"><div className="card-title"><BookOpen size={16} /> Forensic Report</div></div>
            <div className="config-grid">
              <ConfigItem label="Report ID" value={report.report_id?.slice(0, 12) + '...'} />
              <ConfigItem label="Generated" value={report.generated_at ? new Date(report.generated_at).toLocaleString() : '-'} />
              <ConfigItem label="Attribution" value={report.attribution?.status || 'N/A'} />
              <ConfigItem label="Confidence" value={report.attribution?.confidence || 'N/A'} />
              {report.attribution?.recipient_name && <ConfigItem label="Recipient" value={report.attribution.recipient_name} />}
              {report.attribution?.session_id && <ConfigItem label="Session" value={report.attribution.session_id.slice(0, 12) + '...'} />}
            </div>
            {report.limitations && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--warning)', marginBottom: 8 }}>⚠ Limitations</div>
                {report.limitations.map((l, i) => <div key={i} style={{ fontSize: 12, color: 'var(--text-muted)', padding: '2px 0' }}>• {l}</div>)}
              </div>
            )}
          </div>
        )}

        {invs.length > 0 && (
          <div className="card">
            <div className="card-header"><div className="card-title"><FileSearch size={16} /> Previous Investigations ({invs.length})</div></div>
            <div className="table-container">
              <table>
                <thead><tr><th>Investigation</th><th>File</th><th>Extraction</th><th>Verification</th><th>Created</th></tr></thead>
                <tbody>
                  {invs.map(inv => (
                    <tr key={inv.investigation_id}>
                      <td><span className="hash-display">{inv.investigation_id.slice(0, 12)}...</span></td>
                      <td>{inv.input_filename || '-'}</td>
                      <td><span className={`badge ${inv.extracted_watermark_status === 'extracted' ? 'badge-success' : inv.extracted_watermark_status === 'failed' ? 'badge-error' : 'badge-warning'}`}>{inv.extracted_watermark_status}</span></td>
                      <td><span className={`badge ${inv.verification_status === 'VERIFIED' ? 'badge-success' : inv.verification_status === 'FAILED' ? 'badge-error' : 'badge-neutral'}`}>{inv.verification_status || 'pending'}</span></td>
                      <td style={{ fontSize: 12 }}>{inv.created_at ? new Date(inv.created_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

function TimelineStep({ name, status, detail }) {
  return (
    <div className="timeline-item">
      <div className={`timeline-dot ${status}`} />
      <div className="timeline-title">{name}</div>
      {detail && <div className="timeline-detail">{detail}</div>}
    </div>
  );
}

function VerificationItem({ label, status }) {
  const s = status || 'pending';
  const icon = s === 'VERIFIED' ? <CheckCircle2 size={18} /> : s === 'FAILED' ? <XCircle size={18} /> : <Clock size={18} />;
  const cls = s === 'VERIFIED' ? 'verified' : s === 'FAILED' ? 'failed' : 'pending';
  return (
    <div className="verification-item">
      <div className={`verification-icon ${cls}`}>{icon}</div>
      <div>
        <div className="verification-label">{label}</div>
        <div className={`verification-status`} style={{ color: s === 'VERIFIED' ? 'var(--success)' : s === 'FAILED' ? 'var(--error)' : 'var(--warning)' }}>{s}</div>
      </div>
    </div>
  );
}

// ===== VERIFICATION CENTER =====
function Verification({ toast }) {
  const [eventId, setEventId] = useState('');
  const [docId, setDocId] = useState('');
  const [blockIdx, setBlockIdx] = useState('0');
  const [result, setResult] = useState(null);
  const [resultType, setResultType] = useState('');

  const verifySig = async () => {
    if (!eventId) return toast.error('Enter an event ID');
    try { const r = await api.verifySignature(eventId); setResult(r); setResultType('signature'); toast.success('Signature verification complete'); } catch (e) { toast.error(e.message); }
  };
  const verifyDoc = async () => {
    if (!docId) return toast.error('Enter a document ID');
    try { const r = await api.verifyDocHash(docId); setResult(r); setResultType('document'); toast.success('Document hash verification complete'); } catch (e) { toast.error(e.message); }
  };
  const verifyChain = async () => {
    try { const r = await api.verifyChain(); setResult(r); setResultType('chain'); toast.success('Chain verification complete'); } catch (e) { toast.error(e.message); }
  };
  const verifyMerkle = async () => {
    try { const r = await api.verifyMerkle(parseInt(blockIdx) || 0); setResult(r); setResultType('merkle'); toast.success('Merkle proof verified'); } catch (e) { toast.error(e.message); }
  };

  return (
    <>
      <div className="page-header">
        <h2>Cryptographic Verification Center</h2>
        <p>Independently verify signatures, hashes, Merkle proofs, and ledger integrity</p>
      </div>
      <div className="page-body">
        <div className="grid-2" style={{ marginBottom: 24 }}>
          <div className="card">
            <div className="card-header"><div className="card-title"><Fingerprint size={16} /> ML-DSA Signature Verification</div></div>
            <div className="input-group">
              <label className="input-label">Event ID</label>
              <input className="input" placeholder="Enter event ID" value={eventId} onChange={e => setEventId(e.target.value)} />
            </div>
            <button className="btn btn-primary btn-sm" onClick={verifySig}><ShieldCheck size={14} /> Verify Signature</button>
          </div>
          <div className="card">
            <div className="card-header"><div className="card-title"><Hash size={16} /> Document Hash Verification</div></div>
            <div className="input-group">
              <label className="input-label">Document ID</label>
              <input className="input" placeholder="Enter document ID" value={docId} onChange={e => setDocId(e.target.value)} />
            </div>
            <button className="btn btn-primary btn-sm" onClick={verifyDoc}><ShieldCheck size={14} /> Verify Hash</button>
          </div>
          <div className="card">
            <div className="card-header"><div className="card-title"><Database size={16} /> Ledger Chain Verification</div></div>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>Verify the integrity of all validator chains and cross-validate consistency.</p>
            <button className="btn btn-primary btn-sm" onClick={verifyChain}><ShieldCheck size={14} /> Verify All Chains</button>
          </div>
          <div className="card">
            <div className="card-header"><div className="card-title"><Hash size={16} /> Merkle Proof Verification</div></div>
            <div className="input-group">
              <label className="input-label">Block Index</label>
              <input className="input" type="number" min="0" value={blockIdx} onChange={e => setBlockIdx(e.target.value)} />
            </div>
            <button className="btn btn-primary btn-sm" onClick={verifyMerkle}><ShieldCheck size={14} /> Verify Merkle Proof</button>
          </div>
        </div>

        {result && (
          <div className="card">
            <div className="card-header"><div className="card-title"><Eye size={16} /> Verification Result — {resultType.toUpperCase()}</div></div>
            <pre style={{ background: 'var(--bg-input)', padding: 16, borderRadius: 'var(--radius-md)', fontSize: 12, fontFamily: "'JetBrains Mono', monospace", color: 'var(--text-secondary)', overflow: 'auto', whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </>
  );
}

// ===== SYSTEM CONFIG =====
function Config({ toast }) {
  const [config, setConfig] = useState(null);
  const [pqc, setPqc] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([api.getConfig(), api.getPqcInfo()])
      .then(([c, p]) => { setConfig(c); setPqc(p); })
      .catch(e => toast.error(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading />;

  return (
    <>
      <div className="page-header">
        <h2>System Configuration</h2>
        <p>View cryptographic settings, algorithm configuration, and system status</p>
      </div>
      <div className="page-body">
        {config && (
          <>
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header"><div className="card-title"><Settings size={16} /> Application</div></div>
              <div className="config-grid">
                <ConfigItem label="Name" value={config.app_name} />
                <ConfigItem label="Version" value={config.app_version} />
                <ConfigItem label="Offline Mode" value={config.offline_mode ? 'ENABLED' : 'DISABLED'} />
                <ConfigItem label="PQC Available" value={config.pqc_available ? 'YES' : 'NO'} />
                <ConfigItem label="PQC Library" value={config.pqc_library} />
                <ConfigItem label="Formats" value={config.supported_formats?.join(', ')} />
              </div>
            </div>
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header"><div className="card-title"><Lock size={16} /> Cryptographic Algorithms</div></div>
              <div className="config-grid">
                <ConfigItem label="Encryption" value={config.encryption_algorithm} />
                <ConfigItem label="Hash" value={config.hash_algorithm} />
                <ConfigItem label="Digital Signature" value={config.sig_algorithm} />
                <ConfigItem label="Key Encapsulation" value={config.kem_algorithm} />
                <ConfigItem label="Watermark Algorithm" value={config.watermark_algorithm_version} />
              </div>
            </div>
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header"><div className="card-title"><Server size={16} /> Ledger Configuration</div></div>
              <div className="config-grid">
                <ConfigItem label="Validator Count" value={config.ledger_validator_count} />
                <ConfigItem label="Quorum Size" value={config.ledger_quorum_size} />
              </div>
            </div>
          </>
        )}
        {pqc && (
          <div className="card">
            <div className="card-header"><div className="card-title"><KeyRound size={16} /> Post-Quantum Cryptography Details</div></div>
            <div style={{ fontSize: 13 }}>
              <div style={{ marginBottom: 12 }}>
                <strong>Signature Mechanisms:</strong>
                <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                  {(pqc.sig_mechanisms || []).map(m => <span key={m} className="badge badge-info">{m}</span>)}
                </div>
              </div>
              <div>
                <strong>KEM Mechanisms:</strong>
                <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                  {(pqc.kem_mechanisms || []).map(m => <span key={m} className="badge badge-info">{m}</span>)}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="card" style={{ marginTop: 24, borderColor: 'var(--warning-border)', background: 'var(--warning-bg)' }}>
          <div className="card-header"><div className="card-title" style={{ color: 'var(--warning)' }}><AlertTriangle size={16} /> Prototype Disclaimer</div></div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            <p>This is a research prototype. The following limitations apply:</p>
            <ul style={{ marginTop: 8, paddingLeft: 20 }}>
              <li>Private keys are stored in encrypted local files, not hardware-backed storage.</li>
              <li>The keystore password is demo-only. Production requires strong, unique passwords.</li>
              <li>The ledger provides tamper evidence, not absolute immutability.</li>
              <li>Watermark robustness has not been evaluated against all transformations.</li>
              <li>Digital signatures prove key usage, not physical identity.</li>
              <li>A production deployment requires additional security hardening.</li>
            </ul>
          </div>
        </div>
      </div>
    </>
  );
}

function ConfigItem({ label, value }) {
  return (
    <div className="config-item">
      <span className="config-key">{label}</span>
      <span className="config-value">{String(value)}</span>
    </div>
  );
}

function Loading() {
  return <div className="loading-overlay"><div className="spinner" style={{ width: 32, height: 32 }} /><span>Loading...</span></div>;
}

// ===== ANALYTICS & TRENDS =====
// Modularized into ./Analytics.jsx

// ===== APP =====
export default function App() {
  const [page, setPage] = useState('dashboard');
  const toast = useToasts();

  const pages = {
    dashboard: <Dashboard toast={toast} />,
    documents: <Documents toast={toast} />,
    recipients: <Recipients toast={toast} />,
    decryption: <Decryption toast={toast} />,
    ledger: <Ledger toast={toast} />,
    forensics: <Forensics toast={toast} />,
    verification: <Verification toast={toast} />,
    analytics: <Analytics toast={toast} />,
    config: <Config toast={toast} />,
  };

  return (
    <div className="app-layout">
      <Sidebar page={page} setPage={setPage} />
      <main className="main-content">
        {pages[page] || pages.dashboard}
      </main>
      <Toasts toasts={toast.toasts} />
    </div>
  );
}
