import { request } from '@/lib/apiClient';
import type { Connection, ConnectionDraft, DatabaseType } from '@/types';

interface ConnectionPayload {
  id: string;
  name: string;
  db_type: DatabaseType;
  created_at: string;
}

function toConnection(payload: ConnectionPayload): Connection {
  return {
    id: payload.id,
    name: payload.name,
    dbType: payload.db_type,
    createdAt: payload.created_at,
  };
}

export const connectionsApi = {
  async list(): Promise<Connection[]> {
    const payload = await request<{ connections: ConnectionPayload[] }>('/api/connections');
    return payload.connections.map(toConnection);
  },

  async create(draft: ConnectionDraft): Promise<Connection> {
    const payload = await request<ConnectionPayload>('/api/connections', {
      method: 'POST',
      body: {
        name: draft.name,
        db_type: draft.dbType,
        credentials: {
          host: draft.host,
          port: draft.port,
          username: draft.username,
          password: draft.password,
          database_name: draft.databaseName,
        },
      },
    });
    return toConnection(payload);
  },

  async remove(connectionId: string): Promise<void> {
    await request<void>(`/api/connections/${connectionId}`, { method: 'DELETE' });
  },
};
