import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import DocumentVerification from '../components/DocumentVerification/DocumentVerification';
import CircularGauge from '../components/Dashboard/CircularGauge';

import StatCard from '../components/Dashboard/StatCard';
import { 
  SparklesIcon, ExclamationTriangleIcon,
  CurrencyRupeeIcon, DocumentCheckIcon, ArrowRightIcon, 
  ChatBubbleLeftEllipsisIcon, 
  UserCircleIcon, MagnifyingGlassIcon,
  Squares2X2Icon
} from '@heroicons/react/24/outline';

const API_BASE = 'http://127.0.0.1:8001';

export default function Dashboard({ onNavigate, userProfile, activeScheme, savedSchemes, lastSelectedSchemeId, onSavedSchemesChange, onLastSelectedSchemeChange }) {
  const { t } = useTranslation();

  const defaultRequiredDocs = [
    { type: 'aadhaar', label: 'Aadhaar Card' },
    { type: 'pan', label: 'PAN Card' },
    { type: 'gst', label: 'GST Certificate' },
    { type: 'udyam', label: 'Udyam Registration' }
  ];

  const getRequiredDocs = (scheme) => {
    if (!scheme) return [];

    if (scheme.scheme_name?.includes("MUDRA")) {
      return [
        { type: 'aadhaar', label: 'Aadhaar Card' },
        { type: 'pan', label: 'PAN Card' }
      ];
    }

    return [
      { type: 'aadhaar', label: 'Aadhaar Card' }
    ];
  };


  const [schemeCount, setSchemeCount] = useState(383);
  const [topSchemes, setTopSchemes] = useState([]);
  const [schemesLoading, setSchemesLoading] = useState(false);

  const stats = [
    { title: t('dashboard.stats.active_schemes') || 'Active Schemes', value: schemeCount, icon: Squares2X2Icon, color: 'text-brand-primary', bg: 'bg-brand-primary/10' },
    { title: t('dashboard.stats.total_investment') || 'Total Investment', value: '₹12.5 Cr', icon: CurrencyRupeeIcon, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { title: t('dashboard.stats.docs_verified') || 'Documents Verified', value: '3/8', icon: DocumentCheckIcon, color: 'text-amber-600', bg: 'bg-amber-50' },
    { title: t('dashboard.stats.ai_sessions') || 'AI Sessions', value: '12', icon: ChatBubbleLeftEllipsisIcon, color: 'text-purple-600', bg: 'bg-purple-50' },
  ];

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(r => r.json())
      .then(d => setSchemeCount(d.schemes_loaded || 383))
      .catch(() => {});
  }, []);

  // FIXED: AbortController guard (API loop prevention)
  const topSchemesAbortRef = useRef(null);

  useEffect(() => {
    const profile = userProfile || {};
    if (!profile.sector && !profile.state) return;

    // Abort previous request
    topSchemesAbortRef.current?.abort();
    topSchemesAbortRef.current = new AbortController();

    setSchemesLoading(true);
    
    fetch(`${API_BASE}/v1/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: topSchemesAbortRef.current.signal,
      body: JSON.stringify({
        sector: profile.sector || '',
        state: profile.state || '',
        entityType: profile.entityType || '',
        turnover: profile.turnover || '',
        businessDescription: profile.businessDescription || '',
        language: 'en',
      }),
    })
      .then(r => r.json())
      .then(d => setTopSchemes((d.schemes || []).slice(0, 3)))
      .catch(e => {
        if (e.name !== 'AbortError') console.warn('Dashboard top schemes failed:', e);
      })
      .finally(() => setSchemesLoading(false));

    return () => topSchemesAbortRef.current?.abort();
  }, [userProfile]);

  const userInfo = JSON.parse(sessionStorage.getItem('karios_user') || '{}');
  const userName = userProfile?.full_name || userProfile?.businessName || userInfo.full_name || userInfo.fullName || userInfo.email?.split('@')[0] || 'User';
  const profileComplete = userProfile && Object.keys(userProfile).length > 5;

  const matchColor = (score) =>
    score >= 85 ? 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20' :
    score >= 70 ? 'text-blue-400 bg-blue-400/10 border-blue-400/20' :
                  'text-amber-400 bg-amber-400/10 border-amber-400/20';

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="page-title">
            {t('dashboard.welcome_back') || 'Welcome back'}, <span className="gradient-text">{userName}</span> 👋
          </h2>
          <p className="text-slate-500 font-medium mt-1">
            {t('dashboard.subtitle')}
          </p>
        </div>
        <button
          onClick={() => onNavigate?.('discovery')}
          className="btn-primary hidden md:inline-flex"
        >
          <MagnifyingGlassIcon className="w-5 h-5" />
          {t('common.discovery')}
        </button>
      </div>

      {/* Profile Completeness Alert */}
      {!profileComplete && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-center justify-between gap-4"
        >
          <div className="flex items-center gap-3">
            <ExclamationTriangleIcon className="w-5 h-5 text-amber-600 flex-shrink-0" />
            <div>
              <div className="font-bold text-amber-900 text-sm">{t('dashboard.profile_incomplete') || 'Profile incomplete'}</div>
              <div className="text-amber-700 text-xs font-medium">{t('dashboard.profile_incomplete_msg') || 'Complete your business profile for personalized scheme matching.'}</div>
            </div>
          </div>
          <button onClick={() => onNavigate?.('profile')} className="btn-secondary text-xs px-4 py-2 whitespace-nowrap flex-shrink-0">
            {t('dashboard.complete_profile') || 'Complete Profile'}
          </button>
        </motion.div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        {stats.map((s, i) => <StatCard key={i} {...s} delay={i * 0.08} />)}
      </div>

      {/* ── TOP-3 MATCHED SCHEMES ─────────────────────────────────── */}
      <div className="intelligence-card p-8 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden border border-white/10 rounded-3xl">
        <div className="absolute -top-20 -right-20 w-64 h-64 bg-brand-primary/15 rounded-full blur-[80px] pointer-events-none" />
        <div className="relative z-10">
          {/* Header row */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-brand-primary rounded-xl flex items-center justify-center">
                <SparklesIcon className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-black text-white text-base tracking-tight">Top Matched Schemes</h3>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
                  <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">AI Personalised</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => onNavigate?.('discovery')}
              className="flex items-center gap-1.5 text-[11px] font-black text-brand-primary hover:text-blue-400 transition-colors uppercase tracking-widest"
            >
              View all {schemeCount}+ <ArrowRightIcon className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Loading skeleton */}
          {schemesLoading && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="p-5 rounded-2xl bg-white/5 border border-white/10 space-y-3">
                  <div className="h-4 bg-white/10 rounded animate-pulse w-3/4" />
                  <div className="h-3 bg-white/10 rounded animate-pulse w-1/2" />
                  <div className="flex gap-2 mt-3">
                    <div className="h-5 w-20 bg-white/10 rounded-lg animate-pulse" />
                    <div className="h-5 w-24 bg-white/10 rounded-lg animate-pulse" />
                  </div>
                  <div className="h-3 bg-white/10 rounded animate-pulse w-1/3 mt-2" />
                </div>
              ))}
            </div>
          )}

          {/* Scheme cards */}
          {!schemesLoading && topSchemes.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {topSchemes.map((scheme, i) => {
                const rawScore = scheme.final_rank_score || scheme.ai_confidence || 0.7;
                const score = Math.min(99, Math.round(rawScore > 1 ? rawScore : rawScore * 100));
                const reasons = (scheme.match_reasons || []).slice(0, 2);
                return (
                  <motion.div
                    key={scheme.scheme_id || i}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    onClick={() => onNavigate?.('discovery')}
                    className="p-5 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/8 hover:border-white/20 transition-all cursor-pointer group flex flex-col gap-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="font-bold text-white text-[13px] leading-snug line-clamp-2 flex-1">
                        {scheme.scheme_name || scheme.Scheme_Name}
                      </h4>
                      <span className={`flex-shrink-0 text-[10px] font-black px-2 py-0.5 rounded-full border ${matchColor(score)}`}>
                        {score}%
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      {scheme.sector && (
                        <span className="text-[9px] font-black text-slate-400 uppercase tracking-wider">{scheme.sector}</span>
                      )}
                      {scheme.state && (
                        <span className="text-[9px] font-black text-brand-primary uppercase tracking-wider">· {scheme.state}</span>
                      )}
                    </div>
                    {reasons.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {reasons.map((r, ri) => (
                          <span key={ri} className="text-[9px] font-bold px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                            ✓ {r}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="flex items-center gap-1 text-brand-primary text-[10px] font-black uppercase tracking-widest group-hover:gap-2 transition-all mt-auto">
                      View Details <ArrowRightIcon className="w-3 h-3" />
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}

          {/* Fallback: no profile or fetch failed */}
          {!schemesLoading && topSchemes.length === 0 && (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <div className="w-14 h-14 bg-white/5 rounded-2xl flex items-center justify-center mb-4 border border-white/10">
                <SparklesIcon className="w-7 h-7 text-slate-500" />
              </div>
              <p className="text-slate-400 text-sm font-semibold mb-1">Complete your profile to unlock</p>
              <p className="text-slate-500 text-xs font-medium mb-4">AI will match schemes tailored to your business</p>
              <button
                onClick={() => onNavigate?.('profile')}
                className="px-5 py-2.5 bg-brand-primary text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-brand-secondary transition-colors"
              >
                Build Profile
              </button>
            </div>
          )}
        </div>

        {/* Document Verification for Active Scheme */}
        {activeScheme && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8"
          >
            <DocumentVerification
              schemeId={activeScheme.scheme_id || activeScheme.scheme_code || lastSelectedSchemeId}
              schemeName={activeScheme.scheme_name || activeScheme.Scheme_Name || 'PM MUDRA Yojana'}
              requiredDocs={getRequiredDocs(activeScheme)}
            />
          </motion.div>
        )}
      </div>

      {/* AI Match Score */}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-3 intelligence-card p-8 bg-gradient-to-br from-white via-white to-brand-primary/4 relative overflow-hidden group">
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-1.5 h-8 bg-brand-primary rounded-full" />
              <h3 className="text-xl font-extrabold text-slate-800">{t('dashboard.intel_summary') || 'AI Intelligence Summary'}</h3>
            </div>

            <div className="flex flex-wrap gap-10 items-center">
              <CircularGauge
                value={profileComplete ? 76 : 28}
                size={180}
                stroke={16}
                color="#4F7CFF"
                label={t('dashboard.karios_score') || 'Match Score'}
              />
              <div className="flex-1 space-y-6">
                <div>
                  <h4 className="text-xl font-bold text-slate-800 mb-2">
                    {profileComplete ? t('dashboard.status_optimized') : t('dashboard.status_needed')}
                  </h4>
                  <p className="text-base text-slate-500 font-medium leading-relaxed max-w-2xl">
                    {profileComplete ? t('dashboard.optimized_msg') : t('dashboard.needed_msg')}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <div className="px-4 py-2 bg-brand-primary/8 rounded-xl border border-brand-primary/15 text-brand-primary text-[11px] font-black uppercase tracking-widest">
                    {profileComplete ? t('dashboard.priority_high') : t('dashboard.action_required')}
                  </div>
                  {profileComplete && (
                    <div className="px-4 py-2 bg-emerald-50 rounded-xl border border-emerald-100 text-emerald-600 text-[11px] font-black uppercase tracking-widest">
                      {t('dashboard.profile_active')}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
          <div className="absolute top-0 right-0 p-10 opacity-5 group-hover:opacity-10 transition-opacity">
            <SparklesIcon className="w-56 h-56 text-brand-primary" />
          </div>
        </div>
      </div>
    </div>
  );
}
