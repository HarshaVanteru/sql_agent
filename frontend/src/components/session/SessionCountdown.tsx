import { ClockIcon } from '@/components/icons/ClockIcon';
import type { TimeRemaining } from '@/hooks/useTimeRemaining';
import { cn } from '@/lib/cn';

interface SessionCountdownProps {
  time: TimeRemaining | null;
}

/**
 * How long the session has left, as a pill that empties as it goes.
 *
 * This replaced a hairline meter across the very top of the window, which read
 * as a page-loading bar -- the one thing a thin coloured line at the top edge
 * of a browser always reads as. The meter is still here, as a wash filling the
 * pill from the left, so the same information is attached to the words that
 * explain it instead of floating above the whole app.
 */
export function SessionCountdown({ time }: SessionCountdownProps) {
  if (!time) return null;

  const remaining = Math.max(0, 1 - time.spent);

  return (
    <span
      role="progressbar"
      aria-label="Session time remaining"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(remaining * 100)}
      aria-valuetext={time.expired ? 'Session expired' : `${time.label} remaining`}
      className={cn(
        'relative isolate inline-flex items-center gap-1.5 overflow-hidden rounded-full border px-2.5 py-1',
        'font-mono text-[0.75rem]',
        time.expired ? 'border-danger/40 text-danger' : 'border-clock/35 bg-clock-wash text-clock',
      )}
    >
      {!time.expired && (
        <span
          aria-hidden="true"
          className="absolute inset-y-0 left-0 -z-10 bg-clock/10 transition-[width] duration-700 ease-out motion-reduce:transition-none"
          style={{ width: `${remaining * 100}%` }}
        />
      )}
      <ClockIcon className="h-3.5 w-3.5 shrink-0" />
      {time.expired ? 'Session expired' : `${time.label} left`}
    </span>
  );
}
