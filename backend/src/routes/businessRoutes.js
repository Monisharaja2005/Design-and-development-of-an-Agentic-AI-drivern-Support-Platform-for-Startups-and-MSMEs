const express = require('express');
const { authMiddleware } = require('../middleware/auth');
const {
  usersByEmail,
  businessProfilesByEmail,
  panToEmail,
  gstinToEmail,
  udyamToEmail,
  dpiitToEmail,
  persistStore,
} = require('../data/store');
const {
  getBusinessProfileRequirements,
  getBusinessProfileErrors,
  ensureUnique,
  updateUniqueMap,
  buildRecommendations,
} = require('../services/domainService');

const router = express.Router();

router.get('/requirements', (_req, res) => res.status(200).json(getBusinessProfileRequirements()));

router.get('/', authMiddleware, (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const profile = businessProfilesByEmail.get(normalizedEmail);
  if (!profile) return res.status(200).json({ exists: false, profile: null });
  return res.status(200).json({ exists: true, profile });
});

router.get('/recommendations', authMiddleware, (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const profile = businessProfilesByEmail.get(normalizedEmail);
  if (!profile) {
    return res.status(404).json({ message: 'Business profile not found. Complete profile to get recommendations.' });
  }

  return res.status(200).json({
    profileSummary: {
      businessType: profile.businessType,
      sector: profile.sector,
      primaryNeed: profile.primaryNeed,
      annualTurnoverLakhs: profile.annualTurnoverLakhs,
      fundingNeedLakhs: profile.fundingNeedLakhs,
    },
    recommendations: buildRecommendations(profile),
  });
});

router.post('/', authMiddleware, (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const user = usersByEmail.get(normalizedEmail);
  if (!user) return res.status(404).json({ message: 'User not found.' });

  const { errors, normalized } = getBusinessProfileErrors(req.body);
  if (errors.length > 0) return res.status(400).json({ message: 'Business profile validation failed.', errors });

  const panError = ensureUnique(panToEmail, normalized.pan, normalizedEmail, 'PAN');
  if (panError) return res.status(409).json({ message: panError });
  const gstinError = ensureUnique(gstinToEmail, normalized.gstin, normalizedEmail, 'GSTIN');
  if (gstinError) return res.status(409).json({ message: gstinError });
  const udyamError = ensureUnique(udyamToEmail, normalized.udyamNumber, normalizedEmail, 'Udyam number');
  if (udyamError) return res.status(409).json({ message: udyamError });
  const dpiitError = ensureUnique(dpiitToEmail, normalized.dpiitNumber, normalizedEmail, 'DPIIT number');
  if (dpiitError) return res.status(409).json({ message: dpiitError });

  const existingProfile = businessProfilesByEmail.get(normalizedEmail);
  const profile = {
    ...normalized,
    email: normalizedEmail,
    updatedAt: new Date().toISOString(),
    createdAt: existingProfile ? existingProfile.createdAt : new Date().toISOString(),
  };

  businessProfilesByEmail.set(normalizedEmail, profile);
  updateUniqueMap(panToEmail, existingProfile?.pan, profile.pan, normalizedEmail);
  updateUniqueMap(gstinToEmail, existingProfile?.gstin, profile.gstin, normalizedEmail);
  updateUniqueMap(udyamToEmail, existingProfile?.udyamNumber, profile.udyamNumber, normalizedEmail);
  updateUniqueMap(dpiitToEmail, existingProfile?.dpiitNumber, profile.dpiitNumber, normalizedEmail);
  if (!persistStore()) return res.status(500).json({ message: 'Business profile saved in memory but could not persist to disk.' });

  return res.status(200).json({
    message: existingProfile ? 'Business profile updated. Recommendations refreshed.' : 'Business profile created. Recommendations ready.',
    profile,
    recommendations: buildRecommendations(profile),
  });
});

module.exports = router;
