import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0A0B0F',
          secondary: '#12131A',
          card: 'rgba(255, 255, 255, 0.02)',
          'card-hover': 'rgba(255, 255, 255, 0.04)',
        },
        text: {
          primary: '#F9FAFB',
          secondary: '#D1D5DB',
          muted: '#9CA3AF',
        },
        accent: {
          purple: '#6366F1',
        },
        signal: {
          buy: '#00E676',
          sell: '#FF5252',
          hold: '#FFD740',
        },
        border: {
          default: 'rgba(255, 255, 255, 0.06)',
          hover: 'rgba(255, 255, 255, 0.12)',
        },
        semantic: {
          success: '#00E676',
          danger: '#FF5252',
          warning: '#FFD740',
          info: '#6366F1',
        },
      },
      fontFamily: {
        display: ['var(--font-outfit)', 'Outfit', 'sans-serif'],
        body: ['var(--font-outfit)', 'Outfit', 'sans-serif'],
        mono: ['var(--font-jetbrains)', 'JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
