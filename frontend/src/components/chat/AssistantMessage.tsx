import { Collapsible } from '@/components/ui';
import type { Message } from '@/types';
import { Markdown } from './Markdown';
import { ResultTable } from './ResultTable';
import { RowCount } from './RowCount';
import { SqlBlock } from './SqlBlock';

interface AssistantMessageProps {
  message: Message;
}

export function AssistantMessage({ message }: AssistantMessageProps) {
  return (
    // w-full and min-w-0 together: items-start below sizes each child to its
    // content, which is what lets a narrow table hug -- but without a
    // definite width on this container, `max-w-full` on a wide one resolves
    // against nothing and a nine-column result drags the page off screen.
    <div className="flex w-full min-w-0 flex-col items-start gap-2.5">
      {message.content && (
        <div className="w-full max-w-prose">
          <Collapsible>
            <Markdown>{message.content}</Markdown>
          </Collapsible>
        </div>
      )}
      {/* Not max-w-prose: a query is read by its shape, and wrapping it at
          reading width is what made LIMIT clauses disappear off the right. */}
      {message.sqlQuery && (
        <div className="w-full min-w-0">
          <SqlBlock sql={message.sqlQuery} />
        </div>
      )}
      {message.result && (
        <div className="flex w-full min-w-0 flex-col items-start gap-1.5">
          <ResultTable result={message.result} />
          <RowCount count={message.result.rowCount} />
        </div>
      )}
    </div>
  );
}
