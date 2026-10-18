# PII-Shield Prototype Demo — Narration Script (2:30 min)

**Theme:** AI Secured: Innovation Without Exposure — IBM Z Datathon 2026

---

### [00:00 - 00:25] Introduction & The Problem
> "Enterprise adoption of generative AI and LLMs introduces a critical privacy vulnerability: employees inadvertently expose personally identifiable information, healthcare records, and confidential national identifiers to cloud models.
>
> Today, we present **PII-Shield**, a local-first privacy guardrail engineered for enterprise workloads and designed for IBM LinuxONE confidential computing."

---

### [00:25 - 00:55] Chrome Extension & Clean Prompt Baseline
> "Here, our Chrome extension connects to our local high-performance privacy engine.
>
> Notice the status: 'Engine ready', powered by Microsoft Presidio and specialized regex analyzers.
>
> When a user enters a standard technical query—such as summarizing LinuxONE security benefits—the engine scans the prompt and confirms zero detections in under 30 milliseconds. No false positives, no user disruption."

---

### [00:55 - 01:35] Synthetic PII Detection & Tokenized Redaction
> "Now, let's paste an employee onboarding record containing real-world Indian identifiers: a candidate's name, a 12-digit Aadhaar number, PAN card, and business email.
>
> With a single click of 'Analyze', PII-Shield flags every sensitive entity.
>
> When we click 'Sanitize & Preview', the original text is transformed: Priya Sharma becomes `[PERSON_1]`, the Aadhaar is replaced with `[AADHAAR_1]`, and the email becomes `[EMAIL_ADDRESS_1]`.
>
> This sanitized prompt is completely safe to send to external models like ChatGPT or Claude. The external model never sees the original data."

---

### [01:35 - 02:05] Local Restoration (Zero Exposure)
> "When the LLM returns its generated checklist or summary referring to these placeholders, PII-Shield performs client-side local restoration.
>
> Because the mapping exists strictly in local memory and is never logged or exposed to the network, the user receives their complete answer with original names restored locally."

---

### [02:05 - 02:30] Enterprise Admin Dashboard & Conclusion
> "Finally, let's look at the PII-Shield Admin Dashboard.
>
> In the Overview, security administrators monitor detection volume, redaction ratios, and active policies across the organization.
>
> In Audit Events, every transaction is logged for compliance without ever persisting sensitive prompt text.
>
> With PII-Shield, enterprises unlock the full power of generative AI—with zero privacy exposure."
