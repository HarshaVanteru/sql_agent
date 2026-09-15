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
    <div className="flex flex-col items-start gap-2.5">
      {message.content && (
        <div className="w-full max-w-prose">
          <Collapsible>
            <Markdown>{message.content}</Markdown>
          </Collapsible>
        </div>
      )}
      {message.sqlQuery && (
        <div className="w-full max-w-prose">
          <SqlBlock sql={message.sqlQuery} />
        </div>
      )}
      {message.result && (
        <div className="flex max-w-full flex-col items-start gap-1.5">
          <ResultTable result={message.result} />
          <RowCount count={message.result.rowCount} />
        </div>
      )}
    </div>
  );
}
