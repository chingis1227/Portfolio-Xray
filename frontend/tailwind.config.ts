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
          bg: "#050608",
          secondary: "#0B0D10",
          surface: "#111318",
          surface2: "#16191F",
          panel: "#1A1E25",
          border: "#20242B",
          borderSoft: "#303640",
          text: "#ECEFF3",
          text2: "#C4C9D1",
          muted: "#949BA6",
          ivory: "#ECE7DC",
          steelBlue: "#6EA8D7",
          copperRed: "#B66A61",
          amberGold: "#C3A15F",
          blue: "#6EA8D7",
          blueSoft: "#9DCCF0",
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
        decision: "0 26px 70px rgba(0, 0, 0, 0.34)"
      },
      backgroundImage: {
        "decision-radial": "radial-gradient(circle at 76% 4%, rgba(126, 166, 200, 0.085), transparent 30%), radial-gradient(circle at 18% -10%, rgba(236, 239, 243, 0.045), transparent 28%), linear-gradient(180deg, #050608 0%, #030405 100%)"
      }
    }
  },
  plugins: []
};

export default config;
