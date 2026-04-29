/**
 * SoulSync AI - Notification Permission Banner
 * Shows a friendly prompt to enable browser notifications.
 * Disappears once permission is granted or denied.
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bell, BellOff, X } from "lucide-react";
import { getPermissionStatus, requestPermission } from "../services/notifications";
import { startReminderScheduler } from "../services/taskReminder";

export default function NotificationBanner({ userId, userName }) {
  const [status,    setStatus]    = useState(getPermissionStatus());
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem("soulsync_notif_dismissed") === "1"
  );

  // Re-check on mount
  useEffect(() => {
    setStatus(getPermissionStatus());
  }, []);

  // Don't show if: already granted, denied, unsupported, or dismissed
  const shouldShow = status === "default" && !dismissed;

  const handleAllow = async () => {
    const result = await requestPermission();
    setStatus(result);
    if (result === "granted") {
      startReminderScheduler(userId, 60000);
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
    localStorage.setItem("soulsync_notif_dismissed", "1");
  };

  return (
    <AnimatePresence>
      {shouldShow && (
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.3 }}
          className="mx-4 mt-3 mb-0 flex items-center gap-3
                     bg-surface-800/90 border border-soul-600/30
                     rounded-2xl px-4 py-3 shadow-lg shadow-black/20
                     backdrop-blur-sm"
        >
          {/* Icon */}
          <div className="w-8 h-8 rounded-xl bg-soul-600/20 border border-soul-500/30
                          flex items-center justify-center shrink-0">
            <Bell size={15} className="text-soul-400" />
          </div>

          {/* Text */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white leading-tight">
              Enable task reminders
            </p>
            <p className="text-xs text-surface-400 mt-0.5">
              Get notified when tasks are due today or tomorrow
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 shrink-0">
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleAllow}
              className="px-3 py-1.5 rounded-xl bg-soul-600 hover:bg-soul-500
                         text-white text-xs font-semibold transition-colors">
              Allow
            </motion.button>
            <button
              onClick={handleDismiss}
              className="p-1.5 rounded-lg text-surface-500 hover:text-surface-300
                         hover:bg-surface-700 transition-colors">
              <X size={14} />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
