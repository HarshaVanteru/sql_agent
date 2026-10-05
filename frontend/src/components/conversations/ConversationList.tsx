import { useMemo } from 'react';

import { Spinner } from '@/components/ui';
import { dayLabel } from '@/lib/time';
import type { ConversationSummary } from '@/types';
import { ConversationItem } from './ConversationItem';

interface ConversationListProps {
  conversations: ConversationSummary[];
  loading: boolean;
  selectedId: string | null;
  onSelect: (conversationId: string) => void;
}

interface Day {
  label: string;
  conversations: ConversationSummary[];
}

/**
 * Group the list under "Today", "Yesterday", and then dates.
 *
 * The list arrives most-recent first and stays in that order, so walking it
 * once and starting a new group whenever the label changes is enough -- no
 * sorting, and the groups come out in the same order as the conversations.
 */
function groupByDay(conversations: ConversationSummary[]): Day[] {
  const days: Day[] = [];
  for (const conversation of conversations) {
    const label = dayLabel(conversation.updatedAt);
    const current = days.at(-1);
    if (current?.label === label) current.conversations.push(conversation);
    else days.push({ label, conversations: [conversation] });
  }
  return days;
}

export function ConversationList({
  conversations,
  loading,
  selectedId,
  onSelect,
}: ConversationListProps) {
  const days = useMemo(() => groupByDay(conversations), [conversations]);

  if (loading) {
    return (
      <div className="flex justify-center py-6">
        <Spinner className="text-muted" />
      </div>
    );
  }

  if (conversations.length === 0) {
    return <p className="px-2.5 py-3 text-[0.8125rem] text-muted">Nothing asked yet.</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      {days.map((day) => (
        <section key={day.label}>
          <h3 className="px-2.5 pb-1 text-[0.6875rem] tracking-[0.14em] text-muted">
            {day.label.toUpperCase()}
          </h3>
          <ul className="flex flex-col gap-0.5">
            {day.conversations.map((conversation) => (
              <li key={conversation.id}>
                <ConversationItem
                  conversation={conversation}
                  selected={conversation.id === selectedId}
                  onSelect={onSelect}
                />
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
