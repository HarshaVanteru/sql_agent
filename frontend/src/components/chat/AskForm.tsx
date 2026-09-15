import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';

import { SendIcon } from '@/components/icons/SendIcon';
import { cn } from '@/lib/cn';

interface AskFormProps {
  onAsk: (question: string) => void;
  pending: boolean;
  disabled: boolean;
  /** Set from a suggestion chip, to prefill the box. */
  prefill?: string;
}

const MAX_HEIGHT = 160;

export function AskForm({ onAsk, pending, disabled, prefill }: AskFormProps) {
  const [question, setQuestion] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const trimmed = question.trim();
  const canSend = trimmed !== '' && !pending && !disabled;

  useEffect(() => {
    if (prefill) {
      setQuestion(prefill);
      textareaRef.current?.focus();
    }
  }, [prefill]);

  // Grow with the question, up to a point, then scroll.
  useEffect(() => {
    const element = textareaRef.current;
    if (!element) return;
    element.style.height = 'auto';
    element.style.height = `${Math.min(element.scrollHeight, MAX_HEIGHT)}px`;
  }, [question]);

  function send() {
    if (!canSend) return;
    onAsk(trimmed);
    setQuestion('');
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    send();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends, Shift+Enter breaks the line -- the usual bargain in a chat box.
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 rounded-md border border-rule bg-raised p-2 focus-within:border-signal"
    >
      <label htmlFor="question" className="sr-only">
        Ask a question about this database
      </label>
      <textarea
        id="question"
        ref={textareaRef}
        rows={1}
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={disabled ? 'Connect a database first' : 'Ask in plain English'}
        className="max-h-40 flex-1 resize-none bg-transparent px-1.5 py-1.5 text-[0.9375rem] leading-relaxed text-ink placeholder:text-muted focus:outline-none disabled:cursor-not-allowed"
      />
      <button
        type="submit"
        disabled={!canSend}
        aria-label="Ask"
        className={cn(
          'flex h-9 w-9 shrink-0 items-center justify-center rounded transition-colors',
          'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal',
          canSend ? 'bg-signal text-white hover:bg-signal-hover' : 'bg-paper text-muted',
        )}
      >
        <SendIcon />
      </button>
    </form>
  );
}
