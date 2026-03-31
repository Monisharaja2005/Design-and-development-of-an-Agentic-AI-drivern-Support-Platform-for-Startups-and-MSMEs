// GuidancePanel.jsx — AI-powered application guidance (NOT auto-fill)
import React, { useState } from 'react';

const GUIDANCE_STEPS = {
  APPROVED: [
    { icon: '📋', title: 'Download Pre-filled Form', desc: 'All your extracted data is ready. Click to generate a pre-filled application PDF.', action: 'download_form' },
    { icon: '🌐', title: 'Visit Official Portal', desc: 'Go to the official government scheme portal. Links provided below.', action: 'open_portal' },
    { icon: '📝', title: 'Fill Online Form', desc: 'Use the copy buttons on extracted fields to paste your data accurately.', action: null },
    { icon: '📎', title: 'Attach Verified Documents', desc: 'Upload the same documents you verified here.', action: null },
    { icon: '✅', title: 'Submit Application', desc: 'Review and submit your application.', action: null }
  ],
  MANUAL_REVIEW: [
    { icon: '🔍', title: 'Address Warnings First', desc: 'Fix the yellow-flagged issues before applying. See details above.', action: null },
    { icon: '📞', title: 'Contact Scheme Helpdesk', desc: 'Some issues may require manual clarification with the scheme authority.', action: null },
    { icon: '📋', title: 'Re-upload if Needed', desc: 'If documents are unclear, upload better quality scans.', action: null }
  ],
  REJECTED: [
    { icon: '❌', title: 'Fix Critical Issues', desc: 'Documents have failed validation. Review the red issues above.', action: null },
    { icon: '🏦', title: 'Get Genuine Documents', desc: 'Ensure you have original, unedited government-issued documents.', action: null },
    { icon: '🔄', title: 'Re-upload & Re-verify', desc: 'After obtaining correct documents, restart verification.', action: null }
  ]
};

export default function GuidancePanel({ batchResult, schemeName }) {
  const [copied, setCopied] = useState({});
  const decision = batchResult?.overall_decision || 'MANUAL_REVIEW';
  const steps = GUIDANCE_STEPS[decision] || GUIDANCE_STEPS.MANUAL_REVIEW;

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopied(prev => ({ ...prev, [key]: true }));
    setTimeout(() => setCopied(prev => ({ ...prev, [key]: false })), 2000);
  };

  // Collect all extracted fields for copy panel
  const allFields = {};
  if (batchResult?.documents) {
    Object.values(batchResult.documents).forEach(doc => {
      if (doc.fields) Object.assign(allFields, doc.fields);
    });
  }

  return (
    <div className="dv-guidance-panel">
      <div className="dv-guidance-header">
        <span>🤖</span>
        <div>
          <h4>AI Application Guidance</h4>
          {schemeName && <p>For: {schemeName}</p>}
        </div>
      </div>

      {/* Step-by-step guidance */}
      <div className="dv-guidance-steps">
        {steps.map((step, i) => (
          <div key={i} className="dv-guidance-step">
            <div className="dv-guide-num">{i + 1}</div>
            <div className="dv-guide-body">
              <div className="dv-guide-title">{step.icon} {step.title}</div>
              <div className="dv-guide-desc">{step.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Copy Panel — pre-filled data */}
      {Object.keys(allFields).length > 0 && (
        <div className="dv-copy-panel">
          <h5>📋 Pre-filled Data (Copy to Application)</h5>
          <p className="dv-copy-note">
            ⚠️ This platform does NOT auto-fill government portals.
            Use copy buttons to paste into the official website yourself.
          </p>
          <div className="dv-copy-grid">
            {Object.entries(allFields).map(([key, value]) => (
              <div key={key} className="dv-copy-item">
                <label>{key.replace(/_/g, ' ').toUpperCase()}</label>
                <div className="dv-copy-row">
                  <input type="text" value={value} readOnly />
                  <button
                    onClick={() => copyToClipboard(value, key)}
                    className={`dv-copy-action ${copied[key] ? 'copied' : ''}`}
                  >
                    {copied[key] ? '✓ Copied' : '📋 Copy'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Human-in-loop disclaimer */}
      <div className="dv-disclaimer">
        🔒 This AI verifies documents locally. Your files are never stored permanently.
        Final application must be submitted on official government portals.
      </div>
    </div>
  );
}