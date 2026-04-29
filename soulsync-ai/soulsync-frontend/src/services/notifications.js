/**
 * SoulSync AI - Browser Notification Service
 * Handles permission requests and firing notifications.
 */

const ICON = "/vite.svg";   // app icon shown in notification

// ── Permission ────────────────────────────────────────────

export function getPermissionStatus() {
  if (!("Notification" in window)) return "unsupported";
  return Notification.permission;   // "default" | "granted" | "denied"
}

export async function requestPermission() {
  if (!("Notification" in window)) return "unsupported";
  if (Notification.permission === "granted") return "granted";
  if (Notification.permission === "denied")  return "denied";
  const result = await Notification.requestPermission();
  return result;
}

// ── Fire a notification ───────────────────────────────────

export function fireNotification(title, body, options = {}) {
  if (!("Notification" in window)) return;
  if (Notification.permission !== "granted") return;

  const n = new Notification(title, {
    body,
    icon   : ICON,
    badge  : ICON,
    tag    : options.tag || title,          // deduplication key
    silent : false,
    ...options,
  });

  // Click → focus the app tab
  n.onclick = () => {
    window.focus();
    n.close();
    if (options.onClick) options.onClick();
  };

  // Auto-close after 8 seconds
  setTimeout(() => n.close(), 8000);

  return n;
}

// ── Convenience helpers ───────────────────────────────────

export function notifyTaskDueToday(taskTitle) {
  return fireNotification(
    "📋 Task due today!",
    `Don't forget: ${taskTitle}`,
    { tag: `task-today-${taskTitle}` }
  );
}

export function notifyTaskDueTomorrow(taskTitle) {
  return fireNotification(
    "⏰ Task due tomorrow",
    `Heads up: ${taskTitle}`,
    { tag: `task-tomorrow-${taskTitle}` }
  );
}

export function notifyTaskOverdue(taskTitle) {
  return fireNotification(
    "🚨 Overdue task",
    `This was due: ${taskTitle}`,
    { tag: `task-overdue-${taskTitle}` }
  );
}

export function notifyWelcomeBack(userName) {
  return fireNotification(
    `Welcome back, ${userName}! 👋`,
    "SoulSync AI is ready. Check your tasks for today.",
    { tag: "welcome-back" }
  );
}
