import { request } from '@/lib/apiClient';
import type { Session } from '@/types';

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

  /** Ends the session server-side: connections, conversations and all. */
  async end(): Promise<void> {
    await request<void>('/api/session', { method: 'DELETE' });
  },
};
