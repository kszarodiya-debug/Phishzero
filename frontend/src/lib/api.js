import axios from "axios";

const TOKEN_KEY = "phishguard_access_token";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.localStorage.removeItem(TOKEN_KEY);
      window.dispatchEvent(new Event("phishguard:unauthorized"));
    }
    return Promise.reject(error);
  },
);

export const authStorage = {
  getToken: () => window.localStorage.getItem(TOKEN_KEY),
  setToken: (token) => window.localStorage.setItem(TOKEN_KEY, token),
  clear: () => window.localStorage.removeItem(TOKEN_KEY),
};

export function getApiError(error, fallback = "Something went wrong. Please try again.") {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).filter(Boolean).join(" ") || fallback;
  }
  return typeof detail === "string" ? detail : fallback;
}
