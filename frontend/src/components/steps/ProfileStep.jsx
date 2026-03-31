import React from 'react';

const ProfileStep = ({ 
  formData, 
  errors, 
  profileSectionIndex, 
  profileSections, 
  profileCompleteness, 
  womenCategoryEnabled,
  profileSectionProgress,
  onProfileChange,
  onNext,
  onSectionChange,
  validatePanFromProfile,
  panValidation,
  t, 
  trText 
}) => {
  const currentProfileSection = profileSections[profileSectionIndex];

  const renderPromoterSection = () => (
    <div className="profile-stage-grid">
      <div className="field dark-field">
        <label htmlFor="ownerName">{trText("Promoter Full Name *")}</label>
        <input id="ownerName" name="ownerName" value={formData.profile.ownerName} onChange={onProfileChange} placeholder={trText("As per Aadhaar")} />
        {errors.ownerName && <span className="error">{trText(errors.ownerName)}</span>}
      </div>
      <div className="field dark-field">
        <label htmlFor="promoterDob">{trText("Date of Birth *")}</label>
        <input id="promoterDob" name="promoterDob" type="date" value={formData.profile.promoterDob} onChange={onProfileChange} />
        {errors.promoterDob && <span className="error">{trText(errors.promoterDob)}</span>}
      </div>
      <div className="field dark-field">
        <label htmlFor="gender">{trText("Gender *")}</label>
        <select id="gender" name="gender" value={formData.profile.gender} onChange={onProfileChange}>
          <option value="">{t("choose", "Select")}</option>
          {/* genderOptions */}
          {["Female", "Male", "Other", "Prefer not to say"].map((option) => (
            <option key={option} value={option}>{trText(option)}</option>
          ))}
        </select>
        {errors.gender && <span className="error">{trText(errors.gender)}</span>}
      </div>
      {/* Continue with all promoter fields... mobileNumber, socialCategory, email, aadhaarNumber, pan (with validation), womenCategory, education, priorExperience */}
      <div className="field dark-field">
        <label htmlFor="pan">{trText("PAN Number *")}</label>
        <div className="inline-verify-row">
          <input id="pan" name="pan" value={formData.profile.pan} onChange={onProfileChange} onBlur={validatePanFromProfile} placeholder="AAAAA0000A" />
          <button type="button" className="verify-inline-btn" onClick={validatePanFromProfile}>
            {panValidation.status === "loading" ? trText("Checking...") : trText("Verify")}
          </button>
        </div>
        {errors.pan && <span className="error">{trText(errors.pan)}</span>}
        {panValidation.message && <span className={`verify-inline-note ${panValidation.status}`}>
          {trText(panValidation.message)}
        </span>}
      </div>
      {/* ... all other promoter fields */}
    </div>
  );

  // Similar render functions for business, entity, financial, location sections...

  return (
    <>
      <div className="profile-wizard">
        <div className="profile-wizard-top">
          {profileSections.map((section, index) => (
            <button
              key={section.id}
              type="button"
              className={`profile-chip ${index === profileSectionIndex ? "active" : ""} ${index < profileSectionIndex ? "done" : ""}`}
              onClick={() => onSectionChange(index)}
            >
              {trText(section.title)}
            </button>
          ))}
        </div>

        <section className="profile-stage-card">
          <div className="profile-stage-head">
            <span className="profile-stage-kicker">{trText(currentProfileSection.step)}</span>
            <h3>{trText(currentProfileSection.title)}</h3>
          </div>

          {currentProfileSection.id === "promoter" && renderPromoterSection()}
          {currentProfileSection.id === "business" && renderBusinessSection()}
          {currentProfileSection.id === "entity" && renderEntitySection()}
          {currentProfileSection.id === "financial" && renderFinancialSection()}
          {currentProfileSection.id === "location" && renderLocationSection()}

          <div className="profile-stage-progress">
            <span style={{ width: `${profileSectionProgress}%` }} />
          </div>
          <div className="field dark-field full-width">
            <label htmlFor="notes">{t("notes", "Notes")}</label>
            <textarea id="notes" name="notes" value={formData.profile.notes} onChange={onProfileChange} placeholder={trText("Add any context required for eligibility checks.")} />
          </div>
        </section>
      </div>
    </>
  );
};

export default ProfileStep;

