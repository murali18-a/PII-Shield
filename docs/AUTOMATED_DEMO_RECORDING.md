# PII-Shield — Automated Demo Recording & Live Demonstration Guide

This guide explains how to run, demonstrate, and record the PII-Shield live prototype for the IBM Z Datathon 2026.

---

## 1. Quick Start with One-Click Launcher

A Windows batch script is provided to verify all services and launch the demo interfaces:

```cmd
.\RUN_PII_SHIELD_DEMO.bat
```

Or via PowerShell:
```powershell
.\start.ps1
```

### Verified Service URLs
| Service | URL | Status Endpoint |
|---|---|---|
| **Backend API** | `http://127.0.0.1:8000` | `http://127.0.0.1:8000/api/v1/health` |
| **Interactive API Docs** | `http://127.0.0.1:8000/docs` | OpenAPI Swagger UI |
| **Admin Dashboard** | `http://127.0.0.1:5173` | Vite Dev Server |
| **Supported Demo Page** | `file:///.../extension/demo/demo.html` | Or via Extension popup |

---

## 2. Loading the Chrome Extension

1. Open Google Chrome and navigate to:
   ```text
   chrome://extensions/
   ```
2. In the top-right corner, toggle **Developer mode** to **ON**.
3. Click the **Load unpacked** button.
4. Select the project's `extension` directory:
   ```text
   C:\Users\murul\Downloads\PII-Shield\extension
   ```
5. Click the extension icon in the Chrome toolbar. The popup will display:
   - **Protection Enabled**: Toggle ON
   - **Engine status**: `Engine ready (Presidio + Regex)`
   - **Open Demo Page** button
   - **Open Dashboard** button

> **Note on Updates:** If you modify extension files or pull updates, click the **Reload** (circular arrow) button on the PII-Shield card in `chrome://extensions/`.

---

## 3. Important Scope: Demo Page vs. ChatGPT

> [!IMPORTANT]
> **Why the Supported Demo Page is Used for the Hackathon Demonstration:**
> - In `extension/content/content.js`, the content script for third-party websites (like ChatGPT) is currently a **Phase 2 architectural scaffold**.
> - Modern LLM interfaces (like ChatGPT and Claude) utilize complex, obfuscated shadow DOMs and custom event frameworks that block direct browser extension value replacement.
> - The live, production-grade detection, tokenization, redaction, and restoration logic is fully implemented and demonstrated via the **PII-Shield Demo Page (`extension/demo/demo.html`)** and the **Admin Dashboard (`http://127.0.0.1:5173`)**.

---

## 4. End-to-End Demo Script (2–3 Minutes)

### Step 1: Clean Prompt Baseline (Zero False Positives)
1. Open the **Demo Page** (`demo.html`).
2. Verify the top connection indicator shows `Engine ready (Presidio + regex)` with a green dot.
3. Enter a technical prompt with no personal data:
   ```text
   Summarize the key architectural benefits of IBM LinuxONE for enterprise privacy and confidential computing workloads.
   ```
4. Click **🔍 Analyze**.
5. **Observed Result:** 0 detections, 0 categories. Highlights clean execution without false positives.

### Step 2: Synthetic PII Detection & Real-Time Redaction
1. In the prompt box, enter a synthetic record (e.g., employee onboarding or customer support):
   ```text
   Verify this employee onboarding record.

   Name: Priya Sharma
   Aadhaar: 2345 6789 0123
   PAN: ABCDE1234F
   Email: priya.sharma@example.com

   Create a checklist of the documents required for onboarding.
   ```
2. Click **🔍 Analyze**.
3. **Observed Result:**
   - Detects `PERSON` (Priya Sharma) via Presidio/NLP
   - Detects `AADHAAR` (2345 6789 0123) via regex pattern & Luhn/Verhoeff check
   - Detects `EMAIL_ADDRESS` (priya.sharma@example.com) via RFC-compliant regex
   - Displays detection category tags and processing latency (~30ms)
4. Click **🛡️ Sanitize & Preview**.
5. **Observed Result:** Generates the tokenized, sanitized prompt:
   ```text
   Verify this employee onboarding record.

   Name: [PERSON_1]
   Aadhaar: [AADHAAR_1]
   PAN: [ORGANIZATION_1] [PERSON_2]
   Email: [EMAIL_ADDRESS_1]

   Create a checklist of the documents required for onboarding.
   ```
6. The user copies this text and sends it to ChatGPT or any external LLM. The LLM never sees real personal data!

### Step 3: Local Restoration (Client-Side Privacy)
1. In the **🧪 Local Restore Test** box, paste an LLM response that contains the placeholders:
   ```text
   Onboarding Checklist for [PERSON_1] (Aadhaar: [AADHAAR_1]):
   1. Confirm receipt of ID card.
   2. Send confirmation to [EMAIL_ADDRESS_1].
   ```
2. Click **Restore Locally**.
3. **Observed Result:** The original values (`Priya Sharma`, `2345 6789 0123`, `priya.sharma@example.com`) are restored purely in client memory without the external LLM ever accessing the mapping.

### Step 4: Admin Dashboard Tour
1. Navigate to `http://127.0.0.1:5173`.
2. **Overview Tab:** Shows live metrics (Total Detections, Redactions, Active Policy).
3. **Audit Events Tab:** Shows privacy-preserving audit logs (timestamps, policy applied, entity categories redacted; never stores raw PII).
4. **Policy Configuration Tab:** Inspect Default, Strict (blocks high-risk PII), and Permissive policies.
5. **Quick Test Tab:** Run ad-hoc text scans directly from the admin console.

---

## 5. Troubleshooting & FAQ

| Symptom | Cause | Solution |
|---|---|---|
| `ERR_FILE_NOT_FOUND` when clicking "Open Demo Page" | Relative path resolution in Chrome Extension popup | Updated `popup.html` and `popup.js` to use `chrome.runtime.getURL('demo/demo.html')`. Reload extension in `chrome://extensions/`. |
| Popup shows "Backend offline" | FastAPI server is not running on port 8000 | Run `.\RUN_PII_SHIELD_DEMO.bat` or `.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8000`. |
| Dashboard shows connection error | Vite dev server not running on port 5173 | Run `cd dashboard && npx vite --host 127.0.0.1 --port 5173`. |
| ChatGPT prompt is not intercepted | Content script is a Phase 2 scaffold | Demonstrate PII redaction and restoration using the supported **Demo Page**, then copy sanitized text to ChatGPT. |
