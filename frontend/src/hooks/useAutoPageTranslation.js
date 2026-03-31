import { useEffect, useRef } from 'react';
import { normalizeLanguageCode } from '../lib/languages';

const API_BASE = '';
const TEXT_NODE_ORIGINALS = new WeakMap();
const ATTRIBUTE_ORIGINALS = new WeakMap();
const translationCache = new Map();
const TRANSLATABLE_ATTRIBUTES = ['placeholder', 'title', 'aria-label'];

function containsLetters(value) {
  return /[\p{L}]/u.test(value);
}

function shouldTranslateText(value) {
  const text = String(value || '').replace(/\s+/g, ' ').trim();
  if (!text || text.length < 2) return false;
  if (!containsLetters(text)) return false;
  if (!/[A-Za-z]/.test(text)) return false;
  if (/^(https?:\/\/|www\.)/i.test(text)) return false;
  if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(text)) return false;
  if (/^[A-Za-z]:\\/.test(text)) return false;
  if (/^[\d\s₹%+.,:/()\-]+$/.test(text)) return false;
  return true;
}

function shouldSkipElement(element) {
  if (!element) return true;
  if (element.closest('[data-karios-no-translate="true"]')) return true;
  const tagName = element.tagName;
  return ['SCRIPT', 'STYLE', 'TEXTAREA'].includes(tagName);
}

function replaceSourceText(raw, source, translated) {
  if (!raw) return translated;
  const normalizedRaw = String(raw);
  const sourceIndex = normalizedRaw.indexOf(source);
  if (sourceIndex === -1) {
    return translated;
  }
  return `${normalizedRaw.slice(0, sourceIndex)}${translated}${normalizedRaw.slice(sourceIndex + source.length)}`;
}

function getAttributeStore(element) {
  const existing = ATTRIBUTE_ORIGINALS.get(element);
  if (existing) return existing;
  const created = {};
  ATTRIBUTE_ORIGINALS.set(element, created);
  return created;
}

function collectTargets(root) {
  const targets = [];

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.parentElement || shouldSkipElement(node.parentElement)) {
        return NodeFilter.FILTER_REJECT;
      }
      const original = TEXT_NODE_ORIGINALS.get(node) ?? node.nodeValue ?? '';
      const source = original.replace(/\s+/g, ' ').trim();
      return shouldTranslateText(source) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
    },
  });

  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (!TEXT_NODE_ORIGINALS.has(node)) {
      TEXT_NODE_ORIGINALS.set(node, node.nodeValue ?? '');
    }
    const raw = TEXT_NODE_ORIGINALS.get(node) ?? '';
    const source = raw.replace(/\s+/g, ' ').trim();
    targets.push({ type: 'text', node, raw, source });
  }

  root.querySelectorAll('*').forEach((element) => {
    if (shouldSkipElement(element)) return;
    const store = getAttributeStore(element);
    TRANSLATABLE_ATTRIBUTES.forEach((attribute) => {
      const current = element.getAttribute(attribute);
      if (!current || !shouldTranslateText(current)) return;
      if (!(attribute in store)) {
        store[attribute] = current;
      }
      const source = String(store[attribute] || '').replace(/\s+/g, ' ').trim();
      if (!shouldTranslateText(source)) return;
      targets.push({ type: 'attribute', element, attribute, source });
    });
  });

  return targets;
}

function restoreOriginals(root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (TEXT_NODE_ORIGINALS.has(node)) {
      node.nodeValue = TEXT_NODE_ORIGINALS.get(node);
    }
  }

  root.querySelectorAll('*').forEach((element) => {
    const store = ATTRIBUTE_ORIGINALS.get(element);
    if (!store) return;
    Object.entries(store).forEach(([attribute, value]) => {
      if (value === undefined || value === null || value === '') {
        element.removeAttribute(attribute);
      } else {
        element.setAttribute(attribute, value);
      }
    });
  });
}

async function fetchTranslationMap(texts, language) {
  const uniqueTexts = [...new Set(texts.filter((text) => shouldTranslateText(text)))];
  if (!uniqueTexts.length) return {};

  const output = {};
  const missing = [];
  uniqueTexts.forEach((text) => {
    const key = `${language}::${text}`;
    if (translationCache.has(key)) {
      output[text] = translationCache.get(key);
    } else {
      missing.push(text);
    }
  });

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
        batch.forEach((text) => {
          output[text] = text;
        });
        continue;
      }
      const translations = data.translations || {};
      batch.forEach((text) => {
        const translated = translations[text] || text;
        const key = `${language}::${text}`;
        if (translated && translated !== text) {
          translationCache.set(key, translated);
        }
        output[text] = translated;
      });
    } catch {
      batch.forEach((text) => {
        output[text] = text;
      });
    }
  }

  return output;
}

export default function useAutoPageTranslation(rootRef, language) {
  const updateInProgressRef = useRef(false);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return undefined;

    const langCode = normalizeLanguageCode(language);
    let disposed = false;
    let timeoutId = null;
    let observer = null;

    const runTranslation = async () => {
      if (disposed || !rootRef.current) return;
      if (updateInProgressRef.current) return;

      updateInProgressRef.current = true;
      restoreOriginals(rootRef.current);

      if (langCode === 'en') {
        updateInProgressRef.current = false;
        return;
      }

      const targets = collectTargets(rootRef.current);
      const sourceTexts = targets.map((target) => target.source);
      const translationMap = await fetchTranslationMap(sourceTexts, langCode);

      if (!disposed && rootRef.current) {
        targets.forEach((target) => {
          const translated = translationMap[target.source] || target.source;
          if (!translated || translated === target.source) return;
          if (target.type === 'text') {
            target.node.nodeValue = replaceSourceText(target.raw, target.source, translated);
          } else if (target.type === 'attribute') {
            target.element.setAttribute(target.attribute, translated);
          }
        });
      }

      updateInProgressRef.current = false;
    };

    const scheduleTranslation = () => {
      if (disposed) return;
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        runTranslation();
      }, 120);
    };

    observer = new MutationObserver(() => {
      if (!updateInProgressRef.current) {
        scheduleTranslation();
      }
    });

    observer.observe(root, {
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: TRANSLATABLE_ATTRIBUTES,
    });

    scheduleTranslation();

    return () => {
      disposed = true;
      clearTimeout(timeoutId);
      observer?.disconnect();
      updateInProgressRef.current = false;
    };
  }, [language, rootRef]);
}
