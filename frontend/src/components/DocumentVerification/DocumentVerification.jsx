// DocumentVerification.jsx — Main container component
import React, { useState, useCallback } from 'react';
import UploadZone from './UploadZone';
import DocumentCard from './DocumentCard';
import VerificationResult from './VerificationResult';
import GuidancePanel from './GuidancePanel';
import './DocumentVerification.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';
export default function DocumentVerification({ schemeId, schemeName, requiredDocs = [] }) {
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [verificationResults, setVerificationResults] = useState({});
  const [batchResult, setBatchResult] = useState(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [activeStep, setActiveStep] = useState('upload'); // upload | verifying | results

  const handleFileUpload = useCallback((docType, file) => {
    setUploadedDocs(prev => {
      const existing = prev.findIndex(d => d.docType === docType);
      const newDoc = { docType, file, status: 'pending', name: file.name };
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = newDoc;
        return updated;
      }
      return [...prev, newDoc];
    });
  }, []);

  const handleRemoveDoc = useCallback((docType) => {
    setUploadedDocs(prev => prev.filter(d => d.docType !== docType));
    setVerificationResults(prev => {
      const updated = { ...prev };
      delete updated[docType];
      return updated;
    });
  }, []);

  const verifySingle = async (docType, file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type_hint', docType);
    if (schemeId) formData.append('scheme_id', schemeId);

    const res = await fetch(`${API_BASE}/api/verification/document`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  };

  const handleVerifyAll = async () => {
    if (uploadedDocs.length === 0) return;
    setIsVerifying(true);
    setActiveStep('verifying');

    // Verify each doc individually first
    const results = {};
    for (const doc of uploadedDocs) {
      setUploadedDocs(prev =>
        prev.map(d => d.docType === doc.docType ? { ...d, status: 'verifying' } : d)
      );
      try {
        const result = await verifySingle(doc.docType, doc.file);
        results[doc.docType] = { ...result, status: 'done' };
        setUploadedDocs(prev =>
          prev.map(d => d.docType === doc.docType ? { ...d, status: 'done' } : d)
        );
        setVerificationResults(prev => ({ ...prev, [doc.docType]: result }));
      } catch (err) {
        results[doc.docType] = { error: err.message, status: 'error' };
        setUploadedDocs(prev =>
          prev.map(d => d.docType === doc.docType ? { ...d, status: 'error' } : d)
        );
      }
    }

    // Batch cross-validation
    try {
      const batchForm = new FormData();
      uploadedDocs.forEach(doc => batchForm.append('files', doc.file));
      if (schemeId) batchForm.append('scheme_id', schemeId);

      const batchRes = await fetch(`${API_BASE}/api/verification/batch`, {
        method: 'POST',
        body: batchForm
      });
      if (batchRes.ok) {
        const batchData = await batchRes.json();
        setBatchResult(batchData);
      }
    } catch (err) {
      console.error('Batch validation error:', err);
    }

    setIsVerifying(false);
    setActiveStep('results');
  };

  const uploadedTypes = uploadedDocs.map(d => d.docType);
  const missingDocs = requiredDocs.filter(d => !uploadedTypes.includes(d.type || d));
  const allRequiredUploaded = missingDocs.length === 0;

  return (
    <div className="dv-container">
      {/* Header */}
      <div className="dv-header">
        <div className="dv-header-left">
          <span className="dv-icon">🔍</span>
          <div>
            <h2>Document Verification</h2>
            {schemeName && <p className="dv-scheme-name">Scheme: {schemeName}</p>}
          </div>
        </div>
        <div className="dv-step-indicator">
{['upload', 'verifying', 'results'].map((step, i) => {
            const steps = ['upload', 'verifying', 'results'];
            const currentIndex = steps.indexOf(activeStep);
            return (
              <div key={step} className={`dv-step ${activeStep === step ? 'active' : ''} ${currentIndex >= i ? 'completed' : ''}`}>
                <span className="dv-step-num">{i + 1}</span>
                <span className="dv-step-label">{step.charAt(0).toUpperCase() + step.slice(1)}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="dv-body">
        {/* Left: Upload Panel */}
        <div className="dv-left">
          <div className="dv-section-title">
            Required Documents
            <span className="dv-badge">{uploadedDocs.length}/{requiredDocs.length || '?'}</span>
          </div>

          {/* Required doc upload zones */}
          {requiredDocs.map((doc, i) => {
            const docType = doc.type || doc;
            const docLabel = doc.label || doc;
            const uploaded = uploadedDocs.find(d => d.docType === docType);
            return (
              <UploadZone
                key={i}
                docType={docType}
                docLabel={docLabel}
                uploaded={uploaded}
                onUpload={handleFileUpload}
                onRemove={handleRemoveDoc}
                result={verificationResults[docType]}
              />
            );
          })}

          {/* If no scheme specified, allow free upload */}
          {requiredDocs.length === 0 && (
            <UploadZone
              docType="general"
              docLabel="Upload Any Document"
              uploaded={uploadedDocs.find(d => d.docType === 'general')}
              onUpload={handleFileUpload}
              onRemove={handleRemoveDoc}
              result={verificationResults['general']}
            />
          )}

          {/* Missing docs warning */}
          {missingDocs.length > 0 && (
            <div className="dv-missing-warning">
              ⚠️ Missing: {missingDocs.map(d => d.label || d).join(', ')}
            </div>
          )}

          {/* Verify button */}
          <button
            className={`dv-verify-btn ${isVerifying ? 'verifying' : ''}`}
            onClick={handleVerifyAll}
            disabled={isVerifying || uploadedDocs.length === 0}
          >
            {isVerifying ? (
              <><span className="dv-spinner" /> Verifying...</>
            ) : (
              <>🔒 Verify All Documents</>
            )}
          </button>
        </div>

        {/* Right: Results + Guidance */}
        <div className="dv-right">
          {activeStep === 'upload' && (
            <div className="dv-empty-state">
              <div className="dv-empty-icon">📋</div>
              <h3>Upload documents to begin verification</h3>
              <p>Supported: PDF, JPG, PNG — Max 10MB per file</p>
              <ul className="dv-feature-list">
                <li>✅ AI-powered OCR extraction</li>
                <li>✅ Fraud & tamper detection</li>
                <li>✅ Cross-document validation</li>
                <li>✅ Government format compliance</li>
              </ul>
            </div>
          )}

          {activeStep === 'verifying' && (
            <div className="dv-verifying-state">
              <div className="dv-verify-animation">
{uploadedDocs.map(doc => (
                  <DocumentCard key={doc.docType} files={[doc]} />
                ))}
              </div>
            </div>
          )}

          {activeStep === 'results' && (
            <>
              <VerificationResult
                results={verificationResults}
                batchResult={batchResult}
              />
              <GuidancePanel
                batchResult={batchResult}
                schemeName={schemeName}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}