/**
 * ValidationPopup.jsx — 3-Layer Document Validation
 * ===================================================
 * Layer 1 — File format + size (instant, browser)
 * Layer 2 — OCR text extraction + keyword match (browser, no API)
 * Layer 3 — AI vision API (only if layers 1 & 2 pass)
 *
 * If Layer 1 or 2 fails → immediately invalid, API never called.
 */

import React, { useEffect, useRef, useState } from "react";

// ── Icons ──────────────────────────────────────────────────────────────────

const IconCheck = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
    strokeLinecap="round" strokeLinejoin="round" style={{ width: 18, height: 18 }}>
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

const IconX = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
    strokeLinecap="round" strokeLinejoin="round" style={{ width: 18, height: 18 }}>
    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

const IconSkip = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
    strokeLinecap="round" strokeLinejoin="round" style={{ width: 18, height: 18 }}>
    <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
  </svg>
);

const IconSpinner = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
    style={{ width: 18, height: 18, animation: "vp-spin 0.8s linear infinite" }}>
    <circle cx="12" cy="12" r="10" strokeOpacity="0.3" />
    <path d="M12 2a10 10 0 0 1 10 10" />
  </svg>
);

const IconDoc = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" style={{ width: 22, height: 22 }}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="8" y1="13" x2="16" y2="13" />
    <line x1="8" y1="17" x2="12" y2="17" />
  </svg>
);

// ── Step definitions ───────────────────────────────────────────────────────

const STEPS = [
  { id: "layer1_format",  label: "File Format & Size Check",       layer: 1 },
  { id: "layer2_ocr",     label: "OCR Text Extraction",            layer: 2 },
  { id: "layer2_keyword", label: "Document Keyword Verification",  layer: 2 },
  { id: "layer3_ai",      label: "AI Vision Verification",         layer: 3 },
];

// ── Document keyword map for Layer 2 ──────────────────────────────────────

const DOC_KEYWORDS = {
  "aadhaar card":                   ["aadhaar", "aadhar", "uidai", "unique identification", "आधार"],
  "pan card":                       ["permanent account number", "income tax", "pan", "आयकर"],
  "udyam registration certificate": ["udyam", "udyog", "msme", "ministry of micro"],
  "gst certificate":                ["goods and services tax", "gstin", "gst", "cgst", "sgst"],
  "bank statement":                 ["bank", "account", "balance", "transaction", "ifsc", "statement"],
  "project report / dpr":           ["project report", "dpr", "detailed project", "business plan"],
  "itr":                            ["income tax return", "itr", "assessment year", "form 16"],
  "ca certificate":                 ["chartered accountant", "ca certificate", "net worth"],
  "photograph":                     ["photograph"],
  "business address proof":         ["address", "utility", "electricity", "rent agreement"],
  "caste certificate":              ["caste", "sc", "st", "obc", "community certificate"],
  "certificate of incorporation":   ["certificate of incorporation", "mca", "company", "cin"],
  "partnership deed / moa":         ["partnership", "memorandum", "association", "llp"],
  "dpiit startup recognition":      ["dpiit", "startup india", "recognition"],
  "pitch deck":                     ["pitch", "startup", "investor", "funding"],
};

function getKeywordsForDoc(docName) {
  const key = (docName || "").toLowerCase().trim();
  for (const [canonical, keywords] of Object.entries(DOC_KEYWORDS)) {
    if (key.includes(canonical) || canonical.includes(key)) {
      return keywords;
    }
  }
  // Fallback: use words from doc name itself
  return key.split(/\s+/).filter(w => w.length > 3);
}

// ── CSS ────────────────────────────────────────────────────────────────────

const css = `
@keyframes vp-spin { to { transform: rotate(360deg); } }
@keyframes vp-fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }
@keyframes vp-pulse { 0%,100% { opacity:1; } 50% { opacity:.5; } }

.vp-overlay {
  position:fixed; inset:0; background:rgba(0,0,0,.55); backdrop-filter:blur(4px);
  z-index:9999; display:flex; align-items:center; justify-content:center;
  animation:vp-fadeIn .2s ease;
}
.vp-card {
  background:#fff; border-radius:18px; padding:32px 28px 28px;
  width:min(500px, 95vw); box-shadow:0 24px 60px rgba(0,0,0,.22);
  animation:vp-fadeIn .25s ease;
}
.vp-header { display:flex; align-items:center; gap:12px; margin-bottom:20px; }
.vp-header-icon {
  width:44px; height:44px; border-radius:12px; background:#EEF2FF;
  display:flex; align-items:center; justify-content:center; color:#4F46E5; flex-shrink:0;
}
.vp-title { font-size:17px; font-weight:700; color:#111827; margin:0 0 2px; }
.vp-subtitle { font-size:13px; color:#6B7280; margin:0; }
.vp-layer-label {
  font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.06em;
  color:#9CA3AF; margin:14px 0 6px; padding-left:4px;
}
.vp-steps { display:flex; flex-direction:column; gap:0; }
.vp-step {
  display:flex; align-items:flex-start; gap:14px; padding:9px 0;
  border-bottom:1px solid #F3F4F6;
}
.vp-step:last-child { border-bottom:none; }
.vp-step-icon {
  width:30px; height:30px; border-radius:50%; display:flex;
  align-items:center; justify-content:center; flex-shrink:0; margin-top:1px;
}
.vp-step-icon.pending  { background:#F9FAFB; color:#D1D5DB; border:2px dashed #E5E7EB; }
.vp-step-icon.running  { background:#EEF2FF; color:#4F46E5; }
.vp-step-icon.passed   { background:#ECFDF5; color:#059669; }
.vp-step-icon.failed   { background:#FEF2F2; color:#DC2626; }
.vp-step-icon.skipped  { background:#F9FAFB; color:#9CA3AF; }
.vp-step-body { flex:1; min-width:0; }
.vp-step-label { font-size:13px; font-weight:600; color:#374151; margin:0 0 1px; }
.vp-step-label.running { color:#4F46E5; animation:vp-pulse 1.4s ease infinite; }
.vp-step-label.failed  { color:#DC2626; }
.vp-step-detail { font-size:12px; color:#6B7280; margin:0; }
.vp-step-detail.failed { color:#B91C1C; }
.vp-result {
  margin-top:18px; border-radius:12px; padding:14px 16px;
  display:flex; align-items:flex-start; gap:12px;
}
.vp-result.valid   { background:#ECFDF5; border:1px solid #A7F3D0; }
.vp-result.invalid { background:#FEF2F2; border:1px solid #FECACA; }
.vp-result.warning { background:#FFFBEB; border:1px solid #FDE68A; }
.vp-result-icon { font-size:20px; flex-shrink:0; margin-top:1px; }
.vp-result-title { font-size:14px; font-weight:700; margin:0 0 3px; }
.vp-result.valid .vp-result-title   { color:#065F46; }
.vp-result.invalid .vp-result-title { color:#991B1B; }
.vp-result.warning .vp-result-title { color:#92400E; }
.vp-result-message { font-size:13px; margin:0; }
.vp-result.valid .vp-result-message   { color:#047857; }
.vp-result.invalid .vp-result-message { color:#B91C1C; }
.vp-result.warning .vp-result-message { color:#B45309; }
.vp-progress-bar { height:3px; background:#E5E7EB; border-radius:99px; margin-bottom:18px; overflow:hidden; }
.vp-progress-fill { height:100%; background:linear-gradient(90deg,#4F46E5,#7C3AED); border-radius:99px; transition:width .4s ease; }
.vp-footer { display:flex; justify-content:flex-end; gap:10px; margin-top:18px; }
.vp-btn { padding:9px 20px; border-radius:9px; font-size:14px; font-weight:600; cursor:pointer; border:none; transition:all .15s ease; }
.vp-btn-primary { background:#4F46E5; color:#fff; }
.vp-btn-primary:hover { background:#4338CA; }
.vp-btn-ghost { background:#F3F4F6; color:#374151; }
.vp-btn-ghost:hover { background:#E5E7EB; }
.vp-ms { font-size:11px; color:#9CA3AF; margin-top:3px; }
.vp-fields { margin-top:10px; background:#F9FAFB; border-radius:10px; padding:10px 12px; }
.vp-fields-title { font-size:11px; font-weight:700; color:#6B7280; text-transform:uppercase; letter-spacing:.05em; margin:0 0 6px; }
.vp-fields-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:5px 14px; }
.vp-field-key { font-size:10px; color:#9CA3AF; text-transform:uppercase; }
.vp-field-value { font-size:12px; font-weight:600; color:#1F2937; font-family:monospace; }
`;

function injectCss(id, cssText) {
  if (typeof document === "undefined" || document.getElementById(id)) return;
  const el = document.createElement("style");
  el.id = id; el.textContent = cssText;
  document.head.appendChild(el);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Layer 1: File format + size (browser only) ────────────────────────────

const ALLOWED_TYPES = new Set([
  "application/pdf", "image/jpeg", "image/jpg", "image/png",
  "image/webp", "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);
const ALLOWED_EXTS = new Set([".pdf", ".jpg", ".jpeg", ".png", ".webp", ".doc", ".docx"]);

function layer1Check(file) {
  const ext = "." + (file.name.split(".").pop() || "").toLowerCase();
  const typeOk = ALLOWED_TYPES.has(file.type) || ALLOWED_EXTS.has(ext);
  if (!typeOk) {
    return { passed: false, detail: `Unsupported format '${ext}'. Upload PDF, JPG, or PNG.` };
  }
  if (file.size < 5 * 1024) {
    return { passed: false, detail: "File is too small or blank. Upload a clear complete document." };
  }
  if (file.size > 20 * 1024 * 1024) {
    return { passed: false, detail: "File exceeds 20MB limit. Please compress and re-upload." };
  }
  return { passed: true, detail: `${(file.size / 1024).toFixed(0)} KB — format accepted` };
}

// ── Layer 2: OCR keyword check (browser, PDF.js or canvas) ───────────────

async function extractTextFromFile(file) {
  // For images: use browser canvas (no text extraction possible without OCR lib)
  // For PDFs: try to read raw text stream (works for text-based PDFs)
  const ext = (file.name.split(".").pop() || "").toLowerCase();

  if (ext === "pdf") {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const uint8 = new Uint8Array(arrayBuffer);
      // Decode PDF raw bytes and look for text streams
      let text = "";
      for (let i = 0; i < uint8.length - 1; i++) {
        text += String.fromCharCode(uint8[i]);
      }
      // Extract readable ASCII text from PDF stream
      const readable = text.replace(/[^\x20-\x7E\n]/g, " ").replace(/\s+/g, " ");
      return readable.toLowerCase();
    } catch {
      return "";
    }
  }

  // For images — no client-side OCR without library, return empty (layer 2 will skip gracefully)
  return "";
}

function layer2Check(extractedText, docName) {
  if (!extractedText || extractedText.trim().length < 20) {
    // Can't extract text (image PDF or image file) — skip layer 2, go to AI
    return { passed: true, skipped: true, detail: "Image file — AI vision check will verify content." };
  }

  const keywords = getKeywordsForDoc(docName);
  const foundKeywords = keywords.filter(kw => extractedText.includes(kw.toLowerCase()));

  if (foundKeywords.length === 0) {
    return {
      passed: false,
      skipped: false,
      detail: `No ${docName} keywords found in document. This may be a wrong document type.`,
    };
  }

  return {
    passed: true,
    skipped: false,
    detail: `Found keywords: ${foundKeywords.slice(0, 3).join(", ")}`,
  };
}

// ── Main component ─────────────────────────────────────────────────────────

export default function ValidationPopup({
  open,
  docName = "Document",
  file,
  scheme,
  language = "en",
  onResult,
  onClose,
apiBase = "http://127.0.0.1:8001",
}) {
  const [steps, setSteps]   = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [ms, setMs]         = useState(null);
  const abortRef = useRef(null);
  const t0Ref    = useRef(null);

  injectCss("vp-styles", css);

  useEffect(() => {
    if (!open || !file) return;
    // Reset state
    setSteps({});
    setResult(null);
    setMs(null);
    setLoading(true);
    abortRef.current = new AbortController();
    t0Ref.current = Date.now();
    runValidation(abortRef.current.signal);
    return () => abortRef.current?.abort();
    // eslint-disable-next-line
  }, [open, file]);

  function setStep(id, status, detail = "") {
    setSteps(prev => ({ ...prev, [id]: { status, detail } }));
  }

  async function runValidation(signal) {
    // Init all steps as pending
    const initial = {};
    STEPS.forEach(s => { initial[s.id] = { status: "pending", detail: "" }; });
    setSteps(initial);

    await sleep(120); // brief pause so UI renders

    // ── LAYER 1: File format + size ──────────────────────────────────────
    setStep("layer1_format", "running");
    await sleep(300);
    const l1 = layer1Check(file);
    if (!l1.passed) {
      setStep("layer1_format", "failed", l1.detail);
      // Skip remaining layers
      setStep("layer2_ocr",     "skipped", "Skipped — Layer 1 failed");
      setStep("layer2_keyword", "skipped", "Skipped — Layer 1 failed");
      setStep("layer3_ai",      "skipped", "Skipped — Layer 1 failed");
      const r = {
        isValid: false, verdict: "invalid",
        summary: l1.detail,
        errors: [{ message: l1.detail, source: "layer1" }],
        warnings: [], confidenceScore: 0,
      };
      setResult(r);
      setMs(Date.now() - t0Ref.current);
      setLoading(false);
      if (onResult) onResult(r);
      return;
    }
    setStep("layer1_format", "passed", l1.detail);

    // ── LAYER 2: OCR + keyword check ─────────────────────────────────────
    setStep("layer2_ocr", "running");
    let extractedText = "";
    try {
      extractedText = await extractTextFromFile(file);
    } catch { extractedText = ""; }
    setStep("layer2_ocr", "passed",
      extractedText.length > 50
        ? `Extracted ${extractedText.length} characters`
        : "Image file — text extraction skipped"
    );

    setStep("layer2_keyword", "running");
    await sleep(200);
    const l2 = layer2Check(extractedText, docName);

    if (!l2.passed) {
      setStep("layer2_keyword", "failed", l2.detail);
      setStep("layer3_ai", "skipped", "Skipped — document keywords not found");
      const r = {
        isValid: false, verdict: "mismatch",
        summary: `Wrong document type detected. Expected: ${docName}.`,
        errors: [{ message: l2.detail, source: "layer2" }],
        warnings: [], confidenceScore: 15,
      };
      setResult(r);
      setMs(Date.now() - t0Ref.current);
      setLoading(false);
      if (onResult) onResult(r);
      return;
    }
    setStep("layer2_keyword", l2.skipped ? "skipped" : "passed", l2.detail);

    // ── LAYER 3: AI Vision API (only reached if layers 1 & 2 passed) ─────
    setStep("layer3_ai", "running");

    try {
      const fd = new FormData();
      fd.append("file",     file);
      fd.append("doc_name", docName);
      fd.append("scheme",   typeof scheme === "string" ? scheme : JSON.stringify(scheme));
      fd.append("language", language);

const resp = await fetch(`${apiBase}/api/verification/document`, {
  method: "POST",
  body: fd,
  signal
});

      if (!resp.ok) {
        throw new Error(`Server returned ${resp.status}`);
      }

      const data = await resp.json();
      const isValid = data.isValid || data.status === "valid";

      setStep("layer3_ai",
        isValid ? "passed" : "failed",
        data.summary || (isValid ? "AI verification passed" : "AI verification failed")
      );

      const finalResult = {
        ...data,
        isValid,
        verdict: data.verdict || (isValid ? "valid" : "invalid"),
        summary: data.summary || (isValid ? `${docName} verified successfully.` : "Document verification failed."),
      };

      setResult(finalResult);
      setMs(Date.now() - t0Ref.current);
      if (onResult) onResult(finalResult);

    } catch (err) {
      if (err.name === "AbortError") return;
      setStep("layer3_ai", "failed", err.message || "AI service unavailable");
      const r = {
        isValid: false, verdict: "error",
        summary: "AI verification failed. Check server connection.",
        errors: [{ message: err.message }],
        warnings: [], confidenceScore: 0,
      };
      setResult(r);
      setMs(Date.now() - t0Ref.current);
      if (onResult) onResult(r);
    } finally {
      setLoading(false);
    }
  }

  if (!open) return null;

  // ── Progress ──────────────────────────────────────────────────────────
  const totalSteps = STEPS.length;
  const doneSteps  = Object.values(steps).filter(s => s.status !== "pending" && s.status !== "running").length;
  const progressPct = loading ? Math.round((doneSteps / totalSteps) * 90) : 100;

  // ── Result display ────────────────────────────────────────────────────
  const verdict      = result?.verdict;
  const isValid      = result?.isValid;
  const resultClass  = isValid ? "valid" : "invalid";
  const resultEmoji  = isValid ? "✅" : (verdict === "mismatch" ? "🔄" : "❌");
  const resultTitle  = isValid
    ? "Document Verified Successfully"
    : verdict === "mismatch"
      ? "Wrong Document Uploaded"
      : "Verification Failed";
  const resultMsg    = result
    ? (result.errors?.[0]?.message || result.warnings?.[0]?.message || result.summary || "")
    : "";

  const extractedFields = result?.extractedFields || {};
  const fieldEntries    = Object.entries(extractedFields).filter(([, v]) => v);

  // Group steps by layer for display
  const layer1Steps = STEPS.filter(s => s.layer === 1);
  const layer2Steps = STEPS.filter(s => s.layer === 2);
  const layer3Steps = STEPS.filter(s => s.layer === 3);

  function renderStep(def) {
    const s = steps[def.id] || { status: "pending", detail: "" };
    const isPending = s.status === "pending";
    return (
      <div className="vp-step" key={def.id} style={isPending ? { opacity: 0.45 } : {}}>
        <div className={`vp-step-icon ${s.status}`}>
          {s.status === "running"  && <IconSpinner />}
          {s.status === "passed"   && <IconCheck />}
          {s.status === "failed"   && <IconX />}
          {s.status === "skipped"  && <IconSkip />}
          {s.status === "pending"  && <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#D1D5DB", display: "block" }} />}
        </div>
        <div className="vp-step-body">
          <p className={`vp-step-label ${s.status}`}>{def.label}</p>
          {s.detail && <p className={`vp-step-detail ${s.status === "failed" ? "failed" : ""}`}>{s.detail}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="vp-overlay" onClick={e => { if (e.target === e.currentTarget && !loading) onClose?.(); }}>
      <div className="vp-card" role="dialog" aria-modal="true">

        {/* Header */}
        <div className="vp-header">
          <div className="vp-header-icon"><IconDoc /></div>
          <div>
            <p className="vp-title">Verifying: {docName}</p>
            <p className="vp-subtitle">
              {loading
                ? "Running validation checks…"
                : isValid ? "All checks passed." : "Validation stopped early."}
            </p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="vp-progress-bar">
          <div className="vp-progress-fill" style={{ width: `${progressPct}%` }} />
        </div>

        {/* Steps grouped by layer */}
        <div className="vp-steps">
          <p className="vp-layer-label">Layer 1 — File Checks</p>
          {layer1Steps.map(renderStep)}
          <p className="vp-layer-label">Layer 2 — Content Analysis</p>
          {layer2Steps.map(renderStep)}
          <p className="vp-layer-label">Layer 3 — AI Vision</p>
          {layer3Steps.map(renderStep)}
        </div>

        {/* Result */}
        {result && !loading && (
          <div className={`vp-result ${resultClass}`}>
            <div className="vp-result-icon">{resultEmoji}</div>
            <div>
              <p className="vp-result-title">{resultTitle}</p>
              {resultMsg && <p className="vp-result-message">{resultMsg}</p>}
              {ms && <p className="vp-ms">Completed in {ms} ms</p>}
            </div>
          </div>
        )}

        {/* Extracted fields */}
        {fieldEntries.length > 0 && !loading && (
          <div className="vp-fields">
            <p className="vp-fields-title">Extracted Fields</p>
            <div className="vp-fields-grid">
              {fieldEntries.map(([k, v]) => (
                <div key={k}>
                  <p className="vp-field-key">{k.replace(/_/g, " ")}</p>
                  <p className="vp-field-value">{String(v)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="vp-footer">
          {!loading && <button className="vp-btn vp-btn-ghost" onClick={onClose}>Close</button>}
          {!loading && isValid  && <button className="vp-btn vp-btn-primary" onClick={onClose}>Continue →</button>}
          {!loading && !isValid && <button className="vp-btn vp-btn-primary" onClick={onClose}>Upload Again</button>}
        </div>

      </div>
    </div>
  );
}
