// ================= API LAYER =================

const API_BASE = import.meta.env.VITE_API_URL || '';

export const fetchWithCreds = async (url, options = {}) => {
  const finalOptions = {
    ...options,
    credentials: 'include', // Send cookies for session
    headers: {
      ...options.headers,
      'Content-Type': 'application/json',
    },
  };
  
  if (options.body && typeof options.body !== 'string') {
      finalOptions.body = JSON.stringify(options.body);
  }

  const fullUrl = `${API_BASE}${url}`;
  console.log(`[API] ${finalOptions.method || 'GET'} → ${fullUrl}`);

  const res = await fetch(fullUrl, finalOptions);
  
  console.log(`[API] ${finalOptions.method || 'GET'} ${url} ← ${res.status}`);
  
  if (!res.ok && res.status !== 401) {
    console.warn(`[API] Non-OK response: ${res.status} ${res.statusText} for ${url}`);
  }

  return res.json();
};

// 🔐 AUTH
export async function apiLogin(email, password) {
    return fetchWithCreds('/api/auth/login', { method: 'POST', body: { email, password } });
}

export async function apiSignup(email, password) {
    return fetchWithCreds('/api/auth/register', { method: 'POST', body: { email, password } });
}

export async function apiLogout() {
    return fetchWithCreds('/api/auth/logout', { method: 'POST' });
}

export async function apiCheckSession() {
    // New endpoint /api/auth/me returns 200 with user_id or 401 Unauthorized
    try {
        const res = await fetchWithCreds('/api/auth/me', { method: 'GET' });
        return { logged_in: res.status === 'success', user_id: res.user_id };
    } catch(e) {
        return { logged_in: false };
    }
}

// 🔍 DISCOVERY
export async function apiProcess(command) {
    return fetchWithCreds('/process', { method: 'POST', body: { command } });
}

// 🧠 AUDIT (AGENT)
export async function apiAnalyzeOne(db_id) {
    return fetchWithCreds('/analyze_one', { method: 'POST', body: { db_id } });
}

// ✍️ EMAIL
export async function apiGenerateEmail(db_id) {
    return fetchWithCreds('/generate_email', { method: 'POST', body: { db_id } });
}

export async function apiBatchOutreach(ids, query) {
    return fetchWithCreds('/batch_outreach', { method: 'POST', body: { ids, query } });
}

// 📊 ROI
export async function apiCalculateROI(db_id) {
    return fetchWithCreds('/calculate_roi', { method: 'POST', body: { db_id } });
}

// 📦 DATA
export async function apiGetInitialData() {
    return fetchWithCreds('/get_initial_data', { method: 'GET' });
}

export async function apiGetHistoryLeads(query) {
    return fetchWithCreds('/get_history_leads', { method: 'POST', body: { query } });
}

// 🗑️ DELETE
export async function apiDeleteLead(db_id) {
    return fetchWithCreds('/delete_lead', { method: 'POST', body: { db_id } });
}

export async function apiDeleteHistory(query) {
    return fetchWithCreds('/delete_history', { method: 'POST', body: { query } });
}

// ⚙️ SETTINGS
export async function apiSaveSettings(data) {
    return fetchWithCreds('/save_settings', { method: 'POST', body: data });
}

export async function apiGetSettings() {
    return fetchWithCreds('/get_settings', { method: 'GET' });
}

// 📧 GMAIL INTEGRATION
export async function apiGoogleLogin() {
    return fetchWithCreds('/api/gmail/connect', { method: 'GET' });
}

export async function apiGoogleDisconnect() {
    return fetchWithCreds('/api/gmail/disconnect', { method: 'POST' });
}

export async function apiGetGmailStatus() {
    return fetchWithCreds('/api/gmail/status', { method: 'GET' });
}

export async function apiTestGmail() {
    return fetchWithCreds('/api/gmail/test', { method: 'POST' });
}

// 🔑 API KEYS (BYOK)
export async function apiGetKeys() {
    return fetchWithCreds('/api/keys', { method: 'GET' });
}

export async function apiGetUsage() {
    return fetchWithCreds('/api/keys/usage', { method: 'GET' });
}

export async function apiAddKey(provider, api_key) {
    return fetchWithCreds('/api/keys', { method: 'POST', body: { provider, api_key } });
}

export async function apiUpdateKey(provider, api_key) {
    return fetchWithCreds(`/api/keys/${provider}`, { method: 'PUT', body: { api_key } });
}

export async function apiDeleteKey(provider) {
    return fetchWithCreds(`/api/keys/${provider}`, { method: 'DELETE' });
}

export async function apiTestKey(provider) {
    return fetchWithCreds(`/api/keys/test/${provider}`, { method: 'POST' });
}