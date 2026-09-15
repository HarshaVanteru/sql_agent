/**
 * Every cache key in one place, so an invalidation cannot miss a spelling.
 * Keys nest, which is what lets deleting a connection drop its conversations
 * in a single call.
 */
export const queryKeys = {
  session: ['session'] as const,

  connections: ['connections'] as const,

  conversations: (connectionId: string) => ['connections', connectionId, 'conversations'] as const,

  conversation: (connectionId: string, conversationId: string) =>
    ['connections', connectionId, 'conversations', conversationId] as const,
};
