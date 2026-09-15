import { Spinner } from '@/components/ui';
import type { ConversationSummary } from '@/types';
import { ConversationItem } from './ConversationItem';

interface ConversationListProps {
  conversations: ConversationSummary[];
  loading: boolean;
  selectedId: string | null;
  onSelect: (conversationId: string) => void;
}

export function ConversationList({
  conversations,
  loading,
  selectedId,
  onSelect,
}: ConversationListProps) {
  if (loading) {
    return (
      <div className="flex justify-center py-6">
        <Spinner className="text-muted" />
      </div>
    );
  }

  if (conversations.length === 0) {
    return <p className="px-2 py-3 text-[0.8125rem] text-slate">Nothing asked yet.</p>;
  }

  return (
    <ul className="flex flex-col gap-0.5">
      {conversations.map((conversation) => (
        <li key={conversation.id}>
          <ConversationItem
            conversation={conversation}
            selected={conversation.id === selectedId}
            onSelect={onSelect}
          />
        </li>
      ))}
    </ul>
  );
}
