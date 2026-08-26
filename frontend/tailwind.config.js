/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0a0d14',
        surface: '#0f141f',
        'surface-elevated': '#161c2b',
        'surface-card': '#121824',
        border: '#1f293d',
        'border-subtle': '#182030',
        'accent-green': '#00e676',
        'accent-green-dark': '#00b0ff',
        'accent-red': '#ff3b30',
        'accent-red-muted': '#cf6679',
        'accent-cyan': '#00e5ff',
        'accent-gold': '#ffd600',
        'text-primary': '#f1f5f9',
        'text-secondary': '#94a3b8',
        'text-muted': '#64748b',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Roboto Mono', 'ui-monospace', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'glow-green': '0 0 15px -3px rgba(0, 230, 118, 0.25)',
        'glow-red': '0 0 15px -3px rgba(255, 59, 48, 0.25)',
        'glow-cyan': '0 0 15px -3px rgba(0, 229, 255, 0.25)',
      },
    },
  },
  plugins: [],
}
