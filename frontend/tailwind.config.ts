import type { Config } from 'tailwindcss';

/**
 * Colours are declared once here and nowhere else. Components name the role
 * ("rule", "signal") rather than the value, so the palette can move without a
 * search-and-replace through the components.
 *
 * Values live in index.css as CSS variables, one set per theme.
 *
 * The palette is warm: a cream page rather than a white one, and a warm-grey
 * hairline rather than a blue-grey one. Against that, the one saturated colour
 * in the product is a deep forest green, and it is reserved for two things --
 * something you can act on, and a quantity being drawn. Everything else is
 * paper, ink, and the rules between them.
 */
/** A colour backed by an `--c-*` channel triplet in index.css, so `/30` still works. */
const v = (name: string) => `rgb(var(--c-${name}) / <alpha-value>)`;

export default {
  darkMode: ['class', '[data-theme="dark"]'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        /** The workspace canvas. */
        paper: v('paper'),
        /** Chrome that should sit back from the canvas: the sidebar, table heads. */
        surface: v('surface'),
        /** Anything that should read as sitting on top: cards, the composer. */
        raised: v('raised'),

        ink: v('ink'),
        slate: v('slate'),
        muted: v('muted'),
        rule: v('rule'),

        /**
         * Interactive, and quantity. Forest green: buttons, the send control,
         * the bars drawn beside a number. `deep` is the question bubble, which
         * has to hold white text; `wash` tints the row you have selected.
         * `on` is the text colour that sits on `DEFAULT` and `bright`: white in
         * light mode, near-black in dark mode where those greens are lighter.
         */
        signal: {
          DEFAULT: v('signal'),
          hover: v('signal-hover'),
          bright: v('signal-bright'),
          deep: v('signal-deep'),
          wash: v('signal-wash'),
          faint: v('signal-faint'),
          on: v('signal-on'),
        },

        /** Time, and only time: the session meter and its countdown. */
        clock: { DEFAULT: v('clock'), wash: v('clock-wash') },
        danger: { DEFAULT: v('danger'), wash: v('danger-wash') },
        /** Backdrop behind the drawer and dialogs. */
        scrim: v('scrim'),
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
