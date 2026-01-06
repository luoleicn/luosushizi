const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
const TOKEN_KEY = "hanzi_token";
const USER_KEY = "hanzi_user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token, user) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  }
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    window.location.href = "/login";
    return null;
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export const api = {
  login(payload) {
    return request("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  listDictionaries() {
    return request("/dictionaries");
  },
  createDictionary(payload) {
    return request("/dictionaries", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  updateDictionary(dictionaryId, payload) {
    return request(`/dictionaries/${dictionaryId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  deleteDictionary(dictionaryId) {
    return request(`/dictionaries/${dictionaryId}`, {
      method: "DELETE",
    });
  },
  me() {
    return request("/auth/me");
  },
  getQueue(dictionaryId) {
    return request(`/dictionaries/${dictionaryId}/study/queue`);
  },
  review(dictionaryId, payload) {
    return request(`/dictionaries/${dictionaryId}/study/review`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  startSession(dictionaryId) {
    return request(`/dictionaries/${dictionaryId}/study/session/start`, { method: "POST" });
  },
  endSession(dictionaryId, payload) {
    return request(`/dictionaries/${dictionaryId}/study/session/end`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  importCharacters(payload) {
    return request(`/dictionaries/${payload.dictionaryId}/characters/import`, {
      method: "POST",
      body: JSON.stringify({ items: payload.items }),
    });
  },
  getCharacterInfo(dictionaryId, hanzi) {
    return request(`/dictionaries/${dictionaryId}/characters/${encodeURIComponent(hanzi)}/info`);
  },
  getStats(dictionaryId) {
    return request(`/dictionaries/${dictionaryId}/stats/summary`);
  },
};
