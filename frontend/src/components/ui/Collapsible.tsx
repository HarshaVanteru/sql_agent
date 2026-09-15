import { useLayoutEffect, useRef, useState, type ReactNode } from 'react';

interface CollapsibleProps {
  children: ReactNode;
  /** Pixels of content shown before collapsing. */
  collapsedHeight?: number;
}

/**
 * Long content, clamped until asked for.
 *
 * "What tables are in here?" on a real database answers with two hundred
 * names. Uncapped, one reply fills several screens and buries the conversation
 * it belongs to.
 *
 * Measured in pixels rather than lines because the content is rendered
 * markdown -- paragraphs, lists, code blocks -- and line-clamp only counts
 * lines within a single text block. The clamp only appears when the content
 * actually overflows, so ordinary answers are untouched.
 */
export function Collapsible({ children, collapsedHeight = 320 }: CollapsibleProps) {
  const [expanded, setExpanded] = useState(false);
  const [overflows, setOverflows] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const element = ref.current;
    if (!element || expanded) return;
    // Only measurable while collapsed: expanded, scrollHeight is the full
    // height and every answer would look like it fits.
    setOverflows(element.scrollHeight > collapsedHeight + 8);
  }, [children, expanded, collapsedHeight]);

  return (
    <div>
      <div
        className="relative overflow-hidden"
        style={expanded ? undefined : { maxHeight: collapsedHeight }}
      >
        <div ref={ref}>{children}</div>
        {!expanded && overflows && (
          // Signals there is more below without a hard edge mid-sentence.
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-paper to-transparent" />
        )}
      </div>
      {overflows && (
        <button
          type="button"
          onClick={() => setExpanded((open) => !open)}
          aria-expanded={expanded}
          className="mt-1.5 rounded text-[0.8125rem] font-medium text-signal underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}
    </div>
  );
}
