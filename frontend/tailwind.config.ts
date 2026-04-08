import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#080c10",
          900: "#0d1117",
          800: "#161b22",
          700: "#21262d",
          600: "#30363d",
          500: "#3d444d",
          400: "#656d76",
          300: "#9198a1",
          200: "#b7bdc4",
          100: "#e6edf3",
        },
        amber: {
          950: "#431407",
          900: "#7c2d12",
          800: "#9a3412",
          700: "#c2410c",
          600: "#d97706",
          500: "#f59e0b",
          400: "#fbbf24",
          300: "#fcd34d",
          200: "#fde68a",
          100: "#fef3c7",
          50:  "#fffbeb",
        },
        cream: "#e8dcc8",
        "cream-dim": "#b8a990",
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "grain": "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E\")",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.25s ease-out",
      },
      keyframes: {
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideUp: { from: { opacity: "0", transform: "translateY(6px)" }, to: { opacity: "1", transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};

export default config;
