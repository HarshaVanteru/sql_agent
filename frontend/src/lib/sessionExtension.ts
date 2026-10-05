import type { ExtensionOption } from '@/types';

const HOUR = 3_600_000;
const DAY = 24 * HOUR;

/**
 * No session may have more than this left, however many times it is extended.
 * Mirrors SESSION_MAX_LIFETIME_SECONDS on the server, which is what enforces it;
 * it is repeated here only so the dialog can show the outcome before asking.
 */
export const MAX_LIFETIME_MS = 30 * DAY;

/** Under this, an extension is not worth offering. Mirrors the server's threshold. */
const MIN_GAIN_MS = 60_000;

export const EXTENSION_OPTIONS: ReadonlyArray<{
  value: ExtensionOption;
  label: string;
  ms: number;
}> = [
  { value: '24h', label: '24 hours', ms: DAY },
  { value: '7d', label: '7 days', ms: 7 * DAY },
  { value: '30d', label: '30 days', ms: 30 * DAY },
];

export interface ProjectedExtension {
  /** When the session would end after this extension. */
  expiresAt: Date;
  /** The option would be cut short by the 30-day limit. */
  clamped: boolean;
  /** The option would add nothing: the session is already at the limit. */
  noGain: boolean;
}

/** What extending by `ms` would do, using the same add-then-cap rule as the server. */
export function projectExtension(
  expiresAtIso: string,
  ms: number,
  now: number = Date.now(),
): ProjectedExtension {
  const current = new Date(expiresAtIso).getTime();
  const cap = now + MAX_LIFETIME_MS;
  const next = Math.min(current + ms, cap);
  return {
    expiresAt: new Date(next),
    clamped: current + ms > cap,
    noGain: next - current < MIN_GAIN_MS,
  };
}
