import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        pid: {
          process: "#2563eb",
          instrument: "#dc2626",
          annotation: "#16a34a",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
