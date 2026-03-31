// UploadZone.jsx
import React, { useRef, useState } from 'react';

const STATUS_ICONS = {
  pending: '📄',
  verifying: '⏳',
  done: '✅',
  error: '❌'
};

export default function UploadZone({ docType, docLabel, uploaded, onUpload, onRemove, result }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) onUpload(docType, file);
  };

  const handleChange = (e) => {
    const file = e.target.files[0];
    if (file) onUpload(docType, file);
  };

  const getResultBadge = () => {
    if (!result) return null;
    const score = result.confidence?.final_score;
    const decision = result.confidence?.decision;
    if (!score) return null;
    return (
      <span className={`dv-result-badge ${decision?.toLowerCase()}`}>
        {decision} {score}%
      </span>
    );
  };

  return (
    <div
      className={`dv-upload-zone ${dragging ? 'dragging' : ''} ${uploaded ? 'has-file' : ''} ${uploaded?.status || ''}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !uploaded && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.jpg,.jpeg,.png"
        style={{ display: 'none' }}
        onChange={handleChange}
      />

      <div className="dv-zone-content">
        <div className="dv-zone-left">
          <span className="dv-zone-icon">
            {uploaded ? STATUS_ICONS[uploaded.status] || '📄' : '⬆️'}
          </span>
          <div>
            <div className="dv-zone-label">{docLabel}</div>
            {uploaded && (
              <div className="dv-zone-filename">{uploaded.name}</div>
            )}
            {!uploaded && (
              <div className="dv-zone-hint">Click or drag PDF/JPG/PNG</div>
            )}
          </div>
        </div>

        <div className="dv-zone-right">
          {getResultBadge()}
          {uploaded && (
            <button
              className="dv-remove-btn"
              onClick={(e) => { e.stopPropagation(); onRemove(docType); }}
            >×</button>
          )}
        </div>
      </div>

      {/* Inline mini result */}
      {result && result.validation && (
        <div className="dv-zone-mini-result">
          {result.validation.issues?.length > 0 && (
            <span className="dv-mini-issue">⚠ {result.validation.issues[0]}</span>
          )}
          {result.fraud_detection?.fraud_detected && (
            <span className="dv-mini-fraud">🚨 Fraud risk detected</span>
          )}
        </div>
      )}
    </div>
  );
}