/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        void: "#0A0E0C",
        panel: "#111813",
        scan: "#4CE0B3",     // cyan-green: scanning / detection
        signal: "#F5C451",   // amber: price / value
        profit: "#5EE38C",   // green: profitable
        loss: "#E3615E",     // red: not profitable / low confidence
        line: "#1E2A22",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(76, 224, 179, 0.25)",
      },
    },
  },
  plugins: [],
};
