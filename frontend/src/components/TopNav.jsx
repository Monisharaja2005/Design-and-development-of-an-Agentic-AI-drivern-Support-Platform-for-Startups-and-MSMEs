import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  BellIcon,
  CheckCircleIcon,
  SparklesIcon,
  DocumentCheckIcon,
} from '@heroicons/react/24/outline';
import { getLanguageMeta, normalizeLanguageCode } from '../lib/languages';
import LanguageSwitcher from './LanguageSwitcher';

export default function TopNav({ activeTab, appLanguage, onLanguageChange }) {
  const { t, i18n } = useTranslation();
  const [showNotifs, setShowNotifs] = useState(false);
  const [serverStatus, setServerStatus] = useState('checking');
  const user = JSON.parse(sessionStorage.getItem('karios_user') || '{}');
  const userName = user.full_name || user.fullName || 'User';
  const activeLanguage = getLanguageMeta(appLanguage || i18n.resolvedLanguage || i18n.language);
  const notifications = useMemo(() => ([
    {
      text: t('topnav.notifications.shortlist', 'Scheme shortlist updated with the latest matching results.'),
      time: t('topnav.notifications.time_2m', '2m ago'),
      icon: SparklesIcon,
      color: 'text-brand-primary',
    },
    {
      text: t('topnav.notifications.validation', 'Document validation is ready for your active shortlist item.'),
      time: t('topnav.notifications.time_8m', '8m ago'),
      icon: DocumentCheckIcon,
      color: 'text-emerald-600',
    },
    {
      text: t('topnav.notifications.profile', 'Profile signals improved your discovery confidence.'),
      time: t('topnav.notifications.time_14m', '14m ago'),
      icon: CheckCircleIcon,
      color: 'text-blue-600',
    },
  ]), [i18n.resolvedLanguage, t]);

  const PAGE_TITLES = {
    dashboard: { title: t('dashboard.title'), subtitle: t('dashboard.subtitle') },
    discovery: { title: t('common.discovery'), subtitle: t('discovery.subtitle') },
    validation: { title: t('common.validation'), subtitle: t('validation.subtitle') },
    assistant: { title: t('assistant.title'), subtitle: t('assistant.subtitle') },
    profile: { title: t('common.profile'), subtitle: t('common.pro_subtitle_clean', 'Verified businesses get 3x higher priority in scheme matching.') },
  };

  const page = PAGE_TITLES[activeTab] || PAGE_TITLES.dashboard;

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch('/health', { signal: AbortSignal.timeout(3000) });
        if (res.ok) setServerStatus('online');
        else setServerStatus('error');
      } catch {
        setServerStatus('offline');
      }
    };
    check();
    const iv = setInterval(check, 30000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="sticky top-0 z-40 bg-white/90 backdrop-blur-xl border-b border-slate-100/80">
      <div className="flex items-center justify-between px-8 py-4">
        <div>
          <h1 className="text-lg font-extrabold text-slate-900 tracking-tight">{page.title}</h1>
          <p className="text-xs text-slate-400 font-medium whitespace-nowrap">
            {t('common.welcome', { name: userName, defaultValue: `Hello, ${userName}` })} · {page.subtitle}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className={`hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-[10px] font-black uppercase tracking-widest mr-2 ${
            serverStatus === 'online'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
              : serverStatus === 'offline'
                ? 'bg-red-50 border-red-200 text-red-700'
                : 'bg-amber-50 border-amber-200 text-amber-700'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${
              serverStatus === 'online' ? 'bg-emerald-500 animate-pulse'
                : serverStatus === 'offline' ? 'bg-red-500'
                  : 'bg-amber-400 animate-pulse'
            }`} />
            {serverStatus === 'online' ? 'System Ready'
              : serverStatus === 'offline' ? 'System Offline'
                : t('topnav.connecting', 'Connecting...')}
          </div>

          <LanguageSwitcher
            language={activeLanguage.code}
            onChange={(code) => {
              const nextCode = normalizeLanguageCode(code);
              i18n.changeLanguage(nextCode);
              onLanguageChange(nextCode);
            }}
            className="mr-2"
            buttonClassName="uppercase tracking-wider bg-white"
          />

          {notifications.length > 0 && (
            <div className="relative">
              <button
                onClick={() => setShowNotifs((value) => !value)}
                className="relative w-10 h-10 flex items-center justify-center rounded-xl border border-slate-200 text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-all"
              >
                <BellIcon className="w-5 h-5" />
                <span className="absolute top-2 right-2 w-2 h-2 bg-brand-primary rounded-full" />
              </button>

              <AnimatePresence>
                {showNotifs && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setShowNotifs(false)} />
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95, y: -8 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95, y: -8 }}
                      transition={{ duration: 0.15 }}
                      className="absolute right-0 top-12 w-80 bg-white rounded-2xl border border-slate-100 shadow-premium z-50"
                    >
                      <div className="p-4 border-b border-slate-100">
                        <div className="flex items-center justify-between">
                          <span className="font-extrabold text-slate-900 text-sm">{t('topnav.updates_title', 'System Updates')}</span>
                          <span className="badge-primary">
                            {t('topnav.new_count', { count: notifications.length, defaultValue: `${notifications.length} New` })}
                          </span>
                        </div>
                      </div>
                      <div className="p-2">
                        {notifications.map((notification, index) => (
                          <div key={index} className="flex items-start gap-3 p-3 hover:bg-slate-50 rounded-xl transition-colors cursor-pointer">
                            <notification.icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${notification.color}`} />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-700 leading-snug">{notification.text}</p>
                              <p className="text-[10px] text-slate-400 font-bold mt-0.5">{notification.time}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="p-3 border-t border-slate-100">
                        <button className="w-full text-xs font-bold text-brand-primary hover:underline">
                          {t('topnav.view_all', 'View All Activity')}
                        </button>
                      </div>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
