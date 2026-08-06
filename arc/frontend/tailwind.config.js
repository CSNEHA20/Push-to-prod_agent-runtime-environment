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
          bg: "#0B0F19",
          card: "#111827",
          border: "#1F2937",
          accent: "#3B82F6",
          flight: "#6366F1",
          firewall: "#F59E0B",
          recovery: "#10B981"
        }
      }
    },
  },
  plugins: [],
}
