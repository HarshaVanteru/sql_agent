import { useQuery } from '@tanstack/react-query';

import { conversationsApi } from '@/api';
import { queryKeys } from '@/lib/queryKeys';
import type { Conversation, ConversationSummary } from '@/types';

/** A connection's conversations, most recently active first. */
export function useConversations(connectionId: string | null) {
  return useQuery<ConversationSummary[]>({
    queryKey: queryKeys.conversations(connectionId ?? ''),
    queryFn: () => conversationsApi.list(connectionId as string),
    enabled: Boolean(connectionId),
  });
}

/** One conversation, replayed with its SQL and results. */
export function useConversation(connectionId: string | null, conversationId: string | null) {
  return useQuery<Conversation>({
    queryKey: queryKeys.conversation(connectionId ?? '', conversationId ?? ''),
    queryFn: () => conversationsApi.get(connectionId as string, conversationId as string),
    enabled: Boolean(connectionId && conversationId),
  });
}
