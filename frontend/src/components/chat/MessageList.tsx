import { useAutoScroll } from '@/hooks/useAutoScroll';
import type { Message } from '@/types';
import { MessageRow } from './MessageRow';
import { ThinkingRow } from './ThinkingRow';

interface MessageListProps {
  messages: Message[];
  thinking: boolean;
  connectionName: string;
  userInitials: string;
}

export function MessageList({
  messages,
  thinking,
  connectionName,
  userInitials,
}: MessageListProps) {
  const scrollRef = useAutoScroll<HTMLDivElement>(`${messages.length}:${thinking}`);

  return (
    <div ref={scrollRef} className="min-w-0 flex-1 overflow-y-auto">
      {/* 4xl, not 6xl: an answer is read, and a line of prose running the full
          width of a 27" monitor is not. Wide tables still fill the space --
          they scroll inside their own card rather than widening this column. */}
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-8 px-4 py-8 sm:px-6">
        {messages.map((message) => (
          <MessageRow
            key={message.id}
            message={message}
            connectionName={connectionName}
            userInitials={userInitials}
          />
        ))}
        {thinking && <ThinkingRow />}
      </div>
    </div>
  );
}
