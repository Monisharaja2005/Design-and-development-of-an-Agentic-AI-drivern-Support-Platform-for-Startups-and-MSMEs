const jwt = require('jsonwebtoken');
const {
  JWT_SECRET,
  TOKEN_EXPIRES_IN,
  ALLOWED_BUSINESS_TYPES,
  ALLOWED_GENDERS,
  ALLOWED_ENTITY_TYPES,
  ALLOWED_SECTORS,
  ALLOWED_PRIMARY_NEEDS,
  SCHEME_CATALOG,
  DOCUMENT_META,
} = require('../config/constants');

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function getPasswordErrors(password) {
  const errors = [];
  if (password.length < 8) errors.push('Password must be at least 8 characters.');
  if (!/[A-Z]/.test(password)) errors.push('Password needs one uppercase letter.');
  if (!/[a-z]/.test(password)) errors.push('Password needs one lowercase letter.');
  if (!/\d/.test(password)) errors.push('Password needs one number.');
  if (!/[^A-Za-z0-9]/.test(password)) errors.push('Password needs one special character.');
  return errors;
}

function signToken(email) {
  return jwt.sign({ email }, JWT_SECRET, { expiresIn: TOKEN_EXPIRES_IN });
}

function normalizeUpper(value) {
  return String(value || '').trim().toUpperCase();
}

function normalizeLower(value) {
  return String(value || '').trim().toLowerCase();
}

function isValidPan(pan) {
  return /^[A-Z]{5}[0-9]{4}[A-Z]$/.test(pan);
}

function isValidGstin(gstin) {
  return /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$/.test(gstin);
}

function isValidUdyam(udyamNumber) {
  return /^UDYAM-[A-Z]{2}-\d{2}-\d{7}$/.test(udyamNumber);
}

function isValidDpiit(dpiitNumber) {
  return /^DPIIT\d{6,}$/.test(dpiitNumber);
}

function isValidPincode(pincode) {
  return /^\d{6}$/.test(pincode);
}

function isValidWebsite(website) {
  if (!website) return true;
  try {
    const url = new URL(website);
    return ['http:', 'https:'].includes(url.protocol);
  } catch (_error) {
    return false;
  }
}

function parseBoolean(value) {
  return value === true || value === 'true' || value === 1 || value === '1';
}

function getBusinessProfileRequirements() {
  return {
    businessTypes: ALLOWED_BUSINESS_TYPES,
    genders: ALLOWED_GENDERS,
    entityTypes: ALLOWED_ENTITY_TYPES,
    sectors: ALLOWED_SECTORS,
    primaryNeeds: ALLOWED_PRIMARY_NEEDS,
    rules: {
      pan: 'Format: ABCDE1234F',
      gstin: 'Required only if GST registered. Format: 22AAAAA0000A1Z5',
      udyamNumber: 'Required for MSME. Format: UDYAM-XX-00-0000000',
      dpiitNumber: 'Required for Startup. Format: DPIIT123456',
      mobile: '10 digits',
      pincode: '6 digits',
      updateAnytime: true,
      uniqueKeys: ['pan', 'gstin', 'udyamNumber', 'dpiitNumber'],
    },
  };
}

function getBusinessProfileErrors(body) {
  const errors = [];
  const currentYear = new Date().getFullYear();

  const businessType = normalizeLower(body.businessType);
  const legalEntityType = normalizeLower(body.legalEntityType);
  const businessName = String(body.businessName || '').trim();
  const ownerName = String(body.ownerName || '').trim();
  const gender = normalizeLower(body.gender);
  const pan = normalizeUpper(body.pan);
  const mobile = String(body.mobile || '').trim();
  const state = String(body.state || '').trim();
  const city = String(body.city || '').trim();
  const pincode = String(body.pincode || '').trim();
  const sector = normalizeLower(body.sector);
  const primaryNeed = normalizeLower(body.primaryNeed);
  const website = String(body.website || '').trim();
  const gstin = normalizeUpper(body.gstin);
  const udyamNumber = normalizeUpper(body.udyamNumber);
  const dpiitNumber = normalizeUpper(body.dpiitNumber);

  const yearOfIncorporation = Number(body.yearOfIncorporation);
  const employeeCount = Number(body.employeeCount);
  const annualTurnoverLakhs = Number(body.annualTurnoverLakhs);
  const fundingNeedLakhs = Number(body.fundingNeedLakhs);
  const founderShareholding = Number(body.founderShareholding);

  const hasGst = parseBoolean(body.hasGst);
  const womenLed = parseBoolean(body.womenLed);
  const scstLed = parseBoolean(body.scstLed);
  const differentlyAbledLed = parseBoolean(body.differentlyAbledLed);
  const exportFocus = parseBoolean(body.exportFocus);
  const hasIp = parseBoolean(body.hasIp);

  if (!ALLOWED_BUSINESS_TYPES.includes(businessType)) errors.push('Business type must be Startup or MSME.');
  if (!ALLOWED_ENTITY_TYPES.includes(legalEntityType)) errors.push('Legal entity type is required.');
  if (!businessName || businessName.length < 3) errors.push('Business name is required (minimum 3 characters).');
  if (!ownerName || ownerName.length < 3) errors.push('Founder/Owner name is required (minimum 3 characters).');
  if (!ALLOWED_GENDERS.includes(gender)) errors.push('Gender is required.');
  if (!isValidPan(pan)) errors.push('PAN format is invalid. Use ABCDE1234F.');
  if (!/^\d{10}$/.test(mobile)) errors.push('Mobile must be a 10-digit number.');
  if (!state) errors.push('State is required.');
  if (!city) errors.push('City is required.');
  if (!isValidPincode(pincode)) errors.push('Pincode must be 6 digits.');
  if (!ALLOWED_SECTORS.includes(sector)) errors.push('Sector selection is required.');
  if (!ALLOWED_PRIMARY_NEEDS.includes(primaryNeed)) errors.push('Primary need selection is required.');
  if (!Number.isInteger(yearOfIncorporation) || yearOfIncorporation < 1900 || yearOfIncorporation > currentYear) {
    errors.push('Year of incorporation is invalid.');
  }
  if (!Number.isInteger(employeeCount) || employeeCount < 1 || employeeCount > 100000) {
    errors.push('Employee count must be between 1 and 100000.');
  }
  if (Number.isNaN(annualTurnoverLakhs) || annualTurnoverLakhs < 0) errors.push('Annual turnover (in lakhs) must be 0 or more.');
  if (Number.isNaN(fundingNeedLakhs) || fundingNeedLakhs < 0) errors.push('Funding requirement (in lakhs) must be 0 or more.');
  if (Number.isNaN(founderShareholding) || founderShareholding < 0 || founderShareholding > 100) {
    errors.push('Founder shareholding must be between 0 and 100.');
  }
  if (!isValidWebsite(website)) errors.push('Website URL is invalid. Use http:// or https://');
  if (hasGst && !isValidGstin(gstin)) errors.push('GSTIN is required and must be valid when GST is applicable.');
  if (businessType === 'msme' && !isValidUdyam(udyamNumber)) {
    errors.push('Udyam number is required for MSME and must match UDYAM-XX-00-0000000.');
  }
  if (businessType === 'startup' && !isValidDpiit(dpiitNumber)) {
    errors.push('DPIIT number is required for Startup and must match DPIIT123456.');
  }

  return {
    errors,
    normalized: {
      businessType,
      legalEntityType,
      businessName,
      ownerName,
      gender,
      pan,
      mobile,
      state,
      city,
      pincode,
      sector,
      primaryNeed,
      website,
      yearOfIncorporation,
      employeeCount,
      annualTurnoverLakhs,
      fundingNeedLakhs,
      founderShareholding,
      hasGst,
      gstin: hasGst ? gstin : '',
      udyamNumber: businessType === 'msme' ? udyamNumber : '',
      dpiitNumber: businessType === 'startup' ? dpiitNumber : '',
      womenLed,
      scstLed,
      differentlyAbledLed,
      exportFocus,
      hasIp,
    },
  };
}

function updateUniqueMap(map, oldValue, newValue, email) {
  if (oldValue && oldValue !== newValue) map.delete(oldValue);
  if (newValue) map.set(newValue, email);
}

function ensureUnique(map, value, email, label) {
  if (!value) return null;
  const existing = map.get(value);
  if (existing && existing !== email) return `${label} already exists for another account.`;
  return null;
}

function classifyMsmeCategory(profile) {
  if (profile.businessType !== 'msme') return null;
  if (profile.employeeCount <= 10 && profile.annualTurnoverLakhs <= 500) return 'micro';
  if (profile.employeeCount <= 50 && profile.annualTurnoverLakhs <= 5000) return 'small';
  return 'medium';
}

function buildRecommendations(profile) {
  const recommendations = [];
  const currentYear = new Date().getFullYear();
  const businessAge = currentYear - profile.yearOfIncorporation;
  const msmeCategory = classifyMsmeCategory(profile);

  if (profile.businessType === 'startup') {
    recommendations.push({
      id: 'startup_india_seed_fund',
      schemeName: 'Startup India Seed Fund Scheme (SISFS)',
      priority: 'high',
      whyMatched: [
        'Profile marked as Startup',
        `Business age appears to be ${businessAge} years`,
        `Funding requirement entered: INR ${profile.fundingNeedLakhs} lakhs`,
      ],
      keyEligibilitySignals: ['DPIIT number provided', 'Innovation-led startup recommended'],
    });
    recommendations.push({
      id: 'startup_india_benefits',
      schemeName: 'Startup India Recognition Benefits',
      priority: 'high',
      whyMatched: ['DPIIT-recognized startup profile', 'Entity has structured compliance details'],
      keyEligibilitySignals: ['DPIIT registration', 'Incorporation details available'],
    });
  }

  if (profile.businessType === 'msme') {
    recommendations.push({
      id: 'cgtmse_credit_guarantee',
      schemeName: 'CGTMSE Credit Guarantee Support',
      priority: profile.fundingNeedLakhs > 0 ? 'high' : 'medium',
      whyMatched: [
        `Funding need provided: INR ${profile.fundingNeedLakhs} lakhs`,
        `MSME size inferred as ${msmeCategory}`,
      ],
      keyEligibilitySignals: ['Valid Udyam number available', 'PAN and business compliance completed'],
    });
  }

  if (profile.womenLed) {
    recommendations.push({
      id: 'stand_up_india',
      schemeName: 'Stand-Up India (Women-led enterprises)',
      priority: 'high',
      whyMatched: ['Women-led ownership indicated in profile'],
      keyEligibilitySignals: ['Founder demographic criteria captured'],
    });
  }

  if (profile.scstLed) {
    recommendations.push({
      id: 'stand_up_india',
      schemeName: 'Stand-Up India (SC/ST entrepreneurs)',
      priority: 'high',
      whyMatched: ['SC/ST founder flag enabled in profile'],
      keyEligibilitySignals: ['Founder demographic criteria captured'],
    });
  }

  if (profile.exportFocus) {
    recommendations.push({
      id: 'export_promotion_support',
      schemeName: 'Export Promotion and Market Access Support',
      priority: 'medium',
      whyMatched: ['Export focus enabled in profile'],
      keyEligibilitySignals: ['Market access selected as business objective'],
    });
  }

  return recommendations;
}

function getSchemeById(id) {
  return SCHEME_CATALOG.find((scheme) => scheme.id === id) || null;
}

function getMissingDocGuidance(docType) {
  const guidance = {
    aadhar_card: {
      portal: 'https://uidai.gov.in/',
      fees: 'Usually free for standard update/enrolment requests',
      eta: '7 to 30 days',
      steps: ['Visit UIDAI portal', 'Book/update request', 'Track status and download e-Aadhar'],
    },
    pan_card: {
      portal: 'https://www.onlineservices.nsdl.com/paam/endUserRegisterContact.html',
      fees: 'Approx INR 107 (can vary)',
      eta: '7 to 15 days',
      steps: ['Apply through NSDL/UTI portal', 'Upload KYC details', 'Track acknowledgement'],
    },
  };
  return guidance[docType] || {
    portal: 'Relevant department portal',
    fees: 'Depends on issuing authority',
    eta: 'Varies',
    steps: ['Identify issuing authority', 'Submit request with required details', 'Track and download/collect'],
  };
}

function validateDocumentForProfile({ docType, profile, file }) {
  const errors = [];
  const warnings = [];
  const originalName = String(file.originalname || '').toLowerCase();
  const fileSizeKb = Math.round(file.size / 1024);

  if (fileSizeKb < 20) warnings.push('Document quality may be low. Upload a clearer scan if possible.');
  if (docType === 'pan_card') {
    const pan = String(profile?.pan || '').toLowerCase();
    if (pan && !originalName.includes(pan.slice(0, 5).toLowerCase())) {
      warnings.push('PAN not clearly identifiable from filename. Manual review may be needed.');
    }
  }
  if (docType === 'dpiit_certificate' && profile?.businessType !== 'startup') {
    warnings.push('DPIIT certificate is usually for Startup classification.');
  }
  if (docType === 'udyam_certificate' && profile?.businessType !== 'msme') {
    warnings.push('Udyam certificate is usually for MSME classification.');
  }

  const status = errors.length ? 'rejected' : warnings.length ? 'review' : 'verified';
  return { status, errors, warnings };
}

module.exports = {
  validateEmail,
  getPasswordErrors,
  signToken,
  getBusinessProfileRequirements,
  getBusinessProfileErrors,
  updateUniqueMap,
  ensureUnique,
  buildRecommendations,
  getSchemeById,
  getMissingDocGuidance,
  validateDocumentForProfile,
  SCHEME_CATALOG,
  DOCUMENT_META,
};
