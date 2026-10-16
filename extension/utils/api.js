/**
 * PII-Shield — API Client Utility
 *
 * Shared fetch wrapper for calling the PII-Shield backend.
 * Used by content scripts and service worker.
 */

const DEFAULT_API_BASE = 'http://127.0.0.1:8000/api/v1';

/**
 * Send a redaction request to the backend.
 *
 * @param {string} text - Raw text to redact
 * @param {string} policyProfile - Policy profile name
 * @param {string} apiBase - Backend API base URL
 * @returns {Promise<Object>} - RedactResponse from backend
 */
export async function redactText(text, policyProfile = 'default', apiBase = DEFAULT_API_BASE) {
  const response = await fetch(`${apiBase}/redact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, policy_profile: policyProfile }),
    signal: AbortSignal.timeout(10000),
  });

  if (!response.ok) {
    throw new Error(`Redaction failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Send a restoration request to the backend.
 *
 * @param {string} text - Text with placeholders to restore
 * @param {string} sessionId - Session ID from redaction response
 * @param {string} apiBase - Backend API base URL
 * @returns {Promise<Object>} - RestoreResponse from backend
 */
export async function restoreText(text, sessionId, apiBase = DEFAULT_API_BASE) {
  const response = await fetch(`${apiBase}/restore`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, session_id: sessionId }),
    signal: AbortSignal.timeout(10000),
  });

  if (!response.ok) {
    throw new Error(`Restoration failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Check backend health.
 *
 * @param {string} apiBase - Backend API base URL
 * @returns {Promise<Object>} - HealthResponse from backend
 */
export async function checkHealth(apiBase = DEFAULT_API_BASE) {
  const response = await fetch(`${apiBase}/health`, {
    signal: AbortSignal.timeout(3000),
  });

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }

  return response.json();
}
