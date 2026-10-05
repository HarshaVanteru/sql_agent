import { CodeBlock } from './CodeBlock';

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
  return <CodeBlock code={sql} label="SQL" />;
}
