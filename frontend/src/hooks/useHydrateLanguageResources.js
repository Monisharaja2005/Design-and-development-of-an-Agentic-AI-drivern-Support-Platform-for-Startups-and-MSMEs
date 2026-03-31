import { useEffect } from 'react';
import i18n from '../i18n';
import { normalizeLanguageCode } from '../lib/languages';

const API_BASE = '';
const CACHE_PREFIX = 'karios_i18n_dynamic_v2_';

function flattenStrings(value, prefix = '', output = {}) {
  if (!value || typeof value !== 'object') return output;

  Object.entries(value).forEach(([key, nextValue]) => {
    const nextPath = prefix ? `${prefix}.${key}` : key;
    if (typeof nextValue === 'string') {
      output[nextPath] = nextValue;
      return;
    }
    if (nextValue && typeof nextValue === 'object' && !Array.isArray(nextValue)) {
      flattenStrings(nextValue, nextPath, output);
    }
  });

  return output;
}

function setDeepValue(target, path, value) {
  const segments = path.split('.');
  let cursor = target;
  segments.forEach((segment, index) => {
    if (index === segments.length - 1) {
      cursor[segment] = value;
      return;
    }
    if (!cursor[segment] || typeof cursor[segment] !== 'object' || Array.isArray(cursor[segment])) {
      cursor[segment] = {};
    }
    cursor = cursor[segment];
  });
}

function getCache(language) {
  try {
    const raw = localStorage.getItem(`${CACHE_PREFIX}${language}`);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function setCache(language, mapping) {
  try {
    localStorage.setItem(`${CACHE_PREFIX}${language}`, JSON.stringify(mapping));
  } catch {
    // Ignore storage quota or private-mode issues.
  }
}

async function fetchTranslationMap(texts, language) {
  const uniqueTexts = [...new Set(texts.filter(Boolean))];
  if (!uniqueTexts.length) return {};

  const cache = getCache(language);
  const output = { ...cache };
  const missing = uniqueTexts.filter((text) => !output[text]);

  const batchSize = 40;
  for (let start = 0; start < missing.length; start += batchSize) {
    const batch = missing.slice(start, start + batchSize);
    try {
      const response = await fetch(`${API_BASE}/v1/ui/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texts: batch, language }),
      });
      const data = await response.json();
      if (!response.ok) {
        continue;
      }
      const translations = data.translations || {};
      batch.forEach((text) => {
        const translated = translations[text];
        if (translated && translated !== text) {
          output[text] = translated;
        }
      });
    } catch {
      // Keep output untouched so we retry next time.
    }
  }

  setCache(language, output);
  return output;
}

function buildMissingLeafMap(sourceBundle, targetBundle) {
  const sourceFlat = flattenStrings(sourceBundle);
  const targetFlat = flattenStrings(targetBundle);
  const result = [];

  Object.entries(sourceFlat).forEach(([path, englishValue]) => {
    if (!englishValue || path.startsWith('schemes.')) return;
    const currentValue = targetFlat[path];
    if (currentValue && currentValue !== englishValue) return;
    result.push({ path, englishValue });
  });

  return result;
}

function buildPatch(leaves, mapping) {
  const patch = {};
  leaves.forEach(({ path, englishValue }) => {
    const translated = mapping[englishValue];
    if (!translated || translated === englishValue) return;
    setDeepValue(patch, path, translated);
  });
  return patch;
}

export default function useHydrateLanguageResources(language) {
  useEffect(() => {
    const langCode = normalizeLanguageCode(language);
    if (langCode === 'en') return undefined;

    let disposed = false;

    const hydrate = async () => {
      const sourceBundle = i18n.getResourceBundle('en', 'translation') || {};
      const targetBundle = i18n.getResourceBundle(langCode, 'translation') || {};
      const missingLeaves = buildMissingLeafMap(sourceBundle, targetBundle);
      if (!missingLeaves.length) return;

      const mapping = await fetchTranslationMap(
        missingLeaves.map((item) => item.englishValue),
        langCode,
      );
      if (disposed) return;

      const patch = buildPatch(missingLeaves, mapping);
      if (!Object.keys(patch).length) return;

      i18n.addResourceBundle(langCode, 'translation', patch, true, true);
      if (i18n.resolvedLanguage === langCode || i18n.language === langCode) {
        i18n.emit('languageChanged', langCode);
      }
    };

    hydrate();

    return () => {
      disposed = true;
    };
  }, [language]);
}
