import type { Message } from '@/types';
import { AssistantMessage } from './AssistantMessage';
import { UserMessage } from './UserMessage';

interface MessageRowProps {
  message: Message;
}

export function MessageRow({ message }: MessageRowProps) {
  return message.role === 'user' ? (
    <UserMessage content={message.content} />
  ) : (
    <AssistantMessage message={message} />
  );
}
