import React, { useState, useEffect } from 'react';
import SchemeGrid from '../schemes/SchemeGrid';
import { getSessionUser, loadUserSchemes } from '../../lib/userWorkspace.js';

const ShortlistStep = ({ 
  shortlistedSchemes: propShortlistedSchemes, 
  selectedSchemes, 
  selectedCount, 
  exportSelectedSchemes, 
  t, 
  trText, 
  localizeSchemeStatus,
  getLocalizedSchemeName,
  userState,
  onToggleSelection,
  onOpenDetails,
  onSchemesLoad 
}) => {
  const [shortlistedSchemes, setShortlistedSchemes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadSaved = async () => {
      const user = getSessionUser();
      if (!user?.email) {
        console.log('[ShortlistStep] No user - using props');
        setShortlistedSchemes(propShortlistedSchemes || []);
        setLoading(false);
        return;
      }

      try {
        console.log(`[ShortlistStep] Loading saved schemes for ${user.email}`);
        const savedIds = await loadUserSchemes(user.email);
        console.log(`[ShortlistStep] Loaded ${savedIds.length} saved scheme IDs`);

        // Notify parent about loaded schemes (for local state sync)
        onSchemesLoad?.(savedIds);

        // Use IDs as schemes (full schemes loaded via parent)
        setShortlistedSchemes(savedIds);
      } catch (error) {
        console.error('[ShortlistStep] Load failed:', error);
        setShortlistedSchemes(propShortlistedSchemes || []);
      } finally {
        setLoading(false);
      }
    };

    loadSaved();
  }, []);

  const displaySchemes = shortlistedSchemes.length > 0 ? shortlistedSchemes : propShortlistedSchemes || [];
  const displayCount = displaySchemes.length;

  return (
    <div className="schemes">
      <div className="saved-bar">
        <div>
          <strong>{t("shortlisted_schemes", "Shortlisted schemes")}</strong>
          <span>{displayCount} {t("selected", "selected")}</span>
        </div>
        <button
          type="button"
          className="btn secondary"
          onClick={exportSelectedSchemes}
          disabled={displayCount === 0}
        >
          {t("export_selected", "Export selected")}
        </button>
      </div>

      {loading ? (
        <div style={{padding: '40px 20px', textAlign: 'center', color: '#666'}}>
          Loading your saved schemes...
        </div>
      ) : displayCount === 0 ? (
        <div className="helper">
          {t(
            "no_schemes_selected",
            "No schemes selected yet. Go back to the Schemes step and choose the ones you want to shortlist."
          )}
        </div>
      ) : (
        <SchemeGrid
          schemes={displaySchemes}
          selectedSchemes={selectedSchemes}
          onToggleSelection={onToggleSelection}
          onOpenDetails={onOpenDetails}
          t={t}
          trText={trText}
          localizeSchemeStatus={localizeSchemeStatus}
          getLocalizedSchemeName={getLocalizedSchemeName}
          userState={userState}
          isShortlist={true}
        />
      )}
    </div>
  );
};

export default ShortlistStep;

