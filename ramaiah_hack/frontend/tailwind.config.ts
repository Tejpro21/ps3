import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0A0C10",
          900: "#0E1117",
          850: "#111827",
          800: "#141A24"
        }
      },
      boxShadow: {
        glass: "0 0 0 1px rgba(255,255,255,0.06) inset, 0 16px 40px rgba(0,0,0,0.4)"
      }
    }
  },
  plugins: []
} satisfies Config;

