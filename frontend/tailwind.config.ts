import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#fafafa",
        panel: "rgba(255,255,255,0.78)",
        line: "rgba(15,23,42,0.08)",
        accent: "#0f52ff",
        orange: "#ff7a00"
      },
      boxShadow: {
        glass: "0 20px 60px rgba(15, 23, 42, 0.08)"
      },
      fontFamily: {
        sans: ["'SF Pro Display'", "'PingFang SC'", "'Segoe UI'", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;
