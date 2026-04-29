/**
 * SoulSync AI - Task Reminder Scheduler
 * Checks tasks every 60 seconds and fires browser notifications
 * for tasks due today, tomorrow, or overdue.
 */

import { getTasks } from "../api/soulsync";
import {
  notifyTaskDueToday,
  notifyTaskDueTomorrow,
  notifyTaskOverdue,
  getPermissionStatus,
} from "./notifications";

// ── Due date resolver ─────────────────────────────────────
// Tasks store due_date as strings: "today", "tomorrow", "friday", etc.

const DAY_NAMES = ["sunday","monday","tuesday","wednesday","thursday","friday","saturday"];

export function resolveDueDate(dueDateStr) {
  if (!dueDateStr) return null;
  const s     = dueDateStr.toLowerCase().trim();
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (s === "today")    return new Date(today);
  if (s === "tonight")  return new Date(today);
  if (s === "tomorrow") {
    const d = new Date(today);
    d.setDate(d.getDate() + 1);
    return d;
  }
  if (s === "this week") {
    const d = new Date(today);
    // End of this week (Sunday)
    d.setDate(d.getDate() + (7 - d.getDay()));
    return d;
  }
  if (s === "next week") {
    const d = new Date(today);
    d.setDate(d.getDate() + 7);
    return d;
  }
  if (s === "morning" || s === "evening") return new Date(today);

  // Day name: "monday", "friday", etc.
  const dayIdx = DAY_NAMES.indexOf(s);
  if (dayIdx !== -1) {
    const d = new Date(today);
    const diff = (dayIdx - d.getDay() + 7) % 7 || 7;
    d.setDate(d.getDate() + diff);
    return d;
  }

  return null;
}

export function getDueStatus(dueDateStr) {
  const due   = resolveDueDate(dueDateStr);
  if (!due) return null;

  const today    = new Date(); today.setHours(0,0,0,0);
  const tomorrow = new Date(today); tomorrow.setDate(today.getDate() + 1);

  if (due < today)                                    return "overdue";
  if (due.getTime() === today.getTime())              return "today";
  if (due.getTime() === tomorrow.getTime())           return "tomorrow";
  return "upcoming";
}

// ── Notification dedup (localStorage) ────────────────────

const NOTIFIED_KEY = "soulsync_notified_tasks";

function getNotifiedSet() {
  try {
    return new Set(JSON.parse(localStorage.getItem(NOTIFIED_KEY) || "[]"));
  } catch { return new Set(); }
}

function markNotified(taskId) {
  const set = getNotifiedSet();
  set.add(String(taskId));
  // Keep only last 200 entries to avoid unbounded growth
  const arr = [...set].slice(-200);
  localStorage.setItem(NOTIFIED_KEY, JSON.stringify(arr));
}

function wasNotified(taskId) {
  return getNotifiedSet().has(String(taskId));
}

// Clear notified set at midnight so tasks get re-notified next day
function clearIfNewDay() {
  const lastClear = localStorage.getItem("soulsync_notified_date");
  const today     = new Date().toDateString();
  if (lastClear !== today) {
    localStorage.removeItem(NOTIFIED_KEY);
    localStorage.setItem("soulsync_notified_date", today);
  }
}

// ── Main check function ───────────────────────────────────

export async function checkAndNotify(userId) {
  if (getPermissionStatus() !== "granted") return;
  if (!userId) return;

  clearIfNewDay();

  try {
    const res   = await getTasks(userId);
    const tasks = (res.data.tasks || []).filter(t => t.status === "pending");

    for (const task of tasks) {
      if (wasNotified(task.id)) continue;

      const status = getDueStatus(task.due_date);

      if (status === "overdue") {
        notifyTaskOverdue(task.title);
        markNotified(task.id);
      } else if (status === "today") {
        notifyTaskDueToday(task.title);
        markNotified(task.id);
      } else if (status === "tomorrow") {
        notifyTaskDueTomorrow(task.title);
        markNotified(task.id);
      }
    }
  } catch {
    // Silent — don't break the app if notifications fail
  }
}

// ── Scheduler ─────────────────────────────────────────────

let _intervalId = null;

export function startReminderScheduler(userId, intervalMs = 60000) {
  stopReminderScheduler();
  // Run immediately on start
  checkAndNotify(userId);
  // Then every intervalMs
  _intervalId = setInterval(() => checkAndNotify(userId), intervalMs);
}

export function stopReminderScheduler() {
  if (_intervalId) {
    clearInterval(_intervalId);
    _intervalId = null;
  }
}
