import type { Message } from '@/types';
import { AssistantMessage } from './AssistantMessage';
import { UserMessage } from './UserMessage';

interface MessageRowProps {
  message: Message;
  connectionName: string;
  userInitials: string;
}

export function MessageRow({ message, connectionName, userInitials }: MessageRowProps) {
  return message.role === 'user' ? (
    <UserMessage
      content={message.content}
      createdAt={message.createdAt}
      initials={userInitials}
    />
  ) : (
    <AssistantMessage message={message} connectionName={connectionName} />
  );
}
