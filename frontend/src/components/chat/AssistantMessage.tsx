import { Collapsible } from '@/components/ui';
import type { Message } from '@/types';
import { Markdown } from './Markdown';
import { ResultCard } from './ResultCard';
import { SqlBlock } from './SqlBlock';

interface AssistantMessageProps {
  message: Message;
  connectionName: string;
}

/** 1240 -> "1.2s", 124 -> "124ms". Seconds once milliseconds stop being readable. */
function formatElapsed(ms: number): string {
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
}

/**
 * One answer: what the agent said, the SQL it wrote, and the rows that came
 * back.
 *
 * The three are stacked in the order they happened and given different
 * weights, so the turn reads as one thing rather than three boxes -- the prose
 * is the answer, the SQL is the working, and the table is the evidence.
 */
export function AssistantMessage({ message, connectionName }: AssistantMessageProps) {
  return (
    // w-full and min-w-0 together: items-start below sizes each child to its
    // content, which is what lets a narrow table hug -- but without a
    // definite width on this container, `max-w-full` on a wide one resolves
    // against nothing and a nine-column result drags the page off screen.
    <div className="flex w-full min-w-0 flex-col items-start gap-3">
      <div className="flex items-center gap-2.5">
        <span
          aria-hidden="true"
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-signal-bright font-serif text-[0.8125rem] font-semibold text-white"
        >
          A
        </span>
        <h3 className="font-serif text-[0.9375rem] italic text-ink">Database copilot</h3>
        {message.elapsedMs !== null && (
          <span className="font-mono text-[0.6875rem] text-muted">
            &middot; answered in {formatElapsed(message.elapsedMs)}
          </span>
        )}
      </div>

      {/* The card runs the full column so its edges line up with the SQL and
          the result below it -- three cards of three different widths read as
          three unrelated things. The prose inside is still held to a reading
          measure, which is the part that actually has to be narrow. */}
      {message.content && (
        <div className="w-full rounded-xl border border-rule bg-raised px-4 py-3">
          <div className="max-w-prose">
            <Collapsible>
              <Markdown>{message.content}</Markdown>
            </Collapsible>
          </div>
        </div>
      )}

      {/* Not max-w-prose: a query is read by its shape, and wrapping it at
          reading width is what made LIMIT clauses disappear off the right. */}
      {message.sqlQuery && (
        <div className="w-full min-w-0">
          <SqlBlock sql={message.sqlQuery} />
        </div>
      )}

      {message.result && <ResultCard result={message.result} connectionName={connectionName} />}
    </div>
  );
}
