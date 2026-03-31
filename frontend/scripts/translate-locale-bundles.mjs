import fs from 'node:fs/promises';
import path from 'node:path';

const ROOT = process.cwd();
const LOCALES_DIR = path.join(ROOT, 'src', 'locales');
const SOURCE_FILE = path.join(LOCALES_DIR, 'en', 'translation.json');
const ENV_FILE = path.join(ROOT, '..', '.env');

const LANGUAGE_META = {
  hi: 'Hindi (हिन्दी)',
  bn: 'Bengali (বাংলা)',
  gu: 'Gujarati (ગુજરાતી)',
  kn: 'Kannada (ಕನ್ನಡ)',
  ks: 'Kashmiri (कॉशुर)',
  ml: 'Malayalam (മലയാളം)',
  mr: 'Marathi (मराठी)',
  ne: 'Nepali (नेपाली)',
  or: 'Odia (ଓଡ଼ିଆ)',
  pa: 'Punjabi (ਪੰਜਾਬੀ)',
  sat: 'Santali (ᱥᱟᱱᱛᱟᱲᱤ)',
  ta: 'Tamil (தமிழ்)',
  te: 'Telugu (తెలుగు)',
  ur: 'Urdu (اردو)',
  as: 'Assamese (অসমীয়া)',
};

function parseEnv(text) {
  const env = {};
  String(text || '')
    .split(/\r?\n/)
    .forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) return;
      const index = trimmed.indexOf('=');
      if (index === -1) return;
      const key = trimmed.slice(0, index).trim();
      const value = trimmed.slice(index + 1).trim();
      env[key] = value;
    });
  return env;
}

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

function setDeepValue(target, dotPath, value) {
  const segments = dotPath.split('.');
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

function extractJsonArray(raw) {
  const text = String(raw || '').trim();
  if (!text) return [];
  let cleaned = text;
  if (cleaned.startsWith('```json')) cleaned = cleaned.slice(7);
  if (cleaned.startsWith('```')) cleaned = cleaned.slice(3);
  if (cleaned.endsWith('```')) cleaned = cleaned.slice(0, -3);
  const start = cleaned.indexOf('[');
  if (start === -1) {
    throw new Error('No JSON array start found');
  }

  let inString = false;
  let escaped = false;
  let depth = 0;
  let end = -1;

  for (let index = start; index < cleaned.length; index += 1) {
    const char = cleaned[index];

    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === '\\') {
      escaped = true;
      continue;
    }
    if (char === '"') {
      inString = !inString;
      continue;
    }
    if (inString) continue;
    if (char === '[') depth += 1;
    if (char === ']') {
      depth -= 1;
      if (depth === 0) {
        end = index;
        break;
      }
    }
  }

  if (end === -1) {
    throw new Error('No JSON array end found');
  }

  const candidate = cleaned.slice(start, end + 1);
  return JSON.parse(candidate);
}

async function callLmStudio({ baseUrl, model, prompt, system, temperature = 0.2, maxTokens = 3000 }) {
  const response = await fetch(`${baseUrl.replace(/\/$/, '')}/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      messages: [
        { role: 'system', content: system },
        { role: 'user', content: prompt },
      ],
      temperature,
      max_tokens: maxTokens,
    }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`LM Studio request failed: ${response.status} ${errorBody}`);
  }

  const data = await response.json();
  return data?.choices?.[0]?.message?.content || '';
}

function extractPlainText(raw) {
  let text = String(raw || '').trim();
  if (text.startsWith('```')) {
    text = text.replace(/^```[a-zA-Z]*\n?/, '');
    text = text.replace(/```$/, '').trim();
  }
  if ((text.startsWith('"') && text.endsWith('"')) || (text.startsWith("'") && text.endsWith("'"))) {
    text = text.slice(1, -1).trim();
  }
  return text;
}

async function translateBatch(items, languageCode, languageName, config) {
  const prompt = `
TASK: Translate the following JSON array of UI strings into ${languageName}.

JSON INPUT:
${JSON.stringify(items)}

RULES:
1. Return ONLY a raw JSON array of strings.
2. Preserve the array length and original ordering.
3. Preserve placeholders like {{count}}, {{total}}, {{current}}, {{title}} exactly.
4. Preserve URLs, emails, product names like KARIOS, and official acronyms unless a natural local rendering is standard.
5. Do NOT output bilingual text.
6. Use only ${languageName} for explanatory UI text.
`.trim();

  const system = `You are a UI localization engine for an Indian government schemes web application. Translate only into ${languageName}. Return raw JSON only.`;
  const attempts = [
    {
      prompt,
      system,
      temperature: 0.15,
    },
    {
      prompt: `${prompt}\n\nCRITICAL: Return exactly one valid JSON array and nothing else.`,
      system: `${system} Do not add explanations, markdown fences, labels, or notes.`,
      temperature: 0,
    },
  ];

  let lastError = null;
  for (const attempt of attempts) {
    try {
      const raw = await callLmStudio({
        baseUrl: config.baseUrl,
        model: config.model,
        prompt: attempt.prompt,
        system: attempt.system,
        temperature: attempt.temperature,
        maxTokens: 3200,
      });
      const parsed = extractJsonArray(raw);
      if (!Array.isArray(parsed) || parsed.length !== items.length) {
        throw new Error(`Unexpected translation array for ${languageCode}`);
      }
      return parsed.map((value) => String(value ?? '').trim());
    } catch (error) {
      lastError = error;
    }
  }

  if (items.length > 1) {
    const middle = Math.ceil(items.length / 2);
    const left = await translateBatch(items.slice(0, middle), languageCode, languageName, config);
    const right = await translateBatch(items.slice(middle), languageCode, languageName, config);
    return [...left, ...right];
  }

  const singlePrompt = `
Translate this UI string into ${languageName}.

RULES:
1. Return only the translated string.
2. Preserve placeholders like {{count}} exactly.
3. Preserve KARIOS, URLs, emails, and official acronyms when needed.
4. Do not make it bilingual.

TEXT:
${items[0]}
`.trim();

  try {
    const raw = await callLmStudio({
      baseUrl: config.baseUrl,
      model: config.model,
      prompt: singlePrompt,
      system: `You are a UI localization engine. Translate only into ${languageName}.`,
      temperature: 0,
      maxTokens: 400,
    });
    const translated = extractPlainText(raw);
    return [translated || items[0]];
  } catch {
    return [items[0]];
  }
}

async function loadJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function writeJson(filePath, value) {
  await fs.writeFile(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function buildMissingEntries(sourceFlat, targetFlat) {
  return Object.entries(sourceFlat)
    .filter(([dotPath, englishValue]) => {
      if (!englishValue) return false;
      if (dotPath.startsWith('schemes.')) return false;
      const currentValue = targetFlat[dotPath];
      return !currentValue || currentValue === englishValue;
    })
    .map(([dotPath, englishValue]) => ({ dotPath, englishValue }));
}

async function main() {
  const envText = await fs.readFile(ENV_FILE, 'utf8');
  const env = parseEnv(envText);
  const config = {
    baseUrl: env.DOC_VERIFY_LMSTUDIO_BASE_URL || 'http://127.0.0.1:1234/v1',
    model: env.DOC_VERIFY_LLM_MODEL || 'google/gemma-3-4b',
  };

  const sourceBundle = await loadJson(SOURCE_FILE);
  const sourceFlat = flattenStrings(sourceBundle);
  const localeDirs = await fs.readdir(LOCALES_DIR, { withFileTypes: true });

  for (const dirent of localeDirs) {
    if (!dirent.isDirectory()) continue;
    const languageCode = dirent.name;
    if (languageCode === 'en') continue;

    const languageName = LANGUAGE_META[languageCode];
    if (!languageName) continue;

    const targetFile = path.join(LOCALES_DIR, languageCode, 'translation.json');
    const targetBundle = await loadJson(targetFile);
    const targetFlat = flattenStrings(targetBundle);
    const missingEntries = buildMissingEntries(sourceFlat, targetFlat);

    if (!missingEntries.length) {
      console.log(`[skip] ${languageCode}: no missing UI strings`);
      continue;
    }

    const uniqueSourceStrings = [...new Set(missingEntries.map((entry) => entry.englishValue))];
    const translations = new Map();
    const batchSize = 10;

    console.log(`[start] ${languageCode}: translating ${uniqueSourceStrings.length} UI strings`);

    for (let index = 0; index < uniqueSourceStrings.length; index += batchSize) {
      const batch = uniqueSourceStrings.slice(index, index + batchSize);
      const translatedBatch = await translateBatch(batch, languageCode, languageName, config);
      batch.forEach((sourceText, batchIndex) => {
        const translatedText = translatedBatch[batchIndex];
        if (translatedText && translatedText !== sourceText) {
          translations.set(sourceText, translatedText);
        }
      });
      console.log(`[batch] ${languageCode}: ${Math.min(index + batchSize, uniqueSourceStrings.length)}/${uniqueSourceStrings.length}`);
    }

    const nextBundle = structuredClone(targetBundle);
    let updates = 0;
    missingEntries.forEach(({ dotPath, englishValue }) => {
      const translated = translations.get(englishValue);
      if (!translated) return;
      setDeepValue(nextBundle, dotPath, translated);
      updates += 1;
    });

    await writeJson(targetFile, nextBundle);
    console.log(`[done] ${languageCode}: updated ${updates} keys`);
  }

  console.log('Locale translation generation completed.');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
