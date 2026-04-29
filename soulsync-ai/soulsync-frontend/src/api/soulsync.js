/**
 * SoulSync AI - API Client
 * All calls to the FastAPI backend.
 * Auth token is automatically injected from localStorage.
 */

import axios from "axios";

const BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: BASE,
  timeout: 60000,   // 60s — bcrypt verify can take 2-3s, give plenty of room
});

// ── Inject JWT token on every request ────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("soulsync_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Auth ──────────────────────────────────────────────────
export const signup = (name, email, password) =>
  api.post("/auth/signup", { name, email, password });

export const login = (email, password) =>
  api.post("/auth/login", { email, password });

export const getMe = () =>
  api.get("/auth/me");

// ── Chat ──────────────────────────────────────────────────
export const sendMessage = (userId, message) =>
  api.post("/chat", { user_id: userId, message, use_memory: true, use_rag: true });

// ── Memory ────────────────────────────────────────────────
export const getMemories = (userId, limit = 20) =>
  api.get(`/get-memory/${userId}?limit=${limit}`);

// ── Tasks ─────────────────────────────────────────────────
export const getTasks     = (userId)                          => api.get(`/tasks/${userId}`);
export const createTask   = (userId, title, due_date, priority) =>
  api.post("/tasks", { user_id: userId, title, due_date, priority });
export const completeTask = (taskId, userId)                  =>
  api.put(`/tasks/${taskId}/complete?user_id=${userId}`);
export const deleteTask   = (taskId, userId)                  =>
  api.delete(`/tasks/${taskId}?user_id=${userId}`);

// ── Suggestions ───────────────────────────────────────────
export const getSuggestions = (userId) => api.get(`/suggestions/${userId}`);

// ── Processing ────────────────────────────────────────────
export const processMemory = (userId, text) =>
  api.post("/process-memory", { user_id: userId, text });
