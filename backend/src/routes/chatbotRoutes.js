const express = require('express');
const { authMiddleware } = require('../middleware/auth');
const { businessProfilesByEmail } = require('../data/store');
const { getSchemeById, getMissingDocGuidance, SCHEME_CATALOG, DOCUMENT_META } = require('../services/domainService');

const router = express.Router();

router.post('/scheme-assistant', authMiddleware, (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const profile = businessProfilesByEmail.get(normalizedEmail);
  if (!profile) return res.status(404).json({ message: 'Create business profile first.' });

  const schemeId = String(req.body?.schemeId || '');
  const missingDocument = req.body?.missingDocument ? String(req.body.missingDocument) : null;
  const userQuestion = String(req.body?.userQuestion || '').trim();
  const scheme = getSchemeById(schemeId) || SCHEME_CATALOG.find((s) => s.id === schemeId);
  if (!scheme) return res.status(404).json({ message: 'Scheme not found.' });

  const guideSteps = [
    `Check eligibility for ${scheme.schemeName} on the official portal.`,
    'Prepare mandatory documents and ensure profile details match uploaded proofs.',
    'Submit application online with verified contact details and business data.',
    'Track application reference number and respond to clarifications if requested.',
  ];
  const timeline = ['Document prep: 1-3 days', 'Application submission: 1 day', 'Review and approval: 2-8 weeks'];
  const submission = {
    mode: 'Online preferred',
    portalUrl: 'https://www.myscheme.gov.in/',
    offlineOption: 'District Industries Centre (if scheme permits physical submission)',
  };
  const documentRequirements = (scheme.documents || []).map((docType) => ({
    docType,
    ...(DOCUMENT_META[docType] || { label: docType, format: 'PDF/JPG/PNG', why: 'Scheme requirement' }),
    maxSizeMb: 5,
  }));

  const missingDocHelp = missingDocument ? { document: missingDocument, ...getMissingDocGuidance(missingDocument) } : null;
  const assistantReply = userQuestion
    ? `For "${scheme.schemeName}", focus on eligibility and document readiness. ${missingDocument ? `Missing ${missingDocument} can be resolved via the provided steps.` : 'If any document is missing, tell me which one and I will guide you.'}`
    : 'I can guide you step-by-step for this scheme and help with missing documents.';

  return res.status(200).json({
    scheme: { id: scheme.id, schemeName: scheme.schemeName, description: scheme.description },
    guideSteps,
    timeline,
    submission,
    documentRequirements,
    missingDocHelp,
    assistantReply,
  });
});

module.exports = router;
