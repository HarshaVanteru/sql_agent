import type { Config } from 'tailwindcss';

/**
 * Colours are declared once here and nowhere else. Components name the role
 * ("rule", "signal") rather than the value, so the palette can move without a
 * search-and-replace through the components.
 */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#EBEEF2',
        surface: '#F7F9FB',
        raised: '#FFFFFF',
        ink: '#101C2B',
        slate: '#54677D',
        muted: '#8496A8',
        rule: '#CBD5DF',
        /** Interactive. Anything the reader can act on. */
        signal: { DEFAULT: '#2F3BE0', hover: '#2029C4', wash: '#E8EAFC' },
        /** Time, and only time: the session meter and its countdown. */
        clock: { DEFAULT: '#B4641E', wash: '#F7ECE0' },
        danger: { DEFAULT: '#B02A2A', wash: '#F8E9E9' },
      },
      fontFamily: {
        sans: ['Archivo', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        display: ['clamp(2.75rem, 7vw, 4.75rem)', { lineHeight: '0.95', letterSpacing: '-0.035em' }],
        title: ['1.5rem', { lineHeight: '1.2', letterSpacing: '-0.02em' }],
      },
      borderRadius: { DEFAULT: '4px', md: '6px' },
      maxWidth: { prose: '68ch' },
    },
  },
  plugins: [],
} satisfies Config;
