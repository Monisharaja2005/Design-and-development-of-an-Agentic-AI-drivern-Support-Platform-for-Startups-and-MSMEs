export const API_BASE_URL = 'http://localhost:5000';
export const TOKEN_KEY = 'auth_token';

export const passwordChecks = [
  { key: 'length', label: 'At least 8 characters', test: (v) => v.length >= 8 },
  { key: 'upper', label: 'One uppercase letter', test: (v) => /[A-Z]/.test(v) },
  { key: 'lower', label: 'One lowercase letter', test: (v) => /[a-z]/.test(v) },
  { key: 'number', label: 'One number', test: (v) => /[0-9]/.test(v) },
  { key: 'special', label: 'One special character', test: (v) => /[^A-Za-z0-9]/.test(v) },
];

export const initialProfileForm = {
  businessType: 'startup',
  legalEntityType: 'private_limited',
  businessName: '',
  ownerName: '',
  gender: '',
  pan: '',
  mobile: '',
  state: '',
  city: '',
  pincode: '',
  sector: 'it_software',
  primaryNeed: 'grant',
  website: '',
  yearOfIncorporation: '',
  employeeCount: '',
  annualTurnoverLakhs: '',
  fundingNeedLakhs: '',
  founderShareholding: '',
  hasGst: false,
  gstin: '',
  udyamNumber: '',
  dpiitNumber: '',
  womenLed: false,
  scstLed: false,
  differentlyAbledLed: false,
  exportFocus: false,
  hasIp: false,
};

export const profileSteps = [
  { id: 'identity', title: 'Business Identity', detail: 'Classify Startup/MSME and registration details.' },
  { id: 'compliance', title: 'Founder & Compliance', detail: 'Enter PAN/GST and demographic details.' },
  { id: 'finance', title: 'Finance & Scheme Signals', detail: 'Turnover, funding needs and eligibility signals.' },
];
