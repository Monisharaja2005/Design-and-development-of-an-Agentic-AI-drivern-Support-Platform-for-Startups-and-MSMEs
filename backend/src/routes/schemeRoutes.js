const express = require('express');
const { authMiddleware } = require('../middleware/auth');
const { businessProfilesByEmail } = require('../data/store');
const { buildRecommendations, getSchemeById } = require('../services/domainService');

const router = express.Router();

router.get('/', authMiddleware, (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const profile = businessProfilesByEmail.get(normalizedEmail);
  if (!profile) {
    return res.status(404).json({
      message: 'Business profile not found. Complete profile to view mapped schemes.',
      schemes: [],
    });
  }

  const mapped = buildRecommendations(profile).map((item) => {
    const base = getSchemeById(item.id);
    return {
      id: item.id,
      schemeName: item.schemeName,
      description: base?.description || 'Scheme guidance available.',
      eligibility: base?.eligibility || [],
      benefits: base?.benefits || [],
      priority: item.priority,
    };
  });

  return res.status(200).json({ schemes: mapped });
});

module.exports = router;
