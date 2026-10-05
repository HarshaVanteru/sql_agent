import { ChatIcon } from '@/components/icons/ChatIcon';
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
        'flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left transition-colors',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-signal',
        selected ? 'bg-signal-wash' : 'hover:bg-raised',
      )}
    >
      <ChatIcon
        className={cn('h-3.5 w-3.5 shrink-0', selected ? 'text-signal' : 'text-muted')}
      />
      <span
        className={cn(
          'min-w-0 flex-1 truncate text-[0.8125rem]',
          selected ? 'font-medium text-ink' : 'text-slate',
        )}
      >
        {conversation.title}
      </span>
      {/* Mono, so the times form a column down the right rather than a ragged
          edge that moves with every title above it. */}
      <span className="shrink-0 font-mono text-[0.6875rem] tabular-nums text-muted">
        {formatTime(conversation.updatedAt)}
      </span>
    </button>
  );
}
