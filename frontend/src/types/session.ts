export interface Session {
  sessionId: string;
  name: string;
  createdAt: string;
  expiresAt: string;
  connectionCount: number;
}
