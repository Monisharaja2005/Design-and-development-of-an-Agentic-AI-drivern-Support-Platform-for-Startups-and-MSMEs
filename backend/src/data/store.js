const fs = require('fs');
const path = require('path');

const DATA_DIR = __dirname;
const STORE_FILE_PATH = path.join(DATA_DIR, 'app-store.json');

const usersByEmail = new Map();
const businessProfilesByEmail = new Map();
const panToEmail = new Map();
const gstinToEmail = new Map();
const udyamToEmail = new Map();
const dpiitToEmail = new Map();
const resetTokensByEmail = new Map();
const uploadedDocsByEmail = new Map();
const notificationReadsByEmail = new Map();
let docCounter = 1;

function ensureStoreFile() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
  if (!fs.existsSync(STORE_FILE_PATH)) {
    fs.writeFileSync(
      STORE_FILE_PATH,
      JSON.stringify(
        {
          usersByEmail: [],
          businessProfilesByEmail: [],
          panToEmail: [],
          gstinToEmail: [],
          udyamToEmail: [],
          dpiitToEmail: [],
          resetTokensByEmail: [],
          uploadedDocsByEmail: [],
          notificationReadsByEmail: [],
          docCounter: 1,
        },
        null,
        2
      ),
      'utf8'
    );
  }
}

function loadMap(mapRef, entries) {
  mapRef.clear();
  if (!Array.isArray(entries)) return;
  entries.forEach((entry) => {
    if (Array.isArray(entry) && entry.length === 2) mapRef.set(entry[0], entry[1]);
  });
}

function persistStore() {
  try {
    ensureStoreFile();
    const snapshot = {
      usersByEmail: Array.from(usersByEmail.entries()),
      businessProfilesByEmail: Array.from(businessProfilesByEmail.entries()),
      panToEmail: Array.from(panToEmail.entries()),
      gstinToEmail: Array.from(gstinToEmail.entries()),
      udyamToEmail: Array.from(udyamToEmail.entries()),
      dpiitToEmail: Array.from(dpiitToEmail.entries()),
      resetTokensByEmail: Array.from(resetTokensByEmail.entries()),
      uploadedDocsByEmail: Array.from(uploadedDocsByEmail.entries()),
      notificationReadsByEmail: Array.from(notificationReadsByEmail.entries()),
      docCounter,
    };
    fs.writeFileSync(STORE_FILE_PATH, JSON.stringify(snapshot, null, 2), 'utf8');
    return true;
  } catch (_error) {
    return false;
  }
}

function loadStore() {
  try {
    ensureStoreFile();
    const raw = fs.readFileSync(STORE_FILE_PATH, 'utf8');
    const parsed = JSON.parse(raw || '{}');
    loadMap(usersByEmail, parsed.usersByEmail);
    loadMap(businessProfilesByEmail, parsed.businessProfilesByEmail);
    loadMap(panToEmail, parsed.panToEmail);
    loadMap(gstinToEmail, parsed.gstinToEmail);
    loadMap(udyamToEmail, parsed.udyamToEmail);
    loadMap(dpiitToEmail, parsed.dpiitToEmail);
    loadMap(resetTokensByEmail, parsed.resetTokensByEmail);
    loadMap(uploadedDocsByEmail, parsed.uploadedDocsByEmail);
    loadMap(notificationReadsByEmail, parsed.notificationReadsByEmail);
    const counter = Number(parsed.docCounter);
    docCounter = Number.isInteger(counter) && counter > 0 ? counter : 1;
  } catch (_error) {
    docCounter = 1;
  }
}

function getNextDocId() {
  return `DOC-${docCounter++}`;
}

loadStore();

module.exports = {
  usersByEmail,
  businessProfilesByEmail,
  panToEmail,
  gstinToEmail,
  udyamToEmail,
  dpiitToEmail,
  resetTokensByEmail,
  uploadedDocsByEmail,
  notificationReadsByEmail,
  getNextDocId,
  persistStore,
};
