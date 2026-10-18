/**
 * PII-Shield — Extension Popup Script
 *
 * Manages the popup UI: toggle state, backend health check,
 * engine info display, and stats from session storage.
 */

const API_BASE = 'http://127.0.0.1:8000/api/v1';

// ── DOM Elements ────────────────────────────────

const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const enableToggle = document.getElementById('enable-toggle');
const statRedacted = document.getElementById('stat-redacted');
const statRequests = document.getElementById('stat-requests');
const detectionsList = document.getElementById('detections-list');
const engineInfo = document.getElementById('engine-info');
const engineType = document.getElementById('engine-type');
const engineModel = document.getElementById('engine-model');
const engineSessions = document.getElementById('engine-sessions');
const dashboardLink = document.getElementById('dashboard-link');
const demoLink = document.getElementById('demo-link');

// ── Initialisation ──────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
  await loadToggleState();
  await checkBackendHealth();
  await updateStats();

  // Demo page link opens the extension demo page
  if (demoLink) {
    demoLink.addEventListener('click', (e) => {
      e.preventDefault();
      chrome.tabs.create({ url: chrome.runtime.getURL('demo/demo.html') });
    });
  }

  // Dashboard link opens the dashboard HTML (served by backend or locally)
  if (dashboardLink) {
    dashboardLink.addEventListener('click', (e) => {
      e.preventDefault();
      // Open the Vite dev server or fallback to a local file
      chrome.tabs.create({ url: 'http://127.0.0.1:5173' });
    });
  }
});

// ── Toggle ──────────────────────────────────────

enableToggle.addEventListener('change', async () => {
  const enabled = enableToggle.checked;
  await chrome.storage.local.set({ piiShieldEnabled: enabled });

  // Notify content scripts of state change
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    chrome.tabs.sendMessage(tab.id, {
      type: 'PII_SHIELD_TOGGLE',
      enabled,
    }).catch(() => {
      // Content script may not be loaded on this page
    });
  }
});

async function loadToggleState() {
  const result = await chrome.storage.local.get('piiShieldEnabled');
  const enabled = result.piiShieldEnabled !== false; // Default to true
  enableToggle.checked = enabled;
}

// ── Health Check ────────────────────────────────

async function checkBackendHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000),
    });

    if (response.ok) {
      const data = await response.json();
      statusDot.className = 'status-dot connected';

      if (data.presidio_loaded) {
        statusText.textContent = 'Engine ready';
        engineType.textContent = 'Presidio + Regex';
      } else {
        statusText.textContent = 'Regex-only mode';
        engineType.textContent = 'Regex only';
      }

      engineModel.textContent = data.spacy_model || '—';
      engineSessions.textContent = data.active_sessions || 0;
      engineInfo.style.display = 'block';
    } else {
      setDisconnected();
    }
  } catch {
    setDisconnected();
  }
}

function setDisconnected() {
  statusDot.className = 'status-dot disconnected';
  statusText.textContent = 'Backend offline';
  engineInfo.style.display = 'none';
}

// ── Stats Display ───────────────────────────────

async function updateStats() {
  try {
    const result = await chrome.storage.session.get([
      'totalRedacted',
      'totalRequests',
      'recentDetections',
    ]);

    statRedacted.textContent = result.totalRedacted || 0;
    statRequests.textContent = result.totalRequests || 0;

    // Update detections list
    const detections = result.recentDetections || [];
    if (detections.length === 0) {
      detectionsList.innerHTML = '<li class="empty-state">No detections yet</li>';
    } else {
      detectionsList.innerHTML = detections
        .slice(0, 10)
        .map(
          (d) =>
            `<li>
              <span>${d.count} entit${d.count === 1 ? 'y' : 'ies'}</span>
              <span class="entity-badge">${d.type}</span>
            </li>`
        )
        .join('');
    }
  } catch {
    // session storage might not be available
  }
}
