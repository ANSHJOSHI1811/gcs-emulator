/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1a73e8',
          hover: '#1557b0',
          light: '#e8f0fe',
        },
        secondary: {
          DEFAULT: '#5f6368',
          light: '#f1f3f4',
        },
        success: '#1e8e3e',
        warning: '#f9ab00',
        error: '#d93025',
        info: '#1967d2',
      },
    },
  },
  plugins: [],
}
