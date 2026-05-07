/**
 * SoulSync AI - API Client Module
 * 
 * This module provides a centralized interface for all communication with the
 * FastAPI backend. It handles authentication, request/response interception,
 * and provides typed API methods for each backend endpoint.
 * 
 * Features:
 * - Automatic JWT token injection via axios interceptors
 * - Configurable base URL via environment variables
 * - 60-second timeout for long-running operations
 * - Error handling and response transformation
 * 
 * Architecture:
 * - Uses Axios for HTTP requests
 * - Base URL configured via VITE_API_URL environment variable
 * - JWT tokens stored in localStorage and automatically attached to requests
 * - All API methods return Promises for async/await usage
 * 
 * Usage:
 *   import { sendMessage, getTasks } from './api/soulsync';
 *   
 *   // Send a chat message
 *   const response = await sendMessage('user123', 'Hello, how are you?');
 *   console.log(response.data.response);
 *   
 *   // Get user's tasks
 *   const tasks = await getTasks('user123');
 *   console.log(tasks.data);
 * 
 * @module api/soulsync
 * @requires axios
 */

import axios from "axios";

/**
 * Base URL for the API
 * Uses environment variable VITE_API_URL if set, otherwise defaults to localhost:8000
 * The /api/v1 prefix is automatically appended
 */
const BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : "http://localhost:8000/api/v1";

/**
 * Axios instance configuration
 * - baseURL: API endpoint root
 * - timeout: 60 seconds (generous for AI operations and bcrypt verification)
 */
const api = axios.create({
  baseURL: BASE,
  timeout: 60000,   // 60s — bcrypt verify can take 2-3s, give plenty of room
});

/**
 * Request Interceptor
 * Automatically injects JWT authentication token into every request.
 * Token is retrieved from localStorage where it's stored after login.
 * 
 * Flow:
 * 1. Check if token exists in localStorage
 * 2. If found, add Authorization header with Bearer token
 * 3. Return modified config to proceed with request
 */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("soulsync_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ═══════════════════════════════════════════════════════════
// AUTHENTICATION ENDPOINTS
// ═══════════════════════════════════════════════════════════

/**
 * User Registration
 * Creates a new user account and returns JWT token
 * 
 * @param {string} name - User's display name
 * @param {string} email - User's email address (used for login)
 * @param {string} password - User's password (will be hashed server-side)
 * @returns {Promise} Resolves with user data and JWT token
 * 
 * @example
 * const { data } = await signup("John Doe", "john@example.com", "securepassword");
 * console.log(data.token); // JWT token for subsequent requests
 */
export const signup = (name, email, password) =>
  api.post("/auth/signup", { name, email, password });

/**
 * User Login
 * Authenticates user and returns JWT token
 * 
 * @param {string} email - User's email address
 * @param {string} password - User's password
 * @returns {Promise} Resolves with user data and JWT token
 * 
 * @example
 * const { data } = await login("john@example.com", "securepassword");
 * localStorage.setItem("soulsync_token", data.token);
 */
export const login = (email, password) =>
  api.post("/auth/login", { email, password });

/**
 * Get Current User
 * Retrieves authenticated user's profile information
 * Requires valid JWT token in Authorization header
 * 
 * @returns {Promise} Resolves with user profile data
 * 
 * @example
 * const { data } = await getMe();
 * console.log(data.user_id, data.name, data.email);
 */
export const getMe = () =>
  api.get("/auth/me");

// ═══════════════════════════════════════════════════════════
// CHAT ENDPOINTS
// ═══════════════════════════════════════════════════════════

/**
 * Send Chat Message
 * Main conversation endpoint. Sends user message to AI and returns response.
 * Automatically uses memory and RAG for personalized responses.
 * 
 * @param {string} userId - Unique user identifier
 * @param {string} message - User's message text
 * @returns {Promise} Resolves with AI response, retrieved memories, and created tasks
 * 
 * Response structure:
 * {
 *   response: string,           // AI's text response
 *   retrieved_memories: array,  // Relevant past conversations
 *   tasks_created: array,       // Auto-detected tasks
 *   intent: string,            // Detected user intent
 *   stored_fact: object|null,  // Personal fact that was stored
 * }
 * 
 * @example
 * const { data } = await sendMessage("user123", "I'm feeling tired today");
 * console.log(data.response); // AI's empathetic response
 */
export const sendMessage = (userId, message) =>
  api.post("/chat", { user_id: userId, message, use_memory: true, use_rag: true });

// ═══════════════════════════════════════════════════════════
// MEMORY ENDPOINTS
// ═══════════════════════════════════════════════════════════

/**
 * Get User Memories
 * Retrieves stored memories and personal facts for a user
 * 
 * @param {string} userId - Unique user identifier
 * @param {number} limit - Maximum number of memories to return (default: 20)
 * @returns {Promise} Resolves with array of memory objects
 * 
 * @example
 * const { data } = await getMemories("user123", 10);
 * data.forEach(memory => console.log(memory.key, memory.value));
 */
export const getMemories = (userId, limit = 20) =>
  api.get(`/get-memory/${userId}?limit=${limit}`);

// ═══════════════════════════════════════════════════════════
// TASK MANAGEMENT ENDPOINTS
// ═══════════════════════════════════════════════════════════

/**
 * Get User Tasks
 * Retrieves all tasks for a user (pending, completed, etc.)
 * 
 * @param {string} userId - Unique user identifier
 * @returns {Promise} Resolves with array of task objects
 * 
 * Task structure:
 * {
 *   task_id: string,
 *   title: string,
 *   status: "pending" | "completed" | "deleted",
 *   priority: "high" | "medium" | "low",
 *   due_date: string,
 *   created_at: string
 * }
 */
export const getTasks = (userId) => api.get(`/tasks/${userId}`);

/**
 * Create New Task
 * Creates a new task for the user (can be auto-detected from chat)
 * 
 * @param {string} userId - Unique user identifier
 * @param {string} title - Task description
 * @param {string} due_date - When the task is due (e.g., "tomorrow", "Friday")
 * @param {string} priority - Task priority: "high", "medium", or "low"
 * @returns {Promise} Resolves with created task object
 * 
 * @example
 * const { data } = await createTask("user123", "Buy groceries", "tomorrow", "medium");
 * console.log(data.task_id); // ID of newly created task
 */
export const createTask = (userId, title, due_date, priority) =>
  api.post("/tasks", { user_id: userId, title, due_date, priority });

/**
 * Mark Task as Complete
 * Updates task status to "completed" and records completion time
 * 
 * @param {string} taskId - Unique task identifier
 * @param {string} userId - Unique user identifier (for verification)
 * @returns {Promise} Resolves with updated task object
 * 
 * @example
 * await completeTask("task_abc123", "user123");
 * console.log("Task completed!");
 */
export const completeTask = (taskId, userId) =>
  api.put(`/tasks/${taskId}/complete?user_id=${userId}`);

/**
 * Delete Task
 * Permanently removes a task from the system
 * 
 * @param {string} taskId - Unique task identifier
 * @param {string} userId - Unique user identifier (for verification)
 * @returns {Promise} Resolves on successful deletion
 * 
 * @example
 * await deleteTask("task_abc123", "user123");
 * console.log("Task deleted");
 */
export const deleteTask = (taskId, userId) =>
  api.delete(`/tasks/${taskId}?user_id=${userId}`);

// ═══════════════════════════════════════════════════════════
// SUGGESTIONS & INSIGHTS ENDPOINTS
// ═══════════════════════════════════════════════════════════

/**
 * Get Smart Suggestions
 * Retrieves personalized suggestions based on user's activity patterns
 * 
 * @param {string} userId - Unique user identifier
 * @returns {Promise} Resolves with array of suggestion objects
 * 
 * Suggestion structure:
 * {
 *   type: string,        // "activity" | "mood" | "productivity"
 *   title: string,
 *   description: string,
 *   confidence: number   // 0.0 to 1.0
 * }
 */
export const getSuggestions = (userId) => api.get(`/suggestions/${userId}`);

// ═══════════════════════════════════════════════════════════
// PROCESSING ENDPOINTS
// ═══════════════════════════════════════════════════════════

/**
 * Process Memory
 * Extracts structured data from user text (emotions, activities, etc.)
 * Used internally by the chat system for memory enhancement
 * 
 * @param {string} userId - Unique user identifier
 * @param {string} text - Raw user text to process
 * @returns {Promise} Resolves with extracted memory structure
 * 
 * Extracted structure:
 * {
 *   emotion: string,      // Detected emotion
 *   activity: string,     // Detected activity
 *   status: string,       // Activity status
 *   productivity: string, // Productivity level
 *   summary: string       // Text summary
 * }
 */
export const processMemory = (userId, text) =>
  api.post("/process-memory", { user_id: userId, text });

// ═══════════════════════════════════════════════════════════
// EXPORT AXIOS INSTANCE
// ═══════════════════════════════════════════════════════════

/**
 * Export the configured axios instance for advanced use cases
 * This allows direct access to the API client for custom requests
 * 
 * @example
 * import api from './api/soulsync';
 * const response = await api.get('/custom-endpoint');
 */
export default api;