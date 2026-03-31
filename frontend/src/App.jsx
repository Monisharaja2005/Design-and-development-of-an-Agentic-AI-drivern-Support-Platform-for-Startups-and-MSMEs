import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import Sidebar from './components/Sidebar';
import TopNav from './components/TopNav';
import LanguageSwitcher from './components/LanguageSwitcher';
import LandingPage from './pages/LandingPage';
import DashboardView from './pages/Dashboard';
import SchemeDiscoveryView from './pages/SchemeDiscovery';
import DocValidationView from './pages/DocValidation';
import AIChatView from './pages/AIChatAssistant';
import LoginPage from './pages/Login';
import ProfileBuilder from './pages/ProfileBuilder';
import EnrichmentView from './pages/EnrichmentView';
import ErrorBoundary from './ErrorBoundary.jsx';

// ── i18n (safe import) ────────────────────────────────────────────────────────
let i18n = { changeLanguage: () => {} };
try { i18n = (await import('./i18n')).default; } catch {}

// ── Language helpers (safe import) ────────────────────────────────────────────
let DEFAULT_LANGUAGE = 'en';
let normalizeLanguageCode = (l) => l || 'en';
try {
  const langLib = await import('./lib/languages');
  DEFAULT_LANGUAGE = langLib.DEFAULT_LANGUAGE || 'en';
  normalizeLanguageCode = langLib.normalizeLanguageCode || normalizeLanguageCode;
} catch {}

// ── Workspace / session mocks ─────────────────────────────────────────────────
// These replace the missing userWorkspace lib with safe, fully-typed stubs.

const DEFAULT_WORKSPACE = { profile: {}, saved_schemes: [], last_selected_scheme_id: '' };

/** Always returns a safe workspace shape — never undefined. */
const normalizeWorkspace = (workspace, profileData = {}) => {
  const base = workspace && typeof workspace === 'object' ? workspace : {};
  return {
    profile:                  base.profile        || profileData || {},
    saved_schemes:            Array.isArray(base.saved_schemes) ? base.saved_schemes : [],
    last_selected_scheme_id:  base.last_selected_scheme_id || '',
  };
};

const mergeUserWorkspace = (user, extra) => ({
  ...(user  || {}),
  ...(extra || {}),
});

const clearLegacyWorkspaceCache = () => {
  try {
    Object.keys(sessionStorage)
      .filter(k => k.startsWith('workspace_'))
      .forEach(k => sessionStorage.removeItem(k));
  } catch {}
};

const fetchUserWorkspace = async (email) => {
  // Try backend; return cached workspace on any error so we don't crash.
  const cached = (() => {
    try { return JSON.parse(sessionStorage.getItem(`workspace_${email}`) || 'null'); } catch { return null; }
  })();
  try {
    const res = await fetch(`http://127.0.0.1:8001/v1/workspace/${encodeURIComponent(email)}`, {
      headers: { Authorization: `Bearer ${sessionStorage.getItem('scheme_token') || ''}` },
      signal: AbortSignal.timeout(6000),
    });
    if (!res.ok) return cached || DEFAULT_WORKSPACE;
    return await res.json();
  } catch {
    return cached || DEFAULT_WORKSPACE;
  }
};

const saveUserWorkspace = async (email, workspace) => {
  try {
    await fetch(`http://127.0.0.1:8001/v1/workspace/${encodeURIComponent(email)}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${sessionStorage.getItem('scheme_token') || ''}`,
      },
      body: JSON.stringify(workspace),
      signal: AbortSignal.timeout(8000),
    });
  } catch (e) {
    console.warn('saveUserWorkspace failed (non-fatal):', e.message);
  }
};

const getSessionUser = () => {
  try { return JSON.parse(sessionStorage.getItem('karios_user') || 'null'); } catch { return null; }
};

const setSessionUser = (user) => {
  try { sessionStorage.setItem('karios_user', JSON.stringify(user)); } catch {}
};

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const [appState,              setAppState]              = useState('login');
  const [workspaceLoading,      setWorkspaceLoading]      = useState(false);
  const [appLanguage,           setAppLanguage]           = useState(DEFAULT_LANGUAGE);
  const [activeTab,             setActiveTab]             = useState('dashboard');
  const [userProfile,           setUserProfile]           = useState(null);
  const [authUser,              setAuthUser]              = useState(null);
  const [savedSchemes,          setSavedSchemes]          = useState([]);
  const [lastSelectedSchemeId,  setLastSelectedSchemeId]  = useState('');
  const translatedRootRef = useRef(null);

  // ── Apply authenticated user ───────────────────────────────────────────────
  const applyAuthenticatedUser = useCallback(async (user) => {
    if (!user?.email) return;

    clearLegacyWorkspaceCache();

    // Fetch workspace — never throws, always returns a safe object
    setWorkspaceLoading(true);
    try {
      const rawWorkspace = await fetchUserWorkspace(user.email);
      const workspace    = normalizeWorkspace(rawWorkspace, user.profile_data || {});
      const profile      = workspace.profile || {};
      // FIXED: Allow dashboard with minimal/empty profile (login flow fix)
      const profileComplete = Object.keys(profile).length >= 3 || profile.sector || profile.state || profile.businessDescription;
      
      const resolvedUser = mergeUserWorkspace(user, { workspace });

    setAuthUser(resolvedUser);
    setSessionUser(resolvedUser);
    setUserProfile(Object.keys(profile).length ? profile : null);
    setSavedSchemes(workspace.saved_schemes);
    setLastSelectedSchemeId(workspace.last_selected_scheme_id);

    // Cache locally so refresh works offline
    try { sessionStorage.setItem(`workspace_${user.email}`, JSON.stringify(workspace)); } catch {}

    // FIXED: Use profileComplete (allows dashboard even with empty profile)
    setAppState(profileComplete ? 'app' : 'profile');
    } finally {
      setWorkspaceLoading(false);
    }
  }, []);

  // ── Persist workspace ──────────────────────────────────────────────────────
  const persistWorkspaceState = useCallback(async (nextWorkspace) => {
    if (!authUser?.email) return;

    const workspace    = normalizeWorkspace(nextWorkspace, userProfile || authUser?.profile_data || {});
    const mergedUser   = mergeUserWorkspace(authUser, { workspace });

    setAuthUser(mergedUser);
    setSessionUser(mergedUser);
    setUserProfile(Object.keys(workspace.profile).length ? workspace.profile : null);
    setSavedSchemes(workspace.saved_schemes);
    setLastSelectedSchemeId(workspace.last_selected_scheme_id);

    try { sessionStorage.setItem(`workspace_${authUser.email}`, JSON.stringify(workspace)); } catch {}
    await saveUserWorkspace(authUser.email, workspace);
  }, [authUser, userProfile]);

  // ── Restore session on mount ───────────────────────────────────────────────
  useEffect(() => {
    const storedUser = getSessionUser();
    const token      = sessionStorage.getItem('scheme_token');
    if (storedUser && token) {
      applyAuthenticatedUser(storedUser);
    }
  }, [applyAuthenticatedUser]);

  // ── Auth handlers ──────────────────────────────────────────────────────────
  const handleLogin = useCallback((user) => {
    applyAuthenticatedUser(user);
  }, [applyAuthenticatedUser]);

  const handleProfileComplete = useCallback((data) => {
    const workspace  = normalizeWorkspace({
      profile: data,
      saved_schemes: savedSchemes,
      last_selected_scheme_id: lastSelectedSchemeId,
    });
    const mergedUser = mergeUserWorkspace(authUser, { workspace });

    setAuthUser(mergedUser);
    setSessionUser(mergedUser);
    setUserProfile(data);
    setAppState('enrichment');
  }, [authUser, savedSchemes, lastSelectedSchemeId]);

  const handleEnrichmentComplete = useCallback(() => {
    setAppState('app');
    setActiveTab('dashboard');
  }, []);

  const handleLogout = useCallback(() => {
    sessionStorage.removeItem('karios_user');
    sessionStorage.removeItem('scheme_token');
    localStorage.removeItem('scheme_lang');
    clearLegacyWorkspaceCache();
    setAppState('login');
    setUserProfile(null);
    setAuthUser(null);
    setSavedSchemes([]);
    setLastSelectedSchemeId('');
    setActiveTab('dashboard');
  }, []);

  const handleSavedSchemesChange = useCallback((nextSavedSchemes, nextSelectedSchemeId = '') => {
    persistWorkspaceState({
      profile: userProfile || authUser?.profile_data || {},
      saved_schemes: nextSavedSchemes,
      last_selected_scheme_id: nextSelectedSchemeId,
    });
  }, [authUser, persistWorkspaceState, userProfile]);

  const handleLastSelectedSchemeChange = useCallback((nextSelectedSchemeId) => {
    persistWorkspaceState({
      profile: userProfile || authUser?.profile_data || {},
      saved_schemes: savedSchemes,
      last_selected_scheme_id: nextSelectedSchemeId,
    });
  }, [authUser, persistWorkspaceState, savedSchemes, userProfile]);

  const handleNavigate = useCallback((tab) => setActiveTab(tab), []);

  const handleLanguageChange = useCallback((language) => {
    const next = normalizeLanguageCode(language);
    setAppLanguage(next);
    try { i18n.changeLanguage(next); } catch {}
  }, []);

  // ── Derived state ──────────────────────────────────────────────────────────
  const activeSchemeForValidation =
    savedSchemes.find(s => (s.scheme_id || s.scheme_code || s.id) === lastSelectedSchemeId)
    || savedSchemes[0]
    || null;

  // ── Standalone shell (login / landing / profile) ───────────────────────────
  const renderStandaloneShell = (content) => (
    <div className="relative min-h-screen">
      <div className="fixed top-5 right-5 z-[90]">
        <ErrorBoundary>
          <LanguageSwitcher
            language={appLanguage}
            onChange={handleLanguageChange}
            buttonClassName="bg-white/95 backdrop-blur"
          />
        </ErrorBoundary>
      </div>
      {content}
    </div>
  );

  // ── Tab content ────────────────────────────────────────────────────────────
  const renderAppContent = () => {
    try {
      switch (activeTab) {
        case 'dashboard':
          return (
            <ErrorBoundary>
              <DashboardView
                onNavigate={handleNavigate}
                userProfile={userProfile}
                activeScheme={activeSchemeForValidation}
                savedSchemes={savedSchemes}
                lastSelectedSchemeId={lastSelectedSchemeId}
                onSavedSchemesChange={handleSavedSchemesChange}
                onLastSelectedSchemeChange={handleLastSelectedSchemeChange}
              />
            </ErrorBoundary>
          );
        case 'discovery':
          return (
            <ErrorBoundary>
              <SchemeDiscoveryView
                userProfile={userProfile}
                userEmail={authUser?.email || ''}
                language={appLanguage}
                savedSchemes={savedSchemes}
                lastSelectedSchemeId={lastSelectedSchemeId}
                onSavedSchemesChange={handleSavedSchemesChange}
                onLastSelectedSchemeChange={handleLastSelectedSchemeChange}
              />
            </ErrorBoundary>
          );
        case 'validation':
          return (
            <ErrorBoundary>
              <DocValidationView
                userProfile={userProfile}
                userEmail={authUser?.email || ''}
                savedSchemes={savedSchemes}
                lastSelectedSchemeId={lastSelectedSchemeId}
                activeScheme={activeSchemeForValidation}
                onLastSelectedSchemeChange={handleLastSelectedSchemeChange}
                onSavedSchemesChange={handleSavedSchemesChange}
              />
            </ErrorBoundary>
          );
        case 'assistant':
          return (
            <ErrorBoundary>
              <AIChatView
                userProfile={userProfile}
                appLanguage={appLanguage}
                savedSchemes={savedSchemes}
              />
            </ErrorBoundary>
          );
        case 'profile':
          return (
            <ErrorBoundary>
              <div className="max-w-3xl mx-auto">
                <ProfileBuilder
                  user={authUser}
                  prefillData={userProfile}
                  onComplete={handleProfileComplete}
                />
              </div>
            </ErrorBoundary>
          );
        default:
          return (
            <ErrorBoundary>
              <DashboardView onNavigate={handleNavigate} userProfile={userProfile} />
            </ErrorBoundary>
          );
      }
    } catch (error) {
      console.error('renderAppContent error:', error);
      return (
        <div className="p-8 text-center">
          <h3 className="text-lg font-bold text-slate-900 mb-2">Content failed to load</h3>
          <p className="text-slate-500 mb-4">Check console for details.</p>
          <button
            onClick={() => handleNavigate('dashboard')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700"
          >
            Go to Dashboard
          </button>
        </div>
      );
    }
  };

  // ── Full-page states ───────────────────────────────────────────────────────
  if (appState === 'landing') {
    return renderStandaloneShell(<LandingPage onStart={() => setAppState('login')} />);
  }

  if (appState === 'login') {
    return renderStandaloneShell(<LoginPage onLogin={handleLogin} />);
  }

  if (appState === 'profile') {
    return renderStandaloneShell(
      <ProfileBuilder onComplete={handleProfileComplete} user={authUser} />
    );
  }

  if (appState === 'enrichment') {
    return renderStandaloneShell(
      <EnrichmentView onComplete={handleEnrichmentComplete} userProfile={userProfile} />
    );
  }

  // ── Main app layout ────────────────────────────────────────────────────────
  // FIXED: Add workspace loading guard
  if (workspaceLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8 bg-slate-50">
        <div className="max-w-md text-center">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Loading workspace...</h2>
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          <p className="text-sm text-slate-500 mt-2">Fetching your profile & schemes</p>
        </div>
      </div>
    );
  }

  if (!Sidebar || !TopNav) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8 bg-slate-50">
        <div className="max-w-md text-center">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Loading components...</h2>
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      </div>
    );
  }

  return (
    <div ref={translatedRootRef} className="flex min-h-screen bg-slate-50 font-plus selection:bg-blue-500/20">
      {/* Sidebar */}
      <div className="h-screen sticky top-0 shrink-0 z-50">
        <ErrorBoundary>
          <Sidebar
            activeTab={activeTab === 'profile' ? 'profile' : activeTab}
            setActiveTab={setActiveTab}
            savedCount={savedSchemes?.length || 0}
            onLogout={handleLogout}
          />
        </ErrorBoundary>
      </div>

      {/* Main content */}
      <main className="flex-1 min-w-0 flex flex-col">
        <ErrorBoundary>
          <TopNav
            activeTab={activeTab}
            appLanguage={appLanguage}
            onLanguageChange={handleLanguageChange}
          />
        </ErrorBoundary>

        <div className="flex-1 py-10 px-6 md:px-10 max-w-7xl mx-auto w-full">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 12, scale: 0.99 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.99 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            >
              {renderAppContent()}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
