import React from 'react';
import SchemeCard from './SchemeCard';

const SchemeGrid = ({ 
  schemes, 
  selectedSchemes, 
  onToggleSelection, 
  onOpenDetails, 
  t, 
  trText, 
  localizeSchemeStatus,
  getLocalizedSchemeName,
  userState,
  isShortlist = false 
}) => {
  return (
    <div className="scheme-grid">
      {Array.isArray(schemes) && schemes.length > 0 ? schemes.map((scheme, idx) => {
        const schemeId = scheme.Scheme_ID || scheme.scheme_id;
        const isSelected = Boolean(selectedSchemes[schemeId]);
        
        return (
          <SchemeCard
            key={schemeId || idx}
            scheme={scheme}
            isSelected={isSelected}
            onToggleSelection={() => onToggleSelection(schemeId)}
            onOpenDetails={() => onOpenDetails(scheme)}
            t={t}
            trText={trText}
            localizeSchemeStatus={localizeSchemeStatus}
            getLocalizedSchemeName={getLocalizedSchemeName}
            userState={userState}
          />
        );
      }) : (
        <div>{t("no_schemes_found", "No schemes found")}</div>
      )}
    </div>
  );
};

export default SchemeGrid;

