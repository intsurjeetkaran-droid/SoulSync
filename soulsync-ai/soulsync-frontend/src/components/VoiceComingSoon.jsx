/**
 * SoulSync AI — Voice Mode Coming Soon Dialog
 * Renders as a full-screen portal overlay above the entire app.
 * Backdrop blurs the chat window behind it.
 */

import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Sparkles, X, Zap } from "lucide-react";

const FEATURES = [
  { icon: "🎙️", label: "Speak naturally" },
  { icon: "🧠", label: "Memory recall"   },
  { icon: "✅", label: "Task creation"   },
  { icon: "💡", label: "Live insights"   },
];

function Modal({ onClose }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.22 }}
      className="fixed inset-0 z-[9999] flex items-center justify-center px-5"
      onClick={onClose}
    >
      {/* ── Blurred backdrop ─────────────────────────── */}
      <div className="absolute inset-0 bg-surface-950/75 backdrop-blur-md" />

      {/* ── Card ─────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, scale: 0.86, y: 28 }}
        animate={{ opacity: 1, scale: 1,    y: 0   }}
        exit={{    opacity: 0, scale: 0.93,  y: 14  }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 w-full max-w-[360px] overflow-hidden
                   bg-surface-900 border border-surface-700/70
                   rounded-3xl shadow-2xl shadow-black/70"
        onClick={e => e.stopPropagation()}
      >
        {/* Ambient top glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2
                        w-72 h-36 bg-soul-500/12 rounded-full blur-3xl
                        pointer-events-none" />
        {/* Ambient bottom glow */}
        <div className="absolute bottom-0 right-0
                        w-48 h-48 bg-glow-500/8 rounded-full blur-3xl
                        pointer-events-none" />

        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 p-1.5 rounded-xl
                     text-surface-500 hover:text-white hover:bg-surface-800/80
                     transition-all duration-200">
          <X size={16} />
        </button>

        <div className="relative z-10 px-8 pt-8 pb-7 flex flex-col items-center text-center">

          {/* Icon cluster */}
          <div className="relative mb-6">
            <div className="w-[76px] h-[76px] rounded-[22px]
                            bg-gradient-to-br from-soul-600/25 to-soul-800/25
                            border border-soul-500/30
                            flex items-center justify-center
                            shadow-lg shadow-soul-900/30">
              <Mic size={32} className="text-soul-400" />
            </div>
            {/* Gold sparkle badge */}
            <div className="absolute -top-1.5 -right-1.5
                            w-7 h-7 rounded-full
                            bg-gradient-to-br from-glow-400 to-glow-600
                            flex items-center justify-center
                            shadow-md shadow-glow-900/50 border-2 border-surface-900">
              <Sparkles size={12} className="text-surface-950" />
            </div>
          </div>

          {/* Title */}
          <h2 className="text-[22px] font-bold text-white tracking-tight mb-2">
            Voice Mode
          </h2>

          {/* Coming soon badge */}
          <div className="inline-flex items-center gap-1.5
                          bg-glow-500/12 border border-glow-500/30
                          rounded-full px-3.5 py-1 mb-5">
            <Zap size={11} className="text-glow-400" />
            <span className="text-[11px] font-bold text-glow-300
                             uppercase tracking-widest">
              Coming Soon
            </span>
          </div>

          {/* Description */}
          <p className="text-surface-400 text-[13.5px] leading-relaxed mb-6 max-w-[280px]">
            We're crafting a hands-free experience — talk to SoulSync AI
            naturally and everything works through your voice.
          </p>

          {/* Feature pills */}
          <div className="grid grid-cols-2 gap-2 w-full mb-7">
            {FEATURES.map(f => (
              <div key={f.label}
                className="flex items-center gap-2 bg-surface-800/70
                           border border-surface-700/50 rounded-xl
                           px-3 py-2.5">
                <span className="text-base leading-none">{f.icon}</span>
                <span className="text-[12px] text-surface-300 font-medium">
                  {f.label}
                </span>
              </div>
            ))}
          </div>

          {/* CTA button */}
          <button
            onClick={onClose}
            className="w-full py-3.5 rounded-2xl font-semibold text-sm text-white
                       bg-gradient-to-r from-soul-600 to-soul-700
                       hover:from-soul-500 hover:to-soul-600
                       active:scale-[0.98] transition-all duration-200
                       shadow-lg shadow-soul-900/50">
            Got it, can't wait! 🚀
          </button>

          <p className="text-[11px] text-surface-600 mt-3">
            Tap anywhere outside to close
          </p>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function VoiceComingSoon({ open, onClose }) {
  return createPortal(
    <AnimatePresence>
      {open && <Modal onClose={onClose} />}
    </AnimatePresence>,
    document.body
  );
}
