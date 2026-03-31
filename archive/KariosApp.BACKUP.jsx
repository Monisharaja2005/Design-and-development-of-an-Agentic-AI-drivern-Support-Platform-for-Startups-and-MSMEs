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
import i18n from './i18n';
import { DEFAULT_LANGUAGE, normalizeLanguageCode } from './lib/languages';
import {
  clearLegacyWorkspaceCache,
  fetchUserWorkspace,
  getSessionUser,
  mergeUserWorkspace,
  normalizeWorkspace,
  saveUserWorkspace,
  setSessionUser,
} from './lib/userWorkspace';
import useAutoPageTranslation from './hooks/useAutoPageTranslation';
import useHydrateLanguageResources from './hooks/useHydrateLanguageResources';

// App state machine: landing → login → profile → enrichment → app
export default function App() {
  const [appState, setAppState] = useState('login'); // Started at login as per user request
  const [appLanguage, setAppLanguage] = useState(
    normalizeLanguageCode(i18n.resolvedLanguage || i18n.language || DEFAULT_LANGUAGE),
  );
  const [activeTab, setActiveTab] = useState('dashboard');
  const [userProfile, setUserProfile] = useState(null);
  const [authUser, setAuthUser] = useState(null);
  const [savedSchemes, setSavedSchemes] = useState([]);
  const [lastSelectedSchemeId, setLastSelectedSchemeId] = useState('');
  const translatedRootRef = useRef(null);

  useHydrateLanguageResources(appLanguage);
  useAutoPageTranslation(translatedRootRef, appLanguage);

  useEffect(() => {
    const initialLanguage = normalizeLanguageCode(i18n.resolvedLanguage || i18n.language || DEFAULT_LANGUAGE);
    if (initialLanguage !== normalizeLanguageCode(i18n.language)) {
      i18n.changeLanguage(initialLanguage);
    }

    const syncLanguage = (language) => {
      const nextLanguage = normalizeLanguageCode(language);
      setAppLanguage(nextLanguage);
      localStorage.setItem('karios_lang', nextLanguage);
      document.documentElement.lang = nextLanguage;
      document.documentElement.dir = nextLanguage === 'ur' ? 'rtl' : 'ltr';
    };

    syncLanguage(initialLanguage);
    i18n.on('languageChanged', syncLanguage);
    return () => {
      i18n.off('languageChanged', syncLanguage);
    };
  }, []);

  const applyAuthenticatedUser = useCallback(async (user) => {
    if (!user?.email) {
      return;
    }

    clearLegacyWorkspaceCache();

    let resolvedUser = mergeUserWorkspace(user, user.workspace || {});
    try {
      const workspace = await fetchUserWorkspace(user.email);
      resolvedUser = mergeUserWorkspace(user, workspace);
    } catch {
      resolvedUser = mergeUserWorkspace(user, user.workspace || {});
    }

    const workspace = normalizeWorkspace(resolvedUser.workspace, resolvedUser.profile_data || {});
    const nextProfile = workspace.profile;
    const hasProfile = Object.keys(nextProfile || {}).length > 5;

    setAuthUser(resolvedUser);
    setSessionUser(resolvedUser);
    setUserProfile(Object.keys(nextProfile || {}).length ? nextProfile : null);
    setSavedSchemes(workspace.saved_schemes);
    setLastSelectedSchemeId(workspace.last_selected_scheme_id);
    setAppState(hasProfile ? 'app' : 'profile');
  }, []);

  const persistWorkspaceState = useCallback(async (nextWorkspace) => {
    if (!authUser?.email) {
      return;
    }

    const normalizedWorkspace = normalizeWorkspace(nextWorkspace, userProfile || authUser.profile_data || {});
    const mergedUser = mergeUserWorkspace(authUser, normalizedWorkspace);

    setAuthUser(mergedUser);
    setSessionUser(mergedUser);
    setUserProfile(Object.keys(normalizedWorkspace.profile || {}).length ? normalizedWorkspace.profile : null);
    setSavedSchemes(normalizedWorkspace.saved_schemes);
    setLastSelectedSchemeId(normalizedWorkspace.last_selected_scheme_id);

    try {
      const savedWorkspace = await saveUserWorkspace(authUser.email, normalizedWorkspace);
      const savedUser = mergeUserWorkspace(authUser, savedWorkspace);
      setAuthUser(savedUser);
      setSessionUser(savedUser);
      setUserProfile(Object.keys(savedWorkspace.profile || {}).length ? savedWorkspace.profile : null);
      setSavedSchemes(savedWorkspace.saved_schemes);
      setLastSelectedSchemeId(savedWorkspace.last_selected_scheme_id);
    } catch (error) {
      console.error('Could not persist user workspace', error);
    }
  }, [authUser, userProfile]);

  useEffect(() => {
    const storedUser = getSessionUser();
    const token = sessionStorage.getItem('karios_token');
    if (storedUser && token) {
      applyAuthenticatedUser(storedUser);
    }
  }, [applyAuthenticatedUser]);

  const handleLogin = (user) => {
    applyAuthenticatedUser(user);
  };

  const handleProfileComplete = (data) => {
    const nextWorkspace = normalizeWorkspace({
      profile: data,
      saved_schemes: savedSchemes,
      last_selected_scheme_id: lastSelectedSchemeId,
    }, data);
    const mergedUser = mergeUserWorkspace(authUser, nextWorkspace);

    setAuthUser(mergedUser);
    setSessionUser(mergedUser);
    setUserProfile(data);
    setAppState('enrichment');
  };

  const handleEnrichmentComplete = () => {
    setAppState('app');
    setActiveTab('dashboard');
  };

  const handleLogout = () => {
    sessionStorage.removeItem('karios_user');
    sessionStorage.removeItem('karios_token');
    clearLegacyWorkspaceCache();
    setAppState('login');
    setUserProfile(null);
    setAuthUser(null);
    setSavedSchemes([]);
    setLastSelectedSchemeId('');
    setActiveTab('dashboard');
  };

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

  const handleNavigate = (tab) => {
    setActiveTab(tab);
  };

  const handleLanguageChange = (language) => {
    const nextLanguage = normalizeLanguageCode(language);
    setAppLanguage(nextLanguage);
    i18n.changeLanguage(nextLanguage);
  };

  const renderStandaloneShell = (content) => (
    <div ref={translatedRootRef} className="relative min-h-screen">
      <div className="fixed top-5 right-5 z-[90]">
        <LanguageSwitcher
          language={appLanguage}
          onChange={handleLanguageChange}
          buttonClassName="bg-white/95 backdrop-blur"
        />
      </div>
      {content}
    </div>
  );

  // ── Render App Content ──────────────────────────────────────
  const renderAppContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardView onNavigate={handleNavigate} userProfile={userProfile} />;
      case 'discovery':
        return (
          <SchemeDiscoveryView
            userProfile={userProfile}
            language={appLanguage}
            savedSchemes={savedSchemes}
            lastSelectedSchemeId={lastSelectedSchemeId}
            onSavedSchemesChange={handleSavedSchemesChange}
            onLastSelectedSchemeChange={handleLastSelectedSchemeChange}
          />
        );
      case 'validation':
        return (
          <DocValidationView
            userProfile={userProfile}
            savedSchemes={savedSchemes}
            lastSelectedSchemeId={lastSelectedSchemeId}
            onLastSelectedSchemeChange={handleLastSelectedSchemeChange}
          />
        );
      case 'assistant':
        return <AIChatView userProfile={userProfile} appLanguage={appLanguage} savedSchemes={savedSchemes} />;
      case 'profile':
        return (
          <div className="max-w-3xl mx-auto">
            <ProfileBuilder
              user={authUser}
              prefillData={userProfile}
              onComplete={handleProfileComplete}
            />
          </div>
        );
      default:
        return <DashboardView onNavigate={handleNavigate} userProfile={userProfile} />;
    }
  };

  // ── Full-Page States ────────────────────────────────────────
  if (appState === 'landing') {
    return renderStandaloneShell(<LandingPage onStart={() => setAppState('login')} />);
  }

  if (appState === 'login') {
    return renderStandaloneShell(<LoginPage onLogin={handleLogin} />);
  }

  if (appState === 'profile') {
    return renderStandaloneShell(
      <ProfileBuilder
        onComplete={handleProfileComplete}
        user={authUser}
      />
    );
  }

  if (appState === 'enrichment') {
    return renderStandaloneShell(
      <EnrichmentView
        onComplete={handleEnrichmentComplete}
        userProfile={userProfile}
      />
    );
  }

  // ── Main Dashboard Layout ────────────────────────────────────
  return (
    <div ref={translatedRootRef} className="flex min-h-screen bg-brand-intelligence font-plus selection:bg-brand-primary/20">
      {/* Sidebar */}
      <div className="h-screen sticky top-0 shrink-0 z-50">
        <Sidebar
          activeTab={activeTab === 'profile' ? 'profile' : activeTab}
          setActiveTab={setActiveTab}
          savedCount={savedSchemes.length}
          onLogout={handleLogout}
        />
      </div>

      {/* Main Content */}
      <main className="flex-1 min-w-0 flex flex-col">
        <TopNav 
          activeTab={activeTab} 
          appLanguage={appLanguage} 
          onLanguageChange={handleLanguageChange} 
        />

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
