const express = require('express');
const { authMiddleware } = require('../middleware/auth');
const {
  businessProfilesByEmail,
  uploadedDocsByEmail,
  notificationReadsByEmail,
  persistStore,
} = require('../data/store');
const { buildRecommendations } = require('../services/domainService');

const router = express.Router();

router.get('/', authMiddleware, (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const profile = businessProfilesByEmail.get(normalizedEmail);
  const docs = uploadedDocsByEmail.get(normalizedEmail) || [];
  const readSet = new Set(Array.isArray(notificationReadsByEmail.get(normalizedEmail)) ? notificationReadsByEmail.get(normalizedEmail) : []);
  const notifications = [];

  if (!profile) {
    notifications.push({
      id: 'profile_missing',
      severity: 'high',
      title: 'Business profile is incomplete',
      message: 'Complete your business profile to unlock scheme mapping and validation workflows.',
      action: { tab: 'profile', step: 0 },
    });
  } else {
    if (!profile.pan || !profile.mobile || !profile.sector) {
      notifications.push({
        id: 'profile_fields_missing',
        severity: 'medium',
        title: 'Some profile fields need attention',
        message: 'PAN, mobile, and sector details are required for accurate recommendations.',
        action: { tab: 'profile', step: 1 },
      });
    }
  }

  const reviewCount = docs.filter((doc) => doc.status === 'review').length;
  const rejectedCount = docs.filter((doc) => doc.status === 'rejected').length;
  const verifiedCount = docs.filter((doc) => doc.status === 'verified').length;

  if (reviewCount > 0) {
    notifications.push({
      id: 'docs_review',
      severity: 'medium',
      title: `${reviewCount} document(s) under review`,
      message: 'Review pending warnings and upload clearer/revised versions if needed.',
      action: { tab: 'documents' },
    });
  }

  if (rejectedCount > 0) {
    notifications.push({
      id: 'docs_rejected',
      severity: 'high',
      title: `${rejectedCount} document(s) rejected`,
      message: 'Resolve rejection reasons to proceed with scheme applications.',
      action: { tab: 'documents' },
    });
  }

  if (profile) {
    const matchedSchemes = buildRecommendations(profile).length;
    notifications.push({
      id: 'schemes_update',
      severity: 'low',
      title: `${matchedSchemes} scheme(s) matched`,
      message: 'Open the Schemes tab to review latest eligibility mapping.',
      action: { tab: 'schemes' },
    });
  }

  if (docs.length === 0) {
    notifications.push({
      id: 'docs_none',
      severity: 'medium',
      title: 'No documents uploaded yet',
      message: 'Upload required compliance documents to start verification.',
      action: { tab: 'documents' },
    });
  } else if (verifiedCount > 0) {
    notifications.push({
      id: 'docs_verified',
      severity: 'low',
      title: `${verifiedCount} document(s) verified`,
      message: 'Verified documents are ready for scheme submission workflows.',
      action: { tab: 'documents' },
    });
  }

  const withRead = notifications.map((notice) => ({
    ...notice,
    isRead: readSet.has(notice.id),
  }));
  const unreadCount = withRead.filter((item) => !item.isRead).length;

  return res.status(200).json({
    notifications: withRead,
    count: withRead.length,
    unreadCount,
  });
});

router.post('/read/:id', authMiddleware, (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const noticeId = String(req.params.id || '');
  if (!noticeId) return res.status(400).json({ message: 'Notification id is required.' });

  const readSet = new Set(Array.isArray(notificationReadsByEmail.get(normalizedEmail)) ? notificationReadsByEmail.get(normalizedEmail) : []);
  readSet.add(noticeId);
  notificationReadsByEmail.set(normalizedEmail, Array.from(readSet));
  if (!persistStore()) return res.status(500).json({ message: 'Could not save notification state.' });

  return res.status(200).json({ message: 'Notification marked as read.', id: noticeId });
});

router.post('/read-all', authMiddleware, (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const ids = Array.isArray(req.body?.ids) ? req.body.ids.map((id) => String(id)) : [];
  const readSet = new Set(Array.isArray(notificationReadsByEmail.get(normalizedEmail)) ? notificationReadsByEmail.get(normalizedEmail) : []);
  ids.forEach((id) => readSet.add(id));
  notificationReadsByEmail.set(normalizedEmail, Array.from(readSet));
  if (!persistStore()) return res.status(500).json({ message: 'Could not save notification state.' });

  return res.status(200).json({ message: 'Notifications marked as read.', count: ids.length });
});

module.exports = router;
