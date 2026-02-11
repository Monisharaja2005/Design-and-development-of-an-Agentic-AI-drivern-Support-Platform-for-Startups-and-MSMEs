const PORT = process.env.PORT || 5000;
const JWT_SECRET = process.env.JWT_SECRET || 'dev_secret_change_this';
const TOKEN_EXPIRES_IN = '2h';

const ALLOWED_BUSINESS_TYPES = ['startup', 'msme'];
const ALLOWED_GENDERS = ['male', 'female', 'other', 'prefer_not_to_say'];
const ALLOWED_ENTITY_TYPES = ['proprietorship', 'partnership', 'llp', 'private_limited', 'public_limited'];
const ALLOWED_SECTORS = [
  'it_software',
  'manufacturing',
  'agri_food',
  'healthcare',
  'education',
  'fintech',
  'clean_energy',
  'textiles',
  'logistics',
  'other',
];
const ALLOWED_PRIMARY_NEEDS = ['grant', 'loan', 'subsidy', 'mentorship', 'market_access'];
const ALLOWED_USER_TYPES = ['individual', 'business'];

const SCHEME_CATALOG = [
  {
    id: 'startup_india_seed_fund',
    schemeName: 'Startup India Seed Fund Scheme (SISFS)',
    description: 'Early-stage funding support for eligible startups.',
    eligibility: ['DPIIT recognized startup', 'Early-stage innovation focus'],
    benefits: ['Seed grant support', 'Prototype and market entry support'],
    documents: ['aadhar_card', 'pan_card', 'dpiit_certificate', 'bank_statement', 'itr_2_years'],
  },
  {
    id: 'cgtmse_credit_guarantee',
    schemeName: 'CGTMSE Credit Guarantee',
    description: 'Collateral-free credit support for MSME units.',
    eligibility: ['MSME profile', 'Valid Udyam details'],
    benefits: ['Credit guarantee', 'Improved loan accessibility'],
    documents: ['aadhar_card', 'pan_card', 'udyam_certificate', 'bank_statement', 'gst_certificate'],
  },
  {
    id: 'stand_up_india',
    schemeName: 'Stand-Up India',
    description: 'Support for SC/ST and women-led enterprises.',
    eligibility: ['Women-led or SC/ST-led enterprise'],
    benefits: ['Bank-linked loan support', 'Enterprise support'],
    documents: ['aadhar_card', 'pan_card', 'business_registration', 'bank_statement'],
  },
];

const DOCUMENT_META = {
  aadhar_card: { label: 'Aadhar Card', format: 'PDF/JPG/PNG', why: 'Identity proof of applicant' },
  pan_card: { label: 'PAN Card', format: 'PDF/JPG/PNG', why: 'Tax identity and compliance validation' },
  dpiit_certificate: {
    label: 'DPIIT Certificate',
    format: 'PDF/JPG/PNG',
    why: 'Startup recognition verification',
  },
  udyam_certificate: {
    label: 'Udyam Registration Certificate',
    format: 'PDF/JPG/PNG',
    why: 'MSME status verification',
  },
  gst_certificate: { label: 'GST Certificate', format: 'PDF/JPG/PNG', why: 'GST compliance check' },
  business_registration: {
    label: 'Business Registration Certificate',
    format: 'PDF/JPG/PNG',
    why: 'Legal entity validation',
  },
  bank_statement: { label: 'Bank Statement', format: 'PDF/JPG/PNG', why: 'Financial credibility check' },
  itr_2_years: {
    label: 'ITR for Last 2 Years',
    format: 'PDF/JPG/PNG',
    why: 'Income and tax filing history verification',
  },
};

module.exports = {
  PORT,
  JWT_SECRET,
  TOKEN_EXPIRES_IN,
  ALLOWED_BUSINESS_TYPES,
  ALLOWED_GENDERS,
  ALLOWED_ENTITY_TYPES,
  ALLOWED_SECTORS,
  ALLOWED_PRIMARY_NEEDS,
  ALLOWED_USER_TYPES,
  SCHEME_CATALOG,
  DOCUMENT_META,
};
