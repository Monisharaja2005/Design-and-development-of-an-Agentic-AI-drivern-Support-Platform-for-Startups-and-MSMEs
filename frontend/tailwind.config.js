/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#4F7CFF",
          secondary: "#8B9CFF",
          accent: "#6EE7B7",
          gold: "#F59E0B",
          rose: "#F43F5E",
          intelligence: "#F2F5FA",
          dark: "#0D1117",
          navy: "#1A2744",
        },
      },
      fontFamily: {
        plus: ['"Plus Jakarta Sans"', "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
        inter: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        'premium': '0 20px 40px -8px rgba(0,0,0,0.10), 0 8px 16px -8px rgba(0,0,0,0.06)',
        'glass': '0 8px 32px 0 rgba(31,38,135,0.09)',
        'card': '0 2px 8px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.06)',
        'glow': '0 0 32px -4px rgba(79,124,255,0.35)',
        'glow-sm': '0 0 16px -2px rgba(79,124,255,0.25)',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 1.5s infinite',
        'fade-up': 'fadeUp 0.5s ease forwards',
        'fade-in': 'fadeIn 0.4s ease forwards',
        'pulse-soft': 'pulse-soft 2.5s ease-in-out infinite',
        'spin-slow': 'spin-slow 8s linear infinite',
        'blob': 'blob 8s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        fadeUp: {
          'from': { opacity: '0', transform: 'translateY(24px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          'from': { opacity: '0' },
          'to': { opacity: '1' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.7', transform: 'scale(0.95)' },
        },
        'spin-slow': {
          'from': { transform: 'rotate(0deg)' },
          'to': { transform: 'rotate(360deg)' },
        },
        blob: {
          '0%, 100%': { borderRadius: '60% 40% 30% 70% / 60% 30% 70% 40%' },
          '50%': { borderRadius: '30% 60% 70% 40% / 50% 60% 30% 60%' },
        },
      },
    },
  },
  plugins: [],
}
