export const DEFAULT_LANGUAGE = 'en';

export const SUPPORTED_LANGUAGES = [
  { code: 'en', label: 'English', nativeLabel: 'English', shortLabel: 'EN' },
  { code: 'hi', label: 'Hindi', nativeLabel: 'हिन्दी', shortLabel: 'हि' },
  { code: 'bn', label: 'Bengali', nativeLabel: 'বাংলা', shortLabel: 'বা' },
  { code: 'gu', label: 'Gujarati', nativeLabel: 'ગુજરાતી', shortLabel: 'ગુ' },
  { code: 'kn', label: 'Kannada', nativeLabel: 'ಕನ್ನಡ', shortLabel: 'ಕ' },
  { code: 'ks', label: 'Kashmiri', nativeLabel: 'कॉशुर', shortLabel: 'क' },
  { code: 'ml', label: 'Malayalam', nativeLabel: 'മലയാളം', shortLabel: 'മ' },
  { code: 'mr', label: 'Marathi', nativeLabel: 'मराठी', shortLabel: 'म' },
  { code: 'ne', label: 'Nepali', nativeLabel: 'नेपाली', shortLabel: 'ने' },
  { code: 'or', label: 'Odia', nativeLabel: 'ଓଡ଼ିଆ', shortLabel: 'ଓ' },
  { code: 'pa', label: 'Punjabi', nativeLabel: 'ਪੰਜਾਬੀ', shortLabel: 'ਪੰ' },
  { code: 'sat', label: 'Santali', nativeLabel: 'ᱥᱟᱱᱛᱟᱲᱤ', shortLabel: 'ᱥᱟ' },
  { code: 'ta', label: 'Tamil', nativeLabel: 'தமிழ்', shortLabel: 'த' },
  { code: 'te', label: 'Telugu', nativeLabel: 'తెలుగు', shortLabel: 'తె' },
  { code: 'ur', label: 'Urdu', nativeLabel: 'اردو', shortLabel: 'ار' },
  { code: 'as', label: 'Assamese', nativeLabel: 'অসমীয়া', shortLabel: 'অ' },
];

export const SUPPORTED_LANGUAGE_CODES = SUPPORTED_LANGUAGES.map((language) => language.code);

const LANGUAGE_BY_CODE = Object.fromEntries(
  SUPPORTED_LANGUAGES.map((language) => [language.code, language]),
);

const LANGUAGE_ALIASES = {
  english: 'en',
  en: 'en',
  hindi: 'hi',
  hi: 'hi',
  bengali: 'bn',
  bangla: 'bn',
  bn: 'bn',
  gujarati: 'gu',
  gu: 'gu',
  kannada: 'kn',
  kn: 'kn',
  kashmiri: 'ks',
  ks: 'ks',
  malayalam: 'ml',
  ml: 'ml',
  marathi: 'mr',
  mr: 'mr',
  nepali: 'ne',
  ne: 'ne',
  odia: 'or',
  oriya: 'or',
  or: 'or',
  punjabi: 'pa',
  pa: 'pa',
  santali: 'sat',
  sat: 'sat',
  tamil: 'ta',
  ta: 'ta',
  telugu: 'te',
  te: 'te',
  urdu: 'ur',
  ur: 'ur',
  assamese: 'as',
  as: 'as',
  'हिन्दी': 'hi',
  'বাংলা': 'bn',
  'ગુજરાતી': 'gu',
  'ಕನ್ನಡ': 'kn',
  'कॉशुर': 'ks',
  'മലയാളം': 'ml',
  'मराठी': 'mr',
  'नेपाली': 'ne',
  'ଓଡ଼ିଆ': 'or',
  'ਪੰਜਾਬੀ': 'pa',
  'ᱥᱟᱱᱛᱟᱲᱤ': 'sat',
  'தமிழ்': 'ta',
  'తెలుగు': 'te',
  'اردو': 'ur',
  'অসমীয়া': 'as',
};

export function normalizeLanguageCode(value) {
  const raw = String(value || '').trim();
  if (!raw) return DEFAULT_LANGUAGE;

  const lower = raw.toLowerCase();
  const compact = lower.split('(')[0].trim();
  const base = lower.split('-')[0].trim();

  return LANGUAGE_ALIASES[lower]
    || LANGUAGE_ALIASES[compact]
    || LANGUAGE_ALIASES[base]
    || DEFAULT_LANGUAGE;
}

export function getLanguageMeta(value) {
  const code = normalizeLanguageCode(value);
  return LANGUAGE_BY_CODE[code] || LANGUAGE_BY_CODE[DEFAULT_LANGUAGE];
}
