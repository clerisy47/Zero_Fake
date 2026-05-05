import { useEffect, useMemo, useState } from 'react';
import samplePayload from './data/samplePayload';

const endpoint = 'http://127.0.0.1:8000/kyc/submit';

function setValueAtPath(source, path, value) {
  const keys = path.split('.');
  const updated = { ...source };
  let current = updated;

  for (let i = 0; i < keys.length - 1; i += 1) {
    const key = keys[i];
    current[key] = { ...current[key] };
    current = current[key];
  }

  current[keys[keys.length - 1]] = value;
  return updated;
}

function parseValue(type, value) {
  if (type === 'checkbox') return value;
  if (type === 'number') return value === '' ? '' : Number(value);
  return value;
}

function SectionCard({ title, children }) {
  return (
    <section className="card">
      <div className="card-head">
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function App() {
  const [activePage, setActivePage] = useState('home');
  const [formData, setFormData] = useState(samplePayload);
  const [statusLabel, setStatusLabel] = useState('Ready to submit');
  const [responseData, setResponseData] = useState(null);
  const [serverStatus, setServerStatus] = useState('Checking server...');

  const previewJson = useMemo(() => JSON.stringify(formData, null, 2), [formData]);

  useEffect(() => {
    async function checkHealth() {
      try {
        const health = endpoint.replace('/kyc/submit', '/health');
        const res = await fetch(health);
        setServerStatus(res.ok ? 'Backend reachable' : 'Backend responded with error');
      } catch (err) {
        setServerStatus('Backend unreachable');
      }
    }

    checkHealth();
  }, []);

  const handleChange = (path, type) => (event) => {
    const value = type === 'checkbox' ? event.target.checked : event.target.value;
    setFormData((current) => setValueAtPath(current, path, parseValue(type, value)));
  };

  const loadSample = () => {
    setFormData(samplePayload);
    setResponseData(null);
    setStatusLabel('Sample profile loaded');
  };

  const submitKyc = async () => {
    try {
      setStatusLabel('Submitting…');
      setResponseData(null);
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || response.statusText || 'Submission failed');
      }
      setStatusLabel('Decision received');
      setResponseData(payload);
    } catch (error) {
      setStatusLabel('Submission error');
      setResponseData({ error: error.message || 'Unable to connect' });
    }
  };

  return (
    <div className="min-h-screen text-slate-900">
      <nav className="nav-bar">
        <div className="nav-container">
          <div>
            <h1 className="nav-title">KYC Fraud Detection</h1>
          </div>
          <ul className="nav-links">
            {['home', 'submit', 'docs', 'about'].map((page) => (
              <li key={page}>
                <button
                  type="button"
                  onClick={() => setActivePage(page)}
                  className={`nav-link ${activePage === page ? 'active-link' : ''}`}
                >
                  {page === 'home' ? 'Home' : page === 'submit' ? 'Submit KYC' : page === 'docs' ? 'API Docs' : 'About'}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      <main className="page-shell">
        {activePage === 'home' && (
          <div className="space-y-8">
            <section className="hero-panel">
              <div>
                <p className="eyebrow">KYC Fraud Detection</p>
                <h1 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
                  Submit a KYC profile and get instant risk decisions.
                </h1>
                <p className="hero-copy">
                  A premium interface for your fraud detection workflow. Complete the form, preview the request, and review decision outputs in a clean, modern experience.
                </p>
                <div className="hero-actions">
                  <button type="button" onClick={() => setActivePage('submit')} className="button primary">Submit KYC</button>
                  <button type="button" onClick={() => setActivePage('docs')} className="button secondary">View API Docs</button>
                </div>
              </div>

              <div className="hero-card">
                <div className="card-head"><h2>Ready to run</h2></div>
                <p className="text-slate-600">This frontend is connected to the FastAPI backend and ready for submission testing.</p>
                <ul className="hero-list">
                  <li><strong>Backend reachable:</strong> {serverStatus}</li>
                  <li><strong>Structured KYC intake:</strong> professional form-driven UX.</li>
                  <li><strong>Live preview:</strong> immediate payload and decision visibility.</li>
                </ul>
              </div>
            </section>

            <div className="grid gap-8 lg:grid-cols-[1.4fr_1fr]">
              <SectionCard title="Trusted workflow for faster KYC approvals">
                <div className="grid gap-4 sm:grid-cols-2">
                  {[
                    { title: 'Structured profile intake', description: 'Enter data in grouped fields for accuracy and better UX.' },
                    { title: 'Live payload preview', description: 'Inspect the exact request body before sending it to the API.' },
                    { title: 'Instant decision feedback', description: 'Receive fraud decisions and confidence signals in one view.' },
                    { title: 'Designed for production', description: 'Responsive layout, polished typography, and enterprise-ready form design.' },
                  ].map((item) => (
                    <article key={item.title} className="rounded-3xl border border-slate-200 bg-slate-50 p-6 shadow-sm">
                      <h3 className="text-lg font-semibold text-slate-900">{item.title}</h3>
                      <p className="mt-3 text-slate-600">{item.description}</p>
                    </article>
                  ))}
                </div>
              </SectionCard>
              <SectionCard title="Deployment hints">
                <div className="space-y-4 text-slate-600">
                  <p className="rounded-3xl bg-slate-100 p-4 font-medium text-slate-800">
                    Backend URL: <code className="rounded bg-slate-200 px-2 py-1">http://127.0.0.1:8000/kyc/submit</code>
                  </p>
                  <p>Open the Submit section to work with the form and preview the JSON request body. Use the sample profile loader as a starting point.</p>
                  <div className="rounded-3xl bg-white p-4 shadow-sm">
                    <h3 className="text-base font-semibold text-slate-900">Server status</h3>
                    <p className="mt-2 text-slate-600">{serverStatus}</p>
                  </div>
                </div>
              </SectionCard>
            </div>
          </div>
        )}

        {activePage === 'submit' && (
          <div className="grid gap-8 xl:grid-cols-[1.2fr_0.8fr]">
            <SectionCard title="Applicant profile submission">
              <div className="space-y-8">
                <div className="grid gap-6 md:grid-cols-2">
                  <fieldset className="space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-6">
                    <legend className="px-2 text-sm font-semibold text-slate-900">Submission</legend>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>Submission ID</span>
                      <input name="submission_id" value={formData.submission_id} onChange={handleChange('submission_id', 'text')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                    </label>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>Channel</span>
                      <select name="channel" value={formData.channel} onChange={handleChange('channel', 'text')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900">
                        <option value="web">Web</option>
                        <option value="mobile">Mobile</option>
                        <option value="partner">Partner</option>
                      </select>
                    </label>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>Claimed country</span>
                      <input name="claimed_country" value={formData.claimed_country} onChange={handleChange('claimed_country', 'text')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                    </label>
                  </fieldset>

                  <fieldset className="space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-6">
                    <legend className="px-2 text-sm font-semibold text-slate-900">Device & network</legend>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>Device ID</span>
                      <input name="device_id" value={formData.device.device_id} onChange={handleChange('device.device_id', 'text')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                    </label>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>Recent submissions</span>
                      <input name="known_recent_submission_count" type="number" value={formData.device.known_recent_submission_count} onChange={handleChange('device.known_recent_submission_count', 'number')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                    </label>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>IP address</span>
                      <input name="ip" value={formData.network.ip} onChange={handleChange('network.ip', 'text')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                    </label>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <label className="space-y-2 text-sm text-slate-700">
                        <span>VPN detected</span>
                        <input type="checkbox" checked={formData.network.is_vpn} onChange={handleChange('network.is_vpn', 'checkbox')} className="h-5 w-5 rounded border-slate-300 text-slate-900" />
                      </label>
                      <label className="space-y-2 text-sm text-slate-700">
                        <span>Tor detected</span>
                        <input type="checkbox" checked={formData.network.is_tor} onChange={handleChange('network.is_tor', 'checkbox')} className="h-5 w-5 rounded border-slate-300 text-slate-900" />
                      </label>
                    </div>
                  </fieldset>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                  <fieldset className="space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-6">
                    <legend className="px-2 text-sm font-semibold text-slate-900">Document analysis</legend>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>Document type</span>
                      <select value={formData.document.document_type} onChange={handleChange('document.document_type', 'text')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900">
                        <option value="passport">Passport</option>
                        <option value="id_card">ID card</option>
                        <option value="driver_license">Driver license</option>
                      </select>
                    </label>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>Issuing country</span>
                      <input value={formData.document.issuing_country} onChange={handleChange('document.issuing_country', 'text')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                    </label>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>Full name</span>
                      <input value={formData.document.full_name} onChange={handleChange('document.full_name', 'text')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                    </label>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <label className="space-y-2 text-sm text-slate-700">
                        <span>DOB</span>
                        <input type="date" value={formData.document.dob} onChange={handleChange('document.dob', 'text')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                      </label>
                      <label className="space-y-2 text-sm text-slate-700">
                        <span>Expiry</span>
                        <input type="date" value={formData.document.expiry} onChange={handleChange('document.expiry', 'text')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                      </label>
                    </div>
                  </fieldset>

                  <fieldset className="space-y-4 rounded-3xl border border-slate-200 bg-slate-50 p-6">
                    <legend className="px-2 text-sm font-semibold text-slate-900">Biometrics</legend>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>Liveness score</span>
                      <input type="number" step="0.01" min="0" max="1" value={formData.biometric.liveness_score} onChange={handleChange('biometric.liveness_score', 'number')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                    </label>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>Face similarity</span>
                      <input type="number" step="0.01" min="0" max="1" value={formData.biometric.face_similarity_score} onChange={handleChange('biometric.face_similarity_score', 'number')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                    </label>
                    <label className="space-y-2 text-sm text-slate-700">
                      <span>Deepfake score</span>
                      <input type="number" step="0.01" min="0" max="1" value={formData.biometric.deepfake_score} onChange={handleChange('biometric.deepfake_score', 'number')} className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-900" />
                    </label>
                    <label className="inline-flex items-center gap-3 text-sm text-slate-700">
                      <input type="checkbox" checked={formData.biometric.camera_injection_detected} onChange={handleChange('biometric.camera_injection_detected', 'checkbox')} className="h-5 w-5 rounded border-slate-300 text-slate-900" />
                      Camera injection detected
                    </label>
                  </fieldset>
                </div>

                <div className="flex flex-wrap items-center gap-4">
                  <button type="button" onClick={loadSample} className="rounded-full bg-slate-100 px-6 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-200">
                    Load sample profile
                  </button>
                  <button type="button" onClick={submitKyc} className="rounded-full bg-slate-950 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-slate-950/10 transition hover:bg-slate-800">
                    Submit profile
                  </button>
                </div>
              </div>
            </SectionCard>

            <div className="space-y-6">
              <SectionCard title="Request preview">
                <pre className="max-h-[520px] overflow-auto rounded-3xl bg-slate-950/95 p-6 text-sm text-slate-100">
                  {previewJson}
                </pre>
              </SectionCard>

              <SectionCard title="Decision result">
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                  <p className="text-sm text-slate-500">Status</p>
                  <p className="mt-2 text-lg font-semibold text-slate-900">{statusLabel}</p>
                </div>
                <pre className="max-h-[300px] overflow-auto rounded-3xl bg-slate-950/95 p-6 text-sm text-slate-100">
                  {responseData ? JSON.stringify(responseData, null, 2) : 'Submit a profile to view decision data.'}
                </pre>
              </SectionCard>
            </div>
          </div>
        )}

        {activePage === 'docs' && (
          <div className="grid gap-8 lg:grid-cols-2">
            <SectionCard title="API contract">
              <div className="space-y-5 text-slate-600">
                <div>
                  <h3 className="font-semibold text-slate-900">GET /health</h3>
                  <p className="mt-2">Returns the backend health status.</p>
                  <pre className="mt-3 rounded-3xl bg-slate-950/95 p-4 text-sm text-slate-100">{'{"status":"ok"}'}</pre>
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">POST /kyc/submit</h3>
                  <p className="mt-2">Send the full applicant payload generated by the form.</p>
                  <pre className="mt-3 max-h-64 overflow-auto rounded-3xl bg-slate-950/95 p-4 text-sm text-slate-100">{previewJson}</pre>
                </div>
              </div>
            </SectionCard>
            <SectionCard title="Best practices">
              <ul className="space-y-4 text-slate-600">
                <li className="rounded-3xl bg-slate-50 p-5 shadow-sm">
                  <strong className="text-slate-900">Keep payload complete.</strong> Missing fields can reduce decision accuracy.
                </li>
                <li className="rounded-3xl bg-slate-50 p-5 shadow-sm">
                  <strong className="text-slate-900">Use the sample loader.</strong> It provides a valid submission template for quick testing.
                </li>
                <li className="rounded-3xl bg-slate-50 p-5 shadow-sm">
                  <strong className="text-slate-900">Run backend locally.</strong> The UI expects <code className="rounded bg-slate-100 px-1 py-0.5">http://127.0.0.1:8000</code> by default.
                </li>
              </ul>
            </SectionCard>
          </div>
        )}

        {activePage === 'about' && (
          <div className="space-y-8">
            <SectionCard title="About the platform">
              <p className="text-slate-600">
                This interface is designed as a professional frontend for the KYC fraud detection pipeline. Data is entered through grouped fields, not raw JSON, and the result experience is polished for production demo usage.
              </p>
            </SectionCard>
            <SectionCard title="Decision outcomes">
              <div className="grid gap-4 sm:grid-cols-2">
                {[
                  { label: 'auto_approve', description: 'Low risk outcome. Continue onboarding.' },
                  { label: 'step_up_verification', description: 'Medium risk. Require extra proof.' },
                  { label: 'manual_review', description: 'High risk. Escalate to the review team.' },
                  { label: 'auto_reject', description: 'Very high risk. Reject automatically.' },
                ].map((item) => (
                  <div key={item.label} className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                    <p className="font-semibold text-slate-900">{item.label}</p>
                    <p className="mt-2 text-sm text-slate-600">{item.description}</p>
                  </div>
                ))}
              </div>
            </SectionCard>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
