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

  // "View All" link in overview
  document.querySelector('.view-all')?.addEventListener('click', (e) => {
    e.preventDefault();
    switchTab('events');
  });
});

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
  document.querySelectorAll('.nav-item').forEach((n) => n.classList.remove('active'));
  document.querySelector(`.nav-item[data-tab="${tab}"]`)?.classList.add('active');

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

    // Stats
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

    // Action donut
    renderActionDonut(redactCount, warnCount, blockCount);

    // Recent events
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
    container.innerHTML = '<div class="empty-chart">No data yet — run some scans first</div>';
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
    container.innerHTML = '<div class="empty-chart">No data yet</div>';
    return;
  }

  const r = 50, cx = 60, cy = 60;
  const circumference = 2 * Math.PI * r;

  const segments = [
    { label: 'Redacted', value: redact, color: '#4fc3f7' },
    { label: 'Warned', value: warn, color: '#ffa726' },
    { label: 'Blocked', value: block, color: '#ef5350' },
  ].filter(s => s.value > 0);

  let offset = 0;
  const circles = segments.map(s => {
    const pct = s.value / total;
    const dash = pct * circumference;
    const gap = circumference - dash;
    const circle = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${s.color}" stroke-width="16"
      stroke-dasharray="${dash} ${gap}" stroke-dashoffset="${-offset}" opacity="0.85"/>`;
    offset += dash;
    return circle;
  }).join('');

  const legend = segments.map(s => `
    <div class="legend-item">
      <span class="legend-dot" style="background:${s.color}"></span>
      ${s.label}: <span class="legend-value">${s.value}</span>
    </div>
  `).join('');

  container.innerHTML = `
    <div class="donut-wrap">
      <svg class="donut-svg" viewBox="0 0 120 120">
        ${circles}
        <text x="${cx}" y="${cy+4}" text-anchor="middle" fill="#e4e8ee" font-size="18" font-weight="700">${total}</text>
      </svg>
      <div class="donut-legend">${legend}</div>
    </div>
  `;
}

// ── Events Preview ─────────────────────────────
function renderEventsPreview(events) {
  const container = document.getElementById('events-preview');

  if (events.length === 0) {
    container.innerHTML = '<div class="empty-chart">No audit events recorded yet</div>';
    return;
  }

  container.innerHTML = events.map(e => `
    <div class="event-preview-item">
      <span class="event-time">${formatTime(e.timestamp)}</span>
      <span class="event-types">${e.entity_types.map(t => `<span class="type-tag">${t}</span>`).join(' ')}</span>
      <span class="action-tag ${e.action.toLowerCase()}">${e.action}</span>
      <span style="font-size:12px;color:var(--text-muted)">${e.entity_count} found</span>
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

    setText('event-count', `${data.total_events} events`);

    const tbody = document.getElementById('events-tbody');
    if (data.events.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-row">No events yet</td></tr>';
    } else {
      tbody.innerHTML = data.events.map(e => `
        <tr>
          <td><code style="font-size:11px">${e.id}</code></td>
          <td style="font-size:12px;color:var(--text-secondary)">${formatTime(e.timestamp)}</td>
          <td>${e.entity_types.map(t => `<span class="type-tag">${t}</span>`).join(' ')}</td>
          <td style="font-weight:600">${e.entity_count}</td>
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

  let html = `<button class="page-btn" ${eventsPage <= 1 ? 'disabled' : ''} data-page="${eventsPage - 1}">← Prev</button>`;

  for (let i = 1; i <= totalPages; i++) {
    html += `<button class="page-btn ${i === eventsPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
  }

  html += `<button class="page-btn" ${eventsPage >= totalPages ? 'disabled' : ''} data-page="${eventsPage + 1}">Next →</button>`;

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
      redactTags.innerHTML = policy.redact.map(t => `<span class="tag tag-redact">${t}</span>`).join('');
    }
    if (warnTags) {
      warnTags.innerHTML = policy.warn.length > 0
        ? policy.warn.map(t => `<span class="tag tag-warn">${t}</span>`).join('')
        : '<span class="tag tag-muted">None</span>';
    }
    if (blockTags) {
      blockTags.innerHTML = policy.block.length > 0
        ? policy.block.map(t => `<span class="tag tag-block">${t}</span>`).join('')
        : '<span class="tag tag-muted">None</span>';
    }
    if (allowTags) {
      allowTags.innerHTML = policy.allow.length > 0
        ? policy.allow.map(t => `<span class="tag tag-allow">${t}</span>`).join('')
        : '';
    }
  }
}

// ── Quick Test ─────────────────────────────────
async function runQuickTest() {
  const text = document.getElementById('test-text')?.value?.trim();
  const policy = document.getElementById('test-policy')?.value || 'default';
  const results = document.getElementById('test-results');

  if (!text) {
    results.innerHTML = '<div class="empty-chart">Enter some text first</div>';
    return;
  }
  if (!backendOnline) {
    results.innerHTML = '<div class="empty-chart">Backend is offline</div>';
    return;
  }

  results.innerHTML = '<div class="empty-chart">Scanning…</div>';

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
          <div style="text-align:center;padding:20px">
            <div style="font-size:32px">🚫</div>
            <h4 style="color:var(--danger);margin:8px 0">Blocked</h4>
            <p style="font-size:13px;color:var(--text-secondary)">${err.detail.message}</p>
          </div>`;
        return;
      }
      throw new Error(`HTTP ${resp.status}`);
    }

    const data = await resp.json();

    let html = '';

    if (data.detections.length === 0) {
      html = '<div class="empty-chart">No PII detected ✅</div>';
    } else {
      html = data.detections.map(d => `
        <div class="test-result-item">
          <span style="font-weight:600">${d.entity_type}</span>
          <span class="action-tag ${d.action.toLowerCase()}">${d.action}</span>
          <span style="font-size:11px;color:var(--text-muted)">${d.source} · ${(d.score*100).toFixed(0)}%</span>
        </div>
      `).join('');

      html += `
        <div class="test-sanitized">
          <h4>✅ Sanitized Output</h4>
          ${escapeHtml(data.sanitized_text)}
        </div>
        <p style="font-size:11px;color:var(--text-muted);margin-top:8px;font-style:italic">${data.disclaimer}</p>
      `;
    }

    results.innerHTML = html;

    // Refresh overview data
    loadOverview();

  } catch (err) {
    results.innerHTML = `<div class="empty-chart">Error: ${err.message}</div>`;
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
