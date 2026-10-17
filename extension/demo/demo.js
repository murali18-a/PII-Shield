/**
 * PII-Shield — Demo Page Logic
 *
 * Drives the full workflow: analyze → highlight → sanitize → preview → copy.
 * Communicates ONLY with the local backend at 127.0.0.1:8000.
 * Never sends original text to any external service.
 */

const API_BASE = 'http://127.0.0.1:8000/api/v1';

// ── DOM References ─────────────────────────────
const connDot = document.getElementById('conn-dot');
const connText = document.getElementById('conn-text');
const offlineWarning = document.getElementById('offline-warning');
const privacyNotice = document.getElementById('privacy-notice');
const inputText = document.getElementById('input-text');
const charCount = document.getElementById('char-count');
const policySelect = document.getElementById('policy');
const analyzeBtn = document.getElementById('analyze-btn');
const loadSampleBtn = document.getElementById('load-sample-btn');
const retryBtn = document.getElementById('retry-btn');

const emptyState = document.getElementById('empty-state');
const loading = document.getElementById('loading');
const resultsContent = document.getElementById('results-content');
const sanitizedContent = document.getElementById('sanitized-content');
const blockContent = document.getElementById('block-content');

const statDetections = document.getElementById('stat-detections');
const statCategories = document.getElementById('stat-categories');
const statTime = document.getElementById('stat-time');
const overallAction = document.getElementById('overall-action');
const detectionsList = document.getElementById('detections-list');
const highlightedText = document.getElementById('highlighted-text');

const sanitizeBtn = document.getElementById('sanitize-btn');
const sanitizedText = document.getElementById('sanitized-text');
const sessionId = document.getElementById('session-id');
const disclaimerText = document.getElementById('disclaimer-text');
const copyBtn = document.getElementById('copy-btn');
const newScanBtn = document.getElementById('new-scan-btn');

const restoreInput = document.getElementById('restore-input');
const restoreBtn = document.getElementById('restore-btn');
const restoredText = document.getElementById('restored-text');

const blockReason = document.getElementById('block-reason');

// ── State ──────────────────────────────────────
let backendOnline = false;
let lastAnalysis = null;
let lastSessionId = null;

// ── Sample Data ────────────────────────────────
const SAMPLES = [
  "Hi, I'm Jane Doe. My email is jane.doe@example.com, SSN 123-45-6789, and phone (555) 987-6543. My Aadhaar is 2345 6789 0123 and PAN is ABCPD1234E.",
  "Patient: Michael Brown, DOB: 03/14/1985, SSN: 234-56-7890, Phone: (312) 555-0147, Email: m.brown@clinic.net, IP logged: 172.16.254.1",
  "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c\nAWS key: AKIAIOSFODNN7EXAMPLE",
  "Write a cover letter for Sarah Johnson (sarah.j@gmail.com, phone 415-555-0198) applying to Acme Corp as a software engineer. Card: 4111-1111-1111-1111",
  "The weather today is sunny with a high of 75 degrees. Python is a popular programming language.",
];
let sampleIndex = 0;

// ── Init ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  checkBackend();
  inputText.addEventListener('input', onInputChange);
  analyzeBtn.addEventListener('click', doAnalyze);
  loadSampleBtn.addEventListener('click', loadSample);
  sanitizeBtn.addEventListener('click', doSanitize);
  copyBtn.addEventListener('click', doCopy);
  newScanBtn.addEventListener('click', resetUI);
  restoreBtn.addEventListener('click', doRestore);
  if (retryBtn) retryBtn.addEventListener('click', checkBackend);
});

// ── Backend Health ─────────────────────────────
async function checkBackend() {
  try {
    const resp = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
    if (resp.ok) {
      const data = await resp.json();
      backendOnline = true;
      connDot.className = 'conn-dot online';
      connText.textContent = data.presidio_loaded ? 'Engine ready (Presidio + regex)' : 'Engine ready (regex-only)';
      offlineWarning.style.display = 'none';
      analyzeBtn.disabled = !inputText.value.trim();
      return;
    }
  } catch (_) { /* fall through */ }
  backendOnline = false;
  connDot.className = 'conn-dot offline';
  connText.textContent = 'Backend offline';
  offlineWarning.style.display = 'block';
  analyzeBtn.disabled = true;
}

// ── Input Handling ─────────────────────────────
function onInputChange() {
  const len = inputText.value.length;
  charCount.textContent = `${len.toLocaleString()} / 50,000`;
  analyzeBtn.disabled = !inputText.value.trim() || !backendOnline;
}

function loadSample() {
  inputText.value = SAMPLES[sampleIndex % SAMPLES.length];
  sampleIndex++;
  onInputChange();
  resetResults();
}

// ── Analyze ────────────────────────────────────
async function doAnalyze() {
  const text = inputText.value.trim();
  if (!text || !backendOnline) return;

  showPanel('loading');
  analyzeBtn.disabled = true;

  try {
    const resp = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, policy_profile: policySelect.value }),
      signal: AbortSignal.timeout(10000),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      if (resp.status === 422 && err.detail?.error === 'request_blocked') {
        showBlocked(err.detail);
        return;
      }
      throw new Error(`API error: ${resp.status}`);
    }

    lastAnalysis = await resp.json();
    renderAnalysis(lastAnalysis, text);
    showPanel('results');

  } catch (err) {
    console.error('[PII-Shield] Analysis failed:', err);
    showPanel('empty');
    alert(`Analysis failed: ${err.message}`);
  } finally {
    analyzeBtn.disabled = false;
  }
}

// ── Render Analysis ────────────────────────────
function renderAnalysis(data, originalText) {
  // Stats
  statDetections.textContent = data.total_detections;
  statCategories.textContent = data.categories_found.length;
  statTime.textContent = data.processing_time_ms.toFixed(1);

  // Overall action badge
  overallAction.style.display = data.total_detections > 0 ? 'inline' : 'none';
  overallAction.textContent = data.overall_action;
  overallAction.className = `action-badge ${data.overall_action.toLowerCase()}`;

  // Detections list
  if (data.detections.length === 0) {
    detectionsList.innerHTML = '<div class="detection-item" style="color:var(--text-muted);justify-content:center">No PII detected — prompt is clean ✅</div>';
    sanitizeBtn.style.display = 'none';
  } else {
    detectionsList.innerHTML = data.detections.map(d => `
      <div class="detection-item">
        <span class="det-type">${d.entity_type}</span>
        <span class="det-action ${d.action.toLowerCase()}">${d.action}</span>
        <span class="det-source">${d.source}</span>
        <span class="det-score">${(d.score * 100).toFixed(0)}%</span>
      </div>
    `).join('');
    sanitizeBtn.style.display = 'flex';
  }

  // Highlighted text
  renderHighlightedText(originalText, data.detections);
}

function renderHighlightedText(text, detections) {
  if (detections.length === 0) {
    highlightedText.textContent = text;
    return;
  }

  // Sort detections by start position (descending) to build from end
  const sorted = [...detections].sort((a, b) => a.start - b.start);
  let result = '';
  let lastEnd = 0;

  for (const det of sorted) {
    // Text before this detection
    result += escapeHtml(text.slice(lastEnd, det.start));
    // Highlighted span
    const cls = det.action === 'WARN' ? 'pii-highlight warn-hl' : 'pii-highlight';
    result += `<span class="${cls}" title="${det.entity_type} (${det.action})">${escapeHtml(text.slice(det.start, det.end))}</span>`;
    lastEnd = det.end;
  }
  // Remaining text
  result += escapeHtml(text.slice(lastEnd));
  highlightedText.innerHTML = result;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ── Sanitize ───────────────────────────────────
async function doSanitize() {
  const text = inputText.value.trim();
  if (!text || !backendOnline) return;

  sanitizeBtn.disabled = true;
  sanitizeBtn.textContent = '⏳ Sanitizing…';

  try {
    const resp = await fetch(`${API_BASE}/sanitize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, policy_profile: policySelect.value }),
      signal: AbortSignal.timeout(10000),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      if (resp.status === 422 && err.detail?.error === 'request_blocked') {
        showBlocked(err.detail);
        return;
      }
      throw new Error(`Sanitize failed: ${resp.status}`);
    }

    const data = await resp.json();
    lastSessionId = data.session_id;

    // Show sanitized content
    sanitizedText.textContent = data.sanitized_text;
    sessionId.textContent = data.session_id;
    disclaimerText.textContent = data.disclaimer;

    // Pre-fill restore input
    restoreInput.value = data.sanitized_text;
    restoredText.style.display = 'none';

    showPanel('sanitized');

  } catch (err) {
    console.error('[PII-Shield] Sanitize failed:', err);
    alert(`Sanitization failed: ${err.message}`);
  } finally {
    sanitizeBtn.disabled = false;
    sanitizeBtn.innerHTML = '<span class="btn-icon">🛡️</span> Sanitize & Preview';
  }
}

// ── Block ──────────────────────────────────────
function showBlocked(detail) {
  blockReason.textContent = detail.message || 'Request blocked by policy.';
  showPanel('block');
}

// ── Copy ───────────────────────────────────────
async function doCopy() {
  const text = sanitizedText.textContent;
  try {
    await navigator.clipboard.writeText(text);
    showToast('Sanitized text copied to clipboard!');
  } catch {
    // Fallback
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showToast('Copied!');
  }
}

// ── Restore (local test only) ──────────────────
async function doRestore() {
  const text = restoreInput.value.trim();
  if (!text || !lastSessionId || !backendOnline) return;

  try {
    const resp = await fetch(`${API_BASE}/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, session_id: lastSessionId }),
      signal: AbortSignal.timeout(10000),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      restoredText.textContent = `Restore failed: ${err.detail || resp.status}`;
      restoredText.style.display = 'block';
      return;
    }

    const data = await resp.json();
    restoredText.textContent = `Restored (${data.placeholders_restored} placeholders):\n${data.restored_text}`;
    restoredText.style.display = 'block';
    lastSessionId = null; // Session consumed

  } catch (err) {
    restoredText.textContent = `Restore error: ${err.message}`;
    restoredText.style.display = 'block';
  }
}

// ── UI Helpers ─────────────────────────────────
function showPanel(which) {
  emptyState.style.display = which === 'empty' ? 'flex' : 'none';
  loading.style.display = which === 'loading' ? 'flex' : 'none';
  resultsContent.style.display = which === 'results' ? 'block' : 'none';
  sanitizedContent.style.display = which === 'sanitized' ? 'block' : 'none';
  blockContent.style.display = which === 'block' ? 'block' : 'none';
}

function resetResults() {
  showPanel('empty');
  lastAnalysis = null;
  lastSessionId = null;
}

function resetUI() {
  inputText.value = '';
  onInputChange();
  resetResults();
}

function showToast(msg) {
  let toast = document.querySelector('.toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2000);
}
