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
          bg: "#0A0A0A",
          secondary: "#0A0A0A",
          surface: "#191919",
          surface2: "#1A1C20",
          panel: "#191919",
          border: "#212327",
          borderSoft: "rgba(255,255,255,0.25)",
          text: "#FFFFFF",
          text2: "#DADBDF",
          muted: "#7D8187",
          ivory: "#FFFFFF",
          steelBlue: "#A0C3EC",
          copperRed: "#FF7A17",
          amberGold: "#FFC285",
          blue: "#A0C3EC",
          blueSoft: "#C4B5FD",
          positive: "#FFFFFF",
          amber: "#FFC285",
          risk: "#FF7A17",
          gold: "#DADBDF",
          red: "#FF7A17"
        }
      },
      fontFamily: {
        sans: ["var(--font-pmri-sans)", "DM Sans", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-pmri-mono)", "IBM Plex Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"]
      },
      boxShadow: {
        decision: "none"
      },
      backgroundImage: {
        "decision-radial": "linear-gradient(180deg, #0a0a0a 0%, #0a0a0a 100%)"
      }
    }
  },
  plugins: []
};

export default config;
