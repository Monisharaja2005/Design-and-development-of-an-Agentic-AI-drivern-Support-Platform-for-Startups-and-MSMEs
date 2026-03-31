import React from 'react';

const SchemeCard = ({ scheme, isSelected, saving = false, onToggleSelection, onOpenDetails, t, trText, profile }) => {
  const schemeId = scheme.Scheme_ID || scheme.scheme_id;
  const userState = (profile?.state || '').toLowerCase();
  const schemeState = String(scheme.State_Applicable || '').toLowerCase();
  const isStateScheme = schemeState.includes(userState) && !schemeState.includes('central');

  return (
    <article className="scheme-card">
      <div className="scheme-top">
        <div>
          <h3>{scheme.Scheme_Name}</h3>
          <p>{scheme.Ministry || scheme.state}</p>
        </div>
        <span className={`pill-status ${isStateScheme ? 'state-scheme' : 'central-scheme'}`}>
          {isStateScheme ? `${profile?.state || 'State'} Scheme` : 'Central'}
        </span>
        <span className="pill-status">{scheme.Status}</span>
      </div>
      
      <div className="scheme-meta">
        <span>{scheme.Scheme_Category}</span>
        <span>{scheme.State_Applicable}</span>
        <span>{scheme.Target_Sector}</span>
      </div>
      
      <p className="scheme-desc">
        {scheme.Application_Process}
      </p>
      
      <div className="scheme-footer">
        {scheme.timeline_days && (
          <div>
            <strong>Timeline</strong>
            <span>⏱ {scheme.timeline_days} days</span>
          </div>
        )}
        {scheme.priority_label && (
          <div>
            <strong>Priority</strong>
            <span className={`priority ${scheme.priority_label.toLowerCase()}`}>
              {scheme.priority_label} Priority
            </span>
          </div>
        )}
      </div>
      
      <div className="scheme-actions">
        <button className="btn secondary" onClick={onOpenDetails}>
          View details
        </button>
        <button 
          className={`btn select ${isSelected ? 'active' : ''} ${saving ? 'loading' : ''}`}
          onClick={() => onToggleSelection(schemeId)}
          disabled={saving}
        >
          {saving ? (
            <>
              <span className="spinner"></span>
              Saving...
            </>
          ) : isSelected ? 'Selected' : 'Select'}
        </button>
      </div>
      
      {scheme.Website_URL && (
        <a className="scheme-link" href={scheme.Website_URL} target="_blank" rel="noreferrer">
          Visit scheme page
        </a>
      )}
    </article>
  );
};

export default SchemeCard;

