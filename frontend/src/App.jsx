import React, { useState, useEffect, useRef } from 'react';
import { 
  Users, 
  FileText, 
  ClipboardCheck, 
  Award, 
  MessageSquare, 
  Send, 
  Sparkles, 
  Search, 
  Upload, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  FileSpreadsheet, 
  Copy, 
  RefreshCw, 
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  TrendingUp,
  BrainCircuit,
  Sliders,
  ArrowRight,
  Trash2,
  UserCheck
} from 'lucide-react';

const DEFAULT_API_URL = 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('headhunting');
  const [apiUrl, setApiUrl] = useState(DEFAULT_API_URL);
  const [backendStatus, setBackendStatus] = useState({ connected: false, checking: true, data: null });
  const [showConfig, setShowConfig] = useState(false);
  
  // SESSION CANDIDATE ACCUMULATION (All candidates tested in this session)
  const [sessionCandidates, setSessionCandidates] = useState([
    {
      candidate_id: 'CAND-SARAH-JENKINS',
      technical_score: 92.0,
      hr_score: 88.0,
      interview_score: 90.8,
      gate_status: 'PASSED',
      strengths: [
        'High-Throughput Distributed Architecture with Redis (Redlock)',
        'Deep Query Diagnostics (EXPLAIN BUFFERS & Indexing)',
        'Sev-1 Incident Leadership & Post-Mortem Rigor'
      ],
      remaining_gaps: ['Secondary read-replica lag tuning under heavy load'],
      behavioral_red_flags: [],
      evaluation_confidence: 0.96,
      reasoning: 'Sarah demonstrated exceptional depth in distributed locking and production query tuning with clear blameless incident ownership.',
      probing_questions_for_manager: [
        'Ask how they handled replica drift during network partitions.',
        'Probe on engineering mentorship practices.'
      ]
    }
  ]);
  const [selectedCandidateId, setSelectedCandidateId] = useState('CAND-SARAH-JENKINS');

  const checkHealth = async () => {
    setBackendStatus(prev => ({ ...prev, checking: true }));
    try {
      const res = await fetch(`${apiUrl}/api/interview/telemetry/cache`);
      if (res.ok) {
        const data = await res.json();
        setBackendStatus({ connected: true, checking: false, data });
      } else {
        setBackendStatus({ connected: false, checking: false, data: null });
      }
    } catch (e) {
      setBackendStatus({ connected: false, checking: false, data: null });
    }
  };

  useEffect(() => {
    checkHealth();
  }, [apiUrl]);

  // Append or update candidate into session pool
  const handleAddSessionCandidate = (newCand) => {
    setSessionCandidates(prev => {
      const filtered = prev.filter(c => c.candidate_id !== newCand.candidate_id);
      return [newCand, ...filtered];
    });
    setSelectedCandidateId(newCand.candidate_id);
    setActiveTab('decision');
  };

  const handleRemoveCandidate = (candId) => {
    setSessionCandidates(prev => prev.filter(c => c.candidate_id !== candId));
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Header */}
      <header style={{
        background: '#ffffff',
        borderBottom: '1px solid var(--border-color)',
        padding: '0.85rem 2rem',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <img 
              src="/Kayfa.svg" 
              alt="Kayfa Academy" 
              style={{ height: '36px', width: 'auto', display: 'block' }} 
            />
            <div style={{ height: '24px', width: '1px', background: 'var(--border-color)' }}></div>
            <div>
              <h1 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--primary)', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                Kayfa AI Recruitment Orchestrator
                <span style={{ fontSize: '0.68rem', background: 'var(--primary-subtle)', color: 'var(--primary)', padding: '0.15rem 0.5rem', borderRadius: 'var(--radius-full)', fontWeight: 600 }}>
                  Multi-Agent Live
                </span>
              </h1>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Autonomous Headhunting, CV Screening, LLM Question Synthesis & Cumulative Decision Dossier
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div 
              onClick={checkHealth}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.8rem',
                padding: '0.35rem 0.8rem',
                borderRadius: 'var(--radius-full)',
                background: backendStatus.connected ? '#ecfdf5' : '#fef2f2',
                color: backendStatus.connected ? '#047857' : '#b91c1c',
                border: `1px solid ${backendStatus.connected ? '#a7f3d0' : '#fecaca'}`,
                cursor: 'pointer',
                fontWeight: 500
              }}
              title="Click to re-check backend connection"
            >
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: backendStatus.connected ? '#10b981' : '#ef4444',
                display: 'inline-block'
              }}></span>
              {backendStatus.checking ? 'Connecting...' : backendStatus.connected ? 'Backend Online' : 'Backend Offline'}
              <RefreshCw size={12} className={backendStatus.checking ? 'animate-spin' : ''} />
            </div>

            <button 
              onClick={() => setShowConfig(!showConfig)}
              style={{
                background: 'transparent',
                border: '1px solid var(--border-color)',
                padding: '0.35rem 0.65rem',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                fontSize: '0.8rem'
              }}
            >
              <Sliders size={14} />
              Settings
            </button>
          </div>
        </div>

        {showConfig && (
          <div style={{ maxWidth: '1400px', margin: '0.75rem auto 0', padding: '0.75rem', background: 'var(--primary-subtle)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '1rem', border: '1px solid var(--primary-border)' }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--primary)' }}>FastAPI Base URL:</span>
            <input 
              type="text" 
              value={apiUrl} 
              onChange={e => setApiUrl(e.target.value)} 
              style={{ maxWidth: '350px', padding: '0.4rem 0.75rem', fontSize: '0.85rem' }} 
            />
            <button 
              onClick={checkHealth}
              style={{ padding: '0.4rem 0.9rem', background: 'var(--primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem' }}
            >
              Test Connection
            </button>
          </div>
        )}
      </header>

      {/* Navigation Tabs */}
      <nav style={{
        background: '#ffffff',
        borderBottom: '1px solid var(--border-color)',
        padding: '0 2rem'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', gap: '0.5rem', overflowX: 'auto' }}>
          <TabButton 
            active={activeTab === 'headhunting'} 
            onClick={() => setActiveTab('headhunting')}
            icon={<Users size={17} />}
            label="1. Headhunting & Sourcing"
            badge="Groq LLM"
          />
          <TabButton 
            active={activeTab === 'screening'} 
            onClick={() => setActiveTab('screening')}
            icon={<FileText size={17} />}
            label="2. CV Screening"
            badge="Groq Async"
          />
          <TabButton 
            active={activeTab === 'interview'} 
            onClick={() => setActiveTab('interview')}
            icon={<ClipboardCheck size={17} />}
            label="3. Assessment & Interview"
            badge="Groq Synthesis & Eval"
          />
          <TabButton 
            active={activeTab === 'decision'} 
            onClick={() => setActiveTab('decision')}
            icon={<Award size={17} />}
            label="4. Decision Maker"
            badge={`${sessionCandidates.length} in Dossier`}
          />
          <TabButton 
            active={activeTab === 'chatbot'} 
            onClick={() => setActiveTab('chatbot')}
            icon={<MessageSquare size={17} />}
            label="5. Kayfa Academy Assistant"
            badge="RAG & Jobs"
          />
        </div>
      </nav>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '2rem', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
        {activeTab === 'headhunting' && <HeadhuntingTab apiUrl={apiUrl} />}
        {activeTab === 'screening' && <ScreeningTab apiUrl={apiUrl} />}
        {activeTab === 'interview' && (
          <InterviewTab 
            apiUrl={apiUrl} 
            onPassToDecision={handleAddSessionCandidate} 
          />
        )}
        {activeTab === 'decision' && (
          <DecisionTab 
            apiUrl={apiUrl} 
            candidates={sessionCandidates}
            selectedId={selectedCandidateId}
            onSelectId={setSelectedCandidateId}
            onRemove={handleRemoveCandidate}
            onGoToAssessment={() => setActiveTab('interview')}
          />
        )}
        {activeTab === 'chatbot' && <ChatbotTab apiUrl={apiUrl} />}
      </main>

      <footer style={{
        borderTop: '1px solid var(--border-color)',
        padding: '1.25rem 2rem',
        background: '#ffffff',
        textAlign: 'center',
        fontSize: '0.82rem',
        color: 'var(--text-muted)'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            Powered by <strong style={{ color: 'var(--primary)' }}>Kayfa Academy</strong> AI Pipeline Architecture
          </div>
          <div>
            FastAPI Swagger: <a href={`${apiUrl}/docs`} target="_blank" rel="noreferrer" style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 600 }}>/docs</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

function TabButton({ active, onClick, icon, label, badge }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.6rem',
        padding: '0.9rem 1.25rem',
        border: 'none',
        background: 'transparent',
        color: active ? 'var(--primary)' : 'var(--text-muted)',
        borderBottom: active ? '3px solid var(--primary)' : '3px solid transparent',
        fontWeight: active ? 700 : 500,
        fontSize: '0.92rem',
        cursor: 'pointer',
        whiteSpace: 'nowrap'
      }}
    >
      {icon}
      <span>{label}</span>
      {badge && (
        <span style={{
          fontSize: '0.68rem',
          background: active ? 'var(--primary-subtle)' : '#f1f5f9',
          color: active ? 'var(--primary)' : 'var(--text-light)',
          padding: '0.15rem 0.45rem',
          borderRadius: 'var(--radius-full)',
          fontWeight: 600
        }}>
          {badge}
        </span>
      )}
    </button>
  );
}

/* ==========================================================================
   AGENT 1: HEADHUNTING & SOURCING
   ========================================================================== */
function HeadhuntingTab({ apiUrl }) {
  const [prompt, setPrompt] = useState('Senior Python Engineer in Cairo with 3 years experience in FastAPI and MongoDB');
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState([]);
  const [jobId, setJobId] = useState('');
  const [error, setError] = useState('');
  const [outreachLoading, setOutreachLoading] = useState({});
  const [outreachMessages, setOutreachMessages] = useState({});
  const [copiedUrl, setCopiedUrl] = useState('');

  const runSourcing = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError('');
    setCandidates([]);
    setOutreachMessages({});
    try {
      const res = await fetch(`${apiUrl}/sourcing`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Failed with status ${res.status}: ${errText}`);
      }
      const data = await res.json();
      setCandidates(data);
      if (data.length > 0 && data[0].job_id) {
        setJobId(data[0].job_id);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const generateOutreach = async (cand) => {
    const pUrl = cand.profile_url;
    setOutreachLoading(prev => ({ ...prev, [pUrl]: true }));
    try {
      const res = await fetch(`${apiUrl}/outreach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobId || 'current_job',
          candidate_urls: [pUrl]
        })
      });
      if (!res.ok) throw new Error(`Outreach failed with status ${res.status}`);
      const msgs = await res.json();
      if (msgs && msgs.length > 0) {
        setOutreachMessages(prev => ({ ...prev, [pUrl]: msgs[0] }));
      }
    } catch (e) {
      alert(`Error generating outreach: ${e.message}`);
    } finally {
      setOutreachLoading(prev => ({ ...prev, [pUrl]: false }));
    }
  };

  const copyToClipboard = (text, url) => {
    navigator.clipboard.writeText(text);
    setCopiedUrl(url);
    setTimeout(() => setCopiedUrl(''), 2500);
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      <div style={{
        background: 'linear-gradient(135deg, #4652d3 0%, #3741b8 100%)',
        borderRadius: 'var(--radius-lg)',
        padding: '2rem',
        color: '#ffffff',
        boxShadow: 'var(--shadow-lg)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <BrainCircuit size={26} />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700 }}>Agent 1: Autonomous Headhunting & Sourcing</h2>
        </div>
        <p style={{ fontSize: '0.95rem', opacity: 0.9, maxWidth: '850px', lineHeight: 1.6 }}>
          Extracts structured requirements via <strong>Groq LLM</strong>, synthesizes search strategies, 
          evaluates matching profiles against multi-skill rubrics, and creates warm personalized outreach copy.
        </p>
      </div>

      <div style={{
        background: '#ffffff',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-color)',
        padding: '1.5rem',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <label style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.5rem' }}>
          Recruiter Prompt / Job Description:
        </label>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <textarea
            rows={2}
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="e.g. Senior Python Engineer in Cairo with 3 years experience in FastAPI and MongoDB..."
            style={{ flex: 1, resize: 'vertical' }}
          />
          <button
            onClick={runSourcing}
            disabled={loading}
            style={{
              background: 'var(--primary)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: '0 1.75rem',
              fontWeight: 600,
              fontSize: '0.95rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minWidth: '200px',
              justifyContent: 'center'
            }}
          >
            {loading ? (
              <>
                <RefreshCw size={18} className="animate-spin" />
                Sourcing (AI)...
              </>
            ) : (
              <>
                <Search size={18} />
                Find Candidates
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', padding: '1rem', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {candidates.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)' }}>
            Ranked Candidate Pipeline ({candidates.length} Found)
          </h3>
          {jobId && (
            <span style={{ fontSize: '0.82rem', background: '#f1f5f9', padding: '0.3rem 0.75rem', borderRadius: 'var(--radius-full)', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
              Job ID: {jobId}
            </span>
          )}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {candidates.map((item, idx) => {
          const c = item.candidate;
          const pUrl = c.profile_url;
          const outreach = outreachMessages[pUrl];
          const isOutreachLoading = outreachLoading[pUrl];

          return (
            <div key={idx} style={{
              background: '#ffffff',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-color)',
              padding: '1.5rem',
              boxShadow: 'var(--shadow-sm)',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{
                      background: 'var(--primary-subtle)',
                      color: 'var(--primary)',
                      fontWeight: 800,
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.85rem'
                    }}>
                      #{c.rank || idx + 1}
                    </span>
                    <h4 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)' }}>
                      {c.full_name}
                    </h4>
                    {c.recommended && (
                      <span style={{ background: '#ecfdf5', color: '#047857', fontSize: '0.72rem', fontWeight: 700, padding: '0.2rem 0.55rem', borderRadius: 'var(--radius-full)', border: '1px solid #a7f3d0' }}>
                        ★ AI RECOMMENDED
                      </span>
                    )}
                  </div>
                  <a 
                    href={c.profile_url} 
                    target="_blank" 
                    rel="noreferrer" 
                    style={{ fontSize: '0.82rem', color: 'var(--primary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.3rem' }}
                  >
                    {c.profile_url} <ExternalLink size={12} />
                  </a>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{
                    background: c.match_score >= 80 ? '#ecfdf5' : c.match_score >= 60 ? '#fefce8' : '#fef2f2',
                    border: `1px solid ${c.match_score >= 80 ? '#a7f3d0' : c.match_score >= 60 ? '#fef08a' : '#fecaca'}`,
                    borderRadius: 'var(--radius-md)',
                    padding: '0.4rem 0.9rem',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Match Score</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: c.match_score >= 80 ? '#047857' : c.match_score >= 60 ? '#b45309' : '#b91c1c' }}>
                      {c.match_score}%
                    </div>
                  </div>

                  <button
                    onClick={() => generateOutreach(c)}
                    disabled={isOutreachLoading}
                    style={{
                      background: 'var(--primary-subtle)',
                      color: 'var(--primary)',
                      border: '1px solid var(--primary-border)',
                      borderRadius: 'var(--radius-md)',
                      padding: '0.65rem 1rem',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem'
                    }}
                  >
                    {isOutreachLoading ? <RefreshCw size={14} className="animate-spin" /> : <Sparkles size={14} />}
                    Draft Outreach
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>Matched Skills:</span>
                {c.matched_skills && c.matched_skills.map((s, i) => (
                  <span key={i} style={{ background: '#ecfdf5', color: '#047857', fontSize: '0.78rem', padding: '0.15rem 0.6rem', borderRadius: 'var(--radius-full)', border: '1px solid #a7f3d0' }}>
                    ✓ {s}
                  </span>
                ))}
              </div>

              {outreach && (
                <div style={{
                  background: '#f8fafc',
                  border: '1px solid var(--primary-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: '1.15rem',
                  marginTop: '0.5rem'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <Sparkles size={14} /> Personalized LinkedIn Outreach Message
                    </span>
                    <button
                      onClick={() => copyToClipboard(`Subject: ${outreach.subject}

${outreach.body}`, pUrl)}
                      style={{
                        background: '#ffffff',
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-sm)',
                        padding: '0.25rem 0.6rem',
                        fontSize: '0.78rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.3rem',
                        color: copiedUrl === pUrl ? '#047857' : 'var(--text-muted)'
                      }}
                    >
                      {copiedUrl === pUrl ? <CheckCircle size={13} /> : <Copy size={13} />}
                      {copiedUrl === pUrl ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.4rem' }}>
                    Subject: {outreach.subject}
                  </div>
                  <div style={{ fontSize: '0.86rem', color: 'var(--text-muted)', whiteSpace: 'pre-line', lineHeight: 1.6 }}>
                    {outreach.body}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ==========================================================================
   AGENT 2: CV SCREENING (Real Groq Async Execution)
   ========================================================================== */
function ScreeningTab({ apiUrl }) {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState('JOB-PY-01');
  const [role, setRole] = useState('Python Backend Engineer');
  const [requiredSkills, setRequiredSkills] = useState('Python, FastAPI, MongoDB, PostgreSQL, Docker');
  const [minExp, setMinExp] = useState(2);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef();

  const handleScreenCV = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select or upload a CV file (.pdf or .docx)');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('job_id', jobId);
    formData.append('role', role);
    formData.append('required_skills', requiredSkills);
    formData.append('min_years_experience', minExp);

    try {
      const res = await fetch(`${apiUrl}/cv-screening`, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Screening failed: ${text}`);
      }
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      <div style={{
        background: 'linear-gradient(135deg, #4652d3 0%, #3741b8 100%)',
        borderRadius: 'var(--radius-lg)',
        padding: '2rem',
        color: '#ffffff',
        boxShadow: 'var(--shadow-lg)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <FileText size={26} />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700 }}>Agent 2: Deep CV Analysis & Screening</h2>
        </div>
        <p style={{ fontSize: '0.95rem', opacity: 0.9, maxWidth: '850px', lineHeight: 1.6 }}>
          Analyzes candidate resumes in <strong>PDF or DOCX</strong>, extracts skills and experience timelines, 
          and scores match feasibility live via <strong>Groq LLM</strong> without event-loop bottlenecks.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 420px) 1fr', gap: '1.75rem' }}>
        <form onSubmit={handleScreenCV} style={{
          background: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-color)',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.15rem'
        }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
            Screening Parameters
          </h3>

          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.4rem' }}>
              Upload Resume (PDF / DOCX):
            </label>
            <div 
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: '2px dashed var(--primary-border)',
                borderRadius: 'var(--radius-md)',
                padding: '1.75rem 1rem',
                textAlign: 'center',
                background: file ? '#f8fafc' : 'var(--primary-subtle)',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <input 
                ref={fileInputRef}
                type="file" 
                accept=".pdf,.docx,.txt" 
                style={{ display: 'none' }}
                onChange={e => setFile(e.target.files[0] || null)}
              />
              <Upload size={28} style={{ color: 'var(--primary)', margin: '0 auto 0.5rem' }} />
              <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--primary)' }}>
                {file ? file.name : 'Click to select candidate CV'}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Supports .pdf, .docx'}
              </div>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.25rem' }}>Job ID</label>
            <input type="text" value={jobId} onChange={e => setJobId(e.target.value)} required />
          </div>

          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.25rem' }}>Target Role</label>
            <input type="text" value={role} onChange={e => setRole(e.target.value)} required />
          </div>

          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.25rem' }}>Required Skills</label>
            <input type="text" value={requiredSkills} onChange={e => setRequiredSkills(e.target.value)} required />
          </div>

          <div>
            <label style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.25rem' }}>Min Years of Experience</label>
            <input type="number" min={0} value={minExp} onChange={e => setMinExp(Number(e.target.value))} required />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              background: 'var(--primary)',
              color: '#ffffff',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: '0.8rem',
              fontWeight: 600,
              fontSize: '0.95rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              marginTop: '0.5rem'
            }}
          >
            {loading ? <RefreshCw size={17} className="animate-spin" /> : <Sparkles size={17} />}
            {loading ? 'Screening with Groq LLM...' : 'Screen Candidate CV'}
          </button>
        </form>

        <div>
          {error && (
            <div style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#991b1b', padding: '1rem', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <AlertTriangle size={18} />
              <span>{error}</span>
            </div>
          )}

          {result ? (
            <div style={{
              background: '#ffffff',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border-color)',
              padding: '2rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.5rem',
              boxShadow: 'var(--shadow-sm)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Candidate Identifier</div>
                  <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-main)' }}>
                    {result.candidate_id}
                  </h3>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    Job Ref: {result.job_id}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span style={{
                    padding: '0.4rem 1rem',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    background: result.recommendation === 'PROCEED' ? '#ecfdf5' : result.recommendation === 'REVIEW' ? '#fefce8' : '#fef2f2',
                    color: result.recommendation === 'PROCEED' ? '#047857' : result.recommendation === 'REVIEW' ? '#b45309' : '#b91c1c',
                    border: `1px solid ${result.recommendation === 'PROCEED' ? '#a7f3d0' : result.recommendation === 'REVIEW' ? '#fef08a' : '#fecaca'}`
                  }}>
                    {result.recommendation}
                  </span>

                  <div style={{
                    background: 'var(--primary-subtle)',
                    border: '1px solid var(--primary-border)',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.5rem 1rem',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--primary)' }}>CV SCORE</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--primary)' }}>{result.cv_score}%</div>
                  </div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.4rem' }}>Skills Extracted:</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                  {result.matched_skills && result.matched_skills.map((s, i) => (
                    <span key={i} style={{ background: '#ecfdf5', color: '#047857', fontSize: '0.78rem', padding: '0.2rem 0.65rem', borderRadius: 'var(--radius-full)', border: '1px solid #a7f3d0', fontWeight: 600 }}>
                      ✓ {s}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
                <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#047857', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem' }}>
                    <CheckCircle size={15} /> Candidate Strengths
                  </div>
                  <ul style={{ paddingLeft: '1.1rem', fontSize: '0.82rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                    {result.strengths?.map((s, i) => <li key={i}>{s}</li>) || <li>None noted</li>}
                  </ul>
                </div>

                <div style={{ background: '#f8fafc', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#b91c1c', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem' }}>
                    <XCircle size={15} /> Gaps / Competency Gaps
                  </div>
                  <ul style={{ paddingLeft: '1.1rem', fontSize: '0.82rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                    {result.gaps?.map((g, i) => <li key={i}>{g}</li>) || <li>No fatal gaps</li>}
                  </ul>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.4rem' }}>
                  Groq LLM Justification:
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.6, background: 'var(--primary-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--primary-border)' }}>
                  {result.reasoning}
                </div>
              </div>
            </div>
          ) : (
            <div style={{
              background: '#ffffff',
              borderRadius: 'var(--radius-lg)',
              border: '2px dashed var(--border-color)',
              padding: '4rem 2rem',
              textAlign: 'center',
              color: 'var(--text-light)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '0.75rem'
            }}>
              <FileText size={42} style={{ opacity: 0.4 }} />
              <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>No CV Analyzed Yet</div>
              <p style={{ fontSize: '0.88rem', maxWidth: '380px' }}>
                Upload a candidate's resume to see real-time AI scoring and evaluation via Groq LLM.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ==========================================================================
   AGENT 3: ASSESSMENT & INTERVIEW (Rich Input + Groq Synthesis & Eval)
   ========================================================================== */
function InterviewTab({ apiUrl, onPassToDecision }) {
  const [mode, setMode] = useState('generator');
  
  // Comprehensive Rich Inputs for Generator
  const [candidateName, setCandidateName] = useState('Ahmed Mansour');
  const [candidateEmail, setCandidateEmail] = useState('ahmed.mansour@example.com');
  const [jobTitle, setJobTitle] = useState('Senior Python Backend Engineer');
  const [seniority, setSeniority] = useState('SENIOR');
  const [requiredSkills, setRequiredSkills] = useState('Python, FastAPI, Redis, PostgreSQL, Distributed Systems, Docker');
  const [jobDescription, setJobDescription] = useState('Design high-throughput microservices, manage distributed database locking, optimize slow PostgreSQL queries, and participate in Sev-1 on-call rotations.');
  const [cvSummary, setCvSummary] = useState('4 years of experience as Senior Backend Engineer at Swvl & Vodafone Egypt. Built payment services handling 5k req/sec with FastAPI and Redis.');
  
  const [generating, setGenerating] = useState(false);
  const [assessmentData, setAssessmentData] = useState(null);

  // Portal / Candidate Test State
  const [activeToken, setActiveToken] = useState('');
  const [tokenQuestions, setTokenQuestions] = useState([]);
  const [candidateAnswers, setCandidateAnswers] = useState({});
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState(null);

  const startAssessmentWorkflow = async () => {
    setGenerating(true);
    setAssessmentData(null);
    try {
      const candId = `CAND-${candidateName.trim().replace(/\s+/g, '-').toUpperCase()}`;
      const res = await fetch(`${apiUrl}/api/interview/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candId,
          candidate_name: candidateName,
          candidate_email: candidateEmail,
          job_id: 'JOB-ENG-01',
          job_context: {
            job_id: 'JOB-ENG-01',
            title: jobTitle,
            seniority_level: seniority,
            required_skills: requiredSkills.split(',').map(s => s.trim()).filter(Boolean),
            domain: 'Enterprise Cloud & Data Services',
            job_description: jobDescription,
            candidate_cv_summary: cvSummary
          }
        })
      });
      if (!res.ok) throw new Error(`Failed to generate assessment: ${res.status}`);
      const data = await res.json();
      setAssessmentData(data);
      setActiveToken(data.technical_link_token);
    } catch (e) {
      alert(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const loadAssessmentByToken = async () => {
    if (!activeToken.trim()) return;
    try {
      const res = await fetch(`${apiUrl}/api/candidate/assessment/${activeToken}`);
      if (!res.ok) throw new Error('Invalid assessment token');
      const data = await res.json();
      setTokenQuestions(data.questions || []);
      setMode('portal');
    } catch (e) {
      alert(e.message);
    }
  };

  const submitAssessment = async () => {
    setEvaluating(true);
    setEvalResult(null);

    const formattedAnswers = Object.entries(candidateAnswers).map(([qid, val]) => ({
      question_id: qid,
      selected_option: typeof val === 'string' && val.length < 90 ? val : null,
      answer_text: val
    }));

    const candId = assessmentData?.candidate_id || `CAND-${candidateName.trim().replace(/\s+/g, '-').toUpperCase()}`;

    try {
      const res = await fetch(`${apiUrl}/api/candidate/assessment/${activeToken}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candId,
          answers: formattedAnswers
        })
      });
      if (!res.ok) throw new Error('Evaluation submission failed');
      const data = await res.json();
      setEvalResult(data.interview_output);
    } catch (e) {
      alert(e.message);
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      <div style={{
        background: 'linear-gradient(135deg, #4652d3 0%, #3741b8 100%)',
        borderRadius: 'var(--radius-lg)',
        padding: '2rem',
        color: '#ffffff',
        boxShadow: 'var(--shadow-lg)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <ClipboardCheck size={26} />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700 }}>Agent 3: Dynamic LLM Question Synthesis & Evaluation</h2>
        </div>
        <p style={{ fontSize: '0.95rem', opacity: 0.9, maxWidth: '900px', lineHeight: 1.6 }}>
          Uses <strong>Groq LLM</strong> to synthesize tailored questions directly from the candidate's profile, role, and JD. 
          When answers are submitted, <strong>Groq LLM</strong> rigorously evaluates technical depth, anti-cheat signals, and dynamically names the candidate output.
        </p>

        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.25rem' }}>
          <button
            onClick={() => setMode('generator')}
            style={{
              padding: '0.45rem 1rem',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              background: mode === 'generator' ? '#ffffff' : 'rgba(255,255,255,0.2)',
              color: mode === 'generator' ? 'var(--primary)' : '#ffffff',
              fontWeight: 700,
              fontSize: '0.85rem'
            }}
          >
            1. Recruiter Dispatch (Synthesize Questions)
          </button>
          <button
            onClick={() => setMode('portal')}
            style={{
              padding: '0.45rem 1rem',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              background: mode === 'portal' ? '#ffffff' : 'rgba(255,255,255,0.2)',
              color: mode === 'portal' ? 'var(--primary)' : '#ffffff',
              fontWeight: 700,
              fontSize: '0.85rem'
            }}
          >
            2. Candidate Assessment Portal (Answer & Evaluate)
          </button>
        </div>
      </div>

      {mode === 'generator' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(380px, 480px) 1fr', gap: '1.75rem' }}>
          {/* Rich Inputs Form */}
          <div style={{
            background: '#ffffff',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-color)',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Candidate & Assessment Blueprint
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.2rem' }}>Candidate True Name</label>
                <input type="text" value={candidateName} onChange={e => setCandidateName(e.target.value)} placeholder="e.g. Ahmed Mansour" />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.2rem' }}>Candidate Email</label>
                <input type="email" value={candidateEmail} onChange={e => setCandidateEmail(e.target.value)} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.2rem' }}>Target Role</label>
                <input type="text" value={jobTitle} onChange={e => setJobTitle(e.target.value)} />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.2rem' }}>Seniority Tier</label>
                <select value={seniority} onChange={e => setSeniority(e.target.value)}>
                  <option value="JUNIOR">Junior</option>
                  <option value="MID">Mid-Level</option>
                  <option value="SENIOR">Senior</option>
                  <option value="STAFF_PRINCIPAL">Staff / Principal</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.2rem' }}>Required Skills & Tech Stack</label>
              <input type="text" value={requiredSkills} onChange={e => setRequiredSkills(e.target.value)} />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.2rem' }}>Job Context & Core Responsibilities</label>
              <textarea rows={2} value={jobDescription} onChange={e => setJobDescription(e.target.value)} />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-main)', display: 'block', marginBottom: '0.2rem' }}>Candidate Background / CV Focus (for personalized questions)</label>
              <textarea rows={2} value={cvSummary} onChange={e => setCvSummary(e.target.value)} />
            </div>

            <button
              onClick={startAssessmentWorkflow}
              disabled={generating}
              style={{
                background: 'var(--primary)',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                padding: '0.85rem',
                fontWeight: 700,
                fontSize: '0.95rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                marginTop: '0.35rem'
              }}
            >
              {generating ? <RefreshCw size={17} className="animate-spin" /> : <Sparkles size={17} />}
              {generating ? 'Groq LLM Synthesizing Questions...' : 'Synthesize Assessment with Groq LLM'}
            </button>
          </div>

          {/* Generated Questions Panel */}
          <div>
            {assessmentData ? (
              <div style={{
                background: '#ffffff',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-color)',
                padding: '1.75rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.25rem',
                boxShadow: 'var(--shadow-sm)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-main)' }}>
                      Questions Synthesized for {assessmentData.candidate_name || candidateName}
                    </h3>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Assigned ID: <strong>{assessmentData.candidate_id}</strong>
                    </div>
                  </div>
                  <span style={{ fontSize: '0.78rem', background: '#ecfdf5', color: '#047857', padding: '0.3rem 0.75rem', borderRadius: 'var(--radius-full)', fontWeight: 700, border: '1px solid #a7f3d0' }}>
                    {assessmentData.status}
                  </span>
                </div>

                <div style={{ background: 'var(--primary-subtle)', border: '1px solid var(--primary-border)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
                  <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '0.5rem' }}>
                    Signed 72-Hour Access Tokens:
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.82rem' }}>
                    <div>
                      <span style={{ fontWeight: 600 }}>Technical Assessment Token:</span>
                      <div style={{ fontFamily: 'monospace', background: '#ffffff', padding: '0.3rem 0.6rem', borderRadius: '4px', marginTop: '0.2rem', wordBreak: 'break-all' }}>
                        {assessmentData.technical_link_token}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setTokenQuestions(assessmentData.questions || []);
                      setMode('portal');
                    }}
                    style={{
                      background: 'var(--primary)',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: 'var(--radius-sm)',
                      padding: '0.5rem 1rem',
                      fontWeight: 600,
                      fontSize: '0.85rem',
                      marginTop: '0.8rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem'
                    }}
                  >
                    Open in Candidate Portal to Take Assessment <ChevronRight size={14} />
                  </button>
                </div>

                <div>
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.6rem' }}>
                    Synthesized Questions ({assessmentData.questions?.length || 0})
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {assessmentData.questions?.map((q, i) => (
                      <div key={i} style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '0.9rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.3rem' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--primary)', fontFamily: 'monospace' }}>
                            {q.question_id} • {q.track} ({q.question_type.toUpperCase()})
                          </span>
                          <span style={{ fontSize: '0.72rem', background: '#f1f5f9', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
                            Weight: {q.weight}x
                          </span>
                        </div>
                        <p style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-main)' }}>{q.prompt}</p>
                        {q.options && (
                          <div style={{ marginTop: '0.4rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            Options: {q.options.join(' • ')}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div style={{
                background: '#ffffff',
                borderRadius: 'var(--radius-lg)',
                border: '2px dashed var(--border-color)',
                padding: '4rem 2rem',
                textAlign: 'center',
                color: 'var(--text-light)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.75rem'
              }}>
                <ClipboardCheck size={42} style={{ opacity: 0.4 }} />
                <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>No Assessment Initialized</div>
                <p style={{ fontSize: '0.88rem', maxWidth: '380px' }}>
                  Fill in the blueprint parameters and click "Synthesize Assessment with Groq LLM".
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Candidate Portal Mode */
        <div style={{ background: '#ffffff', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-color)', padding: '2rem' }}>
          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '2rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--border-color)' }}>
            <input 
              type="text"
              placeholder="Paste Candidate Assessment Token..."
              value={activeToken}
              onChange={e => setActiveToken(e.target.value)}
              style={{ flex: 1, fontFamily: 'monospace' }}
            />
            <button
              onClick={loadAssessmentByToken}
              style={{
                background: 'var(--primary)',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                padding: '0 1.5rem',
                fontWeight: 600
              }}
            >
              Load Questions
            </button>
          </div>

          {tokenQuestions.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  Assessment Questions for {candidateName}
                </div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{tokenQuestions.length} Questions</span>
              </div>

              {tokenQuestions.map((q, idx) => (
                <div key={idx} style={{ background: '#f8fafc', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '0.35rem' }}>
                    QUESTION {idx + 1}: {q.question_id} ({q.track})
                  </div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.75rem' }}>
                    {q.prompt}
                  </div>

                  {q.question_type === 'mcq' && q.options ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      {q.options.map((opt, optIdx) => (
                        <label key={optIdx} style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          background: candidateAnswers[q.question_id] === opt ? 'var(--primary-subtle)' : '#ffffff',
                          border: `1px solid ${candidateAnswers[q.question_id] === opt ? 'var(--primary)' : 'var(--border-color)'}`,
                          padding: '0.65rem 0.9rem',
                          borderRadius: 'var(--radius-sm)',
                          cursor: 'pointer',
                          fontSize: '0.88rem'
                        }}>
                          <input 
                            type="radio" 
                            name={q.question_id} 
                            value={opt}
                            checked={candidateAnswers[q.question_id] === opt}
                            onChange={() => setCandidateAnswers(prev => ({ ...prev, [q.question_id]: opt }))}
                            style={{ width: 'auto' }}
                          />
                          <span>{opt}</span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <textarea 
                      rows={4}
                      placeholder="Type your comprehensive engineering or leadership response here..."
                      value={candidateAnswers[q.question_id] || ''}
                      onChange={e => setCandidateAnswers(prev => ({ ...prev, [q.question_id]: e.target.value }))}
                    />
                  )}
                </div>
              ))}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                <button
                  onClick={submitAssessment}
                  disabled={evaluating}
                  style={{
                    background: 'var(--primary)',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.85rem 2rem',
                    fontWeight: 700,
                    fontSize: '1rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}
                >
                  {evaluating ? <RefreshCw size={18} className="animate-spin" /> : <ShieldCheck size={18} />}
                  {evaluating ? 'Groq LLM Evaluating Answers...' : 'Submit Answers (Groq LLM Evaluation)'}
                </button>
              </div>

              {/* Evaluation Outcome Box */}
              {evalResult && (
                <div style={{
                  background: '#ffffff',
                  border: '2px solid var(--primary)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '1.75rem',
                  marginTop: '1rem'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                    <div>
                      <h4 style={{ fontSize: '1.25rem', fontWeight: 800 }}>
                        Candidate: <span style={{ color: 'var(--primary)' }}>{evalResult.candidate_id}</span>
                      </h4>
                      <div style={{ fontSize: '0.9rem', marginTop: '0.2rem' }}>
                        Gate Status: <strong style={{ color: evalResult.gate_status === 'PASSED' ? '#047857' : '#b91c1c' }}>{evalResult.gate_status}</strong>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                      <div style={{ textAlign: 'center', background: '#f8fafc', padding: '0.5rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                        <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)' }}>TECH SCORE</div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--primary)' }}>{evalResult.technical_score}%</div>
                      </div>
                      <div style={{ textAlign: 'center', background: '#f8fafc', padding: '0.5rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                        <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-muted)' }}>HR SCORE</div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#0ea5e9' }}>{evalResult.hr_score}%</div>
                      </div>
                      <div style={{ textAlign: 'center', background: 'var(--primary-subtle)', padding: '0.5rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--primary-border)' }}>
                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--primary)' }}>COMPOSITE</div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--primary)' }}>{evalResult.interview_score}%</div>
                      </div>
                    </div>
                  </div>

                  <div style={{ fontSize: '0.9rem', color: 'var(--text-main)', lineHeight: 1.6, background: '#f8fafc', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem' }}>
                    <strong>Groq Executive Reasoning:</strong> {evalResult.reasoning}
                  </div>

                  {/* Strengths & Gaps */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem', fontSize: '0.85rem' }}>
                    <div style={{ background: '#ecfdf5', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid #a7f3d0' }}>
                      <strong style={{ color: '#047857' }}>Validated Strengths:</strong>
                      <ul style={{ paddingLeft: '1.1rem', marginTop: '0.2rem' }}>
                        {evalResult.strengths?.map((s, i) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                    <div style={{ background: '#fef2f2', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid #fecaca' }}>
                      <strong style={{ color: '#b91c1c' }}>Remaining Gaps:</strong>
                      <ul style={{ paddingLeft: '1.1rem', marginTop: '0.2rem' }}>
                        {evalResult.remaining_gaps?.map((g, i) => <li key={i}>{g}</li>)}
                      </ul>
                    </div>
                  </div>

                  {/* DIRECT HANDOFF TO AGENT 4 BUTTON */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'var(--primary-subtle)',
                    border: '1px solid var(--primary-border)',
                    padding: '1rem 1.25rem',
                    borderRadius: 'var(--radius-md)'
                  }}>
                    <div>
                      <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--primary)' }}>
                        Append to Agent 4 Session Dossier
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        Adds <strong>{evalResult.candidate_id}</strong> into the cumulative Excel dossier pool.
                      </div>
                    </div>

                    <button
                      onClick={() => onPassToDecision(evalResult)}
                      style={{
                        background: 'var(--primary)',
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: 'var(--radius-md)',
                        padding: '0.65rem 1.25rem',
                        fontWeight: 700,
                        fontSize: '0.88rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                        boxShadow: 'var(--shadow-sm)'
                      }}
                    >
                      <span>Pass to Agent 4 Dossier</span>
                      <ArrowRight size={15} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: 'var(--text-light)', padding: '2rem' }}>
              Enter a signed token above to load your test questions.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ==========================================================================
   AGENT 4: DECISION MAKER & CUMULATIVE EXCEL EXPORT (Appends all session candidates)
   ========================================================================== */
function DecisionTab({ apiUrl, candidates, selectedId, onSelectId, onRemove, onGoToAssessment }) {
  const [exporting, setExporting] = useState(false);

  // Selected candidate details
  const activeCandidate = candidates.find(c => c.candidate_id === selectedId) || candidates[0] || null;

  const downloadAllExcelDossier = async () => {
    if (!candidates || candidates.length === 0) {
      alert('No candidates in session pool to export.');
      return;
    }
    setExporting(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/decision-maker/rank-and-export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(candidates)
      });
      if (!res.ok) throw new Error(`Excel export failed with status ${res.status}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `HR_Decision_Dossier_Cumulative_${candidates.length}_candidates_${Date.now()}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      alert(`Export error: ${e.message}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      <div style={{
        background: 'linear-gradient(135deg, #4652d3 0%, #3741b8 100%)',
        borderRadius: 'var(--radius-lg)',
        padding: '2rem',
        color: '#ffffff',
        boxShadow: 'var(--shadow-lg)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <Award size={26} />
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700 }}>Agent 4: Cumulative Decision Maker & Excel Dossier</h2>
        </div>
        <p style={{ fontSize: '0.95rem', opacity: 0.9, maxWidth: '850px', lineHeight: 1.6 }}>
          Appends all candidates evaluated during this session into a single cohesive hiring dossier. 
          Ranks them via <strong>SentenceTransformers</strong> vector distance, enforces behavioral vetoes, and exports an openpyxl multi-tab spreadsheet.
        </p>
      </div>

      {/* Session Candidates Pool Table */}
      <div style={{
        background: '#ffffff',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-color)',
        padding: '1.5rem',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Active Session Candidate Pool ({candidates.length} Candidates)
            </h3>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              All evaluated candidates accumulate here. When exported, all candidates are included in the Excel dossier.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={onGoToAssessment}
              style={{
                background: 'var(--primary-subtle)',
                color: 'var(--primary)',
                border: '1px solid var(--primary-border)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.45rem 0.9rem',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              + Evaluate Another Candidate in Agent 3
            </button>

            <button
              onClick={downloadAllExcelDossier}
              disabled={exporting || candidates.length === 0}
              style={{
                background: '#10b981',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                padding: '0.45rem 1.15rem',
                fontSize: '0.85rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem'
              }}
            >
              {exporting ? <RefreshCw size={14} className="animate-spin" /> : <FileSpreadsheet size={15} />}
              Export All ({candidates.length}) to Excel (.xlsx)
            </button>
          </div>
        </div>

        {/* Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ background: 'var(--primary-subtle)', borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                <th style={{ padding: '0.65rem 0.9rem', color: 'var(--primary)', fontWeight: 700 }}>Candidate Identifier</th>
                <th style={{ padding: '0.65rem 0.9rem', color: 'var(--primary)', fontWeight: 700 }}>Tech Score</th>
                <th style={{ padding: '0.65rem 0.9rem', color: 'var(--primary)', fontWeight: 700 }}>HR Score</th>
                <th style={{ padding: '0.65rem 0.9rem', color: 'var(--primary)', fontWeight: 700 }}>Composite Score</th>
                <th style={{ padding: '0.65rem 0.9rem', color: 'var(--primary)', fontWeight: 700 }}>Gate Status</th>
                <th style={{ padding: '0.65rem 0.9rem', color: 'var(--primary)', fontWeight: 700 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((c, i) => (
                <tr 
                  key={i} 
                  onClick={() => onSelectId(c.candidate_id)}
                  style={{
                    borderBottom: '1px solid var(--border-color)',
                    background: selectedId === c.candidate_id ? 'rgba(70, 82, 211, 0.06)' : 'transparent',
                    cursor: 'pointer'
                  }}
                >
                  <td style={{ padding: '0.65rem 0.9rem', fontWeight: 600 }}>
                    {c.candidate_id}
                    {selectedId === c.candidate_id && (
                      <span style={{ marginLeft: '0.5rem', fontSize: '0.7rem', background: 'var(--primary)', color: '#fff', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                        Selected
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '0.65rem 0.9rem' }}>{c.technical_score}%</td>
                  <td style={{ padding: '0.65rem 0.9rem' }}>{c.hr_score}%</td>
                  <td style={{ padding: '0.65rem 0.9rem', fontWeight: 700, color: 'var(--primary)' }}>{c.interview_score}%</td>
                  <td style={{ padding: '0.65rem 0.9rem' }}>
                    <span style={{
                      padding: '0.2rem 0.55rem',
                      borderRadius: 'var(--radius-full)',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      background: c.gate_status === 'PASSED' ? '#ecfdf5' : '#fef2f2',
                      color: c.gate_status === 'PASSED' ? '#047857' : '#b91c1c'
                    }}>
                      {c.gate_status}
                    </span>
                  </td>
                  <td style={{ padding: '0.65rem 0.9rem' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemove(c.candidate_id);
                      }}
                      style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '0.2rem' }}
                      title="Remove from session"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Candidate Details Panel */}
      {activeCandidate && (
        <div style={{
          background: '#ffffff',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-color)',
          padding: '1.75rem',
          boxShadow: 'var(--shadow-sm)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Selected Candidate Details</div>
              <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-main)' }}>
                {activeCandidate.candidate_id}
              </h3>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <div style={{ textAlign: 'center', background: '#f8fafc', padding: '0.4rem 0.8rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.68rem', fontWeight: 600, color: 'var(--text-muted)' }}>TECH</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--primary)' }}>{activeCandidate.technical_score}%</div>
              </div>
              <div style={{ textAlign: 'center', background: '#f8fafc', padding: '0.4rem 0.8rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <div style={{ fontSize: '0.68rem', fontWeight: 600, color: 'var(--text-muted)' }}>HR</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0ea5e9' }}>{activeCandidate.hr_score}%</div>
              </div>
              <div style={{ textAlign: 'center', background: 'var(--primary-subtle)', padding: '0.4rem 0.8rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--primary-border)' }}>
                <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--primary)' }}>COMPOSITE</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--primary)' }}>{activeCandidate.interview_score}%</div>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.85rem' }}>
            <div style={{ background: '#ecfdf5', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid #a7f3d0' }}>
              <strong style={{ color: '#047857' }}>Validated Strengths:</strong>
              <ul style={{ paddingLeft: '1.1rem', marginTop: '0.25rem', color: 'var(--text-muted)' }}>
                {activeCandidate.strengths?.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
            <div style={{ background: '#fef2f2', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid #fecaca' }}>
              <strong style={{ color: '#b91c1c' }}>Identified Gaps:</strong>
              <ul style={{ paddingLeft: '1.1rem', marginTop: '0.25rem', color: 'var(--text-muted)' }}>
                {activeCandidate.remaining_gaps?.map((g, i) => <li key={i}>{g}</li>)}
              </ul>
            </div>
          </div>

          <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)', background: '#f8fafc', padding: '0.9rem', borderRadius: 'var(--radius-sm)' }}>
            <strong>Executive Reasoning:</strong> {activeCandidate.reasoning}
          </div>

          {activeCandidate.probing_questions_for_manager?.length > 0 && (
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', background: 'var(--primary-subtle)', padding: '0.9rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--primary-border)' }}>
              <strong style={{ color: 'var(--primary)' }}>Probing Questions for 1-on-1:</strong>
              <ul style={{ paddingLeft: '1.1rem', marginTop: '0.25rem' }}>
                {activeCandidate.probing_questions_for_manager.map((q, i) => <li key={i}>{q}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ==========================================================================
   AGENT 5: KAYFA ACADEMY CHATBOT
   ========================================================================== */
function ChatbotTab({ apiUrl }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'أهلاً بك في منصة كيف! أنا مساعدك الذكي لاستكشاف مسارات الأكاديمية والوظائف الشاغرة. كيف يمكنني مساعدتك اليوم؟',
      tool_used: 'none',
      dialect: 'Arabic',
      referenced_jobs: []
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (e) => {
    e?.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userText }]);
    setLoading(true);

    try {
      const res = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userText })
      });
      if (!res.ok) throw new Error(`Chat error: ${res.status}`);
      const data = await res.json();
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.reply,
          tool_used: data.tool_used,
          dialect: data.detected_dialect_or_lang,
          referenced_jobs: data.referenced_jobs || [],
          sources: data.sources || []
        }
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `عذراً، حدث خطأ أثناء معالجة الطلب: ${err.message}`,
          tool_used: 'none'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', height: 'calc(100vh - 220px)' }}>
      <div style={{
        background: 'linear-gradient(135deg, #4652d3 0%, #3741b8 100%)',
        borderRadius: 'var(--radius-lg)',
        padding: '1.25rem 2rem',
        color: '#ffffff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <MessageSquare size={24} />
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Agent 5: Kayfa Academy Assistant</h2>
            <p style={{ fontSize: '0.85rem', opacity: 0.9 }}>
              Supports Dialectical Arabic & English • Automated Vector RAG • Live Vacancies Search in MongoDB Atlas
            </p>
          </div>
        </div>
      </div>

      <div style={{
        flex: 1,
        background: '#ffffff',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-color)',
        padding: '1.5rem',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        boxShadow: 'var(--shadow-sm)'
      }}>
        {messages.map((m, idx) => (
          <div key={idx} style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: m.role === 'user' ? 'flex-end' : 'flex-start'
          }}>
            <div style={{
              maxWidth: '85%',
              background: m.role === 'user' ? 'var(--primary)' : 'var(--bg-main)',
              color: m.role === 'user' ? '#ffffff' : 'var(--text-main)',
              padding: '0.9rem 1.25rem',
              borderRadius: 'var(--radius-lg)',
              fontSize: '0.92rem',
              lineHeight: 1.6,
              border: m.role === 'user' ? 'none' : '1px solid var(--border-color)',
              whiteSpace: 'pre-line'
            }}>
              {m.content}

              {m.referenced_jobs && m.referenced_jobs.length > 0 && (
                <div style={{ marginTop: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--primary)' }}>Matching Open Positions:</div>
                  {m.referenced_jobs.map((j, i) => (
                    <div key={i} style={{ background: '#ffffff', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '0.6rem', color: 'var(--text-main)' }}>
                      <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{j.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>📍 {j.location} {j.salary_range ? `• 💰 ${j.salary_range}` : ''}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {m.role === 'assistant' && (m.tool_used !== 'none' || m.dialect) && (
              <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.35rem', fontSize: '0.7rem', color: 'var(--text-light)' }}>
                {m.tool_used && m.tool_used !== 'none' && (
                  <span style={{ background: 'var(--primary-subtle)', color: 'var(--primary)', padding: '0.1rem 0.45rem', borderRadius: 'var(--radius-full)', fontWeight: 600 }}>
                    ⚡ Tool: {m.tool_used}
                  </span>
                )}
                {m.dialect && (
                  <span style={{ background: '#f1f5f9', color: 'var(--text-muted)', padding: '0.1rem 0.45rem', borderRadius: 'var(--radius-full)' }}>
                    🗣 {m.dialect}
                  </span>
                )}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary)', fontSize: '0.85rem' }}>
            <RefreshCw size={15} className="animate-spin" />
            <span>Kayfa Assistant is thinking...</span>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <form onSubmit={sendMessage} style={{ display: 'flex', gap: '0.75rem' }}>
        <input 
          type="text"
          placeholder="Ask in Arabic or English: 'ما هي مسارات الأكاديمية؟' or 'Are there any open developer jobs?'"
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={loading}
          style={{ flex: 1, padding: '0.85rem 1.15rem', fontSize: '0.95rem' }}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            background: 'var(--primary)',
            color: '#ffffff',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            padding: '0 1.5rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem'
          }}
        >
          <Send size={16} />
          Send
        </button>
      </form>
    </div>
  );
}
