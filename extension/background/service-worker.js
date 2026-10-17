/**
 * PII-Shield — Service Worker (Background Script)
 *
 * Manifest V3 service worker. Handles:
 * - Communication between content scripts and popup
 * - Backend health monitoring
 * - Stats tracking via session storage
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

    case 'PII_SHIELD_SANITIZE':
      sanitizeText(message.text, message.policyProfile).then(sendResponse);
      return true;

    case 'PII_SHIELD_UPDATE_STATS':
      updateStats(message.entityCount, message.entityTypes).then(sendResponse);
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

// ── Sanitize via backend ────────────────────────

async function sanitizeText(text, policyProfile = 'default') {
  try {
    const response = await fetch(`${API_BASE}/sanitize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, policy_profile: policyProfile }),
      signal: AbortSignal.timeout(10000),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      return { success: false, error: err.detail || `HTTP ${response.status}` };
    }

    const data = await response.json();

    // Update stats
    await updateStats(data.total_detections, data.categories_found);

    return { success: true, data };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// ── Stats ───────────────────────────────────────

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

async function updateStats(entityCount, entityTypes) {
  if (!entityCount || entityCount === 0) return { ok: true };

  const result = await chrome.storage.session.get([
    'totalRedacted',
    'totalRequests',
    'recentDetections',
  ]);

  const recentDetections = result.recentDetections || [];

  // Add new detection summary
  if (entityTypes && entityTypes.length > 0) {
    for (const type of entityTypes) {
      const existing = recentDetections.find((d) => d.type === type);
      if (existing) {
        existing.count++;
      } else {
        recentDetections.unshift({ type, count: 1 });
      }
    }
    // Keep only last 20 types
    while (recentDetections.length > 20) recentDetections.pop();
  }

  await chrome.storage.session.set({
    totalRedacted: (result.totalRedacted || 0) + entityCount,
    totalRequests: (result.totalRequests || 0) + 1,
    recentDetections,
  });

  return { ok: true };
}
