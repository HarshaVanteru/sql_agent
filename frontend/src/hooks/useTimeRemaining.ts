import { useEffect, useState } from 'react';

import { elapsedFraction, formatDuration, msUntil } from '@/lib/time';

const TICK_MS = 30_000;

export interface TimeRemaining {
  /** "23h 41m", or "expired". */
  label: string;
  /** How much of the session has been spent, 0 to 1. Drives the meter. */
  spent: number;
  expired: boolean;
}

/**
 * How long is left in the session, recomputed on a slow tick.
 *
 * Every 30 seconds, not every second: the display is in minutes, so a faster
 * tick would re-render the whole workspace to change nothing.
 */
export function useTimeRemaining(startedAt?: string, expiresAt?: string): TimeRemaining | null {
  const [, setTick] = useState(0);

  useEffect(() => {
    if (!expiresAt) return;
    const id = window.setInterval(() => setTick((n) => n + 1), TICK_MS);
    return () => window.clearInterval(id);
  }, [expiresAt]);

  if (!startedAt || !expiresAt) return null;

  const remaining = msUntil(expiresAt);
  return {
    label: formatDuration(remaining),
    spent: elapsedFraction(startedAt, expiresAt),
    expired: remaining <= 0,
  };
}
