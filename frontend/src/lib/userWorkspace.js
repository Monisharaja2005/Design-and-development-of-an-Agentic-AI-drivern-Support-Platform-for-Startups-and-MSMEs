const API_BASE = '';

export function emptyWorkspace() {
  return {
    profile: {},
    saved_schemes: [],
    last_selected_scheme_id: '',
  };
}

export function normalizeWorkspace(workspace, fallbackProfile = {}) {
  const base = emptyWorkspace();
  const safeProfile = workspace?.profile && typeof workspace.profile === 'object'
    ? workspace.profile
    : (fallbackProfile && typeof fallbackProfile === 'object' ? fallbackProfile : {});
  const safeSavedSchemes = Array.isArray(workspace?.saved_schemes) ? workspace.saved_schemes : [];
  const safeLastSelectedSchemeId = typeof workspace?.last_selected_scheme_id === 'string'
    ? workspace.last_selected_scheme_id
    : '';

  return {
    ...base,
    profile: safeProfile,
    saved_schemes: safeSavedSchemes,
    last_selected_scheme_id: safeLastSelectedSchemeId,
  };
}

export function getSessionUser() {
  try {
    return JSON.parse(sessionStorage.getItem('karios_user') || 'null');
  } catch {
    return null;
  }
}

export function setSessionUser(user) {
  sessionStorage.setItem('karios_user', JSON.stringify(user || {}));
}

export function clearLegacyWorkspaceCache() {
  localStorage.removeItem('karios_saved');
  localStorage.removeItem('karios_last_selected_scheme');
}

export function mergeUserWorkspace(user, workspace) {
  const normalizedWorkspace = normalizeWorkspace(workspace, user?.profile_data || {});
  return {
    ...(user || {}),
    profile_data: normalizedWorkspace.profile,
    workspace: normalizedWorkspace,
  };
}

export async function fetchUserWorkspace(email) {
  const response = await fetch(`${API_BASE}/v1/workspace/get?email=${encodeURIComponent(email)}`, {
    signal: AbortSignal.timeout(60000),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Could not load user workspace.');
  }
  // Backend returns profile at top level — fall back through all possible shapes
  return normalizeWorkspace(
    data.workspace || {
      profile: data.profile || data.profile_data || {},
      saved_schemes: data.saved_schemes || [],
      last_selected_scheme_id: data.last_selected_scheme_id || '',
    }
  );
}

export async function saveUserSchemes(email, schemeIds) {
  if (!email || !Array.isArray(schemeIds)) {
    throw new Error('Email and schemeIds array required');
  }
  const response = await fetch(`${API_BASE}/v1/schemes/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    signal: AbortSignal.timeout(60000),
    body: JSON.stringify({ email, schemes: schemeIds }),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Save failed: ${response.status}`);
  }
  return schemeIds; // Return saved IDs for confirmation
}

export async function loadUserSchemes(email) {
  if (!email) {
    throw new Error('Email required');
  }
  const response = await fetch(`${API_BASE}/v1/schemes/saved?email=${encodeURIComponent(email)}`, {
    signal: AbortSignal.timeout(60000),
  });
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Load failed: ${response.status}`);
  }
  const data = await response.json();
  return Array.isArray(data?.schemes) ? data.schemes : [];
}

export async function saveUserWorkspace(email, patch) {
  const response = await fetch(`${API_BASE}/v1/workspace/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    signal: AbortSignal.timeout(60000),
    body: JSON.stringify({ email, ...patch }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Could not save user workspace.');
  }
  return normalizeWorkspace(
    data.workspace || {
      profile: data.profile || data.profile_data || {},
      saved_schemes: data.saved_schemes || [],
      last_selected_scheme_id: data.last_selected_scheme_id || '',
    }
  );
}
