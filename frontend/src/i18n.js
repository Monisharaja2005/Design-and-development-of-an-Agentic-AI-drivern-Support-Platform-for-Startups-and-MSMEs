import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { DEFAULT_LANGUAGE, SUPPORTED_LANGUAGE_CODES } from './lib/languages';

import enTranslation from './locales/en/translation.json';
import hiTranslation from './locales/hi/translation.json';
import mrTranslation from './locales/mr/translation.json';
import knTranslation from './locales/kn/translation.json';
import taTranslation from './locales/ta/translation.json';
import teTranslation from './locales/te/translation.json';
import bnTranslation from './locales/bn/translation.json';
import guTranslation from './locales/gu/translation.json';
import mlTranslation from './locales/ml/translation.json';
import orTranslation from './locales/or/translation.json';
import paTranslation from './locales/pa/translation.json';
import urTranslation from './locales/ur/translation.json';
import asTranslation from './locales/as/translation.json';
import satTranslation from './locales/sat/translation.json';
import ksTranslation from './locales/ks/translation.json';
import neTranslation from './locales/ne/translation.json';

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: enTranslation },
      hi: { translation: hiTranslation },
      mr: { translation: mrTranslation },
      kn: { translation: knTranslation },
      ta: { translation: taTranslation },
      te: { translation: teTranslation },
      bn: { translation: bnTranslation },
      gu: { translation: guTranslation },
      ml: { translation: mlTranslation },
      or: { translation: orTranslation },
      pa: { translation: paTranslation },
      ur: { translation: urTranslation },
      as: { translation: asTranslation },
      sat: { translation: satTranslation },
      ks: { translation: ksTranslation },
      ne: { translation: neTranslation }
    },
    fallbackLng: DEFAULT_LANGUAGE,
    supportedLngs: SUPPORTED_LANGUAGE_CODES,
    load: 'languageOnly',
    nonExplicitSupportedLngs: true,
    cleanCode: true,
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      lookupLocalStorage: 'karios_lang',
      caches: ['localStorage'],
    },
    interpolation: {
      escapeValue: false
    },
    returnNull: false,
  });

export default i18n;
