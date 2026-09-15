import { useAutoScroll } from '@/hooks/useAutoScroll';
import type { Message } from '@/types';
import { MessageRow } from './MessageRow';
import { ThinkingRow } from './ThinkingRow';

interface MessageListProps {
  messages: Message[];
  thinking: boolean;
}

export function MessageList({ messages, thinking }: MessageListProps) {
  const scrollRef = useAutoScroll<HTMLDivElement>(`${messages.length}:${thinking}`);

  return (
    <div ref={scrollRef} className="min-w-0 flex-1 overflow-y-auto">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6">
        {messages.map((message) => (
          <MessageRow key={message.id} message={message} />
        ))}
        {thinking && <ThinkingRow />}
      </div>
    </div>
  );
}
