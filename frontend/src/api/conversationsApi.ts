import { request } from '@/lib/apiClient';
import type { Answer, Conversation, ConversationSummary, Message, QueryResult } from '@/types';

interface ResultPayload {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
}

interface MessagePayload {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sql_query: string | null;
  result: ResultPayload | null;
  created_at: string;
  elapsed_ms: number | null;
}

interface SummaryPayload {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface ConversationPayload {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: MessagePayload[];
}

interface AnswerPayload {
  query: string | null;
  columns: string[];
  rows: Array<Record<string, unknown>>;
  row_count: number;
  conversation_id: string | null;
  message: string | null;
  elapsed_ms: number | null;
}

function toResult(payload: ResultPayload | null): QueryResult | null {
  if (!payload) return null;
  return { columns: payload.columns, rows: payload.rows, rowCount: payload.row_count };
}

function toMessage(payload: MessagePayload): Message {
  return {
    id: payload.id,
    role: payload.role,
    content: payload.content,
    sqlQuery: payload.sql_query,
    result: toResult(payload.result),
    createdAt: payload.created_at,
    // Absent on user turns, and on assistant turns recorded before the server
    // started reporting it.
    elapsedMs: payload.elapsed_ms ?? null,
  };
}

function toSummary(payload: SummaryPayload): ConversationSummary {
  return {
    id: payload.id,
    title: payload.title,
    createdAt: payload.created_at,
    updatedAt: payload.updated_at,
    messageCount: payload.message_count,
  };
}

export const conversationsApi = {
  async list(connectionId: string): Promise<ConversationSummary[]> {
    const payload = await request<{ conversations: SummaryPayload[] }>(
      `/api/connections/${connectionId}/conversations`,
    );
    return payload.conversations.map(toSummary);
  },

  async get(connectionId: string, conversationId: string): Promise<Conversation> {
    const payload = await request<ConversationPayload>(
      `/api/connections/${connectionId}/conversations/${conversationId}`,
    );
    return {
      id: payload.id,
      title: payload.title,
      createdAt: payload.created_at,
      updatedAt: payload.updated_at,
      messages: payload.messages.map(toMessage),
    };
  },

  /**
   * Ask a question. Omitting `conversationId` starts a new conversation;
   * passing one continues it, which is what lets a follow-up refine the
   * question before it.
   */
  async ask(connectionId: string, question: string, conversationId?: string): Promise<Answer> {
    const payload = await request<AnswerPayload>(
      `/api/connections/${connectionId}/natural-query`,
      {
        method: 'POST',
        body: { question, conversation_id: conversationId ?? null },
      },
    );
    return {
      query: payload.query,
      columns: payload.columns,
      rows: payload.rows,
      rowCount: payload.row_count,
      conversationId: payload.conversation_id,
      message: payload.message,
      elapsedMs: payload.elapsed_ms ?? null,
    };
  },
};
