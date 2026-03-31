// VerificationResult.jsx
import React, { useState } from 'react';

const DECISION_CONFIG = {
  APPROVED: { color: '#16a34a', bg: '#f0fdf4', icon: '✅', label: 'Approved' },
  MANUAL_REVIEW: { color: '#d97706', bg: '#fffbeb', icon: '🔍', label: 'Manual Review' },
  REJECTED: { color: '#dc2626', bg: '#fef2f2', icon: '❌', label: 'Rejected' }
};

function ScoreBar({ label, value, max = 100, color }) {
  return (
    <div className="dv-score-bar-wrap">
      <div className="dv-score-bar-label">
        <span>{label}</span>
        <span>{value}/{max}</span>
      </div>
      <div className="dv-score-bar-track">
        <div
          className="dv-score-bar-fill"
          style={{ width: `${(value / max) * 100}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function ConfidenceGauge({ score }) {
  const angle = -90 + (score / 100) * 180;
  const color = score >= 75 ? '#16a34a' : score >= 50 ? '#d97706' : '#dc2626';

  return (
    <div className="dv-gauge">
      <svg viewBox="0 0 200 120" width="180">
        {/* Background arc */}
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#e5e7eb" strokeWidth="16" strokeLinecap="round" />
        {/* Score arc */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke={color}
          strokeWidth="16"
          strokeLinecap="round"
          strokeDasharray={`${(score / 100) * 251} 251`}
        />
        {/* Needle */}
        <line
          x1="100" y1="100"
          x2={100 + 65 * Math.cos((angle * Math.PI) / 180)}
          y2={100 + 65 * Math.sin((angle * Math.PI) / 180)}
          stroke={color} strokeWidth="3" strokeLinecap="round"
        />
        <circle cx="100" cy="100" r="5" fill={color} />
        {/* Score text */}
        <text x="100" y="85" textAnchor="middle" fontSize="26" fontWeight="bold" fill={color}>
          {score}%
        </text>
      </svg>
      <div className="dv-gauge-label">Confidence Score</div>
    </div>
  );
}

export default function VerificationResult({ results, batchResult }) {
  const [expandedDoc, setExpandedDoc] = useState(null);

  const overallScore = batchResult?.overall_score || 0;
  const overallDecision = batchResult?.overall_decision || 'MANUAL_REVIEW';
  const config = DECISION_CONFIG[overallDecision] || DECISION_CONFIG.MANUAL_REVIEW;
  const crossValidation = batchResult?.cross_validation;

  return (
    <div className="dv-result-container">
      {/* Overall Decision Banner */}
      <div className="dv-decision-banner" style={{ background: config.bg, borderColor: config.color }}>
        <div className="dv-decision-left">
          <ConfidenceGauge score={Math.round(overallScore)} />
        </div>
        <div className="dv-decision-right">
          <div className="dv-decision-badge" style={{ color: config.color }}>
            {config.icon} {config.label}
          </div>
          <div className="dv-decision-desc">
            {overallDecision === 'APPROVED' && 'All documents verified successfully. You may proceed.'}
            {overallDecision === 'MANUAL_REVIEW' && 'Some checks need human review before approval.'}
            {overallDecision === 'REJECTED' && 'Critical issues found. Please re-upload valid documents.'}
          </div>
        </div>
      </div>

      {/* Cross-document validation */}
      {crossValidation && (
        <div className="dv-cross-section">
          <h4>🔗 Cross-Document Validation</h4>
          {crossValidation.passed?.map((p, i) => (
            <div key={i} className="dv-cross-pass">✅ {p}</div>
          ))}
          {crossValidation.issues?.map((issue, i) => (
            <div key={i} className="dv-cross-issue">🚨 {issue}</div>
          ))}
          {crossValidation.warnings?.map((w, i) => (
            <div key={i} className="dv-cross-warn">⚠️ {w}</div>
          ))}
        </div>
      )}

      {/* Per-document results */}
      <div className="dv-doc-results">
        <h4>📄 Individual Document Results</h4>
        {Object.entries(results).map(([docType, result]) => {
          if (result.error) return (
            <div key={docType} className="dv-doc-card error">
              <span>❌ {docType}: {result.error}</span>
            </div>
          );

          const conf = result.confidence;
          const val = result.validation;
          const fraud = result.fraud_detection;
          const isExpanded = expandedDoc === docType;

          return (
            <div key={docType} className={`dv-doc-card ${conf?.decision?.toLowerCase() || ''}`}>
              <div className="dv-doc-card-header" onClick={() => setExpandedDoc(isExpanded ? null : docType)}>
                <div className="dv-doc-card-title">
                  <span className="dv-doc-type-badge">{docType.toUpperCase()}</span>
                  <span>{result.filename}</span>
                </div>
                <div className="dv-doc-card-meta">
                  <span className={`dv-mini-decision ${conf?.decision?.toLowerCase()}`}>
                    {conf?.decision} — {conf?.final_score}%
                  </span>
                  <span>{isExpanded ? '▲' : '▼'}</span>
                </div>
              </div>

              {isExpanded && (
                <div className="dv-doc-card-body">
                  {/* Score breakdown */}
                  {conf?.breakdown && (
                    <div className="dv-breakdown">
                      <h5>Score Breakdown</h5>
                      <ScoreBar label="OCR Quality" value={conf.breakdown.ocr_quality} color="#3b82f6" />
                      <ScoreBar label="Classification" value={conf.breakdown.classification} color="#8b5cf6" />
                      <ScoreBar label="Field Validation" value={conf.breakdown.validation} color="#10b981" />
                      <ScoreBar label="Fraud Check" value={conf.breakdown.fraud_check} color="#f59e0b" />
                    </div>
                  )}

                  {/* Extracted fields */}
                  {result.extracted_fields && Object.keys(result.extracted_fields).length > 0 && (
                    <div className="dv-fields">
                      <h5>Extracted Fields</h5>
                      <table className="dv-fields-table">
                        <tbody>
                          {Object.entries(result.extracted_fields).map(([k, v]) => (
                            <tr key={k}>
                              <td className="dv-field-key">{k.replace(/_/g, ' ').toUpperCase()}</td>
                              <td className="dv-field-val">{v}</td>
                              <td>
                                <button
                                  className="dv-copy-btn"
                                  onClick={() => navigator.clipboard.writeText(v)}
                                  title="Copy to clipboard"
                                >📋</button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Issues & Warnings */}
                  {val?.issues?.length > 0 && (
                    <div className="dv-issues">
                      <h5>🚨 Issues</h5>
                      {val.issues.map((iss, i) => <div key={i} className="dv-issue-item">{iss}</div>)}
                    </div>
                  )}
                  {val?.warnings?.length > 0 && (
                    <div className="dv-warnings">
                      <h5>⚠️ Warnings</h5>
                      {val.warnings.map((w, i) => <div key={i} className="dv-warn-item">{w}</div>)}
                    </div>
                  )}

                  {/* Fraud report */}
                  {fraud && (
                    <div className={`dv-fraud-report ${fraud.fraud_detected ? 'detected' : 'clean'}`}>
                      <h5>🔬 Fraud Detection</h5>
                      <span>Risk: {fraud.risk_level} | Score: {fraud.fraud_score}/100</span>
                      {fraud.fraud_detected && (
                        <div className="dv-fraud-alert">
                          ⚠️ Potential tampering detected. Please upload original document.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}