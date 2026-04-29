import { useState, useEffect, useCallback } from "react";
import { toast } from "react-hot-toast";
import { LayoutDashboard, MessageSquare, ChevronRight, X, SlidersHorizontal } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";

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
  const [mobileDrawer,   setMobileDrawer]     = useState(false);
  const [activeTab,      setActiveTab]        = useState("tasks");
  const [refreshTrigger, setRefreshTrigger]   = useState(0);
  const [prefill,        setPrefill]          = useState("");
  const [voiceModeOpen,  setVoiceModeOpen]    = useState(false);
  const [voiceComingSoon, setVoiceComingSoon] = useState(false);

  const userId = user?.user_id || "guest";

  useTaskReminder(user);

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

  // Close mobile drawer on resize to desktop
  useEffect(() => {
    const fn = () => { if (window.innerWidth >= 768) setMobileDrawer(false); };
    window.addEventListener("resize", fn);
    return () => window.removeEventListener("resize", fn);
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
        if (data.stored_fact.key === "name") {
          updateUser({ name: data.stored_fact.value });
        }
      }
      if (data.task_action) setRefreshTrigger(v => v + 1);
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
    setMobileDrawer(false);
    logout();
    navigate("/");
    toast.success("Logged out");
  };

  const handleVoiceMessageSent = (data) => {
    if (data.tasks_created?.length > 0 || data.stored_fact) {
      setRefreshTrigger(v => v + 1);
    }
  };

  const TABS = [
    { id: "tasks",    label: "Tasks",    icon: <LayoutDashboard size={13} /> },
    { id: "insights", label: "Insights", icon: <MessageSquare size={13} /> },
  ];

  const SidebarContent = () => (
    <>
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
    </>
  );

  return (
    <div className="flex flex-col h-screen bg-surface-950 overflow-hidden">
      <Header
        userId={user?.name || user?.email?.split("@")[0] || "User"}
        isConnected={isConnected}
        onLogout={handleLogout}
        onVoiceMode={() => setVoiceComingSoon(true)}
        onMobileDrawer={() => setMobileDrawer(v => !v)}
        user={user}
      />

      <NotificationBanner userId={userId} userName={user?.name || user?.email?.split("@")[0]} />

      <div className="flex flex-1 overflow-hidden relative">
        {/* ── Chat ─────────────────────────────────────── */}
        <div className="flex flex-col flex-1 overflow-hidden min-w-0">
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

        {/* ── Desktop sidebar toggle ────────────────────── */}
        <button
          onClick={() => setSidebarOpen(v => !v)}
          className="hidden md:flex absolute top-1/2 -translate-y-1/2 z-10
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

        {/* ── Desktop sidebar ───────────────────────────── */}
        {sidebarOpen && (
          <aside className="hidden md:flex w-72 lg:w-80 bg-surface-900 border-l border-surface-800
                            flex-col overflow-hidden shrink-0">
            <SidebarContent />
          </aside>
        )}
      </div>

      {/* ── Mobile drawer overlay ─────────────────────── */}
      <AnimatePresence>
        {mobileDrawer && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileDrawer(false)}
              className="md:hidden fixed inset-0 bg-black/60 z-40 backdrop-blur-sm"
            />
            {/* Drawer */}
            <motion.aside
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 28, stiffness: 300 }}
              className="md:hidden fixed right-0 top-0 bottom-0 w-[85vw] max-w-sm
                         bg-surface-900 border-l border-surface-800
                         flex flex-col overflow-hidden z-50 shadow-2xl">
              {/* Drawer header */}
              <div className="flex items-center justify-between px-4 py-3
                              border-b border-surface-800 shrink-0">
                <span className="text-sm font-semibold text-white">Dashboard</span>
                <button onClick={() => setMobileDrawer(false)}
                  className="p-1.5 rounded-lg text-surface-500 hover:text-white
                             hover:bg-surface-800 transition-colors">
                  <X size={16} />
                </button>
              </div>
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

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

      <VoiceComingSoon
        open={voiceComingSoon}
        onClose={() => setVoiceComingSoon(false)}
      />
    </div>
  );
}
