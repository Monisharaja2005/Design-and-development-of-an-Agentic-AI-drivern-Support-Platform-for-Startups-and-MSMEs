
import { useMemo, useState } from 'react';

function formatLabel(value) {
  return String(value || '')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function BusinessDashboard({
  currentUser,
  completeness,
  profileSteps,
  activeStep,
  setActiveStep,
  submitBusinessProfile,
  profileForm,
  updateProfileField,
  requirements,
  profileClientErrors,
  profileLoading,
  profile,
  profileMessage,
  profileError,
  recommendations,
  openSchemeAssistant,
  chatbotLoading,
  selectedScheme,
  chatInput,
  setChatInput,
  sendChatMessage,
  chatbotMessages,
  docType,
  setDocType,
  uploadDocument,
  uploading,
  uploadMessage,
  uploadError,
  documents,
  revalidateDocument,
  notifications,
  unreadCount,
  markNotificationRead,
  markAllNotificationsRead,
  logout,
}) {
  const [tab, setTab] = useState('profile');
  const [accountOpen, setAccountOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  const documentStats = useMemo(() => {
    const verified = documents.filter((d) => d.status === 'verified').length;
    const review = documents.filter((d) => d.status === 'review').length;
    const rejected = documents.filter((d) => d.status === 'rejected').length;
    return { verified, review, rejected };
  }, [documents]);

  const schemeCount = recommendations.length;

  function handleNotificationClick(notice) {
    const targetTab = notice?.action?.tab;
    const targetStep = notice?.action?.step;

    if (targetTab) setTab(targetTab);
    if (typeof targetStep === 'number') setActiveStep(targetStep);
    if (!notice?.isRead) markNotificationRead(notice.id);
    setNotificationsOpen(false);
  }

  return (
    <div className="page portal-page">
      <div className="bg-shape" aria-hidden="true" />
      <div className="bg-grid" aria-hidden="true" />

      <main className="portal-layout">
        <aside className="sidebar">
          <div className="brand-block">
            <p className="mini-label">Government Scheme OS</p>
            <h2>Startup and MSME Control Hub</h2>
            <p className="muted-text">
              End-to-end profile intelligence, eligibility mapping, and document readiness in one operational workspace.
            </p>
          </div>

          <div className="progress-card">
            <div className="progress-head">
              <p className="mini-label">Profile Completion</p>
              <strong>{completeness}%</strong>
            </div>
            <div className="meter">
              <div className="meter-fill" style={{ width: `${completeness}%` }} />
            </div>
          </div>

          <div className="kpi-stack">
            <article>
              <span>{schemeCount}</span>
              <small>Matched schemes</small>
            </article>
            <article>
              <span>{documentStats.verified}</span>
              <small>Documents verified</small>
            </article>
            <article>
              <span>{unreadCount}</span>
              <small>Open alerts</small>
            </article>
          </div>

          <div className="steps-card">
            <p className="mini-label">Profile Stages</p>
            {profileSteps.map((step, index) => (
              <button
                key={step.id}
                type="button"
                className={activeStep === index ? 'step-item active' : 'step-item'}
                onClick={() => {
                  setTab('profile');
                  setActiveStep(index);
                }}
              >
                <span>{index + 1}</span>
                <div>
                  <strong>{step.title}</strong>
                  <small>{step.detail}</small>
                </div>
              </button>
            ))}
          </div>

          <button type="button" className="logout-btn" onClick={logout}>
            Logout
          </button>
        </aside>

        <section className="workspace">
          <nav className="topbar">
            <div className="topbar-brand">
              <div className="brand-dot" />
              <div>
                <strong>Scheme Command Center</strong>
                <small>Compliant onboarding and recommendation workflow</small>
              </div>
            </div>

            <div className="topbar-actions">
              <button
                type="button"
                className="icon-btn"
                onClick={() => setNotificationsOpen((v) => !v)}
                aria-label="Notifications"
              >
                Alerts
                <span className="count-pill">{unreadCount}</span>
              </button>

              <button
                type="button"
                className="icon-btn"
                onClick={() => {
                  setTab('profile');
                  setActiveStep(profileSteps.length - 1);
                }}
              >
                Complete Profile
              </button>

              <div className="account-wrap">
                <button type="button" className="account-btn" onClick={() => setAccountOpen((v) => !v)}>
                  Account
                </button>
                {accountOpen ? (
                  <div className="account-menu">
                    <p>{currentUser.email}</p>
                    <button type="button" onClick={logout}>
                      Logout
                    </button>
                  </div>
                ) : null}
              </div>
            </div>
          </nav>

          {notificationsOpen ? (
            <section className="notice-bar">
              <div className="notice-head">
                <strong>Action Alerts</strong>
                <button type="button" className="link-btn" onClick={markAllNotificationsRead}>
                  Mark all read
                </button>
              </div>
              {notifications.length === 0 ? (
                <p>No alerts right now.</p>
              ) : (
                <ul className="notice-list">
                  {notifications.map((notice) => (
                    <li key={notice.id}>
                      <button
                        type="button"
                        className={`notice-item ${notice.severity || 'low'} ${notice.isRead ? 'read' : 'unread'}`}
                        onClick={() => handleNotificationClick(notice)}
                      >
                        <strong>{notice.title}</strong>
                        <span>{notice.message}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          ) : null}

          <section className="summary-strip">
            <article>
              <p>Business Type</p>
              <strong>{formatLabel(profileForm.businessType || 'startup')}</strong>
            </article>
            <article>
              <p>Primary Need</p>
              <strong>{formatLabel(profileForm.primaryNeed || 'grant')}</strong>
            </article>
            <article>
              <p>Turnover (Lakhs)</p>
              <strong>{profileForm.annualTurnoverLakhs || '0'}</strong>
            </article>
            <article>
              <p>Documents Uploaded</p>
              <strong>{documents.length}</strong>
            </article>
          </section>

          <header className="workspace-head">
            <div>
              <p className="mini-label">Signed In</p>
              <h1>{currentUser.email}</h1>
            </div>
            <div className="tabs">
              <button type="button" className={tab === 'profile' ? 'tab active' : 'tab'} onClick={() => setTab('profile')}>
                Business Profile
              </button>
              <button type="button" className={tab === 'schemes' ? 'tab active' : 'tab'} onClick={() => setTab('schemes')}>
                Scheme Mapping
              </button>
              <button type="button" className={tab === 'documents' ? 'tab active' : 'tab'} onClick={() => setTab('documents')}>
                Document Center
              </button>
            </div>
          </header>

          {tab === 'profile' ? (
            <section className="panel">
              <div className="panel-head">
                <h3>Business Profile Workspace</h3>
                <p>Capture legal, identity, and financial details required for accurate scheme classification.</p>
              </div>

              <form className="form" onSubmit={submitBusinessProfile}>
                {activeStep === 0 ? (
                  <>
                    <div className="grid-two">
                      <div>
                        <label htmlFor="businessType">Business Type</label>
                        <select id="businessType" value={profileForm.businessType} onChange={(e) => updateProfileField('businessType', e.target.value)} required>
                          <option value="startup">Startup</option>
                          <option value="msme">MSME</option>
                        </select>
                      </div>
                      <div>
                        <label htmlFor="legalEntityType">Legal Entity</label>
                        <select id="legalEntityType" value={profileForm.legalEntityType} onChange={(e) => updateProfileField('legalEntityType', e.target.value)} required>
                          {(requirements?.entityTypes || ['proprietorship', 'partnership', 'llp', 'private_limited', 'public_limited']).map((item) => (
                            <option key={item} value={item}>{formatLabel(item)}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid-two">
                      <div>
                        <label htmlFor="businessName">Business Name</label>
                        <input id="businessName" value={profileForm.businessName} onChange={(e) => updateProfileField('businessName', e.target.value)} placeholder="ABC Innovations Pvt Ltd" required />
                      </div>
                      <div>
                        <label htmlFor="sector">Sector</label>
                        <select id="sector" value={profileForm.sector} onChange={(e) => updateProfileField('sector', e.target.value)} required>
                          {(requirements?.sectors || []).map((item) => (
                            <option key={item} value={item}>{formatLabel(item)}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid-three">
                      <div>
                        <label htmlFor="yearOfIncorporation">Incorporation Year</label>
                        <input id="yearOfIncorporation" type="number" min="1900" max={new Date().getFullYear()} value={profileForm.yearOfIncorporation} onChange={(e) => updateProfileField('yearOfIncorporation', e.target.value)} required />
                      </div>
                      <div>
                        <label htmlFor="state">State</label>
                        <input id="state" value={profileForm.state} onChange={(e) => updateProfileField('state', e.target.value)} required />
                      </div>
                      <div>
                        <label htmlFor="city">City</label>
                        <input id="city" value={profileForm.city} onChange={(e) => updateProfileField('city', e.target.value)} required />
                      </div>
                    </div>

                    <div>
                      <label htmlFor="pincode">Pincode</label>
                      <input id="pincode" value={profileForm.pincode} onChange={(e) => updateProfileField('pincode', e.target.value.replace(/\D/g, '').slice(0, 6))} required />
                      {profileClientErrors.pincode ? <small className="field-error">{profileClientErrors.pincode}</small> : null}
                    </div>
                  </>
                ) : null}

                {activeStep === 1 ? (
                  <>
                    <div className="grid-two">
                      <div>
                        <label htmlFor="ownerName">Founder / Owner Name</label>
                        <input id="ownerName" value={profileForm.ownerName} onChange={(e) => updateProfileField('ownerName', e.target.value)} required />
                      </div>
                      <div>
                        <label htmlFor="gender">Gender</label>
                        <select id="gender" value={profileForm.gender} onChange={(e) => updateProfileField('gender', e.target.value)} required>
                          <option value="">Select gender</option>
                          <option value="male">Male</option>
                          <option value="female">Female</option>
                          <option value="other">Other</option>
                          <option value="prefer_not_to_say">Prefer not to say</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid-two">
                      <div>
                        <label htmlFor="pan">PAN</label>
                        <input id="pan" value={profileForm.pan} onChange={(e) => updateProfileField('pan', e.target.value.toUpperCase())} required />
                        {profileClientErrors.pan ? <small className="field-error">{profileClientErrors.pan}</small> : null}
                      </div>
                      <div>
                        <label htmlFor="mobile">Mobile</label>
                        <input id="mobile" value={profileForm.mobile} onChange={(e) => updateProfileField('mobile', e.target.value.replace(/\D/g, '').slice(0, 10))} required />
                        {profileClientErrors.mobile ? <small className="field-error">{profileClientErrors.mobile}</small> : null}
                      </div>
                    </div>

                    <div className="grid-two">
                      <label className="check-row" htmlFor="hasGst">
                        <input id="hasGst" type="checkbox" checked={profileForm.hasGst} onChange={(e) => updateProfileField('hasGst', e.target.checked)} />
                        GST registered
                      </label>
                      <div>
                        <label htmlFor="website">Website</label>
                        <input id="website" value={profileForm.website} onChange={(e) => updateProfileField('website', e.target.value)} placeholder="https://yourcompany.com" />
                      </div>
                    </div>

                    {profileForm.hasGst ? (
                      <div>
                        <label htmlFor="gstin">GSTIN</label>
                        <input id="gstin" value={profileForm.gstin} onChange={(e) => updateProfileField('gstin', e.target.value.toUpperCase())} required />
                        {profileClientErrors.gstin ? <small className="field-error">{profileClientErrors.gstin}</small> : null}
                      </div>
                    ) : null}

                    {profileForm.businessType === 'msme' ? (
                      <div>
                        <label htmlFor="udyamNumber">Udyam Number</label>
                        <input id="udyamNumber" value={profileForm.udyamNumber} onChange={(e) => updateProfileField('udyamNumber', e.target.value.toUpperCase())} required />
                        {profileClientErrors.udyamNumber ? <small className="field-error">{profileClientErrors.udyamNumber}</small> : null}
                      </div>
                    ) : (
                      <div>
                        <label htmlFor="dpiitNumber">DPIIT Number</label>
                        <input id="dpiitNumber" value={profileForm.dpiitNumber} onChange={(e) => updateProfileField('dpiitNumber', e.target.value.toUpperCase())} required />
                        {profileClientErrors.dpiitNumber ? <small className="field-error">{profileClientErrors.dpiitNumber}</small> : null}
                      </div>
                    )}
                  </>
                ) : null}
                {activeStep === 2 ? (
                  <>
                    <div className="grid-three">
                      <div>
                        <label htmlFor="employeeCount">Employee Count</label>
                        <input id="employeeCount" type="number" min="1" value={profileForm.employeeCount} onChange={(e) => updateProfileField('employeeCount', e.target.value)} required />
                      </div>
                      <div>
                        <label htmlFor="annualTurnoverLakhs">Annual Turnover (Lakhs)</label>
                        <input id="annualTurnoverLakhs" type="number" min="0" value={profileForm.annualTurnoverLakhs} onChange={(e) => updateProfileField('annualTurnoverLakhs', e.target.value)} required />
                      </div>
                      <div>
                        <label htmlFor="fundingNeedLakhs">Funding Need (Lakhs)</label>
                        <input id="fundingNeedLakhs" type="number" min="0" value={profileForm.fundingNeedLakhs} onChange={(e) => updateProfileField('fundingNeedLakhs', e.target.value)} required />
                      </div>
                    </div>

                    <div className="grid-two">
                      <div>
                        <label htmlFor="founderShareholding">Founder Shareholding (%)</label>
                        <input id="founderShareholding" type="number" min="0" max="100" value={profileForm.founderShareholding} onChange={(e) => updateProfileField('founderShareholding', e.target.value)} required />
                      </div>
                      <div>
                        <label htmlFor="primaryNeed">Primary Requirement</label>
                        <select id="primaryNeed" value={profileForm.primaryNeed} onChange={(e) => updateProfileField('primaryNeed', e.target.value)} required>
                          {(requirements?.primaryNeeds || ['grant', 'loan', 'subsidy', 'mentorship', 'market_access']).map((item) => (
                            <option key={item} value={item}>{formatLabel(item)}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="toggle-grid">
                      <label className="check-row" htmlFor="womenLed"><input id="womenLed" type="checkbox" checked={profileForm.womenLed} onChange={(e) => updateProfileField('womenLed', e.target.checked)} />Women-led enterprise</label>
                      <label className="check-row" htmlFor="scstLed"><input id="scstLed" type="checkbox" checked={profileForm.scstLed} onChange={(e) => updateProfileField('scstLed', e.target.checked)} />SC/ST founder</label>
                      <label className="check-row" htmlFor="differentlyAbledLed"><input id="differentlyAbledLed" type="checkbox" checked={profileForm.differentlyAbledLed} onChange={(e) => updateProfileField('differentlyAbledLed', e.target.checked)} />Differently abled founder</label>
                      <label className="check-row" htmlFor="exportFocus"><input id="exportFocus" type="checkbox" checked={profileForm.exportFocus} onChange={(e) => updateProfileField('exportFocus', e.target.checked)} />Export focused</label>
                      <label className="check-row" htmlFor="hasIp"><input id="hasIp" type="checkbox" checked={profileForm.hasIp} onChange={(e) => updateProfileField('hasIp', e.target.checked)} />Patent/IP available</label>
                    </div>
                  </>
                ) : null}

                <div className="actions-row between">
                  <button type="button" className="ghost-btn" disabled={activeStep === 0} onClick={() => setActiveStep((v) => Math.max(0, v - 1))}>Previous</button>
                  {activeStep < profileSteps.length - 1 ? (
                    <button type="button" className="ghost-btn" onClick={() => setActiveStep((v) => Math.min(profileSteps.length - 1, v + 1))}>Next Stage</button>
                  ) : (
                    <button type="submit" disabled={profileLoading}>{profileLoading ? 'Saving...' : profile ? 'Update Profile' : 'Create Profile'}</button>
                  )}
                </div>
              </form>

              {profileMessage ? <p className="message">{profileMessage}</p> : null}
              {profileError ? <p className="error">{profileError}</p> : null}
            </section>
          ) : null}

          {tab === 'schemes' ? (
            <section className="panel">
              <div className="panel-head">
                <h3>Scheme Recommendation Matrix</h3>
                <p>Open guided assistant for process steps, documents, and expected timelines.</p>
              </div>

              <div className="recommend-list">
                {recommendations.length === 0 ? <p className="subtitle">No schemes yet. Complete your profile first.</p> : null}
                {recommendations.map((rec) => (
                  <article key={rec.id} className="recommend-card">
                    <div className="recommend-head">
                      <strong>{rec.schemeName}</strong>
                      <span className={`badge ${rec.priority}`}>{rec.priority}</span>
                    </div>
                    <p><strong>Why matched:</strong> {rec.whyMatched.join(' | ')}</p>
                    <p><strong>Eligibility signals:</strong> {rec.keyEligibilitySignals.join(' | ')}</p>
                    <div className="actions-row">
                      <button type="button" className="ghost-btn" onClick={() => openSchemeAssistant(rec.id)} disabled={chatbotLoading}>
                        {chatbotLoading ? 'Loading...' : 'Open Assistant'}
                      </button>
                    </div>
                  </article>
                ))}
              </div>

              {selectedScheme ? (
                <section className="assistant-panel">
                  <h4>{selectedScheme.scheme.schemeName}</h4>
                  <p className="subtitle">{selectedScheme.scheme.description}</p>

                  <ol className="plain-list">
                    {selectedScheme.guideSteps.map((step, idx) => (
                      <li key={`${step}-${idx}`}>{step}</li>
                    ))}
                  </ol>

                  <p><strong>Timeline:</strong> {selectedScheme.timeline.join(' | ')}</p>
                  <p><strong>Submission:</strong> {selectedScheme.submission.mode} - {selectedScheme.submission.portalUrl}</p>

                  <form className="chat-form" onSubmit={sendChatMessage}>
                    <input value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Ask about missing documents, application steps, timelines..." />
                    <button type="submit" disabled={chatbotLoading}>Send</button>
                  </form>

                  <div className="chat-log">
                    {chatbotMessages.map((msg, idx) => (
                      <p key={`${msg.role}-${idx}`} className={msg.role === 'user' ? 'chat-user' : 'chat-assistant'}>
                        <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong> {msg.text}
                      </p>
                    ))}
                  </div>
                </section>
              ) : null}
            </section>
          ) : null}

          {tab === 'documents' ? (
            <section className="panel">
              <div className="panel-head">
                <h3>Document Validation Center</h3>
                <p>Upload compliance documents and re-check status after profile or quality updates.</p>
              </div>
              <div className="doc-kpis">
                <article>
                  <p>Verified</p>
                  <strong>{documentStats.verified}</strong>
                </article>
                <article>
                  <p>Review</p>
                  <strong>{documentStats.review}</strong>
                </article>
                <article>
                  <p>Rejected</p>
                  <strong>{documentStats.rejected}</strong>
                </article>
              </div>

              <form onSubmit={uploadDocument} className="form upload-card">
                <div className="grid-two">
                  <div>
                    <label htmlFor="documentType">Document Type</label>
                    <select id="documentType" value={docType} onChange={(e) => setDocType(e.target.value)}>
                      <option value="aadhar_card">Aadhar Card</option>
                      <option value="pan_card">PAN Card</option>
                      <option value="business_registration">Business Registration</option>
                      <option value="udyam_certificate">Udyam Certificate</option>
                      <option value="dpiit_certificate">DPIIT Certificate</option>
                      <option value="gst_certificate">GST Certificate</option>
                      <option value="bank_statement">Bank Statement</option>
                      <option value="itr_2_years">ITR (2 Years)</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="file">Upload File</label>
                    <input id="file" type="file" name="file" accept=".pdf,.png,.jpg,.jpeg" />
                  </div>
                </div>
                <button type="submit" disabled={uploading}>{uploading ? 'Uploading...' : 'Upload Document'}</button>
              </form>

              {uploadMessage ? <p className="message">{uploadMessage}</p> : null}
              {uploadError ? <p className="error">{uploadError}</p> : null}

              <div className="recommend-list">
                {documents.map((doc) => (
                  <article key={doc.id} className="recommend-card document-card">
                    <div className="recommend-head">
                      <strong>{formatLabel(doc.docType)}</strong>
                      <span className={`badge ${doc.status}`}>{doc.status}</span>
                    </div>
                    <p><strong>File:</strong> {doc.fileName}</p>
                    <p><strong>Uploaded:</strong> {new Date(doc.uploadedAt).toLocaleString()}</p>
                    {doc.warnings?.length ? <p><strong>Warnings:</strong> {doc.warnings.join(' | ')}</p> : null}
                    {doc.errors?.length ? <p><strong>Errors:</strong> {doc.errors.join(' | ')}</p> : null}
                    <div className="actions-row">
                      <button type="button" className="ghost-btn" onClick={() => revalidateDocument(doc.id)}>Revalidate</button>
                    </div>
                  </article>
                ))}
                {documents.length === 0 ? <p className="subtitle">No documents uploaded yet.</p> : null}
              </div>
            </section>
          ) : null}
        </section>
      </main>
    </div>
  );
}

export default BusinessDashboard;
