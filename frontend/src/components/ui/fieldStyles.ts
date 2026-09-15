import { cn } from '@/lib/cn';

/**
 * The shared look of every control.
 *
 * Kept here rather than repeated per component so an input and a select cannot
 * drift a pixel apart sitting next to each other in a row.
 */
export function controlClasses(error: boolean, extra?: string): string {
  return cn(
    'h-9 w-full rounded-md border bg-raised px-2.5 text-sm text-ink',
    'transition-[border-color,box-shadow] duration-150',
    'placeholder:text-muted',
    // A wide, faint ring instead of a hard second border: it reads as focus
    // without thickening the box and shifting the row.
    'focus:outline-none focus:ring-[3px]',
    error
      ? 'border-danger focus:border-danger focus:ring-danger/15'
      : 'border-rule hover:border-muted focus:border-signal focus:ring-signal/15',
    'disabled:cursor-not-allowed disabled:bg-surface disabled:text-muted',
    extra,
  );
}
