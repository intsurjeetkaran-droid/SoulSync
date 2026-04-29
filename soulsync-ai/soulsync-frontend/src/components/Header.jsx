import { Brain, Wifi, LogOut, Mic, Bell, BellOff, PanelRight } from "lucide-react";
import { useState, useEffect } from "react";
import { getPermissionStatus, requestPermission } from "../services/notifications";
import { startReminderScheduler } from "../services/taskReminder";

export default function Header({ userId, isConnected, onLogout, onVoiceMode, onMobileDrawer, user }) {
  const [notifStatus, setNotifStatus] = useState(getPermissionStatus());

  useEffect(() => {
    setNotifStatus(getPermissionStatus());
  }, []);

  const handleBellClick = async () => {
    if (notifStatus === "granted") return;
    if (notifStatus === "denied") {
      alert("Notifications are blocked. Please enable them in your browser settings.");
      return;
    }
    const result = await requestPermission();
    setNotifStatus(result);
    if (result === "granted" && user?.user_id) {
      startReminderScheduler(user.user_id, 60000);
    }
  };

  return (
    <header className="flex items-center justify-between px-3 sm:px-6 py-3
                       bg-surface-900/95 backdrop-blur-sm
                       border-b border-surface-800 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2 sm:gap-3">
        <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-gradient-to-br from-soul-500 to-soul-700
                        flex items-center justify-center
                        shadow-lg shadow-soul-900/50 animate-glow-pulse shrink-0">
          <Brain size={17} className="text-white" />
        </div>
        <div className="hidden xs:block">
          <h1 className="text-sm sm:text-base font-bold text-white leading-none tracking-tight">
            SoulSync <span className="text-soul-400">AI</span>
          </h1>
          <p className="text-[10px] sm:text-[11px] text-surface-500 mt-0.5 hidden sm:block">
            Your personal companion
          </p>
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-1.5 sm:gap-3">
        {/* Connection status */}
        <div className={`flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-1 rounded-full
                         text-xs font-medium border transition-colors duration-300
                         ${isConnected
                           ? "bg-soul-500/10 border-soul-500/25 text-soul-400"
                           : "bg-red-500/10 border-red-500/25 text-red-400"}`}>
          <span className={`w-1.5 h-1.5 rounded-full shrink-0
                            ${isConnected ? "bg-soul-400 animate-pulse" : "bg-red-400"}`} />
          <span className="hidden sm:inline">{isConnected ? "Live" : "Offline"}</span>
        </div>

        <div className="w-px h-5 bg-surface-700 hidden sm:block" />

        {/* User avatar + name */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-glow-500 to-glow-700
                          flex items-center justify-center text-xs font-bold text-surface-950
                          shadow-sm shrink-0">
            {userId?.charAt(0)?.toUpperCase() || "U"}
          </div>
          <span className="text-xs sm:text-sm text-surface-300 hidden sm:block
                           max-w-[80px] lg:max-w-[120px] truncate font-medium">
            {userId}
          </span>
        </div>

        {/* Notification bell */}
        <button
          onClick={handleBellClick}
          title={
            notifStatus === "granted" ? "Notifications active"
            : notifStatus === "denied" ? "Notifications blocked"
            : "Enable task reminders"
          }
          className={`p-1.5 rounded-lg transition-all duration-200
            ${notifStatus === "granted"
              ? "text-soul-400 bg-soul-600/10"
              : notifStatus === "denied"
              ? "text-surface-600 cursor-not-allowed"
              : "text-surface-500 hover:text-glow-400 hover:bg-glow-400/10"}`}>
          {notifStatus === "granted"
            ? <Bell size={14} className="fill-soul-400/30" />
            : <BellOff size={14} />}
        </button>

        {/* Voice Mode button */}
        <button
          onClick={onVoiceMode}
          title="Voice Mode — Coming Soon"
          className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl
                     bg-surface-800/60 border border-surface-700/50
                     text-surface-500 cursor-not-allowed
                     text-xs font-medium select-none opacity-60">
          <Mic size={13} />
          <span className="hidden lg:inline">Voice</span>
        </button>

        {/* Mobile drawer toggle */}
        <button
          onClick={onMobileDrawer}
          title="Tasks & Insights"
          className="md:hidden p-1.5 rounded-lg text-surface-500
                     hover:text-soul-400 hover:bg-surface-800
                     transition-all duration-200">
          <PanelRight size={16} />
        </button>

        {/* Logout */}
        {onLogout && (
          <>
            <div className="w-px h-5 bg-surface-700 hidden sm:block" />
            <button
              onClick={onLogout}
              title="Logout"
              className="p-1.5 rounded-lg text-surface-500 hover:text-red-400
                         hover:bg-red-400/10 transition-all duration-200">
              <LogOut size={14} />
            </button>
          </>
        )}
      </div>
    </header>
  );
}
