/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Primary: Emerald-Teal ──────────────────────────
        soul: {
          50 : "#ecfdf8",
          100: "#d1faea",
          200: "#a7f3d4",
          300: "#6ee7b7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
          800: "#065f46",
          900: "#064e3b",
          950: "#022c22",
        },
        // ── Accent: Warm Amber ─────────────────────────────
        glow: {
          50 : "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          300: "#fcd34d",
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
          800: "#92400e",
          900: "#78350f",
        },
        // ── Surface: Warm Charcoal (not cold gray) ─────────
        surface: {
          50 : "#f9f7f4",
          100: "#f0ede8",
          200: "#e2ddd6",
          300: "#c9c2b8",
          400: "#a89e92",
          500: "#8a7f73",
          600: "#6e6358",
          700: "#524940",
          800: "#2e2720",
          850: "#231e18",
          900: "#1a1510",
          950: "#110d08",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "fade-in"   : "fadeIn 0.3s ease-in-out",
        "slide-up"  : "slideUp 0.3s ease-out",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow-pulse": "glowPulse 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn   : { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideUp  : { "0%": { transform: "translateY(10px)", opacity: "0" },
                     "100%": { transform: "translateY(0)", opacity: "1" } },
        glowPulse: {
          "0%, 100%": { boxShadow: "0 0 8px rgba(16,185,129,0.3)" },
          "50%"     : { boxShadow: "0 0 20px rgba(16,185,129,0.6)" },
        },
      },
    },
  },
  plugins: [],
}
