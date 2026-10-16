/**
 * PII-Shield — Extension Popup Script
 *
 * Manages the popup UI: toggle state, backend health check,
 * and display of recent detection stats.
 */

const API_BASE = 'http://127.0.0.1:8000/api/v1';

// ── DOM Elements ────────────────────────────────

const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('status-text');
const enableToggle = document.getElementById('enable-toggle');
const statRedacted = document.getElementById('stat-redacted');
const statRequests = document.getElementById('stat-requests');
const detectionsList = document.getElementById('detections-list');

// ── Initialisation ──────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
  await loadToggleState();
  await checkBackendHealth();
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
      statusText.textContent = 'Backend connected';

      // Update stats if available
      if (data.presidio_loaded) {
        statusText.textContent = 'Engine ready';
      }
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
}

// ── Stats Display ───────────────────────────────

/**
 * Update the popup stats from session storage.
 * Stats are accumulated by the content script / service worker.
 */
async function updateStats() {
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
      .slice(0, 10) // Show last 10
      .map(
        (d) =>
          `<li>
            <span>${d.count} entit${d.count === 1 ? 'y' : 'ies'}</span>
            <span class="entity-badge">${d.type}</span>
          </li>`
      )
      .join('');
  }
}

// Update stats on popup open
updateStats();
