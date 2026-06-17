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
          bg: "#090A0C",
          secondary: "#101114",
          surface: "#17181B",
          surface2: "#1D1F23",
          panel: "#202329",
          border: "#2A2D33",
          borderSoft: "#3A3E46",
          text: "#ECEFF3",
          text2: "#C4C9D1",
          muted: "#949BA6",
          ivory: "#ECE7DC",
          steelBlue: "#4F7EA8",
          copperRed: "#B66A61",
          amberGold: "#C3A15F",
          blue: "#4F7EA8",
          blueSoft: "#7EA6C8",
          positive: "#ECE7DC",
          amber: "#C3A15F",
          risk: "#B66A61",
          gold: "#AAB7C6",
          red: "#B66A61"
        }
      },
      fontFamily: {
        sans: ["var(--font-pmri-sans)", "Inter", "Manrope", "\"Helvetica Neue\"", "Arial", "sans-serif"],
        mono: ["var(--font-pmri-mono)", "SF Mono", "Roboto Mono", "ui-monospace", "SFMono-Regular", "monospace"]
      },
      boxShadow: {
        decision: "0 20px 54px rgba(0, 0, 0, 0.26)"
      },
      backgroundImage: {
        "decision-radial": "radial-gradient(circle at 80% 12%, rgba(143, 177, 216, 0.08), transparent 32%), radial-gradient(circle at 12% 0%, rgba(255, 255, 255, 0.04), transparent 22%)"
      }
    }
  },
  plugins: []
};

export default config;
