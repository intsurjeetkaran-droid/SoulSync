import { useState, useEffect } from "react";
import { TrendingUp, Lightbulb, Loader2, RefreshCw, BarChart3 } from "lucide-react";
import { getSuggestions } from "../api/soulsync";

const EMOTION_CONFIG = {
  happy    : { bar: "bg-glow-400",   emoji: "😊", label: "Happy"     },
  motivated: { bar: "bg-soul-400",   emoji: "🚀", label: "Motivated" },
  neutral  : { bar: "bg-surface-400",emoji: "😐", label: "Neutral"   },
  tired    : { bar: "bg-blue-400",   emoji: "😴", label: "Tired"     },
  stressed : { bar: "bg-orange-400", emoji: "😰", label: "Stressed"  },
  sad      : { bar: "bg-violet-400", emoji: "😢", label: "Sad"       },
  angry    : { bar: "bg-red-400",    emoji: "😠", label: "Angry"     },
  focused  : { bar: "bg-teal-400",   emoji: "🎯", label: "Focused"   },
  anxious  : { bar: "bg-amber-400",  emoji: "😟", label: "Anxious"   },
};

const DEFAULT_CONFIG = { bar: "bg-soul-500", emoji: "🧠", label: "" };

export default function InsightPanel({ userId, refreshTrigger }) {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchInsights = async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const res = await getSuggestions(userId);
      setData(res.data);
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchInsights(); }, [userId, refreshTrigger]);

  const emotions    = data?.analysis?.emotions        || {};
  const suggestions = data?.suggestions               || [];
  const total       = data?.analysis?.total_entries   || 0;
  const dominant    = data?.analysis?.dominant_emotion || "neutral";

  const topEmotions = Object.entries(emotions)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);
  const maxCount = topEmotions[0]?.[1] || 1;

  const domCfg = EMOTION_CONFIG[dominant] || DEFAULT_CONFIG;

  return (
    <div className="flex flex-col h-full gap-4">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 size={15} className="text-soul-400" />
          <span className="text-sm font-semibold text-white">Insights</span>
        </div>
        <button onClick={fetchInsights}
          className="p-1.5 rounded-lg hover:bg-surface-800 text-surface-500
                     hover:text-soul-400 transition-colors">
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {loading && (
        <div className="flex justify-center py-8">
          <Loader2 size={18} className="animate-spin text-soul-500" />
        </div>
      )}

      {!loading && total === 0 && (
        <div className="flex flex-col items-center gap-2 py-8 text-center">
          <TrendingUp size={24} className="text-surface-700" />
          <p className="text-xs text-surface-600">Start chatting to unlock insights</p>
        </div>
      )}

      {!loading && total > 0 && (
        <>
          {/* Dominant mood card */}
          <div className="bg-gradient-to-br from-surface-800 to-surface-900
                          border border-surface-700/60 rounded-2xl p-4">
            <p className="text-[11px] text-surface-500 uppercase tracking-wider mb-2 font-medium">
              Dominant mood
            </p>
            <div className="flex items-center gap-3">
              <span className="text-3xl">{domCfg.emoji}</span>
              <div>
                <p className="text-sm font-bold text-white capitalize">{dominant}</p>
                <p className="text-[11px] text-surface-500 mt-0.5">
                  from {total} conversation{total !== 1 ? "s" : ""}
                </p>
              </div>
              <div className={`ml-auto w-2 h-2 rounded-full ${domCfg.bar} animate-pulse`} />
            </div>
          </div>

          {/* Emotion bars */}
          {topEmotions.length > 0 && (
            <div>
              <p className="text-[11px] text-surface-500 uppercase tracking-wider mb-3 font-medium">
                Emotion breakdown
              </p>
              <div className="space-y-2.5">
                {topEmotions.map(([emotion, count]) => {
                  const cfg = EMOTION_CONFIG[emotion] || DEFAULT_CONFIG;
                  const pct = Math.round((count / maxCount) * 100);
                  return (
                    <div key={emotion}>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-surface-300 flex items-center gap-1.5">
                          <span>{cfg.emoji}</span>
                          <span className="capitalize">{emotion}</span>
                        </span>
                        <span className="text-[11px] text-surface-500 font-medium">{count}</span>
                      </div>
                      <div className="h-1.5 bg-surface-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-700 ${cfg.bar}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="flex-1 overflow-y-auto">
              <div className="flex items-center gap-1.5 mb-3">
                <Lightbulb size={13} className="text-glow-400" />
                <p className="text-[11px] text-surface-500 uppercase tracking-wider font-medium">
                  Suggestions for you
                </p>
              </div>
              <div className="space-y-2">
                {suggestions.map((s, i) => (
                  <div key={i}
                    className="text-xs text-surface-300 bg-surface-800/70
                               border border-surface-700/50 rounded-xl p-3
                               leading-relaxed hover:border-soul-700/50
                               hover:bg-surface-800 transition-all duration-200
                               animate-fade-in">
                    {s}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
