import React from 'react';
import { ChevronDownIcon, GlobeAltIcon } from '@heroicons/react/24/outline';
import { getLanguageMeta, normalizeLanguageCode, SUPPORTED_LANGUAGES } from '../lib/languages';

function languageLabel(language) {
  return language.label === language.nativeLabel
    ? language.label
    : `${language.label} / ${language.nativeLabel}`;
}

export default function LanguageSwitcher({
  language,
  onChange,
  className = '',
  buttonClassName = '',
  menuClassName = '',
  itemClassName = '',
}) {
  const activeLanguage = getLanguageMeta(language);

  return (
    <div data-karios-no-translate="true" className={`relative group ${className}`}>
      <button
        className={`flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200 bg-white/95 text-slate-700 hover:text-slate-900 hover:bg-white transition-all font-bold text-xs shadow-sm ${buttonClassName}`}
      >
        <GlobeAltIcon className="w-4 h-4 text-brand-primary" />
        <span className="hidden sm:inline">{languageLabel(activeLanguage)}</span>
        <span className="sm:hidden">{activeLanguage.nativeLabel}</span>
        <ChevronDownIcon className="w-3 h-3 text-slate-400 group-hover:text-slate-600 transition-colors" />
      </button>

      <div className={`absolute right-0 top-12 w-56 bg-white rounded-2xl border border-slate-100 shadow-premium opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 p-2 ${menuClassName}`}>
        <div className="grid grid-cols-1 gap-1 max-h-72 overflow-y-auto scrollbar-hide">
          {SUPPORTED_LANGUAGES.map((entry) => {
            const isActive = activeLanguage.code === entry.code;
            return (
              <button
                key={entry.code}
                onClick={() => onChange(normalizeLanguageCode(entry.code))}
                className={`text-left px-3 py-2 rounded-lg text-xs font-bold transition-colors ${
                  isActive
                    ? 'bg-brand-primary text-white'
                    : 'text-slate-600 hover:bg-brand-primary/10 hover:text-brand-primary'
                } ${itemClassName}`}
                title={entry.label}
              >
                {languageLabel(entry)}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
