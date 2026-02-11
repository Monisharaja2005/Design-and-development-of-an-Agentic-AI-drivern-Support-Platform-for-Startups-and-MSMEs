export function getRequiredFields(form) {
  const fields = [
    'businessType',
    'legalEntityType',
    'businessName',
    'ownerName',
    'gender',
    'pan',
    'mobile',
    'state',
    'city',
    'pincode',
    'sector',
    'primaryNeed',
    'yearOfIncorporation',
    'employeeCount',
    'annualTurnoverLakhs',
    'fundingNeedLakhs',
    'founderShareholding',
  ];
  if (form.hasGst) fields.push('gstin');
  if (form.businessType === 'msme') fields.push('udyamNumber');
  if (form.businessType === 'startup') fields.push('dpiitNumber');
  return fields;
}

export function getProfileClientErrors(profileForm) {
  const errs = {};
  if (!/^[A-Z]{5}[0-9]{4}[A-Z]$/.test(String(profileForm.pan || '').trim().toUpperCase())) {
    errs.pan = 'PAN must be in format ABCDE1234F';
  }
  if (!/^\d{10}$/.test(String(profileForm.mobile || '').trim())) {
    errs.mobile = 'Mobile must be 10 digits';
  }
  if (!/^\d{6}$/.test(String(profileForm.pincode || '').trim())) {
    errs.pincode = 'Pincode must be 6 digits';
  }
  if (profileForm.hasGst) {
    const gstin = String(profileForm.gstin || '').trim().toUpperCase();
    if (!/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$/.test(gstin)) {
      errs.gstin = 'GSTIN format invalid';
    }
  }
  if (profileForm.businessType === 'msme') {
    const udyam = String(profileForm.udyamNumber || '').trim().toUpperCase();
    if (!/^UDYAM-[A-Z]{2}-\d{2}-\d{7}$/.test(udyam)) {
      errs.udyamNumber = 'Udyam format: UDYAM-XX-00-0000000';
    }
  }
  if (profileForm.businessType === 'startup') {
    const dpiit = String(profileForm.dpiitNumber || '').trim().toUpperCase();
    if (!/^DPIIT\d{6,}$/.test(dpiit)) {
      errs.dpiitNumber = 'DPIIT format: DPIIT123456';
    }
  }
  return errs;
}
