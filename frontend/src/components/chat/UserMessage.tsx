import { formatTime } from '@/lib/time';

interface UserMessageProps {
  content: string;
  createdAt: string;
  initials: string;
}

/**
 * The question, as asked.
 *
 * Right-aligned and in the one dark fill the palette has, so scanning back
 * through a long conversation you can find where each exchange began without
 * reading anything -- the answers below it are all pale cards on a pale page.
 */
export function UserMessage({ content, createdAt, initials }: UserMessageProps) {
  return (
    <div className="flex w-full min-w-0 flex-col items-end gap-1.5">
      <div className="flex max-w-full items-start gap-2.5">
        <p className="max-w-prose whitespace-pre-wrap break-words rounded-xl rounded-tr-sm bg-signal-deep px-4 py-2.5 text-[0.9375rem] leading-relaxed text-white">
          {content}
        </p>
        <span
          aria-hidden="true"
          className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-rule bg-raised text-[0.6875rem] font-semibold text-slate"
        >
          {initials}
        </span>
      </div>
      <p className="pr-[2.625rem] font-mono text-[0.6875rem] text-muted">
        {formatTime(createdAt)} &middot; Natural language
      </p>
    </div>
  );
}
