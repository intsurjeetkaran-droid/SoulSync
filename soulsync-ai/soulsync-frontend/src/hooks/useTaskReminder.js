/**
 * SoulSync AI - useTaskReminder hook
 * Starts/stops the task reminder scheduler based on auth state.
 */

import { useEffect } from "react";
import { getPermissionStatus, notifyWelcomeBack } from "../services/notifications";
import { startReminderScheduler, stopReminderScheduler } from "../services/taskReminder";

export default function useTaskReminder(user) {
  useEffect(() => {
    if (!user?.user_id) {
      stopReminderScheduler();
      return;
    }

    if (getPermissionStatus() === "granted") {
      // Welcome back notification on login
      notifyWelcomeBack(user.name || user.user_id);
      // Start checking tasks every 60 seconds
      startReminderScheduler(user.user_id, 60000);
    }

    return () => stopReminderScheduler();
  }, [user?.user_id]);
}
