export type MessageRole = 'user' | 'assistant';

/** A result set, as returned by a query and as stored with the turn. */
export interface QueryResult {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  rowCount: number;
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  /** The SQL the agent settled on. Absent when it answered without querying. */
  sqlQuery: string | null;
  result: QueryResult | null;
  createdAt: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

export interface Conversation extends Omit<ConversationSummary, 'messageCount'> {
  messages: Message[];
}

/** The answer to one question. */
export interface Answer {
  query: string | null;
  columns: string[];
  rows: Array<Record<string, unknown>>;
  rowCount: number;
  conversationId: string | null;
  message: string | null;
}
