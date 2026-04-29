import { useEffect, useRef } from "react";
import { Brain, User, Zap, CheckSquare, Sparkles, BookMarked } from "lucide-react";
import MessageRenderer from "./MessageRenderer";

const INTENT_BADGE = {
  personal_info_store : { label: "Saved",    color: "text-soul-400  bg-soul-900/40  border-soul-700/40"  },
  personal_info_query : { label: "Recalled", color: "text-glow-400  bg-glow-900/30  border-glow-700/40"  },
  task_command        : { label: "Task",     color: "text-emerald-400 bg-emerald-900/30 border-emerald-700/40" },
  normal_chat         : null,
  conversation        : null,
};

function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  const badge  = !isUser && msg.intent ? INTENT_BADGE[msg.intent] : null;

  return (
    <div className={`flex gap-2 sm:gap-3 animate-slide-up ${isUser ? "flex-row-reverse" : "flex-row"}`}>

      {/* Avatar */}
      <div className={`w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center
                       shrink-0 mt-1 shadow-sm
                       ${isUser
                         ? "bg-gradient-to-br from-glow-500 to-glow-700"
                         : "bg-surface-800 border border-surface-700"}`}>
        {isUser
          ? <User size={12} className="text-surface-950" />
          : <Brain size={12} className="text-soul-400" />}
      </div>

      {/* Content column */}
      <div className={`max-w-[85%] sm:max-w-[78%] flex flex-col gap-1.5
                       ${isUser ? "items-end" : "items-start"}`}>

        {/* Bubble */}
        <div className={`w-full rounded-2xl text-sm
          ${isUser
            ? "bg-gradient-to-br from-soul-600 to-soul-700 text-white rounded-tr-sm shadow-md shadow-soul-900/30 px-3 sm:px-4 py-2.5 sm:py-3"
            : "bg-surface-800/90 text-surface-100 rounded-tl-sm border border-surface-700/60 px-3 sm:px-4 py-2.5 sm:py-3"}`}>
          {isUser
            ? <p className="leading-relaxed text-sm">{msg.text}</p>
            : <MessageRenderer text={msg.text} />
          }
        </div>

        {/* Meta row */}
        <div className="flex items-center gap-1.5 flex-wrap px-1">
          {badge && (
            <span className={`inline-flex items-center gap-1 text-[10px] font-medium
                              px-2 py-0.5 rounded-full border ${badge.color}`}>
              <BookMarked size={9} />
              {badge.label}
            </span>
          )}
          {msg.memories?.length > 0 && (
            <span className="inline-flex items-center gap-1 text-[10px]
                             text-glow-400/80 bg-glow-900/20 border border-glow-700/30
                             px-2 py-0.5 rounded-full">
              <Zap size={9} />
              {msg.memories.length} memor{msg.memories.length > 1 ? "ies" : "y"}
            </span>
          )}
          {msg.tasks?.length > 0 && (
            <span className="inline-flex items-center gap-1 text-[10px]
                             text-emerald-400/80 bg-emerald-900/20 border border-emerald-700/30
                             px-2 py-0.5 rounded-full">
              <CheckSquare size={9} />
              {msg.tasks.length} task{msg.tasks.length > 1 ? "s" : ""}
            </span>
          )}
          <span className="text-[10px] text-surface-600 ml-auto">{msg.time}</span>
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-2 sm:gap-3 animate-fade-in">
      <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-surface-800 border border-surface-700
                      flex items-center justify-center shrink-0">
        <Brain size={12} className="text-soul-400" />
      </div>
      <div className="bg-surface-800 border border-surface-700 rounded-2xl rounded-tl-sm
                      px-4 py-3 flex items-center gap-1.5">
        {[0, 1, 2].map(i => (
          <span key={i}
            className="w-2 h-2 bg-soul-500 rounded-full animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }} />
        ))}
      </div>
    </div>
  );
}

const SUGGESTIONS = [
  "How are you feeling today?",
  "I had a tough day",
  "What tasks do I have?",
];

export default function ChatWindow({ messages, isTyping, onSuggestion }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  return (
    <div className="flex-1 overflow-y-auto px-3 sm:px-5 py-4 sm:py-6 space-y-4 sm:space-y-5
                    bg-gradient-to-b from-surface-950 to-surface-900/60">

      {messages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full
                        text-center gap-4 sm:gap-5 py-12 sm:py-16 animate-fade-in">
          <div className="relative">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl
                            bg-gradient-to-br from-soul-600/20 to-soul-800/20
                            border border-soul-600/25 flex items-center justify-center">
              <Brain size={30} className="text-soul-400 sm:hidden" />
              <Brain size={36} className="text-soul-400 hidden sm:block" />
            </div>
            <div className="absolute -top-1 -right-1 w-5 h-5 sm:w-6 sm:h-6 rounded-full
                            bg-gradient-to-br from-glow-400 to-glow-600
                            flex items-center justify-center shadow-lg">
              <Sparkles size={10} className="text-surface-950" />
            </div>
          </div>

          <div>
            <h2 className="text-lg sm:text-xl font-bold text-white mb-2 tracking-tight">
              Hello! I'm SoulSync AI
            </h2>
            <p className="text-surface-400 text-xs sm:text-sm max-w-[260px] sm:max-w-xs leading-relaxed">
              Your personal companion. I remember your conversations,
              understand your patterns, and grow with you.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 justify-center mt-1">
            {SUGGESTIONS.map(s => (
              <button
                key={s}
                onClick={() => onSuggestion?.(s)}
                className="text-xs bg-surface-800/80 border border-surface-700
                           text-surface-400 hover:text-soul-300 hover:border-soul-600/50
                           hover:bg-soul-900/30 px-3 py-1.5 rounded-full
                           transition-all duration-200 cursor-pointer">
                "{s}"
              </button>
            ))}
          </div>
        </div>
      )}

      {messages.map((msg, i) => (
        <MessageBubble key={i} msg={msg} />
      ))}

      {isTyping && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
