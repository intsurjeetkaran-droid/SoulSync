import { useState, useRef, useEffect } from "react";
import { Send, Mic, MicOff, Loader2 } from "lucide-react";

export default function ChatInput({ onSend, isLoading, prefill }) {
  const [text,      setText]      = useState("");
  const [recording, setRecording] = useState(false);
  const textareaRef               = useRef(null);

  useEffect(() => {
    if (prefill) {
      setText(prefill);
      textareaRef.current?.focus();
    }
  }, [prefill]);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setText("");
    textareaRef.current?.focus();
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleRecording = () => {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
      alert("Speech recognition not supported. Use Chrome.");
      return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SR();
    recognition.lang = "en-US";
    recognition.interimResults = false;

    if (!recording) {
      setRecording(true);
      recognition.start();
      recognition.onresult = (e) => {
        const t = e.results[0][0].transcript;
        setText(prev => prev + (prev ? " " : "") + t);
        setRecording(false);
      };
      recognition.onerror = () => setRecording(false);
      recognition.onend   = () => setRecording(false);
    }
  };

  const hasText = text.trim().length > 0;

  return (
    <div className="px-3 sm:px-4 py-3 sm:py-4 bg-surface-900/80 backdrop-blur-sm
                    border-t border-surface-800 shrink-0">
      <div className={`flex items-end gap-2 bg-surface-800 rounded-2xl px-3 sm:px-4 py-2.5 sm:py-3
                       border transition-all duration-200
                       ${hasText
                         ? "border-soul-600/60 shadow-sm shadow-soul-900/30"
                         : "border-surface-700 focus-within:border-soul-600/50"}`}>
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Message SoulSync AI…"
          rows={1}
          className="flex-1 bg-transparent text-surface-100 placeholder-surface-500
                     text-sm outline-none resize-none leading-relaxed
                     max-h-28 overflow-y-auto"
          style={{ minHeight: "22px" }}
        />

        {/* Voice */}
        <button
          onClick={toggleRecording}
          className={`p-1.5 rounded-lg transition-all duration-200 shrink-0
            ${recording
              ? "text-red-400 bg-red-400/10 animate-pulse"
              : "text-surface-500 hover:text-surface-300 hover:bg-surface-700"}`}
          title="Voice input">
          {recording ? <MicOff size={16} /> : <Mic size={16} />}
        </button>

        {/* Send */}
        <button
          onClick={handleSend}
          disabled={!hasText || isLoading}
          className={`p-1.5 rounded-lg transition-all duration-200 shrink-0
                      active:scale-90 disabled:opacity-35 disabled:cursor-not-allowed
                      ${hasText && !isLoading
                        ? "bg-soul-600 hover:bg-soul-500 text-white shadow-sm shadow-soul-900/40"
                        : "bg-surface-700 text-surface-500"}`}>
          {isLoading
            ? <Loader2 size={16} className="animate-spin" />
            : <Send size={16} />}
        </button>
      </div>

      {/* Keyboard hint — hidden on mobile */}
      <p className="hidden sm:block text-center text-[11px] text-surface-600 mt-2">
        <kbd className="bg-surface-800 px-1.5 py-0.5 rounded text-surface-500 font-mono">Enter</kbd>
        {" "}to send ·{" "}
        <kbd className="bg-surface-800 px-1.5 py-0.5 rounded text-surface-500 font-mono">Shift+Enter</kbd>
        {" "}for new line
      </p>
    </div>
  );
}
