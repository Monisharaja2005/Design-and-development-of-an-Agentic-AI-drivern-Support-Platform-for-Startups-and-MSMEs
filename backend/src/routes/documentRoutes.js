const express = require('express');
const { authMiddleware } = require('../middleware/auth');
const { upload } = require('../middleware/upload');
const { businessProfilesByEmail, uploadedDocsByEmail, getNextDocId, persistStore } = require('../data/store');
const { validateDocumentForProfile } = require('../services/domainService');

const router = express.Router();

router.get('/', authMiddleware, (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const docs = uploadedDocsByEmail.get(normalizedEmail) || [];
  return res.status(200).json({ documents: docs });
});

router.post('/upload', authMiddleware, upload.single('file'), (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const profile = businessProfilesByEmail.get(normalizedEmail);
  if (!profile) return res.status(400).json({ message: 'Create business profile before uploading documents.' });

  const docType = String(req.body?.documentType || '').trim();
  if (!docType) return res.status(400).json({ message: 'documentType is required.' });
  if (!req.file) return res.status(400).json({ message: 'File is required.' });

  const validation = validateDocumentForProfile({ docType, profile, file: req.file });
  const docs = uploadedDocsByEmail.get(normalizedEmail) || [];

  const record = {
    id: getNextDocId(),
    docType,
    fileName: req.file.originalname,
    mimeType: req.file.mimetype,
    sizeBytes: req.file.size,
    status: validation.status,
    warnings: validation.warnings,
    errors: validation.errors,
    uploadedAt: new Date().toISOString(),
    verificationMethod: 'rule_based_stub',
  };

  docs.push(record);
  uploadedDocsByEmail.set(normalizedEmail, docs);
  if (!persistStore()) return res.status(500).json({ message: 'Document uploaded but could not persist to disk.' });
  return res.status(201).json({ message: 'Document uploaded and validated.', document: record });
});

router.post('/revalidate/:id', authMiddleware, (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const profile = businessProfilesByEmail.get(normalizedEmail);
  const docs = uploadedDocsByEmail.get(normalizedEmail) || [];
  const docId = String(req.params.id || '');
  const doc = docs.find((item) => item.id === docId);

  if (!doc) return res.status(404).json({ message: 'Document not found.' });
  if (!profile) return res.status(400).json({ message: 'Business profile missing.' });

  const validation = validateDocumentForProfile({
    docType: doc.docType,
    profile,
    file: { originalname: doc.fileName, size: doc.sizeBytes },
  });

  doc.status = validation.status;
  doc.warnings = validation.warnings;
  doc.errors = validation.errors;
  doc.revalidatedAt = new Date().toISOString();
  if (!persistStore()) return res.status(500).json({ message: 'Revalidation completed but could not persist to disk.' });

  return res.status(200).json({ message: 'Document revalidated.', document: doc });
});

module.exports = router;
