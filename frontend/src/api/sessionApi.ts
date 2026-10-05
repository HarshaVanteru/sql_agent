import { request } from '@/lib/apiClient';
import type { ExtensionOption, Session } from '@/types';

interface SessionPayload {
  session_id: string;
  name: string;
  created_at: string;
  expires_at: string;
  connection_count: number;
}

/** The API speaks snake_case; nothing past this file has to know that. */
function toSession(payload: SessionPayload): Session {
  return {
    sessionId: payload.session_id,
    name: payload.name,
    createdAt: payload.created_at,
    expiresAt: payload.expires_at,
    connectionCount: payload.connection_count,
  };
}

export const sessionApi = {
  async start(name: string): Promise<Session> {
    return toSession(await request<SessionPayload>('/api/session', { method: 'POST', body: { name } }));
  },

  async current(): Promise<Session> {
    return toSession(await request<SessionPayload>('/api/session'));
  },

  /** Adds time to the live session, on top of what it has left. */
  async extend(duration: ExtensionOption): Promise<Session> {
    return toSession(
      await request<SessionPayload>('/api/session/extend', { method: 'POST', body: { duration } }),
    );
  },

  /** Ends the session server-side: connections, conversations and all. */
  async end(): Promise<void> {
    await request<void>('/api/session', { method: 'DELETE' });
  },
};
