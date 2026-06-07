/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        zephyr: {
          night: '#0a0a1a',
          dark: '#1a1a2e',
          mid: '#2d2d44',
          light: '#e8e8f0',
          accent: '#7c3aed',
          'accent-light': '#a78bfa',
          gray: '#8888a0',
          border: '#2a2a40',
        },
      },
    },
  },
  plugins: [],
};
