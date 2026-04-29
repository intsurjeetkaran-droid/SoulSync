/**
 * SoulSync AI — Voice Mode
 *
 * Full-screen overlay with animated sphere.
 * - Web Speech API for STT (no upload, instant)
 * - /api/v1/chat for AI response (full pipeline: memory, tasks, insights)
 * - /api/v1/voice/speak for TTS (pyttsx3 WAV)
 * - 10-minute session timer
 * - Animated sphere reacts to listening / thinking / speaking states
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Mic, MicOff, Volume2, VolumeX, RotateCcw } from "lucide-react";
import { sendMessage } from "../api/soulsync";
import axios from "axios";
import toast from "react-hot-toast";

const BASE = "http://localhost:8000/api/v1";
const SESSION_LIMIT = 10 * 60; // 10 minutes in seconds

// ── States ────────────────────────────────────────────────
const STATE = {
  IDLE      : "idle",       // waiting to start
  LISTENING : "listening",  // mic open, user speaking
  THINKING  : "thinking",   // sent to AI, waiting
  SPEAKING  : "speaking",   // AI audio playing
  PAUSED    : "paused",     // user paused mid-session
  EXPIRED   : "expired",    // 10 min limit reached
};

// ── Sphere color per state ────────────────────────────────
const SPHERE_COLORS = {
  idle     : { from: "#059669", to: "#047857", glow: "rgba(16,185,129,0.3)"  },
  listening: { from: "#10b981", to: "#34d399", glow: "rgba(52,211,153,0.6)"  },
  thinking : { from: "#f59e0b", to: "#fbbf24", glow: "rgba(251,191,36,0.5)"  },
  speaking : { from: "#8b5cf6", to: "#a78bfa", glow: "rgba(167,139,250,0.5)" },
  paused   : { from: "#6b7280", to: "#9ca3af", glow: "rgba(156,163,175,0.3)" },
  expired  : { from: "#ef4444", to: "#f87171", glow: "rgba(248,113,113,0.4)" },
};

const STATE_LABEL = {
  idle     : "Tap to start",
  listening: "Listening…",
  thinking : "Thinking…",
  speaking : "Speaking…",
  paused   : "Paused",
  expired  : "Session ended",
};

// ── Animated Sphere ───────────────────────────────────────
function Sphere({ state, onClick }) {
  const colors = SPHERE_COLORS[state] || SPHERE_COLORS.idle;
  const isActive = state === STATE.LISTENING || state === STATE.SPEAKING;
  const isThinking = state === STATE.THINKING;

  return (
    <div className="relative flex items-center justify-center cursor-pointer"
         onClick={onClick}>

      {/* Outer glow rings — pulse when active */}
      {[1, 2, 3].map(i => (
        <motion.div
          key={i}
          className="absolute rounded-full border"
          style={{
            width:  `${160 + i * 48}px`,
            height: `${160 + i * 48}px`,
            borderColor: colors.glow,
          }}
          animate={isActive ? {
            scale  : [1, 1.08, 1],
            opacity: [0.6 / i, 0.15 / i, 0.6 / i],
          } : isThinking ? {
            rotate : [0, 360],
            opacity: [0.3, 0.6, 0.3],
          } : {
            opacity: 0.15 / i,
          }}
          transition={isActive ? {
            duration: 1.4 + i * 0.3,
            repeat  : Infinity,
            ease    : "easeInOut",
            delay   : i * 0.2,
          } : isThinking ? {
            duration: 2 + i * 0.5,
            repeat  : Infinity,
            ease    : "linear",
          } : { duration: 0.5 }}
        />
      ))}

      {/* Main sphere */}
      <motion.div
        className="relative w-40 h-40 rounded-full flex items-center justify-center
                   select-none z-10"
        style={{
          background: `radial-gradient(circle at 35% 35%, ${colors.from}, ${colors.to})`,
          boxShadow : `0 0 60px ${colors.glow}, 0 0 120px ${colors.glow}40,
                       inset 0 2px 8px rgba(255,255,255,0.15)`,
        }}
        animate={isActive ? {
          scale: [1, 1.04, 1],
        } : isThinking ? {
          scale: [1, 1.02, 0.98, 1],
        } : {
          scale: 1,
        }}
        transition={isActive ? {
          duration: 0.8,
          repeat  : Infinity,
          ease    : "easeInOut",
        } : isThinking ? {
          duration: 1.2,
          repeat  : Infinity,
          ease    : "easeInOut",
        } : { duration: 0.3 }}
        whileHover={{ scale: state === STATE.IDLE || state === STATE.PAUSED ? 1.06 : 1 }}
        whileTap={{ scale: 0.95 }}
      >
        {/* Inner highlight */}
        <div className="absolute top-4 left-6 w-8 h-5 rounded-full
                        bg-white/20 blur-sm" />

        {/* Icon */}
        <motion.div
          animate={isThinking ? { rotate: [0, 10, -10, 0] } : {}}
          transition={{ duration: 1.5, repeat: Infinity }}
        >
          {state === STATE.LISTENING && <Mic size={36} className="text-white drop-shadow-lg" />}
          {state === STATE.THINKING  && (
            <div className="flex gap-1.5">
              {[0,1,2].map(i => (
                <motion.div key={i}
                  className="w-2.5 h-2.5 rounded-full bg-white"
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
                />
              ))}
            </div>
          )}
          {state === STATE.SPEAKING  && <Volume2 size={36} className="text-white drop-shadow-lg" />}
          {state === STATE.IDLE      && <Mic size={36} className="text-white/80 drop-shadow-lg" />}
          {state === STATE.PAUSED    && <MicOff size={36} className="text-white/60" />}
          {state === STATE.EXPIRED   && <RotateCcw size={32} className="text-white/80" />}
        </motion.div>
      </motion.div>

      {/* Sound wave bars — only when speaking */}
      {state === STATE.SPEAKING && (
        <div className="absolute bottom-0 flex items-end gap-1 h-8">
          {[3,5,8,6,4,7,5,3,6,4].map((h, i) => (
            <motion.div
              key={i}
              className="w-1 rounded-full bg-violet-400/70"
              animate={{ height: [`${h * 3}px`, `${h * 6}px`, `${h * 3}px`] }}
              transition={{ duration: 0.4 + i * 0.05, repeat: Infinity, ease: "easeInOut" }}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Timer ring ────────────────────────────────────────────
function TimerRing({ elapsed, limit }) {
  const pct     = Math.min(elapsed / limit, 1);
  const r       = 54;
  const circ    = 2 * Math.PI * r;
  const dash    = circ * (1 - pct);
  const mins    = Math.floor((limit - elapsed) / 60);
  const secs    = (limit - elapsed) % 60;
  const warning = elapsed > limit * 0.8;

  return (
    <div className="relative flex items-center justify-center w-32 h-32">
      <svg className="absolute inset-0 -rotate-90" width="128" height="128">
        <circle cx="64" cy="64" r={r} fill="none"
          stroke="rgba(255,255,255,0.08)" strokeWidth="4" />
        <motion.circle cx="64" cy="64" r={r} fill="none"
          stroke={warning ? "#f87171" : "#10b981"}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={dash}
          animate={{ strokeDashoffset: dash }}
          transition={{ duration: 0.5 }}
        />
      </svg>
      <div className="text-center z-10">
        <div className={`text-xl font-bold tabular-nums ${warning ? "text-red-400" : "text-white"}`}>
          {String(mins).padStart(2,"0")}:{String(secs).padStart(2,"0")}
        </div>
        <div className="text-[10px] text-surface-500 uppercase tracking-wider">left</div>
      </div>
    </div>
  );
}

// ── Main VoiceMode component ──────────────────────────────
export default function VoiceMode({ userId, onClose, onMessageSent }) {
  const [voiceState,    setVoiceState]    = useState(STATE.IDLE);
  const [elapsed,       setElapsed]       = useState(0);
  const [statusText,    setStatusText]    = useState("Tap the sphere to start");
  const [muted,         setMuted]         = useState(false);
  const [sessionActive, setSessionActive] = useState(false);
  const [lastExchange,  setLastExchange]  = useState(null); // {user, ai} — latest only

  const recognitionRef = useRef(null);
  const audioRef       = useRef(null);
  const timerRef       = useRef(null);
  const stateRef       = useRef(voiceState);
  stateRef.current     = voiceState;

  // ── Session timer ──────────────────────────────────────
  useEffect(() => {
    if (!sessionActive) return;
    timerRef.current = setInterval(() => {
      setElapsed(e => {
        if (e + 1 >= SESSION_LIMIT) {
          endSession("Time limit reached (10 min). Start a new session.");
          return SESSION_LIMIT;
        }
        return e + 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [sessionActive]);

  // ── Cleanup on unmount ─────────────────────────────────
  useEffect(() => {
    return () => {
      stopListening();
      clearInterval(timerRef.current);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  // ── Speech recognition setup ───────────────────────────
  const startListening = useCallback(() => {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
      toast.error("Speech recognition not supported. Use Chrome.");
      return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.lang = "en-US";
    rec.continuous = false;
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    rec.onstart  = () => {
      setVoiceState(STATE.LISTENING);
      setStatusText("Listening… speak now");
    };

    rec.onresult = async (e) => {
      const text = e.results[0][0].transcript.trim();
      if (!text) { startListening(); return; }
      setLastExchange({ user: text, ai: null });
      await handleUserSpeech(text);
    };

    rec.onerror = (e) => {
      if (e.error === "no-speech") {
        // Restart silently
        if (stateRef.current !== STATE.EXPIRED && stateRef.current !== STATE.PAUSED) {
          startListening();
        }
      } else {
        setStatusText(`Error: ${e.error}`);
        setVoiceState(STATE.PAUSED);
      }
    };

    rec.onend = () => {
      // If we're still in listening state (no result), restart
      if (stateRef.current === STATE.LISTENING) {
        startListening();
      }
    };

    recognitionRef.current = rec;
    rec.start();
  }, [userId]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch {}
      recognitionRef.current = null;
    }
  }, []);

  // ── Handle user speech → AI → TTS ─────────────────────
  const handleUserSpeech = useCallback(async (text) => {
    stopListening();
    setVoiceState(STATE.THINKING);
    setStatusText("Thinking…");

    try {
      // Send to full chat pipeline (memory, tasks, insights all work)
      const res  = await sendMessage(userId, text);
      const data = res.data;
      const aiText = data.response;

      setLastExchange(prev => ({ user: prev?.user || "", ai: aiText }));

      // Notify parent to refresh sidebar
      if (onMessageSent) onMessageSent(data);

      // Toast for task creation / memory storage
      if (data.tasks_created?.length > 0) {
        toast.success(`${data.tasks_created.length} task(s) created!`, { icon: "✅" });
      }
      if (data.stored_fact) {
        toast.success(`Remembered: ${data.stored_fact.key}`, { icon: "🧠" });
      }

      if (muted) {
        // Skip TTS, go straight back to listening
        setVoiceState(STATE.LISTENING);
        setStatusText("Listening…");
        startListening();
        return;
      }

      // TTS: get audio from backend
      setVoiceState(STATE.SPEAKING);
      setStatusText("Speaking…");

      const ttsRes = await axios.post(
        `${BASE}/voice/speak`,
        { text: aiText },
        { responseType: "arraybuffer", timeout: 30000 }
      );

      const blob = new Blob([ttsRes.data], { type: "audio/wav" });
      const url  = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;

      audio.onended = () => {
        URL.revokeObjectURL(url);
        audioRef.current = null;
        if (stateRef.current !== STATE.EXPIRED && stateRef.current !== STATE.PAUSED) {
          setVoiceState(STATE.LISTENING);
          setStatusText("Listening…");
          startListening();
        }
      };

      audio.onerror = () => {
        URL.revokeObjectURL(url);
        // TTS failed — continue without audio
        if (stateRef.current !== STATE.EXPIRED) {
          setVoiceState(STATE.LISTENING);
          startListening();
        }
      };

      audio.play().catch(() => {
        // Autoplay blocked — continue without audio
        setVoiceState(STATE.LISTENING);
        startListening();
      });

    } catch (err) {
      const msg = err.response?.data?.detail || "Connection error";
      toast.error(msg);
      setVoiceState(STATE.PAUSED);
      setStatusText("Error — tap to resume");
    }
  }, [userId, muted, startListening, stopListening, onMessageSent]);

  // ── Session control ────────────────────────────────────
  const startSession = useCallback(() => {
    setSessionActive(true);
    setElapsed(0);
    setLastExchange(null);
    startListening();
  }, [startListening]);

  const endSession = useCallback((msg = "Session ended") => {
    stopListening();
    clearInterval(timerRef.current);
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    setVoiceState(STATE.EXPIRED);
    setSessionActive(false);
    setStatusText(msg);
  }, [stopListening]);

  const pauseResume = useCallback(() => {
    if (voiceState === STATE.PAUSED) {
      setVoiceState(STATE.LISTENING);
      setStatusText("Listening…");
      startListening();
    } else if (voiceState === STATE.LISTENING) {
      stopListening();
      if (audioRef.current) { audioRef.current.pause(); }
      setVoiceState(STATE.PAUSED);
      setStatusText("Paused — tap to resume");
    }
  }, [voiceState, startListening, stopListening]);

  const handleSphereClick = useCallback(() => {
    if (voiceState === STATE.IDLE)    { startSession(); return; }
    if (voiceState === STATE.EXPIRED) { setVoiceState(STATE.IDLE); setElapsed(0); setLastExchange(null); setStatusText("Tap the sphere to start"); return; }
    pauseResume();
  }, [voiceState, startSession, pauseResume]);

  const toggleMute = () => {
    setMuted(v => !v);
    if (audioRef.current) audioRef.current.muted = !muted;
  };

  const colors = SPHERE_COLORS[voiceState] || SPHERE_COLORS.idle;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex flex-col items-center justify-between
                 bg-surface-950/97 backdrop-blur-2xl overflow-hidden"
    >
      {/* Background ambient glow */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        animate={{ opacity: [0.4, 0.7, 0.4] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        style={{
          background: `radial-gradient(ellipse 60% 50% at 50% 60%, ${colors.glow}, transparent)`,
        }}
      />

      {/* ── Top bar ──────────────────────────────────────── */}
      <div className="w-full flex items-center justify-between px-6 pt-6 z-10">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-soul-400 animate-pulse" />
          <span className="text-sm font-semibold text-white tracking-wide">
            Voice Mode
          </span>
          {sessionActive && (
            <span className="text-xs text-surface-500 bg-surface-800/60
                             px-2 py-0.5 rounded-full border border-surface-700/50">
              Session active
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Mute toggle */}
          <button
            onClick={toggleMute}
            className={`p-2 rounded-xl border transition-all duration-200
                        ${muted
                          ? "bg-red-500/15 border-red-500/30 text-red-400"
                          : "bg-surface-800/60 border-surface-700/50 text-surface-400 hover:text-white"}`}
            title={muted ? "Unmute AI voice" : "Mute AI voice"}
          >
            {muted ? <VolumeX size={16} /> : <Volume2 size={16} />}
          </button>

          {/* Close */}
          <button
            onClick={() => { endSession(); onClose(); }}
            className="p-2 rounded-xl bg-surface-800/60 border border-surface-700/50
                       text-surface-400 hover:text-white hover:bg-surface-700
                       transition-all duration-200"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* ── Last exchange — subtle text only, no bubbles ── */}
      <div className="flex-1 w-full max-w-sm px-6 flex flex-col
                      items-center justify-end pb-4 z-10 gap-3">
        <AnimatePresence mode="wait">
          {lastExchange?.user && (
            <motion.p
              key={lastExchange.user}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 0.5, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="text-xs text-surface-500 text-center italic truncate w-full"
            >
              You: "{lastExchange.user.slice(0, 80)}{lastExchange.user.length > 80 ? "…" : ""}"
            </motion.p>
          )}
          {lastExchange?.ai && (
            <motion.p
              key={lastExchange.ai}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 0.7, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3, delay: 0.1 }}
              className="text-xs text-surface-300 text-center leading-relaxed line-clamp-2 w-full"
            >
              {lastExchange.ai.slice(0, 120)}{lastExchange.ai.length > 120 ? "…" : ""}
            </motion.p>
          )}
          {!lastExchange && voiceState === STATE.IDLE && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-xs text-surface-600 text-center"
            >
              Your conversation will appear here
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      {/* ── Sphere + timer ────────────────────────────────── */}
      <div className="flex flex-col items-center gap-8 pb-10 z-10">
        {/* Timer ring — only when session active */}
        {sessionActive && (
          <TimerRing elapsed={elapsed} limit={SESSION_LIMIT} />
        )}

        {/* Sphere */}
        <Sphere state={voiceState} onClick={handleSphereClick} />

        {/* Status label */}
        <motion.p
          key={statusText}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-surface-400 font-medium tracking-wide"
        >
          {statusText}
        </motion.p>

        {/* Controls row */}
        <div className="flex items-center gap-4">
          {sessionActive && voiceState !== STATE.EXPIRED && (
            <button
              onClick={pauseResume}
              className="px-5 py-2 rounded-xl bg-surface-800/70 border border-surface-700/50
                         text-surface-300 hover:text-white hover:bg-surface-700
                         text-sm font-medium transition-all duration-200"
            >
              {voiceState === STATE.PAUSED ? "Resume" : "Pause"}
            </button>
          )}

          {voiceState === STATE.EXPIRED && (
            <button
              onClick={() => { setVoiceState(STATE.IDLE); setElapsed(0); setTranscript([]); setStatusText("Tap the sphere to start"); }}
              className="px-6 py-2.5 rounded-xl bg-soul-600 hover:bg-soul-500
                         text-white text-sm font-semibold transition-all duration-200
                         flex items-center gap-2"
            >
              <RotateCcw size={14} /> New Session
            </button>
          )}

          {sessionActive && (
            <button
              onClick={() => endSession("Session ended manually")}
              className="px-5 py-2 rounded-xl bg-red-500/10 border border-red-500/20
                         text-red-400 hover:bg-red-500/20 text-sm font-medium
                         transition-all duration-200"
            >
              End Session
            </button>
          )}
        </div>

        {/* Hint */}
        {voiceState === STATE.IDLE && (
          <p className="text-xs text-surface-600 text-center max-w-xs">
            Tap the sphere to start · All commands, memory, tasks and insights work in voice mode
          </p>
        )}
      </div>
    </motion.div>
  );
}
