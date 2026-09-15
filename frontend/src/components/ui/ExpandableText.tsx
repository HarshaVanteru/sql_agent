import { useLayoutEffect, useRef, useState } from 'react';

import { cn } from '@/lib/cn';

interface ExpandableTextProps {
  text: string;
  /** Lines to show before collapsing. */
  collapsedLines?: number;
}

/**
 * Long prose, clamped until asked for.
 *
 * "What tables are in here?" on a real database answers with two hundred
 * names, and a model repeats them in prose. Uncapped, one reply fills several
 * screens and buries the conversation it belongs to. The clamp only appears
 * when the text actually overflows it, so ordinary answers are untouched.
 */
export function ExpandableText({ text, collapsedLines = 12 }: ExpandableTextProps) {
  const [expanded, setExpanded] = useState(false);
  const [clamped, setClamped] = useState(false);
  const ref = useRef<HTMLParagraphElement>(null);

  useLayoutEffect(() => {
    const element = ref.current;
    if (!element || expanded) return;
    // Sticky once true: the measurement is only valid while collapsed, and
    // re-running it expanded would decide nothing overflows.
    setClamped(element.scrollHeight > element.clientHeight + 4);
  }, [text, expanded]);

  return (
    <div className="max-w-prose">
      <p
        ref={ref}
        style={expanded ? undefined : { WebkitLineClamp: collapsedLines }}
        className={cn(
          'whitespace-pre-wrap break-words text-[0.9375rem] leading-relaxed text-ink',
          !expanded && 'overflow-hidden [display:-webkit-box] [-webkit-box-orient:vertical]',
        )}
      >
        {text}
      </p>
      {clamped && (
        <button
          type="button"
          onClick={() => setExpanded((open) => !open)}
          aria-expanded={expanded}
          className="mt-1 rounded text-[0.8125rem] font-medium text-signal underline-offset-4 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}
    </div>
  );
}
