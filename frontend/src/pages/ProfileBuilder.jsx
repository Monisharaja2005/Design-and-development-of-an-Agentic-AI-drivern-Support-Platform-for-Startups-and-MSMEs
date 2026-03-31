import React, { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowRightIcon,
  ArrowLeftIcon,
  CheckCircleIcon,
  BuildingOfficeIcon,
  UserIcon,
  CurrencyRupeeIcon,
  MapPinIcon,
  ChartBarIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';

const API_BASE = '';

const STEP_CONFIG = [
  { id: 'promoter', titleKey: 'profile.steps.promoter', titleDefault: 'Promoter Info', icon: UserIcon, color: 'text-blue-600', bg: 'bg-blue-50' },
  { id: 'business', titleKey: 'profile.steps.business', titleDefault: 'Business Details', icon: BuildingOfficeIcon, color: 'text-purple-600', bg: 'bg-purple-50' },
  { id: 'entity', titleKey: 'profile.steps.entity', titleDefault: 'Entity & Sector', icon: ChartBarIcon, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  { id: 'financial', titleKey: 'profile.steps.financial', titleDefault: 'Financials', icon: CurrencyRupeeIcon, color: 'text-amber-600', bg: 'bg-amber-50' },
  { id: 'location', titleKey: 'profile.steps.location', titleDefault: 'Location', icon: MapPinIcon, color: 'text-rose-600', bg: 'bg-rose-50' },
];

const SECTOR_CHOICES = [
  'Manufacturing',
  'Services',
  'Technology',
  'Retail',
  'Agriculture',
  'Healthcare',
  'Education',
  'Construction',
  'Food Processing',
  'Textiles & Garments',
  'Handicrafts',
  'Tourism & Hospitality',
  'Logistics & Transportation',
  'E-commerce',
  'FinTech',
  'Renewable Energy',
  'Biotechnology',
  'Pharmaceuticals',
  'Electronics Manufacturing',
  'Other',
];

const STATE_CHOICES = [
  'Andhra Pradesh',
  'Arunachal Pradesh',
  'Assam',
  'Bihar',
  'Chhattisgarh',
  'Goa',
  'Gujarat',
  'Haryana',
  'Himachal Pradesh',
  'Jharkhand',
  'Karnataka',
  'Kerala',
  'Madhya Pradesh',
  'Maharashtra',
  'Manipur',
  'Meghalaya',
  'Mizoram',
  'Nagaland',
  'Odisha',
  'Punjab',
  'Rajasthan',
  'Sikkim',
  'Tamil Nadu',
  'Telangana',
  'Tripura',
  'Uttar Pradesh',
  'Uttarakhand',
  'West Bengal',
  'Delhi',
  'Jammu & Kashmir',
  'Ladakh',
  'Puducherry',
  'Chandigarh',
];

const ENTITY_TYPE_CHOICES = [
  'Proprietorship',
  'Partnership Firm',
  'Limited Liability Partnership (LLP)',
  'Private Limited Company',
  'One Person Company (OPC)',
  'Section 8 Company',
  'Startup Registered Entity',
  'Self Help Group',
  'NGO',
];

const TURNOVER_CHOICES = [
  { value: 'Below â‚¹5L', label: 'Below Rs 5L' },
  { value: 'â‚¹5L - â‚¹25L', label: 'Rs 5L - Rs 25L' },
  { value: 'â‚¹25L - â‚¹1Cr', label: 'Rs 25L - Rs 1Cr' },
  { value: 'â‚¹1Cr - â‚¹5Cr', label: 'Rs 1Cr - Rs 5Cr' },
  { value: 'Above â‚¹5Cr', label: 'Above Rs 5Cr' },
];

const GENDER_CHOICES = ['Female', 'Male', 'Other', 'Prefer not to say'];
const CATEGORY_CHOICES = ['General', 'SC', 'ST', 'OBC', 'Minority', 'Other'];
const STAGE_CHOICES = ['Idea Stage', 'Early Stage (0-1 year)', 'Growth Stage (1-3 years)', 'Established (3+ years)'];
const YES_NO_CHOICES = ['Yes', 'No'];
const INVESTMENT_CHOICES = [
  { value: 'Below â‚¹1L', label: 'Below Rs 1L' },
  { value: 'â‚¹1L - â‚¹10L', label: 'Rs 1L - Rs 10L' },
  { value: 'â‚¹10L - â‚¹25L', label: 'Rs 10L - Rs 25L' },
  { value: 'â‚¹25L - â‚¹1Cr', label: 'Rs 25L - Rs 1Cr' },
  { value: 'Above â‚¹1Cr', label: 'Above Rs 1Cr' },
];
const EMPLOYEE_CHOICES = ['1-5', '6-10', '11-25', '26-50', '51-100', '100+'];
const WOMEN_EMPLOYEE_CHOICES = ['0', '1-5', '6-10', '11-25', '26-50', '50+'];
const TECHNOLOGY_CHOICES = ['Traditional / Manual', 'Semi-Automated', 'Automated', 'Advanced / Digital'];
const EXPORT_CHOICES = ['No - Domestic only', 'Planning to Export', 'Currently Exporting'];
const FINANCE_MODE_CHOICES = ['Own contribution', 'Bank Loan + Own', 'Investor + Own', 'Grant + Own'];
const OWN_CONTRIBUTION_CHOICES = ['Below 10%', '10% - 25%', '25% - 50%', 'Above 50%'];
const BANK_CHOICES = ['State Bank of India', 'Indian Bank', 'Canara Bank', 'Punjab National Bank', 'HDFC Bank', 'ICICI Bank', 'Axis Bank', 'Other'];
const LOCATION_TYPE_CHOICES = ['Urban', 'Semi-Urban', 'Rural', 'Industrial Area', 'Special Economic Zone'];
const PREMISES_TYPE_CHOICES = ['Owned', 'Rented', 'Leased', 'Shared Workspace', 'Industrial Shed'];

function toKeySegment(value) {
  const normalized = String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
  if (!normalized) return 'item';
  return /^\d/.test(normalized) ? `item_${normalized}` : normalized;
}

function normalizeChoice(choice) {
  if (typeof choice === 'string') {
    return { value: choice, label: choice };
  }
  return choice;
}

function translateChoices(t, baseKey, choices) {
  return choices.map((choice) => {
    const normalized = normalizeChoice(choice);
    const key = normalized.key || toKeySegment(normalized.value);
    return {
      value: normalized.value,
      label: t(`${baseKey}.${key}`, normalized.label),
    };
  });
}

function Field({ label, required, children }) {
  return (
    <div className="space-y-2">
      <label className="input-label">
        {label} {required && <span className="text-brand-primary">*</span>}
      </label>
      {children}
    </div>
  );
}

function SelectField({ value, onChange, options, placeholder = 'Select...' }) {
  return (
    <div className="relative">
      <select className="v4-select w-full pr-10" value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{placeholder}</option>
        {options.map((choice) => {
          const normalized = normalizeChoice(choice);
          return (
            <option key={normalized.value} value={normalized.value}>
              {normalized.label}
            </option>
          );
        })}
      </select>
      <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  );
}

function RadioGroup({ value, onChange, options }) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((choice) => {
        const normalized = normalizeChoice(choice);
        return (
          <button
            key={normalized.value}
            type="button"
            onClick={() => onChange(normalized.value)}
            className={`px-4 py-2.5 rounded-xl text-sm font-semibold border transition-all duration-200 ${
              value === normalized.value
                ? 'bg-brand-primary text-white border-brand-primary shadow-glow-sm'
                : 'bg-slate-50 text-slate-600 border-slate-200 hover:border-brand-primary/40 hover:text-brand-primary'
            }`}
          >
            {normalized.label}
          </button>
        );
      })}
    </div>
  );
}

function StepPromoter({ data, onChange, t, options }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Field label={t('profile.fields.full_name', 'Full Name')} required>
        <input
          className="v4-input"
          placeholder={t('profile.placeholders.full_name', 'As per Aadhaar')}
          value={data.fullName || ''}
          onChange={(event) => onChange('fullName', event.target.value)}
        />
      </Field>
      <Field label={t('profile.fields.date_of_birth', 'Date of Birth')} required>
        <input className="v4-input" type="date" value={data.dob || ''} onChange={(event) => onChange('dob', event.target.value)} />
      </Field>
      <Field label={t('profile.fields.gender', 'Gender')} required>
        <RadioGroup value={data.gender || ''} onChange={(nextValue) => onChange('gender', nextValue)} options={options.gender} />
      </Field>
      <Field label={t('profile.fields.social_category', 'Social Category')} required>
        <RadioGroup value={data.socialCategory || ''} onChange={(nextValue) => onChange('socialCategory', nextValue)} options={options.categories} />
      </Field>
      <Field label={t('profile.fields.mobile_number', 'Mobile Number')} required>
        <input
          className="v4-input"
          placeholder={t('profile.placeholders.mobile_number', '10-digit mobile')}
          maxLength={10}
          value={data.mobile || ''}
          onChange={(event) => onChange('mobile', event.target.value.replace(/\D/g, ''))}
        />
      </Field>
      <Field label={t('profile.fields.email_address', 'Email Address')} required>
        <input
          className="v4-input"
          type="email"
          placeholder={t('profile.placeholders.email_address', 'name@business.com')}
          value={data.email || ''}
          onChange={(event) => onChange('email', event.target.value)}
        />
      </Field>
      <Field label={t('profile.fields.aadhaar_number', 'Aadhaar Number')}>
        <input
          className="v4-input"
          placeholder={t('profile.placeholders.aadhaar_number', '12-digit')}
          maxLength={12}
          value={data.aadhaar || ''}
          onChange={(event) => onChange('aadhaar', event.target.value.replace(/\D/g, ''))}
        />
      </Field>
      <Field label={t('profile.fields.pan_number', 'PAN Number')} required>
        <input
          className="v4-input"
          placeholder={t('profile.placeholders.pan_number', 'ABCDE1234F')}
          maxLength={10}
          value={data.pan || ''}
          onChange={(event) => onChange('pan', event.target.value.toUpperCase())}
        />
      </Field>
    </div>
  );
}

function StepBusiness({ data, onChange, t, options, yearOptions, selectPlaceholder }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Field label={t('profile.fields.registered_business_name', 'Registered Business Name')} required>
        <input
          className="v4-input"
          placeholder={t('profile.placeholders.registered_business_name', 'As per PAN / Udyam')}
          value={data.businessName || ''}
          onChange={(event) => onChange('businessName', event.target.value)}
        />
      </Field>
      <Field label={t('profile.fields.brand_trade_name', 'Brand / Trade Name')}>
        <input
          className="v4-input"
          placeholder={t('profile.placeholders.brand_trade_name', 'If different from registered')}
          value={data.brandName || ''}
          onChange={(event) => onChange('brandName', event.target.value)}
        />
      </Field>
      <Field label={t('profile.fields.year_of_establishment', 'Year of Establishment')} required>
        <SelectField value={data.yearEstablished || ''} onChange={(nextValue) => onChange('yearEstablished', nextValue)} options={yearOptions} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.business_stage', 'Business Stage')} required>
        <SelectField value={data.businessStage || ''} onChange={(nextValue) => onChange('businessStage', nextValue)} options={options.businessStages} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.udyam_registered', 'Udyam Registered?')} required>
        <RadioGroup value={data.udyamRegistered || ''} onChange={(nextValue) => onChange('udyamRegistered', nextValue)} options={options.yesNo} />
      </Field>
      <Field label={t('profile.fields.gstin_registered', 'GSTIN Registered?')} required>
        <RadioGroup value={data.gstRegistered || ''} onChange={(nextValue) => onChange('gstRegistered', nextValue)} options={options.yesNo} />
      </Field>
      <div className="md:col-span-2">
        <Field label={t('profile.fields.business_description', 'Business Description')} required>
          <textarea
            className="v4-input min-h-[100px] resize-none"
            placeholder={t('profile.placeholders.business_description', 'Describe your products/services in 2-3 sentences...')}
            value={data.businessDescription || ''}
            onChange={(event) => onChange('businessDescription', event.target.value)}
          />
        </Field>
      </div>
    </div>
  );
}

function StepEntity({ data, onChange, t, options, selectPlaceholder }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Field label={t('profile.fields.legal_entity_type', 'Legal Entity Type')} required>
        <SelectField value={data.entityType || ''} onChange={(nextValue) => onChange('entityType', nextValue)} options={options.entityTypes} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.primary_sector', 'Primary Sector')} required>
        <SelectField value={data.sector || ''} onChange={(nextValue) => onChange('sector', nextValue)} options={options.sectors} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.sub_sector_product', 'Sub-Sector / Product')}>
        <input
          className="v4-input"
          placeholder={t('profile.placeholders.sub_sector_product', 'e.g. Organic food, mobile apps')}
          value={data.subSector || ''}
          onChange={(event) => onChange('subSector', event.target.value)}
        />
      </Field>
      <Field label={t('profile.fields.employees', 'No. of Employees')}>
        <SelectField value={data.employees || ''} onChange={(nextValue) => onChange('employees', nextValue)} options={options.employeeCounts} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.women_employees', 'Women Employees')}>
        <SelectField value={data.womenEmployees || ''} onChange={(nextValue) => onChange('womenEmployees', nextValue)} options={options.womenEmployeeCounts} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.technology_level', 'Technology Level')}>
        <SelectField value={data.techLevel || ''} onChange={(nextValue) => onChange('techLevel', nextValue)} options={options.technologyLevels} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.export_intention', 'Export Intention')}>
        <SelectField value={data.exportIntention || ''} onChange={(nextValue) => onChange('exportIntention', nextValue)} options={options.exportIntentions} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.dpiit_registration', 'DPIIT / Startup India Registration')}>
        <input
          className="v4-input"
          placeholder={t('profile.placeholders.dpiit_registration', 'DIPP00000 (if any)')}
          value={data.dpiitNo || ''}
          onChange={(event) => onChange('dpiitNo', event.target.value.toUpperCase())}
        />
      </Field>
    </div>
  );
}

function StepFinancial({ data, onChange, t, options, selectPlaceholder }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Field label={t('profile.fields.total_project_cost', 'Total Project Cost')} required>
        <SelectField value={data.projectCost || ''} onChange={(nextValue) => onChange('projectCost', nextValue)} options={options.investments} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.fixed_capital_investment', 'Fixed Capital Investment')} required>
        <SelectField value={data.fixedCapital || ''} onChange={(nextValue) => onChange('fixedCapital', nextValue)} options={options.investments} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.annual_turnover', 'Annual Turnover')}>
        <SelectField value={data.turnover || ''} onChange={(nextValue) => onChange('turnover', nextValue)} options={options.turnover} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.means_of_finance', 'Means of Finance')} required>
        <SelectField value={data.financeMode || ''} onChange={(nextValue) => onChange('financeMode', nextValue)} options={options.financeModes} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.own_contribution', 'Own Contribution %')}>
        <SelectField value={data.ownContrib || ''} onChange={(nextValue) => onChange('ownContrib', nextValue)} options={options.ownContribution} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.preferred_bank', 'Preferred Bank')}>
        <SelectField value={data.bank || ''} onChange={(nextValue) => onChange('bank', nextValue)} options={options.banks} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.investment_requirement', 'Investment Requirement')}>
        <SelectField value={data.investmentReq || ''} onChange={(nextValue) => onChange('investmentReq', nextValue)} options={options.investments} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.existing_loans_credit', 'Existing Loans / Credit')}>
        <RadioGroup value={data.hasLoans || ''} onChange={(nextValue) => onChange('hasLoans', nextValue)} options={options.yesNo} />
      </Field>
    </div>
  );
}

function StepLocation({ data, onChange, t, options, selectPlaceholder }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Field label={t('profile.fields.state', 'State')} required>
        <SelectField value={data.state || ''} onChange={(nextValue) => onChange('state', nextValue)} options={options.states} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.district', 'District')} required>
        <input
          className="v4-input"
          placeholder={t('profile.placeholders.district', 'Enter district name')}
          value={data.district || ''}
          onChange={(event) => onChange('district', event.target.value)}
        />
      </Field>
      <Field label={t('profile.fields.pin_code', 'PIN Code')} required>
        <input
          className="v4-input"
          placeholder={t('profile.placeholders.pin_code', '6-digit PIN')}
          maxLength={6}
          value={data.pinCode || ''}
          onChange={(event) => onChange('pinCode', event.target.value.replace(/\D/g, ''))}
        />
      </Field>
      <Field label={t('profile.fields.taluk_block', 'Taluk / Block')}>
        <input
          className="v4-input"
          placeholder={t('profile.placeholders.taluk_block', 'Enter taluk name')}
          value={data.taluk || ''}
          onChange={(event) => onChange('taluk', event.target.value)}
        />
      </Field>
      <Field label={t('profile.fields.location_type', 'Location Type')} required>
        <SelectField value={data.locationType || ''} onChange={(nextValue) => onChange('locationType', nextValue)} options={options.locationTypes} placeholder={selectPlaceholder} />
      </Field>
      <Field label={t('profile.fields.premises_type', 'Premises Type')} required>
        <SelectField value={data.premisesType || ''} onChange={(nextValue) => onChange('premisesType', nextValue)} options={options.premisesTypes} placeholder={selectPlaceholder} />
      </Field>
    </div>
  );
}

const STEP_COMPONENTS = [StepPromoter, StepBusiness, StepEntity, StepFinancial, StepLocation];

function validateStep(step, data, t) {
  const reqMap = {
    0: [
      ['fullName', t('profile.fields.full_name', 'Full Name')],
      ['dob', t('profile.fields.date_of_birth', 'Date of Birth')],
      ['gender', t('profile.fields.gender', 'Gender')],
      ['mobile', t('profile.fields.mobile_number', 'Mobile Number')],
      ['pan', t('profile.fields.pan_number', 'PAN Number')],
    ],
    1: [
      ['businessName', t('profile.fields.registered_business_name', 'Registered Business Name')],
      ['yearEstablished', t('profile.fields.year_of_establishment', 'Year of Establishment')],
      ['businessStage', t('profile.fields.business_stage', 'Business Stage')],
      ['businessDescription', t('profile.fields.business_description', 'Business Description')],
    ],
    2: [
      ['entityType', t('profile.fields.legal_entity_type', 'Legal Entity Type')],
      ['sector', t('profile.fields.primary_sector', 'Primary Sector')],
    ],
    3: [
      ['projectCost', t('profile.fields.total_project_cost', 'Total Project Cost')],
      ['fixedCapital', t('profile.fields.fixed_capital_investment', 'Fixed Capital Investment')],
      ['financeMode', t('profile.fields.means_of_finance', 'Means of Finance')],
    ],
    4: [
      ['state', t('profile.fields.state', 'State')],
      ['district', t('profile.fields.district', 'District')],
      ['pinCode', t('profile.fields.pin_code', 'PIN Code')],
      ['locationType', t('profile.fields.location_type', 'Location Type')],
    ],
  };

  const reqs = reqMap[step] || [];
  for (const [key, label] of reqs) {
    if (!data[key] || !String(data[key]).trim()) {
      return t('profile.required_error', { field: label, defaultValue: `${label} is required.` });
    }
  }
  return null;
}

export default function ProfileBuilder({ onComplete, user, prefillData }) {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);
  const [profileData, setProfileData] = useState(prefillData || {});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const stepDefinitions = STEP_CONFIG.map((step) => ({
    ...step,
    title: t(step.titleKey, step.titleDefault),
  }));

  const translatedOptions = {
    gender: translateChoices(t, 'profile.options.gender', GENDER_CHOICES),
    categories: translateChoices(t, 'profile.options.categories', CATEGORY_CHOICES),
    businessStages: translateChoices(t, 'profile.options.business_stages', STAGE_CHOICES),
    yesNo: translateChoices(t, 'profile.options.yes_no', YES_NO_CHOICES),
    entityTypes: translateChoices(t, 'profile.options.entity_types', ENTITY_TYPE_CHOICES),
    sectors: translateChoices(t, 'profile.options.sectors', SECTOR_CHOICES),
    employeeCounts: translateChoices(t, 'profile.options.employee_counts', EMPLOYEE_CHOICES),
    womenEmployeeCounts: translateChoices(t, 'profile.options.women_employee_counts', WOMEN_EMPLOYEE_CHOICES),
    technologyLevels: translateChoices(t, 'profile.options.technology_levels', TECHNOLOGY_CHOICES),
    exportIntentions: translateChoices(t, 'profile.options.export_intentions', EXPORT_CHOICES),
    turnover: translateChoices(t, 'profile.options.turnover', TURNOVER_CHOICES),
    investments: translateChoices(t, 'profile.options.investments', INVESTMENT_CHOICES),
    financeModes: translateChoices(t, 'profile.options.finance_modes', FINANCE_MODE_CHOICES),
    ownContribution: translateChoices(t, 'profile.options.own_contribution', OWN_CONTRIBUTION_CHOICES),
    banks: translateChoices(t, 'profile.options.banks', BANK_CHOICES),
    states: translateChoices(t, 'profile.options.states', STATE_CHOICES),
    locationTypes: translateChoices(t, 'profile.options.location_types', LOCATION_TYPE_CHOICES),
    premisesTypes: translateChoices(t, 'profile.options.premises_types', PREMISES_TYPE_CHOICES),
  };

  const yearOptions = Array.from({ length: 31 }, (_, index) => String(new Date().getFullYear() - index));
  const selectPlaceholder = t('profile.select_placeholder', 'Select...');

  const updateField = useCallback((key, value) => {
    setProfileData((previous) => ({ ...previous, [key]: value }));
    setError('');
  }, []);

  const handleNext = async () => {
    const nextError = validateStep(currentStep, profileData, t);
    if (nextError) {
      setError(nextError);
      return;
    }

    setError('');

    if (currentStep < stepDefinitions.length - 1) {
      setCurrentStep((previous) => previous + 1);
      return;
    }

    setSaving(true);
    try {
      const email = user?.email || JSON.parse(sessionStorage.getItem('karios_user') || '{}').email || '';
      if (email) {
        await fetch(`${API_BASE}/v1/profile/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, profile: profileData }),
        });
      }
      onComplete(profileData);
    } catch {
      onComplete(profileData);
    } finally {
      setSaving(false);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep((previous) => previous - 1);
      setError('');
    }
  };

  const StepComponent = STEP_COMPONENTS[currentStep];
  const stepInfo = stepDefinitions[currentStep];
  const progress = (currentStep / (stepDefinitions.length - 1)) * 100;

  return (
    <div className="min-h-screen bg-brand-intelligence flex items-center justify-center p-6">
      <div className="w-full max-w-3xl">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-brand-primary/10 border border-brand-primary/20 rounded-full text-xs font-bold text-brand-primary mb-4">
            {t('profile.phase_label_clean', 'Phase 2 - Business Intelligence Profile')}
          </div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">{t('profile.title', 'Build Your Intelligence Profile')}</h1>
          <p className="text-slate-500 font-medium mt-2">{t('profile.subtitle', 'This data powers your personalized scheme discovery engine.')}</p>
        </div>

        <div className="bg-white rounded-2xl p-6 mb-6 shadow-card border border-slate-100">
          <div className="flex items-center justify-between mb-4">
            <span className="label-xs">
              {t('profile.step_label', {
                current: currentStep + 1,
                total: stepDefinitions.length,
                title: stepInfo.title,
                defaultValue: `Step ${currentStep + 1} of ${stepDefinitions.length}: ${stepInfo.title}`,
              })}
            </span>
            <span className="label-xs text-brand-primary">
              {Math.round(progress)}% {t('common.complete', 'Complete')}
            </span>
          </div>

          <div className="flex items-center gap-0 mb-4">
            {stepDefinitions.map((step, index) => (
              <React.Fragment key={step.id}>
                <div
                  className={`step-dot cursor-pointer ${index < currentStep ? 'step-dot-done' : index === currentStep ? 'step-dot-active' : 'step-dot-pending'}`}
                  onClick={() => index < currentStep && setCurrentStep(index)}
                  title={step.title}
                >
                  {index < currentStep ? <CheckCircleIcon className="w-4 h-4" /> : <span>{index + 1}</span>}
                </div>
                {index < stepDefinitions.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-1 rounded-full transition-all duration-500 ${index < currentStep ? 'bg-brand-primary' : 'bg-slate-200'}`} />
                )}
              </React.Fragment>
            ))}
          </div>

          <div className="progress-bar">
            <motion.div
              className="progress-fill"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            />
          </div>
        </div>

        <div className="intelligence-card p-8">
          <div className="flex items-center gap-3 mb-8 pb-6 border-b border-slate-100">
            <div className={`w-10 h-10 rounded-xl ${stepInfo.bg} ${stepInfo.color} flex items-center justify-center`}>
              <stepInfo.icon className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-extrabold text-slate-900 text-xl">{stepInfo.title}</h2>
              <p className="text-xs text-slate-400 font-medium">
                {t('profile.current_step', {
                  current: currentStep + 1,
                  total: stepDefinitions.length,
                  defaultValue: `Step ${currentStep + 1} of ${stepDefinitions.length}`,
                })}
              </p>
            </div>
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
            >
              <StepComponent
                data={profileData}
                onChange={updateField}
                t={t}
                options={translatedOptions}
                yearOptions={yearOptions}
                selectPlaceholder={selectPlaceholder}
              />
            </motion.div>
          </AnimatePresence>

          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm font-medium"
            >
              <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
              {error}
            </motion.div>
          )}

          <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-100">
            <button
              onClick={handleBack}
              disabled={currentStep === 0}
              className="btn-secondary disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ArrowLeftIcon className="w-4 h-4" />
              {t('profile.back', 'Back')}
            </button>

            <button onClick={handleNext} disabled={saving} className="btn-primary">
              {saving ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {t('profile.saving', 'Saving...')}
                </>
              ) : currentStep < stepDefinitions.length - 1 ? (
                <>
                  {t('profile.continue', 'Continue')} <ArrowRightIcon className="w-4 h-4" />
                </>
              ) : (
                <>
                  {t('profile.submit', 'Submit & Discover Schemes')} <ArrowRightIcon className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
