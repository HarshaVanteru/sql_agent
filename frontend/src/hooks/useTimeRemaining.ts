import { useEffect, useState } from 'react';

import { formatDuration, msUntil } from '@/lib/time';

const TICK_MS = 30_000;
const DAY_MS = 86_400_000;

export interface TimeRemaining {
  /** "23h 41m", or "expired". */
  label: string;
  /**
   * How much of the final day has been spent, 0 to 1. Drives the meter.
   *
   * Measured against the last 24 hours rather than the whole session: after a
   * 30-day extension a meter spanning the full length would sit at "full" for
   * weeks and say nothing. This way it is full while there is more than a day
   * left, and only starts to drain when it is worth noticing.
   */
  spent: number;
  expired: boolean;
  /** Less than a day left: the point at which extending is worth suggesting. */
  low: boolean;
}

/**
 * How long is left in the session, recomputed on a slow tick.
 *
 * Every 30 seconds, not every second: the display is in minutes, so a faster
 * tick would re-render the whole workspace to change nothing.
 */
export function useTimeRemaining(expiresAt?: string): TimeRemaining | null {
  const [, setTick] = useState(0);

  useEffect(() => {
    if (!expiresAt) return;
    const id = window.setInterval(() => setTick((n) => n + 1), TICK_MS);
    return () => window.clearInterval(id);
  }, [expiresAt]);

  if (!expiresAt) return null;

  const remaining = msUntil(expiresAt);
  return {
    label: formatDuration(remaining),
    spent: 1 - Math.min(1, remaining / DAY_MS),
    expired: remaining <= 0,
    low: remaining < DAY_MS,
  };
}
