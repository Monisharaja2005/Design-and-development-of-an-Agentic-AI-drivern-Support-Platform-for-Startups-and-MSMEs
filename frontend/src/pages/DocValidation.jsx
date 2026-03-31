import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CloudArrowUpIcon,
  DocumentCheckIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  ShieldCheckIcon,
  BookmarkIcon,
  DocumentTextIcon,
  TrashIcon,
  ChartBarIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { useTranslation } from 'react-i18next';
import ValidationPopup from "../components/ValidationPopup";

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';

const FALLBACK_DOC_TYPES = [
  'Aadhaar Card',
  'PAN Card',
  'Udyam Registration Certificate',
  'GST Certificate',
  'Bank Statement',
  'Project Report / DPR',
  'Partnership Deed / MOA',
  'ITR',
  'CA Certificate',
  'Business Address Proof',
];

const STATUS_CONFIG = {
  verified: {
    color: 'text-emerald-700',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    icon: CheckCircleIcon,
    labelKey: 'validation.statuses.verified',
    labelDefault: 'Verified',
  },
  review: {
    color: 'text-amber-700',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    icon: ExclamationTriangleIcon,
    labelKey: 'validation.statuses.needs_review',
    labelDefault: 'Needs Review',
  },
  invalid: {
    color: 'text-red-700',
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: XMarkIcon,
    labelKey: 'validation.statuses.invalid',
    labelDefault: 'Invalid',
  },
  pending: {
    color: 'text-slate-500',
    bg: 'bg-slate-50',
    border: 'border-slate-200',
    icon: ClockIcon,
    labelKey: 'validation.statuses.awaiting_check',
    labelDefault: 'Awaiting Check',
  },
};

function normalizeText(value) {
  return String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
}

function getSchemeId(scheme) {
  return scheme?.scheme_id || scheme?.scheme_code || scheme?.id || '';
}

function getSchemeName(scheme) {
  return scheme?.scheme_name || scheme?.Scheme_Name || scheme?.name || 'Selected Scheme';
}

function getSchemeDocs(scheme) {
  const candidates = [
    scheme?.required_documents,
    scheme?.ai_required_documents,
    scheme?.documents_required,
    scheme?.documents,
    scheme?.docs,
  ];

  for (const value of candidates) {
    if (Array.isArray(value) && value.length) {
      return Array.from(new Set(value.map((item) => String(item || '').trim()).filter(Boolean)));
    }
    if (typeof value === 'string' && value.trim()) {
      return Array.from(
        new Set(
          value
            .split(/\n|,|;/)
            .map((item) => item.trim())
            .filter(Boolean),
        ),
      );
    }
  }

  return [];
}

function buildDocLabelMap(documents, labels = {}) {
  return documents.reduce((map, document) => {
    map[document] = labels[document] || document;
    return map;
  }, {});
}

function getDocumentLabel(document, labels) {
  return labels[document] || document;
}

function documentsMatch(left, right) {
  const leftText = normalizeText(left);
  const rightText = normalizeText(right);
  if (!leftText || !rightText) return false;
  if (leftText === rightText) return true;
  if (leftText.includes(rightText) || rightText.includes(leftText)) return true;

  const leftTokens = new Set(leftText.split(' ').filter(Boolean));
  const rightTokens = new Set(rightText.split(' ').filter(Boolean));
  const overlap = [...leftTokens].filter((token) => rightTokens.has(token)).length;
  const minSize = Math.min(leftTokens.size, rightTokens.size);
  return minSize > 0 && overlap / minSize >= 0.6;
}

function guessDocType(fileName, options) {
  return options.find((option) => documentsMatch(fileName, option)) || '';
}

function DropZone({ onFile, isDragging, setIsDragging, t, disabled }) {
  const fileRef = useRef(null);

  const handleDrop = (event) => {
    event.preventDefault();
    if (disabled) return;
    setIsDragging(false);
    Array.from(event.dataTransfer.files).forEach(onFile);
  };

  return (
    <div
      className={`upload-zone ${isDragging ? 'upload-zone-active' : ''} ${disabled ? 'opacity-60 cursor-not-allowed' : ''}`}
      onDragOver={(event) => {
        if (disabled) return;
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => {
        if (!disabled) fileRef.current?.click();
      }}
    >
      <input
        type="file"
        ref={fileRef}
        className="hidden"
        multiple
        accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx"
        onChange={(event) => {
          Array.from(event.target.files || []).forEach(onFile);
          event.target.value = '';
        }}
      />
      <CloudArrowUpIcon className={`w-10 h-10 transition-colors ${isDragging ? 'text-brand-primary' : 'text-slate-300'}`} />
      <div>
        <p className={`font-bold text-sm transition-colors ${isDragging ? 'text-brand-primary' : 'text-slate-600'}`}>
          {disabled
            ? t('validation.dropzone_disabled', 'Shortlist a scheme first to enable validation uploads.')
            : isDragging
              ? t('validation.dropzone_active', 'Drop your files to attach them to this scheme')
              : t('validation.dropzone_idle', 'Upload documents for the selected shortlisted scheme')}
        </p>
        <p className="text-xs text-slate-400 font-medium mt-1">
          {t('validation.max_size', 'Accepted: PDF, JPG, PNG, WebP, DOC, DOCX')}
        </p>
      </div>
    </div>
  );
}

function ReadinessBar({ score, verifiedCount, totalCount, t }) {
  const color = score >= 80 ? 'bg-emerald-500' : score >= 50 ? 'bg-amber-500' : 'bg-red-500';
  const textColor = score >= 80 ? 'text-emerald-600' : score >= 50 ? 'text-amber-600' : 'text-red-600';

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="label-xs">{t('validation.readiness_score', 'Scheme Readiness Score')}</span>
        <span className={`text-2xl font-black ${textColor}`}>{score}%</span>
      </div>
      <div className="progress-bar h-2">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${color}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <p className="text-xs text-slate-400 font-medium">
        {totalCount === 0
          ? t('validation.no_requirements_loaded', 'No scheme-specific requirements were loaded yet.')
          : t('validation.verified_requirements', {
              verified: verifiedCount,
              total: totalCount,
              defaultValue: `${verifiedCount} of ${totalCount} required documents are verified for this shortlist item.`,
            })}
      </p>
    </div>
  );
}

function EmptyShortlistState() {
  const { t } = useTranslation();
  return (
    <div className="intelligence-card p-8 text-center">
      <DocumentCheckIcon className="w-12 h-12 mx-auto text-brand-primary/50 mb-4" />
      <h3 className="font-black text-slate-900 text-lg mb-2">{t('validation.empty_shortlist.title', 'No shortlisted schemes yet')}</h3>
      <p className="text-sm text-slate-500 max-w-xl mx-auto leading-relaxed">
        {t(
          'validation.empty_shortlist.subtitle',
          'This document verification flow now works only for the schemes the user shortlisted in Scheme Discovery. Save a scheme there, then come back here to validate its required documents.',
        )}
      </p>
    </div>
  );
}

export default function DocValidation({
  savedSchemes = [],
  lastSelectedSchemeId = '',
  activeScheme: activeSchemeFromParent = null,
  onLastSelectedSchemeChange,
  onSavedSchemesChange,
}) {
  const { t, i18n } = useTranslation();
  const [activeSchemeId, setActiveSchemeId] = useState(() => {
    // Prefer the parent-derived activeScheme (already resolved from DB)
    if (activeSchemeFromParent) return getSchemeId(activeSchemeFromParent);
    const preferredExists = savedSchemes.some((scheme) => getSchemeId(scheme) === lastSelectedSchemeId);
    return preferredExists ? lastSelectedSchemeId : getSchemeId(savedSchemes[0]);
  });
  const [requiredDocs, setRequiredDocs] = useState([]);
  const [requiredDocLabels, setRequiredDocLabels] = useState({});
  const [documents, setDocuments] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [validating, setValidating] = useState(null);
  const [contextLoading, setContextLoading] = useState(false);
  const [contextError, setContextError] = useState('');
  // Enriched scheme = activeScheme merged with required_documents from backend
  const [enrichedScheme, setEnrichedScheme] = useState(null);

  const [showPopup, setShowPopup] = useState(false);
  const [pendingFile, setPendingFile] = useState(null);
  const [selectedDocumentName, setSelectedDocumentName] = useState('');
  const [pendingDocumentId, setPendingDocumentId] = useState(null);

  const previousSchemeIdRef = useRef('');

  // Sync when parent loads schemes from DB after mount (async hydration)
  useEffect(() => {
    if (!activeSchemeFromParent) return;
    const parentId = getSchemeId(activeSchemeFromParent);
    if (parentId && parentId !== activeSchemeId) {
      setActiveSchemeId(parentId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSchemeFromParent]);

  useEffect(() => {
    if (!savedSchemes.length) {
      setActiveSchemeId('');
      return;
    }

    const activeExists = savedSchemes.some((scheme) => getSchemeId(scheme) === activeSchemeId);
    if (!activeExists) {
      const preferredExists = savedSchemes.some((scheme) => getSchemeId(scheme) === lastSelectedSchemeId);
      const nextId = preferredExists ? lastSelectedSchemeId : getSchemeId(savedSchemes[0]);
      setActiveSchemeId(nextId);
    }
  }, [activeSchemeId, lastSelectedSchemeId, savedSchemes]);

  const activeScheme = useMemo(
    () => savedSchemes.find((scheme) => getSchemeId(scheme) === activeSchemeId) || null,
    [activeSchemeId, savedSchemes],  // savedSchemes was missing — caused activeScheme to always be null
  );

  useEffect(() => {
    if (!activeScheme) {
      setRequiredDocs([]);
      setRequiredDocLabels({});
      setDocuments([]);
      setContextError('');
      setEnrichedScheme(null);
      previousSchemeIdRef.current = '';
      return;
    }

    const schemeId = getSchemeId(activeScheme);
    const fallbackDocs = getSchemeDocs(activeScheme);
    const schemeChanged = previousSchemeIdRef.current !== schemeId;
    previousSchemeIdRef.current = schemeId;

    onLastSelectedSchemeChange?.(schemeId);
    if (schemeChanged) {
      setDocuments([]);
    }
    setRequiredDocs(fallbackDocs);
    setRequiredDocLabels(buildDocLabelMap(fallbackDocs));
    // Set enrichedScheme immediately with whatever docs we have locally,
    // so ValidationPopup is never blocked waiting for the context fetch.
    setEnrichedScheme(fallbackDocs.length ? { ...activeScheme, required_documents: fallbackDocs } : activeScheme);
    setContextLoading(true);
    setContextError('');

    fetch(`${API_BASE}/v1/validation/context`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(60000),
      body: JSON.stringify({
        scheme_id: schemeId,
        scheme: activeScheme,
        language: i18n.language,
      }),
    })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || t('validation.requirement_load_error', 'Could not load scheme requirements.'));
        }
        const docs = Array.isArray(data.required_documents) ? data.required_documents : [];
        const labels = data.required_document_labels && typeof data.required_document_labels === 'object'
          ? data.required_document_labels
          : {};
        if (docs.length) {
          setRequiredDocs(docs);
          setRequiredDocLabels(buildDocLabelMap(docs, labels));
          // Merge the real required_documents into the scheme object so
          // ValidationPopup sends a fully-populated scheme to the upload endpoint.
          setEnrichedScheme({ ...activeScheme, required_documents: docs });
        } else {
          setRequiredDocLabels(buildDocLabelMap(fallbackDocs, labels));
          setEnrichedScheme(activeScheme);
        }
      })
      .catch((error) => {
        if (!fallbackDocs.length) {
          setContextError(error.message || t('validation.requirement_load_error', 'Could not load scheme requirements.'));
        }
      })
      .finally(() => {
        setContextLoading(false);
      });
}, [activeSchemeId, i18n.language]);

  const docTypeOptions = useMemo(
    () => (requiredDocs.length ? requiredDocs : FALLBACK_DOC_TYPES),
    [requiredDocs],
  );

  const handleFile = useCallback(
    (file) => {
      if (!activeScheme) return;

      const docId = `doc-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
      const guessedType = guessDocType(file.name, docTypeOptions);

      setDocuments((previous) => [
        ...previous,
        {
          id: docId,
          file,
          name: file.name,
          size: file.size,
          type: file.type,
          docType: guessedType,
          status: 'pending',
          trustScore: null,
          validationSummary: '',
          validationDetails: '',
          matchedRequirement: '',
        },
      ]);
    },
    [activeScheme, docTypeOptions],
  );

  const updateDocType = (id, docType) => {
    setDocuments((previous) =>
      previous.map((document) => (
        document.id === id
          ? {
              ...document,
              docType,
              status: 'pending',
              validationSummary: '',
              validationDetails: '',
              matchedRequirement: '',
            }
          : document
      )),
    );
  };

  const removeDoc = (id) => {
    setDocuments((previous) => previous.filter((document) => document.id !== id));
  };

  const handleFileSelected = useCallback((document) => {
    if (!activeScheme) {
      alert(t('validation.alerts.select_scheme', 'Please select a shortlisted scheme first.'));
      return;
    }
    if (!document.docType) {
      alert(t('validation.alerts.select_document_type', 'Please select a document type first.'));
      return;
    }
    setPendingDocumentId(document.id);
    setPendingFile(document.file);
    setSelectedDocumentName(document.docType);
    setShowPopup(true);
    setValidating(document.id);
  }, [activeScheme, t]);

  const validateDocument = useCallback((document) => {
    if (!activeScheme) {
      alert(t('validation.alerts.select_scheme', 'Please select a shortlisted scheme first.'));
      return;
    }
    if (!document.docType) {
      alert(t('validation.alerts.select_document_type', 'Please select a document type first.'));
      return;
    }
    setPendingDocumentId(document.id);
    setPendingFile(document.file);
    setSelectedDocumentName(document.docType);
    setShowPopup(true);
    setValidating(document.id);
  }, [activeScheme, t]);

  const validateAll = useCallback(() => {
    const first = documents.find((doc) => doc.docType && doc.status !== 'verified');
    if (first) validateDocument(first);
  }, [documents, validateDocument]);

  const statusStats = useMemo(() => ({
    verified: documents.filter((document) => document.status === 'verified').length,
    review: documents.filter((document) => document.status === 'review').length,
    invalid: documents.filter((document) => document.status === 'invalid').length,
    pending: documents.filter((document) => document.status === 'pending').length,
  }), [documents]);

  const verifiedRequirementCount = useMemo(
    () => requiredDocs.filter((requirement) => (
      documents.some(
        (document) => document.status === 'verified' && documentsMatch(document.docType, requirement),
      )
    )).length,
    [documents, requiredDocs],
  );

  const readinessScore = requiredDocs.length
    ? Math.round((verifiedRequirementCount / requiredDocs.length) * 100)
    : 0;

  if (!savedSchemes.length) {
    return <EmptyShortlistState />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="page-title">{t('common.validation', 'Document Validation')}</h2>
          <p className="section-subtitle mt-1">
            {t('validation.subtitle', 'Validate uploaded documents only against the scheme the user shortlisted.')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setDocuments([])}
            className="btn-secondary"
            disabled={!documents.length}
          >
            <ArrowPathIcon className="w-4 h-4" />
            {t('validation.reset_uploads', 'Reset uploads')}
          </button>
          <button
            onClick={validateAll}
            className="btn-primary"
            disabled={!documents.length || !activeScheme}
          >
            <ShieldCheckIcon className="w-5 h-5" />
            {t('validation.validate_all', 'Validate all')}
          </button>
        </div>
      </div>

      <div className="intelligence-card p-5 space-y-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 flex-shrink-0">
            <DocumentCheckIcon className="w-5 h-5 text-brand-primary" />
            <span className="font-bold text-slate-700 text-sm">{t('validation.shortlisted_scheme', 'Shortlisted scheme:')}</span>
          </div>
          <div className="relative flex-1 min-w-[220px]">
            <select
              className="v4-select w-full pr-10"
              value={activeSchemeId}
              onChange={(event) => setActiveSchemeId(event.target.value)}
            >
              {savedSchemes.map((scheme) => (
                <option key={getSchemeId(scheme)} value={getSchemeId(scheme)}>
                  {getSchemeName(scheme)}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
          <span className="badge-primary">
            <BookmarkIcon className="w-3 h-3" />
            {t('validation.shortlisted_count', {
              count: savedSchemes.length,
              defaultValue: `${savedSchemes.length} shortlisted`,
            })}
          </span>
        </div>

        {activeScheme && (
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="font-black text-slate-900 text-sm">{getSchemeName(activeScheme)}</span>
              {(activeScheme.state || activeScheme.State_Applicable) && (
                <span className="text-[10px] font-bold uppercase tracking-wider text-brand-primary">
                  {(activeScheme.state || activeScheme.State_Applicable)}
                </span>
              )}
              {(activeScheme.sector || activeScheme.Target_Sector) && (
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  {(activeScheme.sector || activeScheme.Target_Sector)}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 font-medium leading-relaxed">
              {t(
                'validation.scope_text',
                'Uploads on this page are scoped to the currently selected shortlist item only. Switching schemes resets the upload list so we do not mix documents across applications.',
              )}
            </p>
            {contextLoading && (
              <p className="text-[11px] text-slate-400 font-semibold mt-2">
                {t('validation.refreshing_requirements', 'Refreshing the latest scheme requirements...')}
              </p>
            )}
            {contextError && (
              <p className="text-[11px] text-amber-600 font-semibold mt-2">{contextError}</p>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-5">
          <DropZone
            onFile={handleFile}
            isDragging={isDragging}
            setIsDragging={setIsDragging}
            t={t}
            disabled={!activeScheme}
          />

          {documents.length === 0 && (
            <div className="text-center py-10 text-slate-400">
              <DocumentTextIcon className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="font-medium text-sm">{t('validation.no_documents_title', 'No documents uploaded for this scheme yet.')}</p>
              <p className="text-xs mt-1">
                {t(
                  'validation.no_documents_subtitle',
                  'Upload files above, map each file to a required document, and run validation.',
                )}
              </p>
            </div>
          )}

          <div className="space-y-4">
            {documents.map((document) => {
              const statusCfg = STATUS_CONFIG[document.status] || STATUS_CONFIG.pending;
              const isBeingValidated = validating === document.id;
              const statusLabel = t(statusCfg.labelKey, statusCfg.labelDefault);

              return (
                <div
                  key={document.id}
                  className="intelligence-card p-5 animate-in fade-in slide-in-from-bottom-2 duration-300"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center flex-shrink-0">
                      <DocumentTextIcon className="w-6 h-6 text-slate-500" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div className="min-w-0">
                          <p className="font-bold text-slate-900 text-sm truncate">{document.name}</p>
                          <p className="text-[10px] text-slate-400 font-medium">
                            {(document.size / 1024).toFixed(0)}KB
                          </p>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-black border ${statusCfg.bg} ${statusCfg.border} ${statusCfg.color}`}>
                            <statusCfg.icon className="w-3 h-3" />
                            {statusLabel}
                          </div>
                          <button onClick={() => removeDoc(document.id)} className="text-slate-400 hover:text-red-500 transition-colors">
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center gap-3">
                        <div className="relative flex-1 min-w-[180px]">
                          <select
                            className="v4-select text-xs pr-8"
                            value={document.docType}
                            onChange={(event) => updateDocType(document.id, event.target.value)}
                          >
                            <option value="">{t('validation.select_required_document', 'Select required document')}</option>
                            {docTypeOptions.map((option) => (
                              <option key={option} value={option}>
                                {getDocumentLabel(option, requiredDocLabels)}
                              </option>
                            ))}
                          </select>
                          <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </div>
                        </div>
                        <button
                          onClick={() => handleFileSelected(document)}
                          disabled={!document.docType || validating === document.id}
                          className="btn-primary text-xs px-4 py-2 disabled:opacity-50"
                        >
                          {isBeingValidated ? (
                            <>
                              <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                              </svg>
                              {t('validation.validating', 'Validating...')}
                            </>
                          ) : (
                            <>
                              <ShieldCheckIcon className="w-3.5 h-3.5" />
                              {t('validation.validate', 'Validate')}
                            </>
                          )}
                        </button>
                      </div>

                      {(document.validationSummary || document.validationDetails) && (
                        <div
                          className={`mt-3 p-3 rounded-xl border text-xs font-medium animate-in fade-in zoom-in-95 duration-200 ${statusCfg.bg} ${statusCfg.border} ${statusCfg.color}`}
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <statusCfg.icon className="w-3.5 h-3.5" />
                            <span className="font-black uppercase tracking-wider">{statusLabel}</span>
                            {document.trustScore !== null && (
                              <span className="ml-auto font-black">
                                {t('validation.trust_score', {
                                  score: document.trustScore,
                                  defaultValue: `Trust: ${document.trustScore}%`,
                                })}
                              </span>
                            )}
                          </div>
                          <div>{document.validationSummary}</div>
                          {document.validationDetails && document.validationDetails !== document.validationSummary && (
                            <div className="mt-1 opacity-80">{document.validationDetails}</div>
                          )}
                          {document.matchedRequirement && (
                            <div className="mt-1 opacity-80">
                              {t('validation.matched_requirement', {
                                requirement: getDocumentLabel(document.matchedRequirement, requiredDocLabels),
                                defaultValue: `Matched scheme requirement: ${getDocumentLabel(document.matchedRequirement, requiredDocLabels)}`,
                              })}
                            </div>
                          )}
                          {document.validatedAt && (
                            <span className="block mt-1 text-[9px] opacity-70">
                              {document.status === 'verified'
                                ? t('validation.validated_at', {
                                    time: document.validatedAt,
                                    defaultValue: `Validated at ${document.validatedAt}`,
                                  })
                                : t('validation.checked_at', {
                                    time: document.validatedAt,
                                    defaultValue: `Checked at ${document.validatedAt}`,
                                  })}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <ValidationPopup
          open={showPopup}
          docName={selectedDocumentName}
          file={pendingFile}
          scheme={enrichedScheme || activeScheme}
          apiBase={API_BASE}
          onResult={(r) => {
            const docId = pendingDocumentId;
            if (docId) {
              const normalizedVerdict = String(r.verdict || '').toLowerCase();
              const numericConfidence = r.confidenceScore == null ? null : Number(r.confidenceScore);
              const mappedStatus = r.isValid
                ? 'verified'
                : normalizedVerdict === 'error'
                  ? 'review'
                  : 'invalid';
              const topDetail = r.summary || r.errors?.[0]?.message || r.warnings?.[0]?.message || '';
              const trustScore = normalizedVerdict === 'error' || Number.isNaN(numericConfidence)
                ? null
                : numericConfidence;
              setDocuments((previous) =>
                previous.map((item) => (
                  item.id === docId
                    ? {
                        ...item,
                        status: mappedStatus,
                        trustScore,
                        validationSummary: r.summary || t('validation.validation_complete', 'Validation complete.'),
                        validationDetails: topDetail,
                        matchedRequirement: r.matchedRequirement || '',
                        validatedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                      }
                    : item
                )),
              );
            }
            setShowPopup(false);
            setValidating(null);
          }}
          onClose={() => {
            setShowPopup(false);
            if (pendingDocumentId) setValidating(null);
          }}
        />

        <div className="space-y-5">
          <div className="intelligence-card p-6">
            <div className="flex items-center gap-2 mb-5">
              <ChartBarIcon className="w-5 h-5 text-brand-primary" />
              <h3 className="font-extrabold text-slate-800">{t('validation.readiness_report', 'Readiness Report')}</h3>
            </div>
            <ReadinessBar
              score={readinessScore}
              verifiedCount={verifiedRequirementCount}
              totalCount={requiredDocs.length}
              t={t}
            />
            <div className="mt-5 grid grid-cols-4 gap-3">
              {[
                { key: 'verified', label: t('validation.statuses.verified', 'Verified'), color: 'text-emerald-600', bg: 'bg-emerald-50' },
                { key: 'review', label: t('validation.statuses.review', 'Review'), color: 'text-amber-600', bg: 'bg-amber-50' },
                { key: 'invalid', label: t('validation.statuses.invalid', 'Invalid'), color: 'text-red-600', bg: 'bg-red-50' },
                { key: 'pending', label: t('validation.statuses.pending', 'Pending'), color: 'text-slate-500', bg: 'bg-slate-100' },
              ].map((item) => (
                <div key={item.key} className={`p-3 ${item.bg} rounded-xl text-center`}>
                  <div className={`text-xl font-black ${item.color}`}>{statusStats[item.key]}</div>
                  <div className={`text-[9px] font-bold uppercase tracking-wider ${item.color} opacity-70`}>{item.label}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="intelligence-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <DocumentCheckIcon className="w-4 h-4 text-brand-primary" />
              <h3 className="font-bold text-slate-800 text-sm">{t('validation.required_documents_title', 'Required documents for this scheme')}</h3>
            </div>
            <div className="space-y-2">
              {(requiredDocs.length ? requiredDocs : FALLBACK_DOC_TYPES).map((requirement) => {
                const uploaded = documents.find((document) => documentsMatch(document.docType, requirement));
                const isVerified = uploaded?.status === 'verified';
                const isReview = uploaded && uploaded.status !== 'verified' && uploaded.status !== 'pending';

                return (
                  <div key={requirement} className="flex items-center gap-2.5">
                    <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${
                      isVerified
                        ? 'bg-emerald-100 text-emerald-600'
                        : isReview
                          ? 'bg-amber-100 text-amber-600'
                          : uploaded
                            ? 'bg-slate-100 text-slate-500'
                            : 'border-2 border-slate-200'
                    }`}>
                      {isVerified && (
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} stroke="currentColor" d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                      {!isVerified && isReview && <ExclamationTriangleIcon className="w-3 h-3" />}
                      {!isVerified && !isReview && uploaded && <ClockIcon className="w-3 h-3" />}
                    </div>
                    <span className={`text-xs font-medium ${
                      isVerified
                        ? 'text-emerald-700 line-through'
                        : isReview
                          ? 'text-amber-700'
                          : uploaded
                            ? 'text-slate-700'
                            : 'text-slate-600'
                    }`}>
                      {getDocumentLabel(requirement, requiredDocLabels)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="p-5 bg-brand-primary/5 border border-brand-primary/10 rounded-2xl">
            <div className="flex items-center gap-2 mb-2">
              <ShieldCheckIcon className="w-4 h-4 text-brand-primary" />
              <span className="font-black text-brand-primary text-xs uppercase tracking-wider">
                {t('validation.validation_scope', 'Validation scope')}
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium leading-relaxed">
              {t(
                'validation.validation_scope_text',
                "This page is now tied to the user shortlist only. Each upload is checked against the active scheme's requirement list so we do not validate unrelated documents for unrelated schemes.",
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
