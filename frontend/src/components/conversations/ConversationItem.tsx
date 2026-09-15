import { cn } from '@/lib/cn';
import { formatTime } from '@/lib/time';
import type { ConversationSummary } from '@/types';

interface ConversationItemProps {
  conversation: ConversationSummary;
  selected: boolean;
  onSelect: (conversationId: string) => void;
}

export function ConversationItem({ conversation, selected, onSelect }: ConversationItemProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(conversation.id)}
      aria-current={selected ? 'true' : undefined}
      className={cn(
        'block w-full rounded px-2 py-1.5 text-left',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-signal',
        selected ? 'bg-signal-wash' : 'hover:bg-paper',
      )}
    >
      <span className={cn('block truncate text-sm', selected ? 'font-medium text-ink' : 'text-ink')}>
        {conversation.title}
      </span>
      <span className="block text-xs text-slate">{formatTime(conversation.updatedAt)}</span>
    </button>
  );
}
