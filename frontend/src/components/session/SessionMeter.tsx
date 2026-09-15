import type { TimeRemaining } from '@/hooks/useTimeRemaining';

interface SessionMeterProps {
  time: TimeRemaining | null;
}

/**
 * A hairline across the top of the workspace that empties over the session's
 * 24 hours.
 *
 * The session's whole point is that it ends, so the clock is the one thing
 * given any visual weight -- everything below this line stays quiet.
 */
export function SessionMeter({ time }: SessionMeterProps) {
  const remaining = time ? 1 - time.spent : 1;

  return (
    <div
      className="h-[3px] w-full bg-clock-wash"
      role="progressbar"
      aria-label="Session time remaining"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(remaining * 100)}
      aria-valuetext={time ? `${time.label} remaining` : undefined}
    >
      <div
        className="h-full bg-clock transition-[width] duration-700 ease-out motion-reduce:transition-none"
        style={{ width: `${remaining * 100}%` }}
      />
    </div>
  );
}
