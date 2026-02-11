import { useEffect, useMemo, useState } from 'react';
import AuthScreen from './components/AuthScreen.jsx';
import BusinessDashboard from './components/BusinessDashboard.jsx';
import { API_BASE_URL, TOKEN_KEY, initialProfileForm, passwordChecks, profileSteps } from './constants/profile.js';
import { getProfileClientErrors, getRequiredFields } from './utils/profileValidation.js';

function App() {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [userType, setUserType] = useState('business');
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [showForgot, setShowForgot] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');

  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '');
  const [currentUser, setCurrentUser] = useState(null);

  const [requirements, setRequirements] = useState(null);
  const [profile, setProfile] = useState(null);
  const [profileForm, setProfileForm] = useState(initialProfileForm);
  const [recommendations, setRecommendations] = useState([]);
  const [activeStep, setActiveStep] = useState(0);

  const [initializing, setInitializing] = useState(true);
  const [authLoading, setAuthLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [profileMessage, setProfileMessage] = useState('');
  const [profileError, setProfileError] = useState('');
  const [selectedScheme, setSelectedScheme] = useState(null);
  const [chatbotMessages, setChatbotMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatbotLoading, setChatbotLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadMessage, setUploadMessage] = useState('');
  const [docType, setDocType] = useState('aadhar_card');

  const checks = useMemo(
    () => passwordChecks.map((item) => ({ ...item, pass: item.test(password) })),
    [password]
  );
  const strength = useMemo(() => checks.filter((item) => item.pass).length, [checks]);

  const completeness = useMemo(() => {
    const req = getRequiredFields(profileForm);
    const done = req.filter((key) => String(profileForm[key] ?? '').trim() !== '').length;
    return Math.round((done / req.length) * 100);
  }, [profileForm]);

  const profileClientErrors = useMemo(() => getProfileClientErrors(profileForm), [profileForm]);

  useEffect(() => {
    async function loadRequirements() {
      try {
        const res = await fetch(`${API_BASE_URL}/api/business-profile/requirements`);
        const data = await res.json();
        if (res.ok) setRequirements(data);
      } catch (_error) {}
    }
    loadRequirements();
  }, []);

  useEffect(() => {
    async function restoreSession() {
      if (!token) {
        setCurrentUser(null);
        setProfile(null);
        setInitializing(false);
        return;
      }
      try {
        const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.message || 'Session check failed.');
        setCurrentUser(data.user);
      } catch (_error) {
        localStorage.removeItem(TOKEN_KEY);
        setToken('');
        setCurrentUser(null);
        setProfile(null);
      } finally {
        setInitializing(false);
      }
    }
    restoreSession();
  }, [token]);

  useEffect(() => {
    async function loadBusinessData() {
      if (!token || !currentUser?.email) return;

      try {
        const profileRes = await fetch(`${API_BASE_URL}/api/business-profile`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const profileData = await profileRes.json();
        if (!profileRes.ok) throw new Error(profileData.message || 'Failed to load profile.');

        if (profileData.exists && profileData.profile) {
          const p = profileData.profile;
          setProfile(p);
          setProfileForm({
            ...initialProfileForm,
            ...p,
            yearOfIncorporation: String(p.yearOfIncorporation || ''),
            employeeCount: String(p.employeeCount || ''),
            annualTurnoverLakhs: String(p.annualTurnoverLakhs || ''),
            fundingNeedLakhs: String(p.fundingNeedLakhs || ''),
            founderShareholding: String(p.founderShareholding || ''),
          });
        } else {
          setProfile(null);
          setProfileForm(initialProfileForm);
        }
      } catch (err) {
        setProfileError(err.message || 'Failed to load profile.');
      }

      await refreshRecommendations(token);
    }

    loadBusinessData();
  }, [token, currentUser?.email]);

  useEffect(() => {
    async function loadDocuments() {
      if (!token || !currentUser?.email) return;
      try {
        const res = await fetch(`${API_BASE_URL}/api/documents`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!res.ok) return;
        setDocuments(Array.isArray(data.documents) ? data.documents : []);
      } catch (_error) {}
    }
    loadDocuments();
  }, [token, currentUser?.email]);

  useEffect(() => {
    async function loadNotifications() {
      if (!token || !currentUser?.email) return;
      try {
        const res = await fetch(`${API_BASE_URL}/api/notifications`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!res.ok) return;
        setNotifications(Array.isArray(data.notifications) ? data.notifications : []);
        setUnreadCount(Number(data.unreadCount || 0));
      } catch (_error) {}
    }
    loadNotifications();
  }, [token, currentUser?.email, profile?.updatedAt, documents.length, recommendations.length]);

  async function markNotificationRead(id) {
    if (!id) return;
    try {
      await fetch(`${API_BASE_URL}/api/notifications/read/${id}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (_error) {}
    setNotifications((prev) => prev.map((item) => (item.id === id ? { ...item, isRead: true } : item)));
    setUnreadCount((prev) => Math.max(0, prev - 1));
  }

  async function markAllNotificationsRead() {
    const unreadIds = notifications.filter((item) => !item.isRead).map((item) => item.id);
    if (unreadIds.length === 0) return;
    try {
      await fetch(`${API_BASE_URL}/api/notifications/read-all`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ ids: unreadIds }),
      });
    } catch (_error) {}
    setNotifications((prev) => prev.map((item) => ({ ...item, isRead: true })));
    setUnreadCount(0);
  }

  async function refreshRecommendations(authToken) {
    try {
      const res = await fetch(`${API_BASE_URL}/api/business-profile/recommendations`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      const data = await res.json();
      if (!res.ok) {
        setRecommendations([]);
        return;
      }
      setRecommendations(Array.isArray(data.recommendations) ? data.recommendations : []);
    } catch (_error) {
      setRecommendations([]);
    }
  }

  async function openSchemeAssistant(schemeId) {
    setChatbotLoading(true);
    setUploadError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/chatbot/scheme-assistant`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ schemeId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Failed to open scheme assistant.');

      setSelectedScheme(data);
      setChatbotMessages([{ role: 'assistant', text: data.assistantReply }]);
    } catch (err) {
      setProfileError(err.message || 'Could not open scheme assistant.');
    } finally {
      setChatbotLoading(false);
    }
  }

  async function sendChatMessage(event) {
    event.preventDefault();
    if (!chatInput.trim() || !selectedScheme?.scheme?.id) return;

    const question = chatInput.trim();
    setChatInput('');
    setChatbotMessages((prev) => [...prev, { role: 'user', text: question }]);
    setChatbotLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/chatbot/scheme-assistant`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ schemeId: selectedScheme.scheme.id, userQuestion: question }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Chatbot request failed.');
      setSelectedScheme(data);
      setChatbotMessages((prev) => [...prev, { role: 'assistant', text: data.assistantReply }]);
    } catch (err) {
      setChatbotMessages((prev) => [...prev, { role: 'assistant', text: err.message }]);
    } finally {
      setChatbotLoading(false);
    }
  }

  async function uploadDocument(event) {
    event.preventDefault();
    const file = event.target.file?.files?.[0];
    if (!file) {
      setUploadError('Please choose a file.');
      return;
    }

    const form = new FormData();
    form.append('documentType', docType);
    form.append('file', file);

    setUploading(true);
    setUploadError('');
    setUploadMessage('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/documents/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Upload failed.');

      setDocuments((prev) => [data.document, ...prev]);
      setUploadMessage(data.message || 'Uploaded.');
      event.target.reset();
    } catch (err) {
      setUploadError(err.message || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  }

  async function revalidateDocument(docId) {
    if (!docId) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/documents/revalidate/${docId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Revalidation failed.');
      setDocuments((prev) => prev.map((doc) => (doc.id === docId ? data.document : doc)));
      setUploadMessage(data.message || 'Document revalidated.');
      setUploadError('');
    } catch (err) {
      setUploadError(err.message || 'Could not revalidate document.');
    }
  }

  function updateProfileField(key, value) {
    setProfileForm((prev) => ({ ...prev, [key]: value }));
  }

  async function submitAuth(event) {
    event.preventDefault();
    setAuthLoading(true);
    setMessage('');
    setError('');
    try {
      const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register';
      const payload = mode === 'login' ? { email, password } : { email, password, phone, userType };
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        const details = Array.isArray(data.errors) ? ` ${data.errors.join(' ')}` : '';
        throw new Error(`${data.message || 'Request failed.'}${details}`);
      }
      if (data.token) {
        if (remember) localStorage.setItem(TOKEN_KEY, data.token);
        setToken(data.token);
      }
      setCurrentUser(data.user || null);
      setMessage(data.message || 'Success');
      setEmail('');
      setPassword('');
      setPhone('');
      setUserType('business');
    } catch (err) {
      setError(err.message || 'Unexpected error.');
    } finally {
      setAuthLoading(false);
    }
  }

  async function requestResetToken(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resetEmail }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Could not request reset token.');
      setMessage(data.message || 'Reset token generated.');
      if (data.resetToken) setResetToken(data.resetToken);
    } catch (err) {
      setError(err.message || 'Reset request failed.');
    }
  }

  async function submitResetPassword(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resetEmail, resetToken, newPassword }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Reset failed.');
      setMessage(data.message || 'Password reset successful.');
      setShowForgot(false);
      setResetToken('');
      setNewPassword('');
    } catch (err) {
      setError(err.message || 'Reset failed.');
    }
  }

  async function submitBusinessProfile(event) {
    event.preventDefault();
    setProfileLoading(true);
    setProfileMessage('');
    setProfileError('');
    if (Object.keys(profileClientErrors).length > 0) {
      setProfileLoading(false);
      setProfileError(Object.values(profileClientErrors)[0]);
      return;
    }
    try {
      const payload = {
        ...profileForm,
        pan: String(profileForm.pan || '').trim().toUpperCase(),
        gstin: String(profileForm.gstin || '').trim().toUpperCase(),
        udyamNumber: String(profileForm.udyamNumber || '').trim().toUpperCase(),
        dpiitNumber: String(profileForm.dpiitNumber || '').trim().toUpperCase(),
        yearOfIncorporation: Number(profileForm.yearOfIncorporation),
        employeeCount: Number(profileForm.employeeCount),
        annualTurnoverLakhs: Number(profileForm.annualTurnoverLakhs),
        fundingNeedLakhs: Number(profileForm.fundingNeedLakhs),
        founderShareholding: Number(profileForm.founderShareholding),
      };
      const res = await fetch(`${API_BASE_URL}/api/business-profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        const details = Array.isArray(data.errors) ? ` ${data.errors.join(' ')}` : '';
        throw new Error(`${data.message || 'Profile save failed.'}${details}`);
      }
      setProfile(data.profile);
      setProfileMessage(data.message || 'Business profile saved.');
      setRecommendations(Array.isArray(data.recommendations) ? data.recommendations : []);
    } catch (err) {
      setProfileError(err.message || 'Business profile save failed.');
    } finally {
      setProfileLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken('');
    setCurrentUser(null);
    setProfile(null);
    setRecommendations([]);
    setProfileForm(initialProfileForm);
    setMessage('You have logged out.');
    setError('');
    setMode('login');
    setActiveStep(0);
  }

  if (initializing) {
    return (
      <div className="page">
        <main className="card">
          <h1>Loading</h1>
          <p className="subtitle">Checking your session...</p>
        </main>
      </div>
    );
  }

  const canSubmit = mode === 'login' || strength === 5;

  if (currentUser) {
    return (
      <BusinessDashboard
        currentUser={currentUser}
        completeness={completeness}
        profileSteps={profileSteps}
        activeStep={activeStep}
        setActiveStep={setActiveStep}
        submitBusinessProfile={submitBusinessProfile}
        profileForm={profileForm}
        updateProfileField={updateProfileField}
        requirements={requirements}
        profileClientErrors={profileClientErrors}
        profileLoading={profileLoading}
        profile={profile}
        profileMessage={profileMessage}
        profileError={profileError}
        recommendations={recommendations}
        openSchemeAssistant={openSchemeAssistant}
        chatbotLoading={chatbotLoading}
        selectedScheme={selectedScheme}
        chatInput={chatInput}
        setChatInput={setChatInput}
        sendChatMessage={sendChatMessage}
        chatbotMessages={chatbotMessages}
        docType={docType}
        setDocType={setDocType}
        uploadDocument={uploadDocument}
        uploading={uploading}
        uploadMessage={uploadMessage}
        uploadError={uploadError}
        documents={documents}
        revalidateDocument={revalidateDocument}
        notifications={notifications}
        unreadCount={unreadCount}
        markNotificationRead={markNotificationRead}
        markAllNotificationsRead={markAllNotificationsRead}
        logout={logout}
      />
    );
  }

  return (
    <AuthScreen
      mode={mode}
      setMode={setMode}
      email={email}
      setEmail={setEmail}
      password={password}
      setPassword={setPassword}
      phone={phone}
      setPhone={setPhone}
      userType={userType}
      setUserType={setUserType}
      showPassword={showPassword}
      setShowPassword={setShowPassword}
      remember={remember}
      setRemember={setRemember}
      checks={checks}
      strength={strength}
      authLoading={authLoading}
      canSubmit={canSubmit}
      submitAuth={submitAuth}
      showForgot={showForgot}
      setShowForgot={setShowForgot}
      resetEmail={resetEmail}
      setResetEmail={setResetEmail}
      resetToken={resetToken}
      setResetToken={setResetToken}
      newPassword={newPassword}
      setNewPassword={setNewPassword}
      requestResetToken={requestResetToken}
      submitResetPassword={submitResetPassword}
      message={message}
      error={error}
    />
  );
}

export default App;
