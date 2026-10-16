/**
 * PII-Shield — Service Worker (Background Script)
 *
 * Runs as the Manifest V3 service worker. Handles:
 * - Communication between content scripts and popup
 * - Backend health monitoring
 * - Session management
 *
 * TODO [Phase 2]: Implement full background logic.
 */

const API_BASE = 'http://127.0.0.1:8000/api/v1';

// ── Installation ────────────────────────────────

chrome.runtime.onInstalled.addListener((details) => {
  console.log('[PII-Shield] Extension installed:', details.reason);

  // Set default settings
  chrome.storage.local.set({
    piiShieldEnabled: true,
    backendUrl: API_BASE,
  });
});

// ── Message handling ────────────────────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'PII_SHIELD_HEALTH_CHECK':
      checkHealth().then(sendResponse);
      return true; // async response

    case 'PII_SHIELD_GET_STATS':
      getStats().then(sendResponse);
      return true;

    default:
      break;
  }
});

// ── Health check ────────────────────────────────

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`, {
      signal: AbortSignal.timeout(3000),
    });
    if (response.ok) {
      return { connected: true, data: await response.json() };
    }
    return { connected: false, error: 'Backend returned error' };
  } catch (error) {
    return { connected: false, error: error.message };
  }
}

// ── Stats retrieval ─────────────────────────────

async function getStats() {
  const result = await chrome.storage.session.get([
    'totalRedacted',
    'totalRequests',
  ]);
  return {
    totalRedacted: result.totalRedacted || 0,
    totalRequests: result.totalRequests || 0,
  };
}
