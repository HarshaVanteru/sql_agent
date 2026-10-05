import { useMutation, useQueryClient } from '@tanstack/react-query';

import { conversationsApi } from '@/api';
import { queryKeys } from '@/lib/queryKeys';
import type { Answer } from '@/types';

interface AskVariables {
  question: string;
  conversationId?: string;
}

/**
 * Ask a question of a connected database.
 *
 * On success the conversation is refetched rather than patched locally: the
 * server is what assembled the turn, including the result snapshot, and a
 * first question also creates the conversation this is about to open.
 */
export function useAskQuestion(
  connectionId: string | null,
  onAnswered?: (answer: Answer) => void,
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ question, conversationId }: AskVariables) =>
      conversationsApi.ask(connectionId as string, question, conversationId),
    onSuccess: (answer) => {
      if (!connectionId) return;
      void queryClient.invalidateQueries({ queryKey: queryKeys.conversations(connectionId) });
      if (answer.conversationId) {
        void queryClient.invalidateQueries({
          queryKey: queryKeys.conversation(connectionId, answer.conversationId),
        });
      }
      onAnswered?.(answer);
    },
  });
}
