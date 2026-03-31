import React from 'react';

const SchemeFilters = ({ t }) => {
  return (
    <div className="filters">
      <div className="helper">
        AI Recommendations ({matchedSchemes} matched schemes)
      </div>

      <input
        className="search"
        placeholder={t("search", "Search") + " by scheme name or ministry"}
      />
    </div>
  );
};

export default SchemeFilters;

