const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/** Milliseconds until `isoTimestamp`, floored at zero. */
export function msUntil(isoTimestamp: string): number {
  return Math.max(0, new Date(isoTimestamp).getTime() - Date.now());
}

/**
 * A duration as someone would say it: "6d 4h", "23h 41m", "48m", "under a minute".
 * Hours and minutes only -- seconds ticking down would pull the eye away from
 * the work for information nobody acts on.
 */
export function formatDuration(ms: number): string {
  if (ms <= 0) return 'expired';
  if (ms < MINUTE) return 'under a minute';

  // Past two days, hours are noise: "6d 4h" says everything "148h" does, faster.
  if (ms >= 2 * DAY) {
    const days = Math.floor(ms / DAY);
    const rest = Math.floor((ms % DAY) / HOUR);
    return rest === 0 ? `${days}d` : `${days}d ${rest}h`;
  }

  const hours = Math.floor(ms / HOUR);
  const minutes = Math.floor((ms % HOUR) / MINUTE);
  if (hours === 0) return `${minutes}m`;
  return minutes === 0 ? `${hours}h` : `${hours}h ${minutes}m`;
}

/** A timestamp as a short local time, for conversation rows. */
export function formatTime(isoTimestamp: string): string {
  return new Date(isoTimestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

/**
 * The heading a timestamp belongs under in the history list: "Today",
 * "Yesterday", then the date itself.
 *
 * Compared by calendar day rather than by elapsed hours, so something asked at
 * 11pm is still "Today" at 11:30pm and becomes "Yesterday" at midnight --
 * which is how people talk about it, and not what a 24-hour window would say.
 */
export function dayLabel(isoTimestamp: string, now: Date = new Date()): string {
  const then = new Date(isoTimestamp);
  const days = calendarDaysBetween(then, now);
  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 7) return then.toLocaleDateString([], { weekday: 'long' });
  return then.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function calendarDaysBetween(earlier: Date, later: Date): number {
  const a = new Date(earlier.getFullYear(), earlier.getMonth(), earlier.getDate());
  const b = new Date(later.getFullYear(), later.getMonth(), later.getDate());
  return Math.round((b.getTime() - a.getTime()) / 86_400_000);
}
