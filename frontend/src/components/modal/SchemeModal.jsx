import React from 'react';

const SchemeModal = ({ activeScheme, t, trText, verificationReport, onCloseModal }) => {
  if (!activeScheme) return null;

  return (
    <div className="modal-backdrop" onClick={onCloseModal}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{trText(activeScheme.Scheme_Name)}</h3>
          <button type="button" className="ghost-btn" onClick={onCloseModal}>
            {t("close")}
          </button>
        </div>
        <div className="modal-body">
          <p><strong>{t("ministry")}:</strong> {trText(activeScheme.Ministry)}</p>
          <p><strong>{t("category")}:</strong> {trText(activeScheme.Scheme_Category)}</p>
          <p><strong>{t("status")}:</strong> {trText(activeScheme.Status)}</p>
          <p><strong>{t("timeline")}:</strong> {activeScheme.Timeline_Days} {t("days")}</p>
          
          {activeScheme.Website_URL && (
            <a className="scheme-link" href={activeScheme.Website_URL} target="_blank" rel="noreferrer">
              {t("visit_scheme_page")}
            </a>
          )}

          {/* Chat section placeholder */}
          <div className="chat-panel">
            <div className="chat-header">
              <strong>{t("scheme_detail_assistant")}</strong>
            </div>
            {/* Chat messages, input will receive full props during App.jsx integration */}
          </div>

          {/* Verification panel placeholder */}
          {verificationReport && (
            <div className="verification-panel">
              <span className="pill-status tone-good">
                Score: {verificationReport.authenticity_score}%
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SchemeModal;

