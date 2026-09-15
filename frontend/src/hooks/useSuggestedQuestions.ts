import { useMemo } from 'react';

import { suggestQuestions } from '@/lib/suggestedQuestions';
import type { Message } from '@/types';

/**
 * Three questions to offer, drawn from what the conversation is about.
 *
 * The context is the last answer plus the SQL and column names that came with
 * it -- the column names matter most, because they are where a real schema's
 * vocabulary shows up ("user_id", "expires_at") even when the prose is vague.
 *
 * Recomputed only when the last message changes, so the three do not reshuffle
 * under the pointer while someone is reading them.
 */
export function useSuggestedQuestions(messages: readonly Message[], count = 3): string[] {
  const last = messages.at(-1);

  return useMemo(
    () => {
      const recent = messages.slice(-2);
      const context = recent
        .flatMap((message) => [
          message.content,
          message.sqlQuery ?? '',
          (message.result?.columns ?? []).join(' '),
        ])
        .join(' ');

      return suggestQuestions({
        context,
        asked: messages.filter((m) => m.role === 'user').map((m) => m.content),
        count,
      });
    },
    // Keyed on the last message rather than the array: a refetch returns a new
    // array of the same turns, and that must not redraw the suggestions.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [last?.id, messages.length, count],
  );
}
