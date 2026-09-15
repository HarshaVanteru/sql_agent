import { Children, isValidElement, type ReactElement, type ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { CodeBlock } from './CodeBlock';

interface MarkdownProps {
  children: string;
}

/**
 * The agent's prose, rendered as the markdown it actually is.
 *
 * Models write `**bold**`, backticked identifiers and ```sql fences whether or
 * not anyone asked them to, and as plain text those arrive on screen as
 * literal asterisks and backticks around the very words meant to stand out.
 *
 * Every element is mapped to this app's own type and spacing rather than left
 * to browser defaults, so a reply looks like part of the page. Raw HTML is not
 * enabled: this is text a model produced from a database's contents, and it
 * has no business injecting markup.
 */
export function Markdown({ children }: MarkdownProps) {
  return (
    <div className="text-[0.9375rem] leading-relaxed text-ink">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
          strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
          em: ({ children }) => <em className="italic">{children}</em>,

          // `pre` renders the block itself and never its children, so the
          // nested `code` element below is only ever reached inline.
          pre: ({ children }) => {
            const child = Children.toArray(children).find(isValidElement) as
              | ReactElement<{ className?: string; children?: ReactNode }>
              | undefined;
            const language = /language-(\w+)/.exec(child?.props?.className ?? '')?.[1];
            const code = String(child?.props?.children ?? '').replace(/\n$/, '');
            return (
              <div className="mb-3 last:mb-0">
                <CodeBlock code={code} label={language === 'sql' ? 'SQL' : (language ?? 'code')} />
              </div>
            );
          },
          code: ({ children }) => (
            <code className="rounded bg-paper px-1 py-0.5 font-mono text-[0.85em] text-ink">
              {children}
            </code>
          ),

          ul: ({ children }) => (
            <ul className="mb-3 list-disc space-y-0.5 pl-5 last:mb-0">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-3 list-decimal space-y-0.5 pl-5 last:mb-0">{children}</ol>
          ),
          li: ({ children }) => <li className="pl-0.5">{children}</li>,

          // Models reach for headings inside a two-line answer, so these stay
          // close to body size -- the weight is what marks them, not the scale.
          h1: ({ children }) => <h3 className="mb-2 font-semibold text-ink">{children}</h3>,
          h2: ({ children }) => <h3 className="mb-2 font-semibold text-ink">{children}</h3>,
          h3: ({ children }) => <h4 className="mb-2 font-semibold text-ink">{children}</h4>,

          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer noopener"
              className="text-signal underline underline-offset-2"
            >
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote className="mb-3 border-l-2 border-rule pl-3 text-slate last:mb-0">
              {children}
            </blockquote>
          ),
          hr: () => <hr className="my-4 border-rule" />,

          table: ({ children }) => (
            <div className="mb-3 overflow-x-auto last:mb-0">
              <table className="w-auto border-collapse text-left text-[0.8125rem]">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="whitespace-nowrap border border-rule bg-surface px-2.5 py-1.5 font-medium text-slate">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-rule px-2.5 py-1.5 align-top">{children}</td>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
