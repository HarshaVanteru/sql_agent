import { ExpandableText } from '@/components/ui';
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
      {message.content && <ExpandableText text={message.content} />}
      {message.sqlQuery && <SqlBlock sql={message.sqlQuery} />}
      {message.result && (
        <div className="flex flex-col items-start gap-1.5">
          <ResultTable result={message.result} />
          <RowCount count={message.result.rowCount} />
        </div>
      )}
    </div>
  );
}
