/**
 * PII-Shield — Admin Dashboard Logic
 *
 * Fetches data from the local backend API (proxied via Vite).
 * Renders overview stats, audit events, policy config, and quick test.
 * All data stays local — no external calls.
 */

const API_BASE = '/api/v1';

// ── Policy definitions (mirroring backend/policy/rules.py) ──
const POLICIES = {
  default: {
    redact: ['US_SSN', 'CREDIT_CARD', 'AWS_ACCESS_KEY', 'JWT_TOKEN', 'AADHAAR', 'PAN', 'PASSWORD', 'API_KEY'],
    warn: ['DATE_OF_BIRTH', 'US_PASSPORT'],
    block: [],
    allow: [],
    minScore: 0.5,
  },
  strict: {
    redact: ['US_SSN', 'CREDIT_CARD', 'AWS_ACCESS_KEY', 'JWT_TOKEN', 'AADHAAR', 'PAN', 'PASSWORD', 'API_KEY',
             'PHONE_NUMBER', 'EMAIL_ADDRESS', 'IP_ADDRESS', 'PERSON', 'LOCATION', 'ORGANIZATION', 'DATE_OF_BIRTH', 'US_PASSPORT'],
    warn: [],
    block: ['US_SSN', 'CREDIT_CARD', 'AADHAAR'],
    allow: [],
    minScore: 0.3,
  },
  permissive: {
    redact: ['US_SSN', 'CREDIT_CARD', 'AWS_ACCESS_KEY', 'AADHAAR', 'PAN', 'PASSWORD'],
    warn: ['EMAIL_ADDRESS', 'PHONE_NUMBER'],
    block: [],
    allow: ['LOCATION', 'DATE_OF_BIRTH', 'ORGANIZATION'],
    minScore: 0.7,
  },
};

// ── Sample prompts for quick test ──
const SAMPLES = [
  "Hi, I'm Jane Doe. My email is jane.doe@example.com, SSN 123-45-6789, and phone (555) 987-6543. My Aadhaar is 2345 6789 0123 and PAN is ABCPD1234E.",
  "Patient: Michael Brown, DOB: 03/14/1985, SSN: 234-56-7890, Phone: (312) 555-0147, Email: m.brown@clinic.net",
  "Write a cover letter for Sarah Johnson (sarah.j@gmail.com, phone 415-555-0198) applying to Acme Corp as a software engineer. Card: 4111-1111-1111-1111",
  "The weather today is sunny with a high of 75 degrees. Python is a popular programming language.",
];
let sampleIndex = 0;

// ── State ──────────────────────────────────────
let currentTab = 'overview';
let eventsPage = 1;
const EVENTS_PAGE_SIZE = 15;
let backendOnline = false;

// ── Init ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  renderPolicyCards();
  checkBackend().then(() => {
    if (backendOnline) {
      loadOverview();
      loadEvents();
    }
  });

  document.getElementById('refresh-btn')?.addEventListener('click', loadOverview);
  document.getElementById('events-refresh-btn')?.addEventListener('click', () => loadEvents());
  document.getElementById('test-btn')?.addEventListener('click', runQuickTest);
  document.getElementById('load-sample-btn')?.addEventListener('click', loadSample);

  // "View All" link in overview
  document.querySelector('.view-all')?.addEventListener('click', (e) => {
    e.preventDefault();
    switchTab('events');
  });
});

// ── Load sample ────────────────────────────────
function loadSample() {
  const textarea = document.getElementById('test-text');
  if (textarea) {
    textarea.value = SAMPLES[sampleIndex % SAMPLES.length];
    sampleIndex++;
  }
}

// ── Backend Health ─────────────────────────────
async function checkBackend() {
  const dot = document.getElementById('sidebar-dot');
  const status = document.getElementById('sidebar-status');

  try {
    const resp = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
    if (resp.ok) {
      const data = await resp.json();
      backendOnline = true;
      dot.className = 'conn-dot online';
      status.textContent = data.presidio_loaded ? 'Presidio + Regex' : 'Regex only';
      return;
    }
  } catch (_) { /* fall through */ }

  backendOnline = false;
  dot.className = 'conn-dot offline';
  status.textContent = 'Backend offline';
}

// ── Tab System ─────────────────────────────────
function setupTabs() {
  document.querySelectorAll('.nav-item').forEach((item) => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const tab = item.dataset.tab;
      if (tab) switchTab(tab);
    });
  });
}

function switchTab(tab) {
  currentTab = tab;

  document.querySelectorAll('.nav-item').forEach((n) => {
    n.classList.remove('active');
    n.setAttribute('aria-selected', 'false');
  });
  const activeNav = document.querySelector(`.nav-item[data-tab="${tab}"]`);
  if (activeNav) {
    activeNav.classList.add('active');
    activeNav.setAttribute('aria-selected', 'true');
  }

  document.querySelectorAll('.tab-content').forEach((t) => t.classList.remove('active'));
  document.getElementById(`tab-${tab}`)?.classList.add('active');

  if (tab === 'events') loadEvents();
}

// ── Overview ───────────────────────────────────
async function loadOverview() {
  if (!backendOnline) return;

  try {
    const resp = await fetch(`${API_BASE}/events?page=1&page_size=100`);
    if (!resp.ok) return;
    const data = await resp.json();

    const events = data.events;
    const totalDetections = events.reduce((sum, e) => sum + e.entity_count, 0);
    const redactCount = events.filter((e) => e.action === 'REDACT').length;
    const warnCount = events.filter((e) => e.action === 'WARN').length;
    const blockCount = events.filter((e) => e.action === 'BLOCK').length;

    setText('total-detections', totalDetections);
    setText('total-redacted', redactCount);
    setText('total-warned', warnCount);
    setText('total-blocked', blockCount);

    // Category breakdown
    const categories = {};
    events.forEach((e) => {
      e.entity_types.forEach((t) => {
        categories[t] = (categories[t] || 0) + e.entity_count;
      });
    });
    renderCategoryBars(categories);
    renderActionDonut(redactCount, warnCount, blockCount);
    renderEventsPreview(events.slice(0, 5));
  } catch (err) {
    console.error('Failed to load overview:', err);
  }
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

// ── Category Bars ──────────────────────────────
function renderCategoryBars(categories) {
  const container = document.getElementById('category-bars');
  const entries = Object.entries(categories).sort((a, b) => b[1] - a[1]);

  if (entries.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No data yet. Run a scan to see category distribution.</p></div>';
    return;
  }

  const max = Math.max(...entries.map(([, v]) => v));

  container.innerHTML = entries.slice(0, 10).map(([type, count]) => `
    <div class="category-bar-item">
      <span class="cat-label">${type}</span>
      <div class="cat-bar-wrap">
        <div class="cat-bar" style="width: ${(count / max * 100).toFixed(1)}%"></div>
      </div>
      <span class="cat-count">${count}</span>
    </div>
  `).join('');
}

// ── Action Donut ───────────────────────────────
function renderActionDonut(redact, warn, block) {
  const container = document.getElementById('action-donut');
  const total = redact + warn + block;

  if (total === 0) {
    container.innerHTML = '<div class="empty-state"><p>No actions recorded yet.</p></div>';
    return;
  }

  const r = 42, cx = 55, cy = 55, strokeWidth = 14;
  const circumference = 2 * Math.PI * r;

  const segments = [
    { label: 'Redacted', value: redact, color: '#4f46e5' },
    { label: 'Warned', value: warn, color: '#d97706' },
    { label: 'Blocked', value: block, color: '#dc2626' },
  ].filter(s => s.value > 0);

  let offset = 0;
  const circles = segments.map(s => {
    const pct = s.value / total;
    const dash = pct * circumference;
    const gap = circumference - dash;
    const circle = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${s.color}" stroke-width="${strokeWidth}"
      stroke-dasharray="${dash} ${gap}" stroke-dashoffset="${-offset}" stroke-linecap="round"/>`;
    offset += dash;
    return circle;
  }).join('');

  const legend = segments.map(s => `
    <div class="legend-item">
      <span class="legend-dot" style="background:${s.color}"></span>
      ${s.label} <span class="legend-value">${s.value}</span>
    </div>
  `).join('');

  container.innerHTML = `
    <div class="donut-wrap">
      <svg class="donut-svg" viewBox="0 0 110 110" aria-label="Action distribution chart">
        ${circles}
        <text x="${cx}" y="${cy + 5}" text-anchor="middle" fill="#1a1d23" font-size="18" font-weight="700" font-family="Inter, sans-serif">${total}</text>
      </svg>
      <div class="donut-legend">${legend}</div>
    </div>
  `;
}

// ── Events Preview ─────────────────────────────
function renderEventsPreview(events) {
  const container = document.getElementById('events-preview');

  if (events.length === 0) {
    container.innerHTML = '<div class="empty-state"><p>No audit events recorded yet.</p></div>';
    return;
  }

  container.innerHTML = events.map(e => `
    <div class="event-preview-item">
      <span class="event-time">${formatTime(e.timestamp)}</span>
      <span class="event-types">${e.entity_types.map(t => `<span class="type-tag">${t}</span>`).join('')}</span>
      <span class="action-tag ${e.action.toLowerCase()}">${e.action}</span>
      <span class="event-count-badge">${e.entity_count} found</span>
    </div>
  `).join('');
}

// ── Events Table ───────────────────────────────
async function loadEvents() {
  if (!backendOnline) return;

  try {
    const resp = await fetch(`${API_BASE}/events?page=${eventsPage}&page_size=${EVENTS_PAGE_SIZE}`);
    if (!resp.ok) return;
    const data = await resp.json();

    setText('event-count', `${data.total_events} event${data.total_events !== 1 ? 's' : ''}`);

    const tbody = document.getElementById('events-tbody');
    if (data.events.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-row">No events recorded yet.</td></tr>';
    } else {
      tbody.innerHTML = data.events.map(e => `
        <tr>
          <td><code>${e.id}</code></td>
          <td style="color:var(--color-text-secondary);font-size:12px">${formatTime(e.timestamp)}</td>
          <td>${e.entity_types.map(t => `<span class="type-tag">${t}</span>`).join(' ')}</td>
          <td class="text-right" style="font-weight:600">${e.entity_count}</td>
          <td><span class="type-tag">${e.policy_profile}</span></td>
          <td><span class="action-tag ${e.action.toLowerCase()}">${e.action}</span></td>
        </tr>
      `).join('');
    }

    renderPagination(data.total_events);
  } catch (err) {
    console.error('Failed to load events:', err);
  }
}

function renderPagination(total) {
  const container = document.getElementById('pagination');
  const totalPages = Math.ceil(total / EVENTS_PAGE_SIZE);

  if (totalPages <= 1) {
    container.innerHTML = '';
    return;
  }

  let html = `<button class="page-btn" ${eventsPage <= 1 ? 'disabled' : ''} data-page="${eventsPage - 1}">Prev</button>`;

  for (let i = 1; i <= totalPages; i++) {
    html += `<button class="page-btn ${i === eventsPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
  }

  html += `<button class="page-btn" ${eventsPage >= totalPages ? 'disabled' : ''} data-page="${eventsPage + 1}">Next</button>`;

  container.innerHTML = html;
  container.querySelectorAll('.page-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const p = parseInt(btn.dataset.page);
      if (p >= 1 && p <= totalPages) {
        eventsPage = p;
        loadEvents();
      }
    });
  });
}

// ── Policy Cards ───────────────────────────────
function renderPolicyCards() {
  for (const [name, policy] of Object.entries(POLICIES)) {
    const redactTags = document.getElementById(`${name}-redact-tags`);
    const warnTags = document.getElementById(`${name}-warn-tags`);
    const blockTags = document.getElementById(`${name}-block-tags`);
    const allowTags = document.getElementById(`${name}-allow-tags`);

    if (redactTags) {
      redactTags.innerHTML = policy.redact.map(t => `<span class="tag tag--redact">${t}</span>`).join('');
    }
    if (warnTags) {
      warnTags.innerHTML = policy.warn.length > 0
        ? policy.warn.map(t => `<span class="tag tag--warn">${t}</span>`).join('')
        : '<span class="tag tag--muted">None</span>';
    }
    if (blockTags) {
      blockTags.innerHTML = policy.block.length > 0
        ? policy.block.map(t => `<span class="tag tag--block">${t}</span>`).join('')
        : '<span class="tag tag--muted">None</span>';
    }
    if (allowTags) {
      allowTags.innerHTML = policy.allow.length > 0
        ? policy.allow.map(t => `<span class="tag tag--allow">${t}</span>`).join('')
        : '';
    }
  }
}

// ── Quick Test ─────────────────────────────────
async function runQuickTest() {
  const text = document.getElementById('test-text')?.value?.trim();
  const policy = document.getElementById('test-policy')?.value || 'default';
  const results = document.getElementById('test-results');
  const timing = document.getElementById('test-timing');

  if (!text) {
    results.innerHTML = '<div class="empty-state"><p>Enter some text to scan.</p></div>';
    return;
  }
  if (!backendOnline) {
    results.innerHTML = '<div class="empty-state"><p>The backend is offline. Start the server first.</p></div>';
    return;
  }

  // Loading state
  results.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Scanning for PII…</p>
    </div>`;
  if (timing) timing.textContent = '';

  try {
    const resp = await fetch(`${API_BASE}/sanitize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, policy_profile: policy }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      if (resp.status === 422 && err.detail?.error === 'request_blocked') {
        results.innerHTML = `
          <div class="test-blocked">
            <div class="test-blocked-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
            </div>
            <h3>Request blocked</h3>
            <p>${escapeHtml(err.detail.message || 'The policy blocked this request due to high-risk PII.')}</p>
          </div>`;
        return;
      }
      throw new Error(`HTTP ${resp.status}`);
    }

    const data = await resp.json();

    if (timing) timing.textContent = `${data.processing_time_ms.toFixed(0)} ms`;

    if (data.detections.length === 0) {
      results.innerHTML = `
        <div class="test-clean">
          <div class="test-clean-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          </div>
          <h3 style="color:var(--color-success);font-size:15px">No PII detected</h3>
          <p style="font-size:13px;color:var(--color-text-secondary)">This text appears clean — no sensitive information was found.</p>
        </div>`;
    } else {
      let html = data.detections.map(d => `
        <div class="test-result-item">
          <span class="det-entity-type">${d.entity_type}</span>
          <span class="action-tag ${d.action.toLowerCase()}">${d.action}</span>
          <span class="det-meta">${d.source} · ${(d.score * 100).toFixed(0)}%</span>
        </div>
      `).join('');

      html += `
        <div class="test-sanitized-wrap">
          <div class="test-sanitized-label">Sanitized output</div>
          <div class="test-sanitized-text">${escapeHtml(data.sanitized_text)}</div>
        </div>
        <p class="test-disclaimer">${escapeHtml(data.disclaimer)}</p>
      `;

      results.innerHTML = html;
    }

    // Refresh overview data
    loadOverview();

  } catch (err) {
    results.innerHTML = `<div class="empty-state"><p>Error: ${escapeHtml(err.message)}</p></div>`;
  }
}

// ── Helpers ────────────────────────────────────
function formatTime(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-US', {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch {
    return iso;
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
