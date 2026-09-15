const MINUTE = 60_000;
const HOUR = 60 * MINUTE;

/** Milliseconds until `isoTimestamp`, floored at zero. */
export function msUntil(isoTimestamp: string): number {
  return Math.max(0, new Date(isoTimestamp).getTime() - Date.now());
}

/**
 * How much of a window has been used, 0 to 1.
 * Drives the meter across the top of the workspace.
 */
export function elapsedFraction(startIso: string, endIso: string): number {
  const start = new Date(startIso).getTime();
  const end = new Date(endIso).getTime();
  if (end <= start) return 1;
  return Math.min(1, Math.max(0, (Date.now() - start) / (end - start)));
}

/**
 * A duration as someone would say it: "23h 41m", "48m", "under a minute".
 * Hours and minutes only -- seconds ticking down would pull the eye away from
 * the work for information nobody acts on.
 */
export function formatDuration(ms: number): string {
  if (ms <= 0) return 'expired';
  if (ms < MINUTE) return 'under a minute';

  const hours = Math.floor(ms / HOUR);
  const minutes = Math.floor((ms % HOUR) / MINUTE);
  if (hours === 0) return `${minutes}m`;
  return minutes === 0 ? `${hours}h` : `${hours}h ${minutes}m`;
}

/** A timestamp as a short local time, for conversation rows. */
export function formatTime(isoTimestamp: string): string {
  return new Date(isoTimestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}
