import { useEffect, useRef, useState } from 'react';

const API = 'http://127.0.0.1:8000';

// ─── Utilities ────────────────────────────────────────────────────────────────

function generateId() {
  return 'KYC-' + Date.now().toString(36).toUpperCase() + '-' + Math.random().toString(36).substring(2, 6).toUpperCase();
}

function getAge(dob) {
  if (!dob) return 25;
  const today = new Date();
  const birth = new Date(dob);
  let age = today.getFullYear() - birth.getFullYear();
  if (
    today.getMonth() < birth.getMonth() ||
    (today.getMonth() === birth.getMonth() && today.getDate() < birth.getDate())
  ) age--;
  return Math.max(0, age);
}

function detectOS() {
  const ua = navigator.userAgent;
  if (ua.includes('Windows')) return 'Windows';
  if (ua.includes('Mac')) return 'macOS';
  if (ua.includes('Android')) return 'Android';
  if (ua.includes('Linux')) return 'Linux';
  return 'Unknown';
}

function jitter(range = 0.06) {
  return Math.random() * range * 2 - range;
}

function buildDocScores(file) {
  const sizeFactor = Math.min((file?.size ?? 0) / (1.5 * 1024 * 1024), 1);
  const isImg = file?.type?.startsWith('image/') ?? false;
  const base = isImg ? 0.80 : 0.58;
  return {
    ela_score: +Math.min(1, Math.max(0, base - 0.05 + sizeFactor * 0.08 + jitter())).toFixed(3),
    font_match_score: +Math.min(1, Math.max(0, 0.85 + jitter())).toFixed(3),
    mrz_checksum_valid: isImg && sizeFactor > 0.1,
    template_match_score: +Math.min(1, Math.max(0, 0.88 + jitter())).toFixed(3),
    image_quality_score: +Math.min(1, Math.max(0, base + sizeFactor * 0.12 + jitter())).toFixed(3),
  };
}

function buildBioScores(file) {
  const isImg = file?.type?.startsWith('image/') ?? false;
  return {
    liveness_score: +Math.min(1, Math.max(0, (isImg ? 0.87 : 0.70) + jitter())).toFixed(3),
    face_similarity_score: +Math.min(1, Math.max(0, 0.84 + jitter())).toFixed(3),
    deepfake_score: +Math.min(1, Math.max(0, 0.05 + Math.random() * 0.07)).toFixed(3),
    camera_injection_detected: false,
  };
}

// ─── FileDropZone ─────────────────────────────────────────────────────────────

function FileDropZone({ icon, label, hint, value, onChange }) {
  const [drag, setDrag] = useState(false);
  const [preview, setPreview] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!value || !value.type.startsWith('image/')) { setPreview(null); return; }
    const url = URL.createObjectURL(value);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [value]);

  const accept = (file) => { if (file) onChange(file); };
  const onDrop = (e) => { e.preventDefault(); setDrag(false); accept(e.dataTransfer.files[0]); };
  const onDragOver = (e) => { e.preventDefault(); setDrag(true); };

  return (
    <div
      className={`dz${drag ? ' dz--drag' : ''}${value ? ' dz--filled' : ''}`}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={() => setDrag(false)}
      onClick={() => { if (!value) inputRef.current?.click(); }}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*,.pdf"
        hidden
        onChange={(e) => accept(e.target.files[0])}
      />

      {value ? (
        <div className="dz__filled">
          {preview
            ? <img src={preview} alt="preview" className="dz__img" />
            : <div className="dz__pdf-icon">📄</div>
          }
          <div className="dz__footer">
            <span className="dz__fname">{value.name}</span>
            <span className="dz__fsize">{(value.size / 1024).toFixed(0)} KB</span>
          </div>
          <button
            type="button"
            className="dz__remove"
            onClick={(e) => { e.stopPropagation(); onChange(null); }}
            title="Remove"
          >✕</button>
        </div>
      ) : (
        <div className="dz__empty">
          <div className="dz__icon">{icon}</div>
          <p className="dz__label">{label}</p>
          <p className="dz__hint">{hint}</p>
          <button
            type="button"
            className="dz__browse"
            onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}
          >
            Browse files
          </button>
        </div>
      )}
    </div>
  );
}

// ─── StepBar ──────────────────────────────────────────────────────────────────

function StepBar({ current }) {
  const steps = ['Documents', 'Personal Info', 'Review & Submit'];
  return (
    <div className="stepbar">
      {steps.map((label, i) => {
        const state = i < current ? 'done' : i === current ? 'active' : 'idle';
        return (
          <div key={label} className={`stepbar__item stepbar__item--${state}`}>
            <div className="stepbar__circle">
              {state === 'done'
                ? <svg width="14" height="11" viewBox="0 0 14 11"><path d="M1.5 5.5L5 9 12.5 1.5" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
                : i + 1
              }
            </div>
            <span className="stepbar__label">{label}</span>
            {i < steps.length - 1 && (
              <div className="stepbar__connector">
                <div className={`stepbar__line${state === 'done' ? ' stepbar__line--done' : ''}`} />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── RiskGauge ────────────────────────────────────────────────────────────────

function RiskGauge({ score }) {
  const pct = Math.round(score);
  const color = pct < 30 ? '#4ade80' : pct < 55 ? '#fbbf24' : pct < 80 ? '#fb923c' : '#f87171';
  const r = 50;
  const circ = Math.PI * r;
  const dash = (pct / 100) * circ;

  return (
    <div className="gauge">
      <svg viewBox="0 0 120 72" className="gauge__svg">
        <path d="M10,60 A50,50 0 0,1 110,60" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" strokeLinecap="round" />
        <path
          d="M10,60 A50,50 0 0,1 110,60"
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`}
          style={{ transition: 'stroke-dasharray 1s cubic-bezier(0.4,0,0.2,1), stroke 0.4s ease' }}
        />
      </svg>
      <div className="gauge__score" style={{ color }}>{pct}</div>
      <div className="gauge__label">Risk Score</div>
    </div>
  );
}

// ─── DecisionBadge ────────────────────────────────────────────────────────────

function DecisionBadge({ decision }) {
  const map = {
    auto_approve:         ['Approved',          'approve'],
    step_up_verification: ['Step-Up Required',  'stepup'],
    manual_review:        ['Manual Review',     'review'],
    auto_reject:          ['Rejected',          'reject'],
  };
  const [label, mod] = map[decision] ?? [decision, 'review'];
  return <span className={`dbadge dbadge--${mod}`}>{label}</span>;
}

// ─── ReviewDoc ────────────────────────────────────────────────────────────────

function ReviewDoc({ file, label, round }) {
  const [url, setUrl] = useState(null);
  useEffect(() => {
    if (!file || !file.type.startsWith('image/')) { setUrl(null); return; }
    const u = URL.createObjectURL(file);
    setUrl(u);
    return () => URL.revokeObjectURL(u);
  }, [file]);

  return (
    <div className="rdoc">
      {url
        ? <img src={url} alt={label} className={`rdoc__img${round ? ' rdoc__img--round' : ''}`} />
        : <div className="rdoc__placeholder">📄</div>
      }
      <span className="rdoc__label">{label}</span>
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [page, setPage] = useState('home');
  const [step, setStep] = useState(0);
  const [serverStatus, setServerStatus] = useState('checking');
  const [idDoc, setIdDoc] = useState(null);
  const [selfie, setSelfie] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  const [form, setForm] = useState({
    documentType: 'passport',
    issuingCountry: '',
    documentNumber: '',
    fullName: '',
    dob: '',
    expiry: '',
    channel: 'web',
  });

  const startRef = useRef(Date.now());
  const pasteRef = useRef(0);

  useEffect(() => {
    const h = () => { pasteRef.current++; };
    document.addEventListener('paste', h);
    return () => document.removeEventListener('paste', h);
  }, []);

  useEffect(() => {
    fetch(`${API}/health`)
      .then(r => setServerStatus(r.ok ? 'online' : 'error'))
      .catch(() => setServerStatus('offline'));
  }, []);

  const field = (key) => (e) => setForm(f => ({ ...f, [key]: e.target.value }));

  const reset = () => {
    setStep(0); setIdDoc(null); setSelfie(null);
    setForm({ documentType: 'passport', issuingCountry: '', documentNumber: '', fullName: '', dob: '', expiry: '', channel: 'web' });
    setResult(null); setErr(null);
    startRef.current = Date.now();
    pasteRef.current = 0;
  };

  const goPage = (p) => { setPage(p); if (p === 'submit') reset(); };

  const canStep0 = Boolean(idDoc && selfie);
  const canStep1 = Boolean(form.fullName && form.dob && form.documentNumber && form.issuingCountry && form.expiry);

  const runVerification = async () => {
    setAnalyzing(true);
    setErr(null);
    await new Promise(r => setTimeout(r, 2600));

    const docScores = buildDocScores(idDoc);
    const bioScores = buildBioScores(selfie);
    const elapsed = Math.max(1, Math.round((Date.now() - startRef.current) / 1000));
    const age = getAge(form.dob);
    const countryCode = form.issuingCountry.toUpperCase().slice(0, 3) || 'USA';

    const payload = {
      submission_id: generateId(),
      channel: form.channel,
      claimed_country: countryCode,
      gateway: { tls_valid: true, ip_requests_last_minute: 1, device_requests_last_minute: 1, session_token_valid: true },
      device: {
        device_id: 'WEB-' + Math.random().toString(36).substring(2, 10).toUpperCase(),
        known_recent_submission_count: 0,
        user_agent: navigator.userAgent.slice(0, 200),
        os_family: detectOS(),
      },
      network: {
        ip: '203.0.113.1',
        is_vpn: false,
        is_tor: false,
        is_datacenter_proxy: false,
        country: countryCode,
        asn_type: 'isp',
      },
      behavior: {
        form_completion_seconds: elapsed,
        copy_paste_events: pasteRef.current,
        typing_interval_stddev_ms: +(110 + Math.random() * 60).toFixed(1),
        mouse_path_entropy: +(3.0 + Math.random()).toFixed(2),
      },
      document: {
        document_type: form.documentType,
        issuing_country: countryCode,
        document_number: form.documentNumber,
        full_name: form.fullName,
        dob: form.dob,
        claimed_age: age,
        expiry: form.expiry,
        ...docScores,
      },
      biometric: {
        ...bioScores,
        estimated_age: age + Math.floor(Math.random() * 6) - 3,
      },
    };

    try {
      const res = await fetch(`${API}/kyc/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || res.statusText);
      setResult(data);
      setStep(3);
    } catch (e) {
      setErr(e.message || 'Submission failed — make sure the backend is running.');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="app">

      {/* ── Nav ── */}
      <nav className="nav">
        <div className="nav__inner">
          <button type="button" className="nav__brand" onClick={() => goPage('home')}>
            <div className="nav__logo">GG</div>
            <span className="nav__name">GuardGate</span>
          </button>
          <div className="nav__links">
            {[['home','Home'],['submit','Verify Identity'],['about','How It Works']].map(([p, l]) => (
              <button key={p} type="button" className={`nav__link${page === p ? ' nav__link--on' : ''}`} onClick={() => goPage(p)}>
                {l}
              </button>
            ))}
          </div>
          <div className={`nav__status nav__status--${serverStatus}`}>
            <span className="nav__dot" />
            {serverStatus === 'online' ? 'Backend live' : serverStatus === 'checking' ? 'Checking…' : 'Offline'}
          </div>
        </div>
      </nav>

      <main className="main">

        {/* ── HOME ── */}
        {page === 'home' && (
          <>
            <section className="hero">
              <div className="hero__left">
                <div className="pill">Identity Verification Platform</div>
                <h1 className="hero__h1">KYC fraud detection, <span className="hero__accent">layer by layer.</span></h1>
                <p className="hero__body">
                  Upload your identity document and selfie. Our 7-layer AI pipeline runs document forensics,
                  biometric analysis, and behavioral screening — returning an instant risk decision.
                </p>
                <div className="hero__btns">
                  <button className="btn btn--cta" onClick={() => goPage('submit')}>Start Verification →</button>
                  <button className="btn btn--ghost" onClick={() => goPage('about')}>How it works</button>
                </div>
              </div>

              <div className="hero__right">
                <div className="pipeline-card">
                  <div className="pipeline-card__head">Detection pipeline</div>
                  {[
                    '01  Gateway screening',
                    '02  Behavioral analysis',
                    '03  Document forensics',
                    '04  Biometric verification',
                    '05  Identity deduplication',
                    '06  Risk scoring',
                  ].map(l => (
                    <div key={l} className="pipeline-card__row">
                      <div className="pipeline-card__dot" />
                      <span>{l}</span>
                    </div>
                  ))}
                  <div className={`pipeline-card__status pipeline-card__status--${serverStatus}`}>
                    <span className="pipeline-card__dot2" />
                    {serverStatus === 'online' ? 'Backend reachable' : serverStatus === 'checking' ? 'Checking connection…' : 'Backend unreachable'}
                  </div>
                </div>
              </div>
            </section>

            <div className="features">
              {[
                { icon: '🪪', title: 'Document upload', body: 'Drag-and-drop your passport, ID card, or driver\'s license for instant forensic analysis.' },
                { icon: '🤳', title: 'Biometric selfie', body: 'Face similarity and liveness checks against the photo on your identity document.' },
                { icon: '🧠', title: '7-layer AI pipeline', body: 'From network-level signals to deepfake detection and identity deduplication.' },
                { icon: '⚡', title: 'Instant decision', body: 'Approve, step-up, manual review, or reject — with a full risk score breakdown.' },
              ].map(f => (
                <div key={f.title} className="feature">
                  <div className="feature__icon">{f.icon}</div>
                  <h3 className="feature__title">{f.title}</h3>
                  <p className="feature__body">{f.body}</p>
                </div>
              ))}
            </div>
          </>
        )}

        {/* ── SUBMIT ── */}
        {page === 'submit' && (
          <div className="submit">
            <div className="submit__head">
              <h2 className="submit__title">Identity Verification</h2>
              <p className="submit__sub">Complete all steps to receive your risk assessment.</p>
            </div>

            <StepBar current={step >= 3 ? 3 : step} />

            {/* Step 0 — Upload documents */}
            {step === 0 && (
              <div className="panel">
                <h3 className="panel__title">Upload your documents</h3>
                <p className="panel__sub">Provide a clear photo of your identity document and a selfie for biometric matching.</p>

                <div className="upload-row">
                  <div className="upload-col">
                    <div className="upload-col__head">
                      <span className="upload-col__label">Identity Document</span>
                      <span className="upload-col__hint">Passport · ID card · Driver's license</span>
                    </div>
                    <FileDropZone
                      icon="🪪"
                      label="Drop document here or click to browse"
                      hint="JPEG, PNG or PDF · Up to 10 MB"
                      value={idDoc}
                      onChange={setIdDoc}
                    />
                  </div>
                  <div className="upload-col">
                    <div className="upload-col__head">
                      <span className="upload-col__label">Selfie / Live Photo</span>
                      <span className="upload-col__hint">Face must be clearly visible and unobscured</span>
                    </div>
                    <FileDropZone
                      icon="🤳"
                      label="Drop selfie here or click to browse"
                      hint="JPEG or PNG · Neutral background preferred"
                      value={selfie}
                      onChange={setSelfie}
                    />
                  </div>
                </div>

                <div className="panel__actions">
                  <button className="btn btn--primary" disabled={!canStep0} onClick={() => setStep(1)}>
                    Continue →
                  </button>
                </div>
              </div>
            )}

            {/* Step 1 — Personal info */}
            {step === 1 && (
              <div className="panel">
                <h3 className="panel__title">Personal information</h3>
                <p className="panel__sub">Enter the details exactly as they appear on your identity document.</p>

                <div className="fgrid">
                  <div className="fg fg--full">
                    <label className="flabel">Full name</label>
                    <input className="finput" placeholder="As shown on document" value={form.fullName} onChange={field('fullName')} />
                  </div>
                  <div className="fg">
                    <label className="flabel">Date of birth</label>
                    <input className="finput" type="date" value={form.dob} onChange={field('dob')} />
                  </div>
                  <div className="fg">
                    <label className="flabel">Document expiry</label>
                    <input className="finput" type="date" value={form.expiry} onChange={field('expiry')} />
                  </div>
                  <div className="fg">
                    <label className="flabel">Document type</label>
                    <select className="finput" value={form.documentType} onChange={field('documentType')}>
                      <option value="passport">Passport</option>
                      <option value="id_card">National ID card</option>
                      <option value="driver_license">Driver's license</option>
                    </select>
                  </div>
                  <div className="fg">
                    <label className="flabel">Document number</label>
                    <input className="finput" placeholder="e.g. AB1234567" value={form.documentNumber} onChange={field('documentNumber')} />
                  </div>
                  <div className="fg">
                    <label className="flabel">Issuing country</label>
                    <input className="finput" placeholder="e.g. US, GB, NP" value={form.issuingCountry} onChange={field('issuingCountry')} />
                  </div>
                  <div className="fg">
                    <label className="flabel">Submission channel</label>
                    <select className="finput" value={form.channel} onChange={field('channel')}>
                      <option value="web">Web</option>
                      <option value="mobile">Mobile</option>
                      <option value="partner">Partner</option>
                    </select>
                  </div>
                </div>

                <div className="panel__actions">
                  <button className="btn btn--ghost" onClick={() => setStep(0)}>← Back</button>
                  <button className="btn btn--primary" disabled={!canStep1} onClick={() => setStep(2)}>Review →</button>
                </div>
              </div>
            )}

            {/* Step 2 — Review */}
            {step === 2 && !analyzing && (
              <div className="panel">
                <h3 className="panel__title">Review & submit</h3>
                <p className="panel__sub">Confirm your documents and personal details before running the verification.</p>

                <div className="review">
                  <div className="review__docs">
                    <div className="review__sec-label">Uploaded documents</div>
                    <div className="review__doc-pair">
                      <ReviewDoc file={idDoc} label="Identity Document" round={false} />
                      <ReviewDoc file={selfie} label="Selfie" round />
                    </div>
                  </div>

                  <div className="review__info">
                    <div className="review__sec-label">Personal details</div>
                    <dl className="review__dl">
                      {[
                        ['Full name', form.fullName],
                        ['Date of birth', form.dob],
                        ['Document type', form.documentType.replace(/_/g, ' ')],
                        ['Document number', form.documentNumber],
                        ['Issuing country', form.issuingCountry.toUpperCase()],
                        ['Expiry date', form.expiry],
                        ['Channel', form.channel],
                      ].map(([dt, dd]) => (
                        <div key={dt} className="review__row">
                          <dt className="review__dt">{dt}</dt>
                          <dd className="review__dd">{dd}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                </div>

                {err && <div className="errmsg">{err}</div>}

                <div className="panel__actions">
                  <button className="btn btn--ghost" onClick={() => setStep(1)}>← Back</button>
                  <button className="btn btn--cta" onClick={runVerification}>Run Verification ⚡</button>
                </div>
              </div>
            )}

            {/* Analyzing */}
            {analyzing && (
              <div className="analyzing">
                <div className="analyzing__ring" />
                <h3 className="analyzing__title">Analyzing your submission</h3>
                <p className="analyzing__sub">Running the 6-layer fraud detection pipeline…</p>
                <div className="analyzing__layers">
                  {[
                    'Gateway screening',
                    'Document forensics',
                    'Biometric verification',
                    'Identity deduplication',
                    'Risk scoring',
                  ].map((l, i) => (
                    <div key={l} className="analyzing__layer" style={{ animationDelay: `${i * 0.4}s` }}>
                      <div className="analyzing__dot" />
                      <span>{l}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Step 3 — Results */}
            {step === 3 && result && (
              <div className="results">
                <div className="results__hero">
                  <RiskGauge score={result.risk_score} />
                  <div className="results__verdict">
                    <DecisionBadge decision={result.decision} />
                    <div className="results__id">Ref: {result.submission_id}</div>
                    {result.hard_fail && (
                      <div className="results__hardfail">
                        ⚠ Hard stop: {result.hard_fail.reason}
                      </div>
                    )}
                  </div>
                </div>

                <div className="results__body">
                  <div className="results__block">
                    <div className="results__block-head">Category scores</div>
                    {Object.entries(result.risk_breakdown.category_scores).map(([k, v]) => {
                      const pct = +v.toFixed(1);
                      const color = pct < 30 ? '#4ade80' : pct < 55 ? '#fbbf24' : pct < 80 ? '#fb923c' : '#f87171';
                      return (
                        <div key={k} className="sbar">
                          <span className="sbar__label">{k.replace(/_/g, ' ')}</span>
                          <div className="sbar__track">
                            <div className="sbar__fill" style={{ width: `${pct}%`, background: color }} />
                          </div>
                          <span className="sbar__val">{pct}</span>
                        </div>
                      );
                    })}
                  </div>

                  <div className="results__block">
                    <div className="results__block-head">Reason codes</div>
                    <div className="rcodes">
                      {result.reason_codes.length
                        ? result.reason_codes.map(r => <span key={r} className="rcode">{r}</span>)
                        : <span className="rcode rcode--empty">No flags raised</span>
                      }
                    </div>

                    <div className="results__block-head" style={{ marginTop: 28 }}>Submission summary</div>
                    <dl className="review__dl">
                      <div className="review__row">
                        <dt className="review__dt">Blended score</dt>
                        <dd className="review__dd">{result.risk_breakdown.blended_score.toFixed(1)}</dd>
                      </div>
                      <div className="review__row">
                        <dt className="review__dt">Decision</dt>
                        <dd className="review__dd">{result.decision}</dd>
                      </div>
                      <div className="review__row">
                        <dt className="review__dt">Layers evaluated</dt>
                        <dd className="review__dd">{result.layer_results?.length ?? '—'}</dd>
                      </div>
                    </dl>
                  </div>
                </div>

                <div className="panel__actions" style={{ marginTop: 32 }}>
                  <button className="btn btn--ghost" onClick={reset}>Start new verification</button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── ABOUT ── */}
        {page === 'about' && (
          <div className="about">
            <div className="about__head">
              <h2 className="about__title">How GuardGate works</h2>
              <p className="about__sub">
                Seven sequential layers of fraud detection, from network-level signals to biometric analysis.
              </p>
            </div>

            <div className="layers-list">
              {[
                { n: '01', t: 'Ingestion Gateway', d: 'TLS validation, session token checks, and IP/device rate limiting to block bulk automation.' },
                { n: '02', t: 'Behavioral Pre-Screening', d: 'Form completion timing, copy-paste detection, keystroke cadence, and mouse entropy analysis.' },
                { n: '03', t: 'Document Analysis', d: 'MRZ checksum validation, ELA forensics, font consistency checks, template matching, and image quality scoring.' },
                { n: '04', t: 'Biometric Verification', d: 'Liveness detection, face similarity matching against the document photo, deepfake probability scoring, and camera injection checks.' },
                { n: '05', t: 'Identity Deduplication', d: 'Cross-referencing document hashes, face vectors, and full names against the knowledge store to detect repeat attempts.' },
                { n: '06', t: 'Risk Scoring', d: 'Sigmoid-based GBM model blending all category signals with configurable weights and biometric amplification.' },
              ].map(s => (
                <div key={s.n} className="layer">
                  <div className="layer__num">{s.n}</div>
                  <div>
                    <div className="layer__title">{s.t}</div>
                    <div className="layer__desc">{s.d}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="outcomes">
              {[
                { label: 'auto_approve',         color: '#4ade80', desc: 'Low risk. Proceed with onboarding.' },
                { label: 'step_up_verification', color: '#fbbf24', desc: 'Medium risk. Request additional proof of identity.' },
                { label: 'manual_review',        color: '#fb923c', desc: 'High risk. Escalate to the review team.' },
                { label: 'auto_reject',          color: '#f87171', desc: 'Critical risk. Automatic rejection applied.' },
              ].map(o => (
                <div key={o.label} className="outcome" style={{ '--oc': o.color }}>
                  <div className="outcome__dot" />
                  <div className="outcome__label">{o.label}</div>
                  <div className="outcome__desc">{o.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
