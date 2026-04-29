import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Activity, TrendingUp,
         Heart, CheckSquare, Lightbulb } from "lucide-react";

const USE_CASES = [
  {
    id: 1,
    color: "from-blue-600 to-indigo-600",
    glow: "shadow-blue-500/20",
    border: "border-blue-500/30",
    dot: "bg-blue-500",
    icon: <Activity size={28} />,
    title: "Track Your Daily Life",
    description: "SoulSync learns your patterns and turns daily logs into meaningful insights about your life.",
    steps: [
      { emoji: "💬", label: "You say", text: '"Log my day — gym done, felt tired"' },
      { emoji: "🧠", label: "AI stores", text: "Activity, emotion & context saved to memory" },
      { emoji: "📊", label: "AI analyzes", text: "Patterns detected across days and weeks" },
      { emoji: "✨", label: "AI gives", text: "Personalized insights & recommendations" },
    ],
  },
  {
    id: 2,
    color: "from-violet-600 to-purple-600",
    glow: "shadow-violet-500/20",
    border: "border-violet-500/30",
    dot: "bg-violet-500",
    icon: <TrendingUp size={28} />,
    title: "Improve Productivity",
    description: "Identify your weak spots and let SoulSync build a smarter work system around you.",
    steps: [
      { emoji: "📅", label: "You say", text: '"Analyze my week"' },
      { emoji: "🔍", label: "AI finds", text: "Low-focus periods and missed tasks identified" },
      { emoji: "💡", label: "AI suggests", text: "Time-blocking, Pomodoro, priority shifts" },
      { emoji: "✅", label: "AI creates", text: "Optimized task list for the next week" },
    ],
  },
  {
    id: 3,
    color: "from-rose-600 to-pink-600",
    glow: "shadow-rose-500/20",
    border: "border-rose-500/30",
    dot: "bg-rose-500",
    icon: <Heart size={28} />,
    title: "Get Personal Support",
    description: "SoulSync listens, understands your emotions, and responds with genuine empathy.",
    steps: [
      { emoji: "😔", label: "You share", text: '"I\'ve been feeling really overwhelmed lately"' },
      { emoji: "🎯", label: "AI detects", text: "Stress pattern + emotional context from memory" },
      { emoji: "💙", label: "AI responds", text: "Empathetic, personalized support message" },
      { emoji: "📈", label: "AI tracks", text: "Mood over time to spot trends early" },
    ],
  },
  {
    id: 4,
    color: "from-amber-500 to-orange-600",
    glow: "shadow-amber-500/20",
    border: "border-amber-500/30",
    dot: "bg-amber-500",
    icon: <CheckSquare size={28} />,
    title: "Automate Your Tasks",
    description: "Just speak naturally — SoulSync extracts tasks, sets priorities, and tracks completion.",
    steps: [
      { emoji: "🗣️", label: "You say", text: '"Plan my tomorrow"' },
      { emoji: "📋", label: "AI creates", text: "Full schedule based on your goals & history" },
      { emoji: "⏰", label: "AI adds", text: "Smart reminders at optimal times" },
      { emoji: "🏆", label: "AI tracks", text: "Completion rate and celebrates wins" },
    ],
  },
  {
    id: 5,
    color: "from-emerald-600 to-teal-600",
    glow: "shadow-emerald-500/20",
    border: "border-emerald-500/30",
    dot: "bg-emerald-500",
    icon: <Lightbulb size={28} />,
    title: "Make Better Decisions",
    description: "SoulSync uses your history to give advice that's actually relevant to your life.",
    steps: [
      { emoji: "🤔", label: "You ask", text: '"Should I take this new job offer?"' },
      { emoji: "🔎", label: "AI checks", text: "Your goals, values & past decisions from memory" },
      { emoji: "⚖️", label: "AI compares", text: "Pros/cons aligned with your personal context" },
      { emoji: "🎯", label: "AI suggests", text: "The best path forward — just for you" },
    ],
  },
];

const AUTOPLAY_MS = 5000;

export default function UseCaseCarousel() {
  const [active, setActive]       = useState(0);
  const [direction, setDirection] = useState(1);   // 1 = forward, -1 = backward
  const [paused, setPaused]       = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const timerRef = useRef(null);

  const goTo = useCallback((idx, dir = 1) => {
    setDirection(dir);
    setActive(idx);
    setActiveStep(0);
  }, []);

  const next = useCallback(() => {
    goTo((active + 1) % USE_CASES.length, 1);
  }, [active, goTo]);

  const prev = useCallback(() => {
    goTo((active - 1 + USE_CASES.length) % USE_CASES.length, -1);
  }, [active, goTo]);

  // Auto-play
  useEffect(() => {
    if (paused) return;
    timerRef.current = setInterval(next, AUTOPLAY_MS);
    return () => clearInterval(timerRef.current);
  }, [paused, next]);

  // Step reveal animation
  useEffect(() => {
    setActiveStep(0);
    const steps = USE_CASES[active].steps.length;
    let i = 0;
    const t = setInterval(() => {
      i++;
      if (i >= steps) { clearInterval(t); return; }
      setActiveStep(i);
    }, 400);
    return () => clearInterval(t);
  }, [active]);

  const uc = USE_CASES[active];

  const slideVariants = {
    enter:  (d) => ({ x: d > 0 ? 80 : -80, opacity: 0 }),
    center: { x: 0, opacity: 1 },
    exit:   (d) => ({ x: d > 0 ? -80 : 80, opacity: 0 }),
  };

  return (
    <section
      className="py-24 px-4 relative overflow-hidden"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-gray-950 via-gray-900/50 to-gray-950" />

      <div className="max-w-6xl mx-auto relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="inline-block text-xs font-semibold tracking-widest
                           text-soul-400 uppercase mb-4 px-3 py-1
                           bg-soul-500/10 rounded-full border border-soul-500/20">
            Use Cases
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            How will you use{" "}
            <span className="bg-gradient-to-r from-soul-400 to-violet-400
                             bg-clip-text text-transparent">
              SoulSync AI?
            </span>
          </h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Five ways SoulSync transforms your daily life — pick your journey.
          </p>
        </motion.div>

        {/* Carousel */}
        <div className="relative">
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={active}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
              className={`bg-gray-900/60 backdrop-blur-xl border ${uc.border}
                          rounded-3xl p-8 md:p-12 shadow-2xl ${uc.glow}`}
            >
              <div className="grid md:grid-cols-2 gap-10 items-center">
                {/* Left: info */}
                <div>
                  <div className={`inline-flex items-center justify-center w-14 h-14
                                   rounded-2xl bg-gradient-to-br ${uc.color}
                                   text-white mb-6 shadow-lg`}>
                    {uc.icon}
                  </div>

                  <div className="text-xs font-semibold tracking-widest text-gray-500
                                  uppercase mb-2">
                    Use Case {active + 1} of {USE_CASES.length}
                  </div>

                  <h3 className="text-3xl font-bold text-white mb-4">{uc.title}</h3>
                  <p className="text-gray-400 text-lg leading-relaxed">{uc.description}</p>

                  {/* Progress bar */}
                  <div className="mt-8">
                    <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                      <motion.div
                        className={`h-full bg-gradient-to-r ${uc.color} rounded-full`}
                        initial={{ width: "0%" }}
                        animate={{ width: paused ? undefined : "100%" }}
                        transition={{ duration: AUTOPLAY_MS / 1000, ease: "linear" }}
                        key={`${active}-${paused}`}
                      />
                    </div>
                  </div>
                </div>

                {/* Right: steps */}
                <div className="space-y-4">
                  {uc.steps.map((step, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: i <= activeStep ? 1 : 0.25, x: 0 }}
                      transition={{ duration: 0.35, delay: i * 0.05 }}
                      className={`flex items-start gap-4 p-4 rounded-2xl transition-all
                                  duration-300 ${i <= activeStep
                                    ? "bg-gray-800/80 border border-gray-700/50"
                                    : "bg-gray-900/40"}`}
                    >
                      <span className="text-2xl shrink-0 mt-0.5">{step.emoji}</span>
                      <div>
                        <div className="text-xs font-semibold text-gray-500 uppercase
                                        tracking-wider mb-0.5">
                          {step.label}
                        </div>
                        <div className="text-white font-medium">{step.text}</div>
                      </div>
                      {i <= activeStep && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className={`ml-auto shrink-0 w-2 h-2 rounded-full ${uc.dot} mt-2`}
                        />
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Nav buttons */}
          <button
            onClick={prev}
            className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-5
                       w-10 h-10 rounded-full bg-gray-800 border border-gray-700
                       flex items-center justify-center text-gray-400
                       hover:text-white hover:bg-gray-700 transition-all
                       shadow-lg hidden md:flex"
          >
            <ChevronLeft size={20} />
          </button>
          <button
            onClick={next}
            className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-5
                       w-10 h-10 rounded-full bg-gray-800 border border-gray-700
                       flex items-center justify-center text-gray-400
                       hover:text-white hover:bg-gray-700 transition-all
                       shadow-lg hidden md:flex"
          >
            <ChevronRight size={20} />
          </button>
        </div>

        {/* Dot indicators + mobile nav */}
        <div className="flex items-center justify-center gap-4 mt-8">
          <button onClick={prev}
            className="md:hidden w-9 h-9 rounded-full bg-gray-800 border border-gray-700
                       flex items-center justify-center text-gray-400 hover:text-white">
            <ChevronLeft size={18} />
          </button>

          <div className="flex gap-2">
            {USE_CASES.map((uc, i) => (
              <button
                key={i}
                onClick={() => goTo(i, i > active ? 1 : -1)}
                className={`transition-all duration-300 rounded-full
                  ${i === active
                    ? `w-8 h-2.5 ${uc.dot}`
                    : "w-2.5 h-2.5 bg-gray-700 hover:bg-gray-500"}`}
              />
            ))}
          </div>

          <button onClick={next}
            className="md:hidden w-9 h-9 rounded-full bg-gray-800 border border-gray-700
                       flex items-center justify-center text-gray-400 hover:text-white">
            <ChevronRight size={18} />
          </button>
        </div>

        {/* Use case tabs (desktop) */}
        <div className="hidden md:flex gap-3 mt-8 justify-center flex-wrap">
          {USE_CASES.map((uc, i) => (
            <button
              key={i}
              onClick={() => goTo(i, i > active ? 1 : -1)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm
                          font-medium transition-all duration-200 border
                          ${i === active
                            ? `bg-gradient-to-r ${uc.color} text-white border-transparent shadow-lg`
                            : "bg-gray-900 text-gray-400 border-gray-800 hover:border-gray-600 hover:text-white"}`}
            >
              {uc.icon && <span className="scale-75">{uc.icon}</span>}
              {uc.title}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
