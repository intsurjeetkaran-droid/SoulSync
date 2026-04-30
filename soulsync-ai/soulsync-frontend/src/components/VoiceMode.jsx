/**
 * SoulSync AI — Voice Mode (Alexa-style)
 *
 * Pure voice experience — no chat bubbles, no sidebar.
 * Tap sphere → it listens → thinks → speaks back → listens again.
 * Exactly like talking to Alexa.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Volume2, VolumeX, RotateCcw } from "lucide-react";
import { sendMessage } from "../api/soulsync";
import axios from "axios";
import toast from "react-hot-toast";

const BASE          = import.meta.env.VITE_API_URL || "http://localhost:8000";
const SESSION_LIMIT = 10 * 60;

const STATE = {
  IDLE      : "idle",
  LISTENING : "listening",
  THINKING  : "thinking",
  SPEAKING  : "speaking",
  PAUSED    : "paused",
  EXPIRED   : "expired",
};

const SPHERE_COLORS = {
  idle     : { from: "#059669", to: "#047857", glow: "rgba(16,185,129,0.25)" },
  listening: { from: "#10b981", to: "#34d399", glow: "rgba(52,211,153,0.55)" },
  thinking : { from: "#f59e0b", to: "#fbbf24", glow: "rgba(251,191,36,0.45)" },
  speaking : { from: "#8b5cf6", to: "#a78bfa", glow: "rgba(167,139,250,0.55)"},
  paused   : { from: "#6b7280", to: "#9ca3af", glow: "rgba(156,163,175,0.2)" },
  expired  : { from: "#ef4444", to: "#f87171", glow: "rgba(248,113,113,0.35)"},
};

const STATUS_TEXT = {
  idle     : "Tap to start",
  listening: "Listening…",
  thinking : "Thinking…",
  speaking : "Speaking…",
  paused   : "Paused — tap to resume",
  expired  : "Session ended — tap to restart",
};

// ── Animated Sphere ───────────────────────────────────────
function Sphere({ state, onClick }) {
  const c         = SPHERE_COLORS[state] || SPHERE_COLORS.idle;
  const isActive  = state === STATE.LISTENING || state === STATE.SPEAKING;
  const isThink   = state === STATE.THINKING;

  return (
    <div className="relative flex items-center justify-center cursor-pointer select-none"
         onClick={onClick}>

      {/* Glow rings */}
      {[1, 2, 3, 4].map(i => (
        <motion.div key={i}
          className="absolute rounded-full"
          style={{
            width : `${200 + i * 60}px`,
            height: `${200 + i * 60}px`,
            border: `1px solid ${c.glow}`,
          }}
          animate={isActive ? {
            scale  : [1, 1.06 + i * 0.01, 1],
            opacity: [0.5 / i, 0.1 / i, 0.5 / i],
          } : isThink ? {
            rotate : [0, 360],
            opacity: [0.25, 0.5, 0.25],
          } : { opacity: 0.1 / i }}
          transition={isActive ? {
            duration: 1.6 + i * 0.35, repeat: Infinity, ease: "easeInOut", delay: i * 0.2,
          } : isThink ? {
            duration: 2.5 + i * 0.4, repeat: Infinity, ease: "linear",
          } : { duration: 0.6 }}
        />
      ))}

      {/* Main sphere */}
      <motion.div
        className="relative w-52 h-52 rounded-full flex items-center justify-center z-10"
        style={{
          background: `radial-gradient(circle at 35% 30%, ${c.from}, ${c.to})`,
          boxShadow : `0 0 80px ${c.glow}, 0 0 160px ${c.glow}50,
                       inset 0 3px 12px rgba(255,255,255,0.18)`,
        }}
        animate={isActive  ? { scale: [1, 1.04, 1] }
               : isThink   ? { scale: [1, 1.02, 0.98, 1] }
               : { scale: 1 }}
        transition={isActive ? { duration: 0.9, repeat: Infinity, ease: "easeInOut" }
                  : isThink  ? { duration: 1.3, repeat: Infinity, ease: "easeInOut" }
                  : { duration: 0.4 }}
        whileHover={{ scale: [STATE.IDLE, STATE.PAUSED, STATE.EXPIRED].includes(state) ? 1.05 : 1 }}
        whileTap={{ scale: 0.96 }}
      >
        {/* Highlight */}
        <div className="absolute top-6 left-8 w-10 h-6 rounded-full bg-white/20 blur-md" />

        {/* Listening — sound wave bars */}
        {state === STATE.LISTENING && (
          <div className="flex items-end gap-1.5 h-12">
            {[4,7,11,9,6,10,8,5,9,7,4].map((h, i) => (
              <motion.div key={i}
                className="w-1.5 rounded-full bg-white/90"
                animate={{ height: [`${h * 3}px`, `${h * 6}px`, `${h * 3}px`] }}
                transition={{ duration: 0.35 + i * 0.04, repeat: Infinity, ease: "easeInOut", delay: i * 0.06 }}
              />
            ))}
          </div>
        )}

        {/* Thinking — bouncing dots */}
        {state === STATE.THINKING && (
          <div className="flex gap-2.5">
            {[0, 1, 2].map(i => (
              <motion.div key={i}
                className="w-3.5 h-3.5 rounded-full bg-white/90"
                animate={{ y: [0, -12, 0] }}
                transition={{ duration: 0.65, repeat: Infinity, delay: i * 0.18 }}
              />
            ))}
          </div>
        )}

        {/* Speaking — radiate rings */}
        {state === STATE.SPEAKING && (
          <div className="relative flex items-center justify-center">
            {[0, 1, 2].map(i => (
              <motion.div key={i}
                className="absolute rounded-full border-2 border-white/40"
                animate={{ scale: [1, 2.2], opacity: [0.6, 0] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.4, ease: "easeOut" }}
                style={{ width: "40px", height: "40px" }}
              />
            ))}
            <Volume2 size={36} className="text-white/90 drop-shadow-lg relative z-10" />
          </div>
        )}

        {/* Idle */}
        {(state === STATE.IDLE || state === STATE.PAUSED || state === STATE.EXPIRED) && (
          <motion.div
            animate={{ scale: [1, 1.08, 1], opacity: [0.7, 1, 0.7] }}
            transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }}
          >
            {state === STATE.EXPIRED
              ? <RotateCcw size={40} className="text-white/80" />
              : <svg width="44" height="44" viewBox="0 0 24 24" fill="none">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"
                        fill="rgba(255,255,255,0.85)" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2M12 19v4M8 23h8"
                        stroke="rgba(255,255,255,0.85)" strokeWidth="2"
                        strokeLinecap="round" strokeLinejoin="round" />
                </svg>
            }
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}

// ── Timer arc (minimal, top-right) ────────────────────────
function TimerArc({ elapsed, limit }) {
  const pct     = Math.min(elapsed / limit, 1);
  const r       = 18;
  const circ    = 2 * Math.PI * r;
  const offset  = circ * (1 - pct);
  const mins    = Math.floor((limit - elapsed) / 60);
  const secs    = (limit - elapsed) % 60;
  const warn    = elapsed > limit * 0.8;

  return (
    <div className="relative flex items-center justify-center w-12 h-12">
      <svg className="absolute inset-0 -rotate-90" width="48" height="48">
        <circle cx="24" cy="24" r={r} fill="none"
          stroke="rgba(255,255,255,0.07)" strokeWidth="3" />
        <motion.circle cx="24" cy="24" r={r} fill="none"
          stroke={warn ? "#f87171" : "#10b981"}
          strokeWidth="3" strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.5 }} />
      </svg>
      <span className={`text-[9px] font-bold tabular-nums z-10
                        ${warn ? "text-red-400" : "text-white/70"}`}>
        {String(mins).padStart(2,"0")}:{String(secs).padStart(2,"0")}
      </span>
    </div>
  );
}

// ── Main component ────────────────────────────────────────
export default function VoiceMode({ userId, onClose, onMessageSent }) {
  const [voiceState,    setVoiceState]    = useState(STATE.IDLE);
  const [elapsed,       setElapsed]       = useState(0);
  const [muted,         setMuted]         = useState(false);
  const [sessionActive, setSessionActive] = useState(false);

  const recognitionRef = useRef(null);
  const audioRef       = useRef(null);
  const timerRef       = useRef(null);
  const stateRef       = useRef(voiceState);
  stateRef.current     = voiceState;

  // Session timer
  useEffect(() => {
    if (!sessionActive) return;
    timerRef.current = setInterval(() => {
      setElapsed(e => {
        if (e + 1 >= SESSION_LIMIT) {
          endSession();
          return SESSION_LIMIT;
        }
        return e + 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [sessionActive]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopListening();
      clearInterval(timerRef.current);
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    };
  }, []);

  // ── STT ───────────────────────────────────────────────
  const startListening = useCallback(() => {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
      toast.error("Speech recognition not supported. Use Chrome.");
      return;
    }
    const SR  = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.lang            = "en-US";
    rec.continuous      = false;
    rec.interimResults  = false;
    rec.maxAlternatives = 1;

    rec.onstart  = () => setVoiceState(STATE.LISTENING);

    rec.onresult = async (e) => {
      const text = e.results[0][0].transcript.trim();
      if (!text) { startListening(); return; }
      await handleUserSpeech(text);
    };

    rec.onerror = (e) => {
      if (e.error === "no-speech") {
        if (stateRef.current !== STATE.EXPIRED && stateRef.current !== STATE.PAUSED)
          startListening();
      } else {
        setVoiceState(STATE.PAUSED);
      }
    };

    rec.onend = () => {
      if (stateRef.current === STATE.LISTENING) startListening();
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

  // ── AI + TTS ──────────────────────────────────────────
  const handleUserSpeech = useCallback(async (text) => {
    stopListening();
    setVoiceState(STATE.THINKING);

    try {
      const res    = await sendMessage(userId, text);
      const data   = res.data;
      const aiText = data.response;

      if (onMessageSent) onMessageSent(data);

      if (muted) {
        setVoiceState(STATE.LISTENING);
        startListening();
        return;
      }

      setVoiceState(STATE.SPEAKING);

      const ttsRes = await axios.post(
        `${BASE}/api/v1/voice/speak`,
        { text: aiText },
        { responseType: "arraybuffer", timeout: 30000 }
      );

      const blob  = new Blob([ttsRes.data], { type: "audio/wav" });
      const url   = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;

      audio.onended = () => {
        URL.revokeObjectURL(url);
        audioRef.current = null;
        if (stateRef.current !== STATE.EXPIRED && stateRef.current !== STATE.PAUSED) {
          setVoiceState(STATE.LISTENING);
          startListening();
        }
      };

      audio.onerror = () => {
        URL.revokeObjectURL(url);
        if (stateRef.current !== STATE.EXPIRED) {
          setVoiceState(STATE.LISTENING);
          startListening();
        }
      };

      audio.play().catch(() => {
        setVoiceState(STATE.LISTENING);
        startListening();
      });

    } catch (err) {
      toast.error(err.response?.data?.detail || "Connection error");
      setVoiceState(STATE.PAUSED);
    }
  }, [userId, muted, startListening, stopListening, onMessageSent]);

  // ── Session control ───────────────────────────────────
  const startSession = useCallback(() => {
    setSessionActive(true);
    setElapsed(0);
    startListening();
  }, [startListening]);

  const endSession = useCallback(() => {
    stopListening();
    clearInterval(timerRef.current);
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    setVoiceState(STATE.EXPIRED);
    setSessionActive(false);
  }, [stopListening]);

  const pauseResume = useCallback(() => {
    if (voiceState === STATE.PAUSED) {
      setVoiceState(STATE.LISTENING);
      startListening();
    } else if (voiceState === STATE.LISTENING) {
      stopListening();
      if (audioRef.current) audioRef.current.pause();
      setVoiceState(STATE.PAUSED);
    }
  }, [voiceState, startListening, stopListening]);

  const handleSphereClick = useCallback(() => {
    if (voiceState === STATE.IDLE)    { startSession(); return; }
    if (voiceState === STATE.EXPIRED) {
      setVoiceState(STATE.IDLE);
      setElapsed(0);
      return;
    }
    pauseResume();
  }, [voiceState, startSession, pauseResume]);

  const toggleMute = () => {
    setMuted(v => !v);
    if (audioRef.current) audioRef.current.muted = !muted;
  };

  const c = SPHERE_COLORS[voiceState] || SPHERE_COLORS.idle;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex flex-col bg-[#080c10] overflow-hidden"
    >
      {/* Full-screen ambient glow that reacts to state */}
      <motion.div
        className="absolute inset-0 pointer-events-none"
        animate={{ opacity: [0.5, 0.8, 0.5] }}
        transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
        style={{
          background: `radial-gradient(ellipse 70% 60% at 50% 55%, ${c.glow}, transparent)`,
        }}
      />

      {/* ── Top bar — minimal ─────────────────────────── */}
      <div className="flex items-center justify-between px-6 pt-5 shrink-0 z-10">
        <div className="flex items-center gap-2.5">
          <motion.div
            className="w-2 h-2 rounded-full bg-soul-400"
            animate={{ opacity: sessionActive ? [1, 0.3, 1] : 1 }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
          <span className="text-sm font-semibold text-white/80 tracking-wide">
            SoulSync
          </span>
        </div>

        <div className="flex items-center gap-2">
          {sessionActive && <TimerArc elapsed={elapsed} limit={SESSION_LIMIT} />}

          <button onClick={toggleMute}
            className={`p-2 rounded-xl border transition-all duration-200
                        ${muted
                          ? "bg-red-500/15 border-red-500/30 text-red-400"
                          : "bg-white/5 border-white/10 text-white/40 hover:text-white/70"}`}>
            {muted ? <VolumeX size={15} /> : <Volume2 size={15} />}
          </button>

          <button onClick={() => { endSession(); onClose(); }}
            className="p-2 rounded-xl bg-white/5 border border-white/10
                       text-white/40 hover:text-white/70 transition-all duration-200">
            <X size={15} />
          </button>
        </div>
      </div>

      {/* ── Centre — sphere only ──────────────────────── */}
      <div className="flex-1 flex flex-col items-center justify-center gap-10 z-10">
        <Sphere state={voiceState} onClick={handleSphereClick} />

        {/* Status label */}
        <AnimatePresence mode="wait">
          <motion.p
            key={voiceState}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.3 }}
            className="text-sm font-medium tracking-widest uppercase text-white/40"
          >
            {STATUS_TEXT[voiceState]}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* ── Bottom — only End Session when active ─────── */}
      <div className="flex justify-center pb-10 shrink-0 z-10">
        {sessionActive && voiceState !== STATE.EXPIRED && (
          <button onClick={endSession}
            className="px-6 py-2 rounded-full bg-white/5 border border-white/10
                       text-white/40 hover:text-white/70 hover:bg-white/10
                       text-xs font-medium tracking-wider uppercase
                       transition-all duration-200">
            End Session
          </button>
        )}
      </div>
    </motion.div>
  );
}
