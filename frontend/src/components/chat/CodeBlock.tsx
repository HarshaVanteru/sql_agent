import { useState } from 'react';

interface CodeBlockProps {
  code: string;
  /** What the code is, shown in the bar: "SQL", "json", "python". */
  label: string;
}

/**
 * A block of code, with the one affordance that matters for it: copy.
 *
 * Shared by the query the agent settled on and any fenced block inside its
 * prose, so a SQL statement looks the same wherever it appears in the reply.
 */
export function CodeBlock({ code, label }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access can be refused; the code is selectable either way.
    }
  }

  return (
    <div className="w-full overflow-hidden rounded border border-rule bg-surface">
      <div className="flex items-center justify-between border-b border-rule px-3 py-1.5">
        <span className="text-xs font-medium text-slate">{label}</span>
        <button
          type="button"
          onClick={copy}
          className="rounded px-1.5 py-0.5 text-xs text-slate transition-colors hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-signal"
        >
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="overflow-x-auto px-3 py-2.5 font-mono text-[0.8125rem] leading-relaxed text-ink">
        <code>{code}</code>
      </pre>
    </div>
  );
}
