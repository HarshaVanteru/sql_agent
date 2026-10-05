export interface Session {
  sessionId: string;
  name: string;
  createdAt: string;
  expiresAt: string;
  connectionCount: number;
}

/** How much time a visitor can add to a live session. */
export type ExtensionOption = '24h' | '7d' | '30d';
