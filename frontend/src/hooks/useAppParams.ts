import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

/**
 * The URL is where "what am I looking at" lives.
 *
 *   /workspace?session=venu-1789489589-HBlY&connection=cb37&conversation=9c2a
 *
 * Keeping it there rather than in component state means a refresh, a back
 * button, or a pasted link all land on the same database and the same chat.
 *
 * The session id is mirrored here for legibility and deep links only -- it is
 * not what authenticates. That is the HttpOnly cookie, so a URL sent to someone
 * else shows them a start screen, not this session's databases.
 */
export const PARAM = {
  session: 'session',
  connection: 'connection',
  conversation: 'conversation',
} as const;

export interface AppParams {
  sessionId: string | null;
  connectionId: string | null;
  conversationId: string | null;
  /** Select a database. Drops the open conversation, which belonged to the old one. */
  selectConnection: (connectionId: string | null) => void;
  /** Open a conversation, or pass null for a fresh one. */
  selectConversation: (conversationId: string | null) => void;
  /** Write the session id the server actually gave us into the URL. */
  syncSession: (sessionId: string) => void;
  /** Wipe every param. Used when the session ends. */
  clear: () => void;
}

export function useAppParams(): AppParams {
  const [searchParams, setSearchParams] = useSearchParams();

  const sessionId = searchParams.get(PARAM.session);
  const connectionId = searchParams.get(PARAM.connection);
  const conversationId = searchParams.get(PARAM.conversation);

  const update = useCallback(
    (changes: Partial<Record<keyof typeof PARAM, string | null>>, replace = false) => {
      setSearchParams(
        (current) => {
          const next = new URLSearchParams(current);
          for (const [key, value] of Object.entries(changes)) {
            if (value === null) next.delete(PARAM[key as keyof typeof PARAM]);
            else next.set(PARAM[key as keyof typeof PARAM], value);
          }
          return next;
        },
        { replace },
      );
    },
    [setSearchParams],
  );

  const selectConnection = useCallback(
    (id: string | null) => update({ connection: id, conversation: null }),
    [update],
  );

  const selectConversation = useCallback(
    (id: string | null) => update({ conversation: id }),
    [update],
  );

  // replace: true -- correcting the URL to match the real session is not a
  // place anyone should be able to navigate back to.
  const syncSession = useCallback((id: string) => update({ session: id }, true), [update]);

  const clear = useCallback(
    () => update({ session: null, connection: null, conversation: null }, true),
    [update],
  );

  return useMemo(
    () => ({
      sessionId,
      connectionId,
      conversationId,
      selectConnection,
      selectConversation,
      syncSession,
      clear,
    }),
    [sessionId, connectionId, conversationId, selectConnection, selectConversation, syncSession, clear],
  );
}
