import { useState } from 'react';

import { FormError } from '@/components/ui';
import { useAskQuestion } from '@/hooks/useAskQuestion';
import { useSuggestedQuestions } from '@/hooks/useSuggestedQuestions';
import { useConversation } from '@/hooks/useConversations';
import { errorMessage, isApiError } from '@/lib/ApiError';
import type { Connection } from '@/types';
import { AskForm } from './AskForm';
import { ChatEmptyState } from './ChatEmptyState';
import { FollowUpQuestions } from './FollowUpQuestions';
import { MessageList } from './MessageList';

interface ChatPanelProps {
  connection: Connection;
  conversationId: string | null;
  onConversationStarted: (conversationId: string) => void;
}

export function ChatPanel({ connection, conversationId, onConversationStarted }: ChatPanelProps) {
  const [prefill, setPrefill] = useState<string>();
  const conversation = useConversation(connection.id, conversationId);

  const ask = useAskQuestion(connection.id, (answer) => {
    // A first question creates the conversation, so the URL has to catch up
    // before its history can be shown.
    if (answer.conversationId && answer.conversationId !== conversationId) {
      onConversationStarted(answer.conversationId);
    }
  });

  const messages = conversation.data?.messages ?? [];
  const suggestions = useSuggestedQuestions(messages);
  const showEmptyState = !conversationId && !ask.isPending && messages.length === 0;

  // A 401 is handled a level up, by sending the visitor back to the start.
  const askError =
    ask.error && !(isApiError(ask.error) && ask.error.isSessionExpired) ? ask.error : null;

  return (
    <section className="flex min-h-0 min-w-0 flex-1 flex-col bg-paper">
      {showEmptyState ? (
        <ChatEmptyState
          connectionName={connection.name}
          questions={suggestions}
          onPick={setPrefill}
          disabled={ask.isPending}
        />
      ) : (
        <MessageList messages={messages} thinking={ask.isPending} />
      )}

      <div className="shrink-0 border-t border-rule bg-surface px-4 py-3 sm:px-6">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-2.5">
          {messages.length > 0 && !ask.isPending && (
            <FollowUpQuestions
              questions={suggestions}
              onPick={setPrefill}
              disabled={ask.isPending}
            />
          )}
          <FormError message={askError ? errorMessage(askError, 'The question could not be answered.') : null} />
          <AskForm
            onAsk={(question) =>
              ask.mutate({ question, conversationId: conversationId ?? undefined })
            }
            pending={ask.isPending}
            disabled={false}
            prefill={prefill}
          />
        </div>
      </div>
    </section>
  );
}
