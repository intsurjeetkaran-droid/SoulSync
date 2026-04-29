import { useState, useEffect, useCallback } from "react";
import { toast } from "react-hot-toast";
import { LayoutDashboard, MessageSquare, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence } from "framer-motion";

import Header              from "./components/Header";
import ChatWindow          from "./components/ChatWindow";
import ChatInput           from "./components/ChatInput";
import TaskPanel           from "./components/TaskPanel";
import InsightPanel        from "./components/InsightPanel";
import VoiceMode           from "./components/VoiceMode";
import NotificationBanner  from "./components/NotificationBanner";
import VoiceComingSoon     from "./components/VoiceComingSoon";
import useTaskReminder     from "./hooks/useTaskReminder";
import { sendMessage } from "./api/soulsync";
import { useAuth } from "./context/AuthContext";

const now = () =>
  new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

export default function App() {
  const { user, logout, updateUser }            = useAuth();
  const navigate                              = useNavigate();
  const [messages,       setMessages]         = useState([]);
  const [isTyping,       setIsTyping]         = useState(false);
  const [isConnected,    setIsConnected]      = useState(false);
  const [sidebarOpen,    setSidebarOpen]      = useState(true);
  const [activeTab,      setActiveTab]        = useState("tasks");
  const [refreshTrigger, setRefreshTrigger]   = useState(0);
  const [prefill,        setPrefill]          = useState("");
  const [voiceModeOpen,  setVoiceModeOpen]    = useState(false);
  const [voiceComingSoon, setVoiceComingSoon] = useState(false);

  const userId = user?.user_id || "guest";

  // ── Start task reminder scheduler when logged in ───────
  useTaskReminder(user);

  // ── Reset all session state when user identity changes ──
  // This is a safety net on top of the key-based remount in main.jsx.
  // Covers edge cases like token refresh restoring a different user.
  useEffect(() => {
    setMessages([]);
    setPrefill("");
    setRefreshTrigger(0);
    setActiveTab("tasks");
  }, [userId]);

  useEffect(() => {
    fetch("http://localhost:8000/")
      .then(() => setIsConnected(true))
      .catch(() => {
        setIsConnected(false);
        toast.error("Backend offline. Start the server first.", { duration: 5000 });
      });
  }, []);

  const handleSend = useCallback(async (text) => {
    setPrefill("");
    setMessages(prev => [...prev, { role: "user", text, time: now() }]);
    setIsTyping(true);

    try {
      const res  = await sendMessage(userId, text);
      const data = res.data;

      setMessages(prev => [...prev, {
        role    : "assistant",
        text    : data.response,
        time    : now(),
        memories: data.retrieved_memories || [],
        tasks   : data.tasks_created      || [],
        intent  : data.intent,
      }]);

      if (data.tasks_created?.length > 0) {
        toast.success(
          `${data.tasks_created.length} task${data.tasks_created.length > 1 ? "s" : ""} created!`,
          { icon: "✅" }
        );
        setRefreshTrigger(v => v + 1);
      }
      if (data.stored_fact) {
        toast.success(
          `Remembered: ${data.stored_fact.key} → ${data.stored_fact.value}`,
          { icon: "🧠" }
        );
        // If name was updated via chat → reflect instantly in header
        if (data.stored_fact.key === "name") {
          updateUser({ name: data.stored_fact.value });
        }
      }
      // Refresh task panel on any task operation
      if (data.task_action) {
        setRefreshTrigger(v => v + 1);
      }
      setRefreshTrigger(v => v + 1);

    } catch (err) {
      const msg = err.response?.data?.detail || "Connection error.";
      toast.error(msg);
      setMessages(prev => [...prev, {
        role: "assistant",
        text: "⚠️ Couldn't reach the server. Is the backend running?",
        time: now(),
      }]);
    } finally {
      setIsTyping(false);
    }
  }, [userId]);

  const handleLogout = () => {
    setMessages([]);
    setPrefill("");
    setVoiceModeOpen(false);
    logout();
    navigate("/");
    toast.success("Logged out");
  };

  const handleVoiceMessageSent = (data) => {
    // Voice mode sent a message — refresh sidebar
    if (data.tasks_created?.length > 0 || data.stored_fact) {
      setRefreshTrigger(v => v + 1);
    }
  };

  const TABS = [
    { id: "tasks",    label: "Tasks",    icon: <LayoutDashboard size={13} /> },
    { id: "insights", label: "Insights", icon: <MessageSquare size={13} /> },
  ];

  return (
    <div className="flex flex-col h-screen bg-surface-950 overflow-hidden">
      <Header
        userId={user?.name || user?.email?.split("@")[0] || "User"}
        isConnected={isConnected}
        onLogout={handleLogout}
        onVoiceMode={() => setVoiceComingSoon(true)}
        user={user}
      />

      {/* Notification permission banner */}
      <NotificationBanner userId={userId} userName={user?.name || user?.email?.split("@")[0]} />

      <div className="flex flex-1 overflow-hidden relative">
        {/* ── Chat ─────────────────────────────────────── */}
        <div className="flex flex-col flex-1 overflow-hidden">
          <ChatWindow
            messages={messages}
            isTyping={isTyping}
            onSuggestion={setPrefill}
          />
          <ChatInput
            onSend={handleSend}
            isLoading={isTyping}
            prefill={prefill}
          />
        </div>

        {/* ── Sidebar toggle tab ────────────────────────── */}
        <button
          onClick={() => setSidebarOpen(v => !v)}
          className="hidden sm:flex absolute top-1/2 -translate-y-1/2 z-10
                     w-5 h-12 bg-surface-800 border border-surface-700
                     rounded-l-lg items-center justify-center
                     text-surface-500 hover:text-soul-400
                     hover:bg-surface-700 transition-all duration-200"
          style={{ right: sidebarOpen ? "320px" : "0" }}>
          <ChevronRight
            size={12}
            className={`transition-transform duration-200 ${sidebarOpen ? "rotate-0" : "rotate-180"}`}
          />
        </button>

        {/* ── Sidebar ───────────────────────────────────── */}
        {sidebarOpen && (
          <aside className="w-80 bg-surface-900 border-l border-surface-800
                            flex flex-col overflow-hidden shrink-0">
            {/* Tab bar */}
            <div className="flex border-b border-surface-800 shrink-0 px-1 pt-1">
              {TABS.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex-1 flex items-center justify-center gap-1.5
                              py-2.5 text-xs font-medium rounded-t-lg
                              transition-all duration-200
                              ${activeTab === tab.id
                                ? "text-soul-300 bg-surface-800 border-b-2 border-soul-500"
                                : "text-surface-500 hover:text-surface-300 hover:bg-surface-800/50"}`}>
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab content */}
            <div className="flex-1 overflow-hidden p-4">
              {activeTab === "tasks"    && <TaskPanel    userId={userId} refreshTrigger={refreshTrigger} />}
              {activeTab === "insights" && <InsightPanel userId={userId} refreshTrigger={refreshTrigger} />}
            </div>
          </aside>
        )}
      </div>

      {/* ── Voice Mode overlay ────────────────────────── */}
      <AnimatePresence>
        {voiceModeOpen && (
          <VoiceMode
            userId={userId}
            onClose={() => setVoiceModeOpen(false)}
            onMessageSent={handleVoiceMessageSent}
          />
        )}
      </AnimatePresence>

      {/* ── Voice Coming Soon dialog (portal) ─────────── */}
      <VoiceComingSoon
        open={voiceComingSoon}
        onClose={() => setVoiceComingSoon(false)}
      />
    </div>
  );
}
