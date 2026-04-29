import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Brain, Zap, Shield, BarChart2, CheckSquare, ArrowRight,
  Menu, X, Star, ChevronDown, Cpu, Database, Layers,
  MessageSquare, ExternalLink,
} from "lucide-react";
import UseCaseCarousel from "../components/UseCaseCarousel";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" } },
};
const stagger = {
  hidden: {},
  show:   { transition: { staggerChildren: 0.12 } },
};

function Orb({ className }) {
  return <div className={`absolute rounded-full blur-3xl pointer-events-none ${className}`} />;
}

// ── Navbar ────────────────────────────────────────────────
function Navbar() {
  const [open,     setOpen]     = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", fn);
    return () => window.removeEventListener("scroll", fn);
  }, []);

  const links = [
    { label: "How It Works", href: "#how"      },
    { label: "Use Cases",    href: "#usecases" },
    { label: "Features",     href: "#features" },
    { label: "Why Different",href: "#why"      },
  ];

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300
                     ${scrolled
                       ? "bg-surface-950/92 backdrop-blur-xl border-b border-surface-800/70 shadow-xl"
                       : "bg-transparent"}`}>
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-soul-500 to-soul-700
                          flex items-center justify-center shadow-lg shadow-soul-900/50">
            <Brain size={19} className="text-white" />
          </div>
          <span className="text-lg font-bold text-white tracking-tight">
            SoulSync <span className="text-soul-400">AI</span>
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {links.map(l => (
            <a key={l.label} href={l.href}
              className="text-sm text-surface-400 hover:text-white transition-colors">
              {l.label}
            </a>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-3">
          <Link to="/login"
            className="text-sm text-surface-400 hover:text-white transition-colors px-4 py-2">
            Sign In
          </Link>
          <Link to="/signup"
            className="btn-primary text-sm px-5 py-2.5 flex items-center gap-1.5">
            Get Started <ArrowRight size={14} />
          </Link>
        </div>

        <button onClick={() => setOpen(v => !v)}
          className="md:hidden text-surface-400 hover:text-white transition-colors">
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {open && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:hidden bg-surface-900/97 backdrop-blur-xl
                     border-b border-surface-800 px-6 py-4 space-y-3"
        >
          {links.map(l => (
            <a key={l.label} href={l.href} onClick={() => setOpen(false)}
              className="block text-surface-300 hover:text-white py-2 transition-colors">
              {l.label}
            </a>
          ))}
          <div className="flex gap-3 pt-2">
            <Link to="/login" onClick={() => setOpen(false)}
              className="flex-1 text-center py-2.5 rounded-xl border border-surface-700
                         text-surface-300 hover:text-white text-sm transition-colors">
              Sign In
            </Link>
            <Link to="/signup" onClick={() => setOpen(false)}
              className="flex-1 btn-primary text-center text-sm py-2.5">
              Get Started
            </Link>
          </div>
        </motion.div>
      )}
    </nav>
  );
}

// ── Hero ──────────────────────────────────────────────────
function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center
                        overflow-hidden px-4 pt-20">
      {/* Orbs — emerald + amber, no blue */}
      <Orb className="w-[700px] h-[700px] bg-soul-600/15 top-1/2 left-1/2
                      -translate-x-1/2 -translate-y-1/2" />
      <Orb className="w-[350px] h-[350px] bg-glow-500/10 top-16 right-16" />
      <Orb className="w-[280px] h-[280px] bg-teal-600/10 bottom-24 left-12" />

      {/* Subtle grid */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(16,185,129,0.025)_1px,transparent_1px),linear-gradient(90deg,rgba(16,185,129,0.025)_1px,transparent_1px)]
                      bg-[size:60px_60px] pointer-events-none" />

      <div className="relative z-10 text-center max-w-5xl mx-auto">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 bg-soul-500/10 border border-soul-500/30
                     rounded-full px-4 py-1.5 mb-8"
        >
          <span className="w-2 h-2 rounded-full bg-soul-400 animate-pulse" />
          <span className="text-soul-300 text-sm font-medium">
            Powered by Groq — sub-second AI responses
          </span>
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-4xl sm:text-5xl md:text-7xl font-extrabold text-white leading-tight mb-6"
        >
          Your Personal{" "}
          <span className="bg-gradient-to-r from-soul-400 via-glow-400 to-teal-400
                           bg-clip-text text-transparent">
            Intelligence
          </span>
          <br />System
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-base sm:text-xl text-surface-400 max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          A command-driven AI that understands, remembers, and acts for you.
          Not just a chatbot — a companion that grows with you.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <Link to="/signup">
            <motion.button
              whileHover={{ scale: 1.04, boxShadow: "0 0 32px rgba(16,185,129,0.35)" }}
              whileTap={{ scale: 0.97 }}
              className="btn-primary px-8 py-4 text-base flex items-center gap-2"
            >
              Get Started Free <ArrowRight size={18} />
            </motion.button>
          </Link>
          <Link to="/login">
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.97 }}
              className="px-8 py-4 text-base rounded-xl border border-surface-700
                         text-surface-300 hover:text-white hover:border-surface-500
                         transition-all duration-200 flex items-center gap-2"
            >
              <MessageSquare size={18} /> Try Demo
            </motion.button>
          </Link>
        </motion.div>

        {/* Social proof */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="flex items-center justify-center gap-6 mt-12 text-sm text-surface-500"
        >
          <div className="flex items-center gap-1.5">
            <div className="flex -space-x-2">
              {["R","A","S","M"].map((l, i) => (
                <div key={i}
                  className="w-7 h-7 rounded-full bg-gradient-to-br from-soul-600 to-soul-800
                             border-2 border-surface-950
                             flex items-center justify-center text-xs font-bold text-soul-200">
                  {l}
                </div>
              ))}
            </div>
            <span>1,000+ users</span>
          </div>
          <div className="flex items-center gap-1">
            {[1,2,3,4,5].map(i => (
              <Star key={i} size={14} className="text-glow-400 fill-glow-400" />
            ))}
            <span className="ml-1">4.9/5</span>
          </div>
        </motion.div>

        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 2 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 text-surface-600"
        >
          <ChevronDown size={24} />
        </motion.div>
      </div>
    </section>
  );
}

// ── How It Works ──────────────────────────────────────────
function HowItWorks() {
  const steps = [
    { icon: <MessageSquare size={24} />, title: "Command",  desc: "Speak naturally — no special syntax. Just talk to SoulSync like a person." },
    { icon: <Database size={24} />,      title: "Memory",   desc: "Every interaction is stored, structured, and indexed for instant recall." },
    { icon: <Cpu size={24} />,           title: "Analysis", desc: "AI detects patterns, emotions, and intent across your entire history." },
    { icon: <Zap size={24} />,           title: "Action",   desc: "Tasks created, insights surfaced, decisions supported — automatically." },
  ];

  return (
    <section id="how" className="py-24 px-4">
      <div className="max-w-6xl mx-auto">
        <motion.div variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true }}
          className="text-center mb-16">
          <motion.span variants={fadeUp}
            className="inline-block text-xs font-semibold tracking-widest text-soul-400
                       uppercase mb-4 px-3 py-1 bg-soul-500/10 rounded-full border border-soul-500/20">
            How It Works
          </motion.span>
          <motion.h2 variants={fadeUp} className="text-4xl md:text-5xl font-bold text-white mb-4">
            Four steps to a smarter life
          </motion.h2>
          <motion.p variants={fadeUp} className="text-surface-400 text-lg max-w-xl mx-auto">
            SoulSync turns your words into structured intelligence.
          </motion.p>
        </motion.div>

        <motion.div variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 relative">
          <div className="hidden md:block absolute top-12 left-[12.5%] right-[12.5%]
                          h-px bg-gradient-to-r from-transparent via-soul-500/30 to-transparent" />
          {steps.map((s, i) => (
            <motion.div key={i} variants={fadeUp}
              className="relative flex flex-col items-center text-center p-6
                         bg-surface-900/70 border border-surface-800 rounded-2xl
                         hover:border-soul-600/40 hover:bg-surface-900
                         transition-all duration-300 group">
              <div className="w-14 h-14 rounded-2xl bg-soul-600/15 border border-soul-500/25
                              flex items-center justify-center text-soul-400 mb-4
                              group-hover:bg-soul-600/25 transition-colors">
                {s.icon}
              </div>
              <div className="absolute -top-3 -right-3 w-7 h-7 rounded-full
                              bg-gradient-to-br from-soul-500 to-soul-700
                              flex items-center justify-center text-xs font-bold text-white shadow-md">
                {i + 1}
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{s.title}</h3>
              <p className="text-surface-400 text-sm leading-relaxed">{s.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

// ── Features ──────────────────────────────────────────────
function Features() {
  const features = [
    { icon: <Brain size={22} />,      color: "text-soul-400",   bg: "bg-soul-500/10",   border: "border-soul-500/20",   title: "Deep Memory System",  desc: "Structured personal facts + semantic vector search. SoulSync remembers your name, goals, habits, and history — forever." },
    { icon: <Zap size={22} />,        color: "text-glow-400",   bg: "bg-glow-500/10",   border: "border-glow-500/20",   title: "Command Execution",   desc: "Natural language commands trigger real actions — task creation, mood logging, schedule planning — no buttons needed." },
    { icon: <BarChart2 size={22} />,  color: "text-teal-400",   bg: "bg-teal-500/10",   border: "border-teal-500/20",   title: "Personal Insights",   desc: "Mood trends, productivity patterns, emotional analysis — SoulSync surfaces what matters from your data." },
    { icon: <CheckSquare size={22} />,color: "text-emerald-400",bg: "bg-emerald-500/10",border: "border-emerald-500/20",title: "Task Automation",     desc: "Auto-detects tasks from conversation. Prioritizes, schedules, and tracks completion without manual input." },
    { icon: <Shield size={22} />,     color: "text-rose-400",   bg: "bg-rose-500/10",   border: "border-rose-500/20",   title: "Private & Secure",    desc: "Your data is isolated per user with JWT auth. Memories are yours alone — never shared, never mixed." },
    { icon: <Layers size={22} />,     color: "text-cyan-400",   bg: "bg-cyan-500/10",   border: "border-cyan-500/20",   title: "Intent Detection",    desc: "Understands whether you're storing info, asking a question, or giving a command — and routes accordingly." },
  ];

  return (
    <section id="features" className="py-24 px-4 bg-surface-900/25">
      <div className="max-w-6xl mx-auto">
        <motion.div variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true }}
          className="text-center mb-16">
          <motion.span variants={fadeUp}
            className="inline-block text-xs font-semibold tracking-widest text-soul-400
                       uppercase mb-4 px-3 py-1 bg-soul-500/10 rounded-full border border-soul-500/20">
            Features
          </motion.span>
          <motion.h2 variants={fadeUp} className="text-4xl md:text-5xl font-bold text-white mb-4">
            Everything you need
          </motion.h2>
          <motion.p variants={fadeUp} className="text-surface-400 text-lg max-w-xl mx-auto">
            Built for people who want more than a chatbot.
          </motion.p>
        </motion.div>

        <motion.div variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true }}
          className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6">
          {features.map((f, i) => (
            <motion.div key={i} variants={fadeUp}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              className={`p-6 bg-surface-900/70 border ${f.border} rounded-2xl
                          hover:shadow-xl hover:bg-surface-900
                          transition-all duration-300 group cursor-default`}>
              <div className={`w-11 h-11 rounded-xl ${f.bg} border ${f.border}
                               flex items-center justify-center ${f.color} mb-4
                               group-hover:scale-110 transition-transform duration-200`}>
                {f.icon}
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-surface-400 text-sm leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

// ── Why Different ─────────────────────────────────────────
function WhyDifferent() {
  const rows = [
    { feature: "Memory",          others: "Forgets after session",  soul: "Permanent structured memory"    },
    { feature: "Personalization", others: "Generic responses",      soul: "Knows your name, goals, habits" },
    { feature: "Actions",         others: "Only answers questions",  soul: "Creates tasks, logs mood, plans"},
    { feature: "Intent",          others: "Treats all input same",   soul: "Detects store / query / command"},
    { feature: "Privacy",         others: "Shared model context",    soul: "Isolated per user with JWT auth"},
    { feature: "Speed",           others: "Slow local models",       soul: "Groq API — sub-second responses"},
  ];

  return (
    <section id="why" className="py-24 px-4">
      <div className="max-w-4xl mx-auto">
        <motion.div variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true }}
          className="text-center mb-16">
          <motion.span variants={fadeUp}
            className="inline-block text-xs font-semibold tracking-widest text-soul-400
                       uppercase mb-4 px-3 py-1 bg-soul-500/10 rounded-full border border-soul-500/20">
            Why Different
          </motion.span>
          <motion.h2 variants={fadeUp} className="text-4xl md:text-5xl font-bold text-white mb-4">
            Not just another AI chat
          </motion.h2>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }} transition={{ duration: 0.6 }}
          className="bg-surface-900/70 border border-surface-800 rounded-2xl overflow-hidden">
          <div className="grid grid-cols-3 bg-surface-800/60 px-3 sm:px-6 py-4 text-xs sm:text-sm font-semibold">
            <span className="text-surface-400">Feature</span>
            <span className="text-surface-500 text-center">Others</span>
            <span className="text-soul-400 text-center">SoulSync</span>
          </div>
          {rows.map((r, i) => (
            <div key={i}
              className={`grid grid-cols-3 px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm items-center
                          ${i % 2 === 0 ? "bg-surface-900/40" : ""}`}>
              <span className="font-medium text-surface-300">{r.feature}</span>
              <span className="text-center text-surface-500 flex items-center justify-center gap-1">
                <X size={11} className="text-red-500 shrink-0 hidden sm:block" />
                <span className="text-[10px] sm:text-xs">{r.others}</span>
              </span>
              <span className="text-center text-soul-400 flex items-center justify-center gap-1">
                <CheckSquare size={11} className="shrink-0 hidden sm:block" />
                <span className="text-[10px] sm:text-xs">{r.soul}</span>
              </span>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

// ── CTA ───────────────────────────────────────────────────
function CTA() {
  return (
    <section className="py-24 px-4">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }} transition={{ duration: 0.6 }}
          className="relative overflow-hidden rounded-3xl
                     bg-gradient-to-br from-soul-700 via-soul-600 to-teal-700
                     p-8 sm:p-12 text-center shadow-2xl shadow-soul-900/60">
          <Orb className="w-64 h-64 bg-glow-400/20 top-0 right-0" />
          <Orb className="w-48 h-48 bg-teal-300/15 bottom-0 left-0" />
          <div className="relative z-10">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white mb-4">
              Start building your smarter life today
            </h2>
            <p className="text-soul-100/80 text-lg mb-8 max-w-xl mx-auto">
              Join thousands of people using SoulSync AI to understand themselves better,
              work smarter, and live more intentionally.
            </p>
            <Link to="/signup">
              <motion.button
                whileHover={{ scale: 1.05, boxShadow: "0 0 40px rgba(255,255,255,0.25)" }}
                whileTap={{ scale: 0.97 }}
                className="bg-white text-soul-800 font-bold px-10 py-4 rounded-2xl
                           text-lg flex items-center gap-2 mx-auto
                           hover:bg-soul-50 transition-colors shadow-xl">
                Sign Up Free <ArrowRight size={20} />
              </motion.button>
            </Link>
            <p className="text-soul-200/60 text-sm mt-4">No credit card required</p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// ── Footer ────────────────────────────────────────────────
function Footer() {
  return (
    <footer className="border-t border-surface-800 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8 mb-10">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-soul-500 to-soul-700
                              flex items-center justify-center">
                <Brain size={19} className="text-white" />
              </div>
              <span className="text-lg font-bold text-white tracking-tight">
                SoulSync <span className="text-soul-400">AI</span>
              </span>
            </div>
            <p className="text-surface-500 text-sm leading-relaxed max-w-xs">
              A personal AI companion that remembers, understands, and grows with you.
            </p>
            <div className="flex gap-3 mt-4">
              {[ExternalLink, ExternalLink, ExternalLink].map((Icon, i) => (
                <a key={i} href="#"
                  className="w-9 h-9 rounded-lg bg-surface-800 border border-surface-700
                             flex items-center justify-center text-surface-500
                             hover:text-white hover:border-surface-600 transition-all">
                  <Icon size={15} />
                </a>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Product</h4>
            <ul className="space-y-2.5">
              {["Features", "How It Works", "Use Cases", "Pricing"].map(l => (
                <li key={l}>
                  <a href="#" className="text-sm text-surface-500 hover:text-surface-300 transition-colors">{l}</a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold text-white mb-4">Company</h4>
            <ul className="space-y-2.5">
              {["About", "Blog", "Privacy Policy", "Terms of Service"].map(l => (
                <li key={l}>
                  <a href="#" className="text-sm text-surface-500 hover:text-surface-300 transition-colors">{l}</a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="border-t border-surface-800 pt-6 flex flex-col sm:flex-row
                        items-center justify-between gap-4">
          <p className="text-xs text-surface-600">© 2026 SoulSync AI. All rights reserved.</p>
          <p className="text-xs text-surface-600">Built with ❤️ using FastAPI + React + Groq</p>
        </div>
      </div>
    </footer>
  );
}

// ── Main ──────────────────────────────────────────────────
export default function Landing() {
  return (
    <div className="bg-surface-950 text-surface-100 min-h-screen">
      <Navbar />
      <Hero />
      <HowItWorks />
      <div id="usecases"><UseCaseCarousel /></div>
      <Features />
      <WhyDifferent />
      <CTA />
      <Footer />
    </div>
  );
}
