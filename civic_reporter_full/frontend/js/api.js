/**
 * GroundTruth -- API client
 *
 * Set API_BASE to wherever your Django backend (the project from the
 * previous step) is actually deployed. GitHub Pages only serves static
 * files, so the Django API has to be hosted separately (Railway, Render,
 * PythonAnywhere, a VPS, etc.) -- this file is the only place that needs
 * updating once you know that URL.
 */
// Leave this empty when Django serves the site (same origin -> no CORS needed).
// Only set it if you host the frontend folder somewhere else (e.g. GitHub Pages),
// e.g. "https://my-backend.onrender.com/api".
const API_BASE_OVERRIDE = "";
const API_BASE =
  API_BASE_OVERRIDE ||
  (window.location.protocol === "file:" ? "http://127.0.0.1:8000/api" : "/api");

const TOKEN_KEY = "gt_access_token";
const REFRESH_KEY = "gt_refresh_token";

const auth = {
  getAccess: () => localStorage.getItem(TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  setTokens: (access, refresh) => {
    localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
  isLoggedIn: () => !!localStorage.getItem(TOKEN_KEY),
};

async function apiRequest(path, { method = "GET", body, auth: needsAuth = false } = {}) {
  const isFormData = body instanceof FormData;
  const headers = {};
  if (!isFormData) headers["Content-Type"] = "application/json";
  if (needsAuth) {
    const token = auth.getAccess();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? (isFormData ? body : JSON.stringify(body)) : undefined,
  });

  let data = null;
  try {
    data = await res.json();
  } catch (_) {
    /* empty body, e.g. 204 */
  }

  if (!res.ok) {
    const message =
      (data && (data.detail || firstErrorMessage(data))) ||
      `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

/** DRF validation errors come back as {field: ["msg", ...]} -- surface the first one. */
function firstErrorMessage(data) {
  for (const key in data) {
    const val = data[key];
    if (Array.isArray(val) && val.length) return val[0];
  }
  return null;
}

const Api = {
  register: (payload) => apiRequest("/auth/register/", { method: "POST", body: payload }),
  login: (payload) => apiRequest("/auth/login/", { method: "POST", body: payload }),
  me: () => apiRequest("/auth/me/", { auth: true }),
  areas: () => apiRequest("/reports/areas/", { auth: true }),
  categories: () => apiRequest("/reports/categories/", { auth: true }),
  mine: () => apiRequest("/reports/mine/", { auth: true }),
  reports: () => apiRequest("/reports/", { auth: true }),
  createReport: (payload) => apiRequest("/reports/", { method: "POST", body: payload, auth: true }),
  comment: (id, body) => apiRequest(`/reports/${id}/comments/`, { method: "POST", body, auth: true }),
  upvote: (id) => apiRequest(`/reports/${id}/upvote/`, { method: "POST", body: {}, auth: true }),
};
