/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        arc: {
          bg: "#0A0A0F",
          surface: "#12121A",
          card: "#12121A",
          border: "#1E1E2E",
          accent: "#6366F1",
          success: "#10B981",
          warning: "#F59E0B",
          danger: "#EF4444",
          textPrimary: "#F1F5F9",
          textSecondary: "#94A3B8",
        }
      }
    },
  },
  plugins: [],
}
