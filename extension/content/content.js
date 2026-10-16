/**
 * PII-Shield — Content Script
 *
 * Injected into LLM chat pages (ChatGPT, Claude, Gemini, Copilot).
 * Intercepts user input before submission, sends it to the local
 * PII-Shield backend for redaction, and replaces the input with
 * the sanitised version.
 *
 * TODO [Phase 2]: Implement full interception logic.
 * The current version is a scaffold that:
 *   1. Listens for toggle messages from the popup
 *   2. Observes the DOM for chat input fields
 *   3. Provides the interception hook structure
 */

let isEnabled = true;

// ── Listen for toggle from popup ────────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'PII_SHIELD_TOGGLE') {
    isEnabled = message.enabled;
    console.log(`[PII-Shield] Protection ${isEnabled ? 'enabled' : 'disabled'}`);
    sendResponse({ ok: true });
  }
  return true;
});

// ── Load initial state ──────────────────────────

chrome.storage.local.get('piiShieldEnabled', (result) => {
  isEnabled = result.piiShieldEnabled !== false;
  console.log(`[PII-Shield] Content script loaded. Protection: ${isEnabled}`);
});

// ── DOM Observation ─────────────────────────────

/**
 * Observe the page for dynamically inserted chat input fields.
 * LLM chat UIs often render inputs lazily.
 */
function observeInputFields() {
  const observer = new MutationObserver((mutations) => {
    // TODO [Phase 2]: Detect chat input fields and attach interception
    // Look for textarea, contenteditable divs, or specific selectors
    // per LLM site (ChatGPT uses a specific form structure, etc.)
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });
}

// ── Interception Hook ───────────────────────────

/**
 * Intercept text before it's submitted to the LLM.
 *
 * @param {string} rawText - The user's original input
 * @returns {Promise<string>} - The sanitised text to submit
 */
async function interceptAndRedact(rawText) {
  if (!isEnabled || !rawText.trim()) {
    return rawText;
  }

  try {
    // TODO [Phase 2]: Import from utils/api.js
    const response = await fetch('http://127.0.0.1:8000/api/v1/redact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: rawText }),
    });

    if (!response.ok) {
      console.warn('[PII-Shield] Redaction failed, sending original text');
      return rawText;
    }

    const data = await response.json();

    // Store session_id for later restoration
    if (data.session_id) {
      await chrome.storage.session.set({
        lastSessionId: data.session_id,
      });
    }

    // Update stats
    const stats = await chrome.storage.session.get(['totalRedacted', 'totalRequests']);
    await chrome.storage.session.set({
      totalRedacted: (stats.totalRedacted || 0) + data.stats.total_entities,
      totalRequests: (stats.totalRequests || 0) + 1,
    });

    console.log(`[PII-Shield] Redacted ${data.stats.total_entities} entities`);
    return data.sanitized_text;
  } catch (error) {
    console.error('[PII-Shield] Backend error:', error.message);
    return rawText; // Fail open — don't block the user
  }
}

// ── Initialise ──────────────────────────────────

observeInputFields();
