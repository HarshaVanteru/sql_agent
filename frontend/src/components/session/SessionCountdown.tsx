import { ClockIcon } from '@/components/icons/ClockIcon';
import { PlusIcon } from '@/components/icons/PlusIcon';
import type { TimeRemaining } from '@/hooks/useTimeRemaining';
import { cn } from '@/lib/cn';

interface SessionCountdownProps {
  time: TimeRemaining | null;
  /** When given, the pill is a button that opens the extend dialog. */
  onExtend?: () => void;
}

/**
 * How long the session has left, as a pill that empties as it goes.
 *
 * This replaced a hairline meter across the very top of the window, which read
 * as a page-loading bar -- the one thing a thin coloured line at the top edge
 * of a browser always reads as. The meter is still here, as a wash filling the
 * pill from the left, so the same information is attached to the words that
 * explain it instead of floating above the whole app.
 *
 * It is also where more time is asked for, so the one control that shows the
 * problem is the one that fixes it. With a handler it is a button and says so
 * in its name; without one it is a plain meter.
 */
export function SessionCountdown({ time, onExtend }: SessionCountdownProps) {
  if (!time) return null;

  const remaining = Math.max(0, 1 - time.spent);
  const interactive = Boolean(onExtend) && !time.expired;
  const Tag = interactive ? 'button' : 'span';

  return (
    <Tag
      {...(interactive
        ? {
            type: 'button' as const,
            onClick: onExtend,
            'aria-label': `${time.label} left in this session. Extend session`,
            title: 'Extend session',
          }
        : {
            role: 'progressbar',
            'aria-label': 'Session time remaining',
            'aria-valuemin': 0,
            'aria-valuemax': 100,
            'aria-valuenow': Math.round(remaining * 100),
            'aria-valuetext': time.expired ? 'Session expired' : `${time.label} remaining`,
          })}
      className={cn(
        'relative isolate inline-flex shrink-0 items-center gap-1.5 overflow-hidden rounded-full border px-2.5 py-1',
        'font-mono text-[0.75rem]',
        time.expired ? 'border-danger/40 text-danger' : 'border-clock/35 bg-clock-wash text-clock',
        interactive &&
          'transition-colors hover:border-clock focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal',
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
      {interactive && <PlusIcon className="h-3 w-3 shrink-0" />}
    </Tag>
  );
}
