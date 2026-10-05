import { cn } from '@/lib/cn';

/**
 * The shared look of every control.
 *
 * Kept here rather than repeated per component so an input, a select and an
 * input-with-a-button cannot drift a pixel apart sitting next to each other.
 */
const SURFACE =
  'w-full rounded-md border bg-raised text-sm text-ink transition-[border-color,box-shadow] duration-150';

/** The same surface at the standard 36px control height. */
const BOX = cn(SURFACE, 'h-9');

/**
 * The focus and hover language, in one place.
 *
 * Hover is scoped to "not focused" on purpose. Tailwind emits focus-within
 * before hover, so a plain `hover:border-muted` wins whenever the pointer
 * happens to rest on a focused field -- and the border drops back to grey while
 * the field is being typed in.
 */
const REST =
  '[&:hover:not(:focus-within)]:border-muted border-rule focus-within:border-signal focus-within:ring-signal/15';
const INVALID = 'border-danger focus-within:border-danger focus-within:ring-danger/15';

// The ring is spelled out at each use rather than built from a constant: a
// class Tailwind cannot read as a whole string in the source never gets
// generated, so `focus:${RING}` silently produces no CSS at all.
//
// A wide, faint ring instead of a hard second border: it reads as focus without
// thickening the box and shifting the row.

export function controlClasses(error: boolean, extra?: string): string {
  return cn(
    BOX,
    'px-2.5 placeholder:text-muted focus:outline-none focus:ring-[3px]',
    error
      ? 'border-danger focus:border-danger focus:ring-danger/15'
      : 'border-rule hover:border-muted focus:border-signal focus:ring-signal/15',
    'disabled:cursor-not-allowed disabled:bg-surface disabled:text-muted',
    extra,
  );
}

/**
 * The same box, but drawn around a group -- an input plus a button, say.
 *
 * The border and ring move to the wrapper and react to focus-within, so the
 * field lights up whichever child has focus and the button inside it sits on
 * the same background rather than on a box of its own.
 */
export function controlGroupClasses(error: boolean): string {
  return cn(
    BOX,
    'flex items-center gap-1 pl-2.5 pr-1 focus-within:ring-[3px]',
    error ? INVALID : REST,
  );
}

/**
 * The composer: the same box, sized by what is typed into it rather than to
 * the standard 36px, with a rail along the bottom for the send button and the
 * things worth knowing before pressing it.
 *
 * It draws its border and ring from the same two constants as every other
 * control, which is the point of it living here. The composer is the most-used
 * field in the product and was the only one drawing its own focus state -- a
 * bare border change, no ring -- so the box people type into all day was the
 * one box that did not look like the rest of the app.
 *
 * `overflow-hidden` lets the rail's own background reach the rounded corners
 * without repeating the radius on it. It does not clip the focus ring: that is
 * a box-shadow on this element, and overflow clips children, not shadows.
 */
export function composerClasses(error: boolean): string {
  return cn(SURFACE, 'flex flex-col overflow-hidden focus-within:ring-[3px]', error ? INVALID : REST);
}

/** The bare input inside a group: the wrapper is already drawing the box. */
export const groupedInputClasses =
  'h-full min-w-0 flex-1 bg-transparent text-sm text-ink placeholder:text-muted focus:outline-none disabled:cursor-not-allowed disabled:text-muted';
