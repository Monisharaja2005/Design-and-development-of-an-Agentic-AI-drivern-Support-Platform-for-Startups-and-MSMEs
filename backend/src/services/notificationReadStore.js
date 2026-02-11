const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');
const FILE_PATH = path.join(DATA_DIR, 'notification-reads.json');

function ensureFile() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
  if (!fs.existsSync(FILE_PATH)) fs.writeFileSync(FILE_PATH, JSON.stringify({}, null, 2), 'utf8');
}

function loadNotificationReads() {
  try {
    ensureFile();
    const raw = fs.readFileSync(FILE_PATH, 'utf8');
    const parsed = JSON.parse(raw || '{}');
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch (_error) {
    return {};
  }
}

function saveNotificationReads(notificationReadsByEmail) {
  try {
    ensureFile();
    fs.writeFileSync(FILE_PATH, JSON.stringify(notificationReadsByEmail, null, 2), 'utf8');
    return true;
  } catch (_error) {
    return false;
  }
}

module.exports = {
  loadNotificationReads,
  saveNotificationReads,
};
