/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"Source Serif 4"', 'serif'],
        sans: ['"Inter"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        arc: {
          bg: "#131316",
          surface: "#1F1C19",
          outline: "#34302C",
          primary: "#DA7756",
          tertiary: "#10B981",
          secondary: "#F59E0B",
          error: "#EF4444",
          textPrimary: "#F1F5F9",
          textSecondary: "#94A3B8",
        }
      }
    },
  },
  plugins: [],
}
