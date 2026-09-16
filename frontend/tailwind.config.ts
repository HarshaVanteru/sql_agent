import type { Config } from 'tailwindcss';

/**
 * Colours are declared once here and nowhere else. Components name the role
 * ("rule", "signal") rather than the value, so the palette can move without a
 * search-and-replace through the components.
 *
 * The palette is warm: a cream page rather than a white one, and a warm-grey
 * hairline rather than a blue-grey one. Against that, the one saturated colour
 * in the product is a deep forest green, and it is reserved for two things --
 * something you can act on, and a quantity being drawn. Everything else is
 * paper, ink, and the rules between them.
 */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        /** The workspace canvas. */
        paper: '#FAF9F6',
        /** Chrome that should sit back from the canvas: the sidebar, table heads. */
        surface: '#F5F2EA',
        /** Anything that should read as sitting on top: cards, the composer. */
        raised: '#FFFFFF',

        ink: '#121A17',
        slate: '#57605B',
        muted: '#8D938E',
        rule: '#E6E1D6',

        /**
         * Interactive, and quantity. Forest green: buttons, the send control,
         * the bars drawn beside a number. `deep` is the question bubble, which
         * has to hold white text; `wash` tints the row you have selected.
         */
        signal: {
          DEFAULT: '#145344',
          hover: '#0E3E33',
          bright: '#1B6A56',
          deep: '#12281F',
          wash: '#DFE8E3',
          faint: '#ECFDF5',
        },

        /** Time, and only time: the session meter and its countdown. */
        clock: { DEFAULT: '#B45309', wash: '#FFFBEB' },
        danger: { DEFAULT: '#A13333', wash: '#FBEDEA' },
      },
      fontFamily: {
        sans: ['Archivo', 'system-ui', 'sans-serif'],
        /**
         * The serif carries the product's voice: the wordmark, the name of a
         * panel, the agent's own name. Never body copy and never data -- it is
         * there to say who is speaking, not to be read at length.
         */
        serif: ['Newsreader', 'Georgia', 'serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        display: ['clamp(2.75rem, 7vw, 4.75rem)', { lineHeight: '0.95', letterSpacing: '-0.035em' }],
        title: ['1.5rem', { lineHeight: '1.2', letterSpacing: '-0.02em' }],
      },
      borderRadius: { DEFAULT: '4px', md: '6px', lg: '10px', xl: '14px' },
      maxWidth: { prose: '68ch' },
    },
  },
  plugins: [],
} satisfies Config;
