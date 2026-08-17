/**
 * Single entry point for every backend call.
 *
 * Previously "http://127.0.0.1:5000" was hardcoded in eight components, so
 * pointing the app at any other host meant editing eight files, and each
 * caller did its own ad-hoc error handling (mostly none).
 *
 * Override the base URL with REACT_APP_API_BASE_URL in frontend/.env.
 */

const BASE_URL = (
  process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000/api/v1"
).replace(/\/$/, "");

const ADMIN_TOKEN_KEY = "hsd_admin_token";

/* =========================
   ADMIN TOKEN STORAGE
   ========================= */

export function getAdminToken() {
  return sessionStorage.getItem(ADMIN_TOKEN_KEY);
}

export function setAdminToken(token) {
  sessionStorage.setItem(ADMIN_TOKEN_KEY, token);
  // Kept in sync so Navbar's existing listener keeps working.
  sessionStorage.setItem("admin_auth", "true");
  window.dispatchEvent(new Event("admin-auth-change"));
}

export function clearAdminToken() {
  sessionStorage.removeItem(ADMIN_TOKEN_KEY);
  sessionStorage.removeItem("admin_auth");
  window.dispatchEvent(new Event("admin-auth-change"));
}

export function isAdminAuthenticated() {
  return Boolean(getAdminToken());
}

/* =========================
   ERRORS
   ========================= */

export class ApiError extends Error {
  constructor(message, { status, code, details } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/* =========================
   CORE REQUEST
   ========================= */

async function request(path, options = {}) {
  const { method = "GET", body, admin = false, raw = false, headers = {} } =
    options;

  const requestHeaders = { ...headers };
  let payload;

  if (body instanceof FormData) {
    payload = body; // let the browser set the multipart boundary
  } else if (body !== undefined) {
    requestHeaders["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  if (admin) {
    const token = getAdminToken();
    if (token) requestHeaders["X-ADMIN-KEY"] = token;
  }

  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: requestHeaders,
      body: payload,
    });
  } catch (networkError) {
    throw new ApiError(
      "Could not reach the API. Is the backend running?",
      { status: 0, code: "network_error" }
    );
  }

  // An expired/invalid admin token should not leave the UI in a logged-in state.
  if (response.status === 401 && admin) {
    clearAdminToken();
  }

  if (response.status === 204) return null;

  if (raw) {
    if (!response.ok) {
      throw new ApiError(`Request failed (${response.status})`, {
        status: response.status,
      });
    }
    return response;
  }

  const contentType = response.headers.get("Content-Type") || "";
  const isJson = contentType.includes("application/json");
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    const error = (data && data.error) || {};
    throw new ApiError(
      error.message || `Request failed (${response.status})`,
      {
        status: response.status,
        code: error.code,
        details: error.details,
      }
    );
  }

  return data;
}

/* =========================
   PREDICTIONS
   ========================= */

export const predictions = {
  create: (text) => request("/predictions", { method: "POST", body: { text } }),

  list: ({ page = 1, perPage = 20, label, lang, q } = {}) => {
    const params = new URLSearchParams({ page, per_page: perPage });
    if (label !== undefined && label !== null && label !== "")
      params.set("label", label);
    if (lang) params.set("lang", lang);
    if (q) params.set("q", q);
    return request(`/predictions?${params}`);
  },

  get: (id) => request(`/predictions/${id}`),

  remove: (id) => request(`/predictions/${id}`, { method: "DELETE", admin: true }),

  exportUrl: () => `${BASE_URL}/predictions/export?format=csv`,
};

/* =========================
   ANNOTATIONS (FEEDBACK)
   ========================= */

export const annotations = {
  create: ({ text, label, language }) =>
    request("/annotations", {
      method: "POST",
      body: { text, label, language },
    }),
};

/* =========================
   FLAGGED TERMS
   ========================= */

export const flaggedTerms = {
  list: ({ minFrequency = 2 } = {}) =>
    request(`/flagged-terms?min_frequency=${minFrequency}`),

  create: ({ words, label }) =>
    request("/flagged-terms", { method: "POST", body: { words, label } }),

  remove: (word) =>
    request(`/flagged-terms/${encodeURIComponent(word)}`, {
      method: "DELETE",
      admin: true,
    }),
};

/* =========================
   ANALYTICS
   ========================= */

export const analytics = {
  dashboard: ({ days = 30 } = {}) => request(`/analytics?days=${days}`),
  summary: () => request("/analytics/summary"),
  models: () => request("/analytics/models"),
  dataset: () => request("/analytics/dataset"),
};

/* =========================
   SURVEY
   ========================= */

export const survey = {
  /** Resolves to null once every text has been labelled. */
  next: async () => {
    try {
      return await request("/survey/items/next");
    } catch (error) {
      if (error.status === 404 && error.code === "survey_exhausted") {
        return null;
      }
      throw error;
    }
  },

  vote: ({ text, label }) =>
    request("/survey/votes", { method: "POST", body: { text, label } }),

  stats: () => request("/survey/stats", { admin: true }),
};

/* =========================
   ADMIN
   ========================= */

export const admin = {
  login: async (password) => {
    const data = await request("/admin/sessions", {
      method: "POST",
      body: { password },
    });
    setAdminToken(data.token);
    return data;
  },

  logout: async () => {
    try {
      await request("/admin/sessions/current", {
        method: "DELETE",
        admin: true,
      });
    } finally {
      clearAdminToken();
    }
  },

  trends: () => request("/admin/trends", { admin: true }),

  dataset: () => request("/admin/datasets", { admin: true }),

  uploadDataset: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/admin/datasets", {
      method: "POST",
      body: form,
      admin: true,
    });
  },

  startTraining: () =>
    request("/admin/training-jobs", { method: "POST", admin: true }),

  getTrainingJob: (id) =>
    request(`/admin/training-jobs/${id}`, { admin: true }),

  listTrainingJobs: () => request("/admin/training-jobs", { admin: true }),
};

/* =========================
   META
   ========================= */

export const meta = {
  health: () => request("/health"),
  index: () => request("/"),
};

export const API_BASE_URL = BASE_URL;
