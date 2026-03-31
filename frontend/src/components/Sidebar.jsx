import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Squares2X2Icon, MagnifyingGlassIcon, DocumentCheckIcon,
  UserCircleIcon, ChevronLeftIcon, ChevronRightIcon,
  ChatBubbleLeftRightIcon, BookmarkIcon, ArrowRightStartOnRectangleIcon
} from '@heroicons/react/24/outline';
import { 
  Squares2X2Icon as Squares2X2Solid,
  MagnifyingGlassIcon as MagnifyingGlassSolid,
  DocumentCheckIcon as DocumentCheckSolid,
  UserCircleIcon as UserCircleSolid
} from '@heroicons/react/24/solid';
import { useTranslation } from 'react-i18next';

export default function Sidebar({ activeTab, setActiveTab, onLogout, savedCount = 0 }) {
  const { t } = useTranslation();
  const [collapsed, setCollapsed] = useState(false);
  const userInfo = JSON.parse(sessionStorage.getItem('karios_user') || '{}');

  const NAV_ITEMS = [
    {
      id: 'dashboard',
      label: t('common.dashboard'),
      icon: Squares2X2Icon,
      iconSolid: Squares2X2Solid,
      badge: null,
      color: 'text-blue-600',
    },
    {
      id: 'discovery',
      label: t('common.discovery'),
      icon: MagnifyingGlassIcon,
      iconSolid: MagnifyingGlassSolid,
      badge: null,
      color: 'text-purple-600',
    },
    {
      id: 'validation',
      label: t('common.validation'),
      icon: DocumentCheckIcon,
      iconSolid: DocumentCheckSolid,
      badge: null,
      color: 'text-emerald-600',
    },
    {
      id: 'assistant',
      label: t('common.assistant'),
      icon: ChatBubbleLeftRightIcon,
      iconSolid: ChatBubbleLeftRightIcon,
      badge: t('common.active'),
      color: 'text-brand-primary',
    },
    {
      id: 'profile',
      label: t('common.profile'),
      icon: UserCircleIcon,
      iconSolid: UserCircleSolid,
      badge: null,
      color: 'text-slate-600',
    },
  ];

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="h-screen bg-white border-r border-slate-100 flex flex-col shadow-card relative overflow-hidden"
    >
      {/* Logo */}
      {/* Logo Section Removed */}
      <div className="px-4 py-5 border-b border-slate-100 flex items-center justify-end">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="relative w-7 h-7 bg-white border border-slate-200 rounded-full flex items-center justify-center shadow-sm text-slate-400 hover:text-slate-700 transition-colors z-10"
        >
          {collapsed ? <ChevronRightIcon className="w-3.5 h-3.5" /> : <ChevronLeftIcon className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {!collapsed && (
          <div className="px-2 pb-2">
            <span className="label-xs opacity-50">{t('common.navigation')}</span>
          </div>
        )}
        {NAV_ITEMS.map((item) => {
          const isActive = activeTab === item.id;
          const Icon = isActive ? item.iconSolid : item.icon;

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl text-left transition-all duration-200 group relative ${
                isActive
                  ? 'bg-brand-primary/8 text-brand-primary font-bold border border-brand-primary/15'
                  : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800 font-semibold'
              }`}
              title={collapsed ? item.label : ''}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-brand-primary' : item.color} transition-colors`} />

              <AnimatePresence>
                {!collapsed && (
                  <motion.span
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -5 }}
                    className="text-sm flex-1 whitespace-nowrap"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>

              {!collapsed && item.badge && (
                <span className={`text-[9px] font-black px-2 py-0.5 rounded-full ${
                  item.badge === 'LIVE'
                    ? 'bg-emerald-100 text-emerald-700 animate-pulse-soft'
                    : 'bg-slate-100 text-slate-500'
                }`}>
                  {item.badge}
                </span>
              )}

              {isActive && (
                <motion.div
                  layoutId="nav-active"
                  className="absolute left-0 top-2 bottom-2 w-0.5 bg-brand-primary rounded-full"
                />
              )}
            </button>
          );
        })}

        {/* Saved Schemes shortcut */}
        {savedCount > 0 && !collapsed && (
          <div className="pt-4">
            <div className="px-2 pb-2">
              <span className="label-xs opacity-50">{t('common.shortlisted')}</span>
            </div>
            <button
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-500 hover:bg-slate-50 hover:text-slate-800 font-semibold transition-all"
              onClick={() => {}}
            >
              <BookmarkIcon className="w-4 h-4 text-emerald-600" />
              <span className="text-sm flex-1 text-left">{t('common.saved_schemes')}</span>
              <span className="text-[9px] font-black px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full">
                {savedCount}
              </span>
            </button>
          </div>
        )}
      </nav>

      {/* Bottom: User & Logout */}
      <div className="border-t border-slate-100 p-3 space-y-1">
        {!collapsed ? (
          <div className="flex items-center gap-3 px-3 py-3 rounded-xl bg-slate-50 mb-2" data-karios-no-translate="true">
            <div className="w-8 h-8 rounded-xl bg-brand-primary/10 text-brand-primary font-black flex items-center justify-center text-sm flex-shrink-0">
              {(userInfo.full_name || userInfo.email || 'U')[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-bold text-slate-900 text-xs truncate">
                {userInfo.full_name || userInfo.email?.split('@')[0] || 'User'}
              </div>
              <div className="text-[9px] text-slate-400 font-medium truncate">{userInfo.email}</div>
            </div>
          </div>
        ) : (
          <div className="flex justify-center mb-1">
            <div className="w-8 h-8 rounded-xl bg-brand-primary/10 text-brand-primary font-black flex items-center justify-center text-sm">
              {(userInfo.full_name || userInfo.email || 'U')[0].toUpperCase()}
            </div>
          </div>
        )}

        <button
          onClick={onLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-slate-500 hover:bg-red-50 hover:text-red-600 transition-all font-semibold"
          title={collapsed ? t('common.logout') : ''}
        >
          <ArrowRightStartOnRectangleIcon className="w-5 h-5 flex-shrink-0" />
          {!collapsed && <span className="text-sm">{t('common.logout')}</span>}
        </button>
      </div>
    </motion.aside>
  );
}
