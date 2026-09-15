import type { Message } from '@/types';
import { ResultTable } from './ResultTable';
import { RowCount } from './RowCount';
import { SqlBlock } from './SqlBlock';

interface AssistantMessageProps {
  message: Message;
}

export function AssistantMessage({ message }: AssistantMessageProps) {
  return (
    <div className="flex flex-col gap-2.5">
      {message.content && (
        <p className="max-w-prose whitespace-pre-wrap text-[0.9375rem] leading-relaxed text-ink">
          {message.content}
        </p>
      )}
      {message.sqlQuery && <SqlBlock sql={message.sqlQuery} />}
      {message.result && (
        <div className="flex flex-col gap-1.5">
          <ResultTable result={message.result} />
          <RowCount count={message.result.rowCount} />
        </div>
      )}
    </div>
  );
}
