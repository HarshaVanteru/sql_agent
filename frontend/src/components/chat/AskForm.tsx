import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';

import { DatabaseIcon } from '@/components/icons/DatabaseIcon';
import { SendIcon } from '@/components/icons/SendIcon';
import { Spinner } from '@/components/ui';
import { composerClasses } from '@/components/ui/fieldStyles';
import { cn } from '@/lib/cn';

/** Matches the backend's cap, so a long paste is refused here rather than there. */
const MAX_QUESTION = 4000;

/**
 * How little room has to be left before the counter appears.
 *
 * A counter that is always on is noise: for the first 3,600 characters of a
 * 4,000 character budget it reports a number nobody has any use for. It earns
 * its place only once running out is a real possibility.
 */
const COUNTER_APPEARS_AT = 400;

/** Roughly five lines. Past this the box stops growing and starts scrolling. */
const MAX_HEIGHT = 160;

/** Set the box to the height of what is in it, within the cap. */
function fitToContent(element: HTMLTextAreaElement): void {
  // Collapsed first, or scrollHeight only ever reports the current height and
  // the box can grow but never shrink back.
  element.style.height = 'auto';
  element.style.height = `${Math.min(element.scrollHeight, MAX_HEIGHT)}px`;
}

interface AskFormProps {
  onAsk: (question: string) => void;
  pending: boolean;
  disabled: boolean;
  /**
   * The database that will answer this. Named on the composer because the
   * sidebar that otherwise holds it is closed on a phone, so without it you
   * can type a whole question with no idea which database is about to run it.
   */
  connectionName: string;
  /** Whether the last question came back as an error, which decides whether the draft is kept. */
  failed: boolean;
  /** Set from a suggestion chip, to prefill the box. */
  prefill?: string;
}

export function AskForm({
  onAsk,
  pending,
  disabled,
  connectionName,
  failed,
  prefill,
}: AskFormProps) {
  const [question, setQuestion] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const trimmed = question.trim();
  const remaining = MAX_QUESTION - question.length;
  const tooLong = remaining < 0;
  const canSend = trimmed !== '' && !tooLong && !pending && !disabled;

  useEffect(() => {
    if (prefill) {
      setQuestion(prefill);
      textareaRef.current?.focus();
    }
  }, [prefill]);

  // Grow with the question, up to a point, then scroll.
  useEffect(() => {
    if (textareaRef.current) fitToContent(textareaRef.current);
  }, [question]);

  // Width changes rewrap the text and change how tall the box needs to be, and
  // nothing above recomputes it: the question has not changed, so that effect
  // does not run. Rotating a phone, or opening the sidebar over the panel, left
  // the box at its old height with the last line clipped off inside it.
  //
  // The observer watches the element whose height it sets, so it has to be able
  // to tell its own writes from a real resize -- hence the width guard, which
  // is also the only measurement being read.
  useEffect(() => {
    const element = textareaRef.current;
    if (!element) return;

    let lastWidth = element.clientWidth;
    const observer = new ResizeObserver(() => {
      if (element.clientWidth === lastWidth) return;
      lastWidth = element.clientWidth;
      fitToContent(element);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  // The box is cleared when the question has been answered, not when it is
  // sent. Clearing on send meant a request that failed left its error message
  // sitting above an empty box with the question gone, and the only way to
  // retry was to type the whole thing out again.
  const submitted = useRef<string | null>(null);
  const wasPending = useRef(false);
  useEffect(() => {
    const answered = wasPending.current && !pending;
    wasPending.current = pending;
    if (!answered || failed) return;
    // Unless the box has moved on: the composer stays live while the agent
    // works, so the next question may already be half typed into it.
    setQuestion((current) => (current === submitted.current ? '' : current));
  }, [pending, failed]);

  function send() {
    if (!canSend) return;
    submitted.current = question;
    onAsk(trimmed);
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
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-2">
      <div className={cn(composerClasses(tooLong), 'rounded-xl px-3 pb-2.5 pt-2.5')}>
        {/* What this question is about to do, before it is sent: which database
            answers, and -- only once it matters -- how much room is left. */}
        <div className="mb-1.5 flex items-center gap-2">
          <span className="inline-flex min-w-0 items-center gap-1.5 rounded-full border border-rule bg-surface px-2 py-0.5">
            <DatabaseIcon className="h-3 w-3 shrink-0 text-signal-bright" />
            <span className="min-w-0 truncate font-mono text-[0.6875rem] text-slate">
              {connectionName}
            </span>
          </span>

          {remaining <= COUNTER_APPEARS_AT && (
            <span
              className={cn(
                'ml-auto shrink-0 font-mono text-[0.6875rem] tabular-nums',
                tooLong ? 'font-medium text-danger' : 'text-muted',
              )}
            >
              {tooLong
                ? `${(-remaining).toLocaleString()} over`
                : `${remaining.toLocaleString()} left`}
            </span>
          )}
        </div>

        <div className="flex items-end gap-2">
          <label htmlFor="question" className="sr-only">
            Ask {connectionName} a question
          </label>
          <textarea
            id="question"
            ref={textareaRef}
            rows={1}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            aria-invalid={tooLong ? true : undefined}
            placeholder={
              disabled
                ? 'Connect a database first'
                : "Ask in plain English (e.g. 'Which customers ordered most last quarter?')"
            }
            className="max-h-40 min-w-0 flex-1 resize-none bg-transparent py-1.5 text-[0.9375rem] leading-relaxed text-ink placeholder:text-muted focus:outline-none disabled:cursor-not-allowed"
          />

          <button
            type="submit"
            disabled={!canSend}
            aria-label={pending ? 'Waiting for an answer' : 'Ask'}
            className={cn(
              'flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition-colors',
              'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal',
              canSend
                ? 'bg-signal text-white hover:bg-signal-hover'
                : 'border border-rule bg-surface text-muted',
            )}
          >
            {pending ? <Spinner className="text-slate" /> : <SendIcon />}
          </button>
        </div>
      </div>

      {tooLong ? (
        <p role="alert" className="px-1 text-[0.8125rem] text-danger">
          Trim {(-remaining).toLocaleString()} characters to send. The limit is{' '}
          {MAX_QUESTION.toLocaleString()}.
        </p>
      ) : (
        <div className="flex items-center justify-between gap-3 px-1">
          {/* Both of these are true of every query this sends: the guard rejects
              anything that is not a single read, and the driver is given a
              statement timeout of 30 seconds. */}
          <p className="min-w-0 truncate font-serif text-[0.75rem] italic text-muted">
            Queries run read-only, with a 30-second timeout.
          </p>
          <p className="hidden shrink-0 font-mono text-[0.6875rem] text-muted sm:block">
            Shift + Enter for a new line
          </p>
        </div>
      )}
    </form>
  );
}
