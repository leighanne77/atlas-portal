/** @type {import('tailwindcss').Config} */
// team Brand Guidelines v1.0 + Mobile Annex v1.0.
// - Exact brand HEX values from master §4.1
// - darkMode: 'class' so we can toggle and default-by-viewport
//   (mobile = dark, desktop = light, per Mobile Annex §6.1)
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        "brand-red-600": "#C8202F",
        "brand-red-400": "#D43545",
        "brand-amber-500": "#E8A82A",
        "brand-amber-300": "#F0BB52",
        "brand-slate-600": "#4A6B8A",
        "brand-slate-700": "#3A5670",
        "brand-slate-900": "#1A2332",
        "brand-slate-800": "#2A3548",
        "brand-slate-50": "#F5EEE0",
        "brand-slate-100": "#FAF6EC",
      },
      fontFamily: {
        display: ["Oswald", "Impact", "Arial Black", "sans-serif"],
        body: ["Arial", "Helvetica", "sans-serif"],
        mono: ["Courier New", "Consolas", "monospace"],
      },
      // Two-iteration pulse used to draw the eye to Send right after a
      // dictation lands in the textarea. Brand-gold ring + light scale.
      keyframes: {
        "send-pulse": {
          "0%, 100%": {
            transform: "scale(1)",
            boxShadow: "0 0 0 0 rgba(232, 168, 42, 0)",
          },
          "50%": {
            transform: "scale(1.06)",
            boxShadow: "0 0 0 8px rgba(232, 168, 42, 0.35)",
          },
        },
      },
      animation: {
        "send-pulse": "send-pulse 0.7s ease-in-out 2",
      },
    },
  },
  plugins: [],
};
