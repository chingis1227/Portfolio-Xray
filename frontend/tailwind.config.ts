import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        pmri: {
          bg: "#07111F",
          secondary: "#0D1B2A",
          surface: "#12263A",
          surface2: "#172B42",
          panel: "#1c1f29",
          border: "#334155",
          borderSoft: "#434655",
          text: "#F8FAFC",
          text2: "#CBD5E1",
          muted: "#94A3B8",
          blue: "#3B82F6",
          blueSoft: "#60A5FA",
          positive: "#10B981",
          amber: "#F59E0B",
          risk: "#EF4444",
          gold: "#D4AF37"
        }
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"]
      },
      boxShadow: {
        decision: "0 24px 80px rgba(0, 0, 0, 0.26)"
      },
      backgroundImage: {
        "decision-radial": "radial-gradient(circle at 80% 12%, rgba(59, 130, 246, 0.14), transparent 32%), radial-gradient(circle at 12% 0%, rgba(212, 175, 55, 0.10), transparent 22%)"
      }
    }
  },
  plugins: []
};

export default config;
