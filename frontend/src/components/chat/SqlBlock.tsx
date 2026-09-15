import { useState } from 'react';

interface SqlBlockProps {
  sql: string;
}

/**
 * The query the agent settled on.
 *
 * Shown rather than hidden behind a toggle: the SQL is how someone checks the
 * answer is the answer to their question, and it is the thing they copy into
 * their own client afterwards.
 */
export function SqlBlock({ sql }: SqlBlockProps) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access can be refused; the query is selectable either way.
    }
  }

  return (
    <div className="overflow-hidden rounded border border-rule bg-surface">
      <div className="flex items-center justify-between border-b border-rule px-3 py-1.5">
        <span className="text-xs font-medium text-slate">SQL</span>
        <button
          type="button"
          onClick={copy}
          className="rounded px-1.5 py-0.5 text-xs text-slate transition-colors hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-signal"
        >
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="overflow-x-auto px-3 py-2.5 font-mono text-[0.8125rem] leading-relaxed text-ink">
        <code>{sql}</code>
      </pre>
    </div>
  );
}
