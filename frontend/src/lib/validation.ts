/**
 * Field rules.
 *
 * Each returns a message when the value is wrong and undefined when it is fine,
 * so a field's rules compose by running until one speaks up. The messages say
 * what to do, not what failed a check.
 */
export type Rule<T> = (value: T) => string | undefined;

export function required(label: string): Rule<string> {
  return (value) => (value.trim() === '' ? `${label} is required` : undefined);
}

export function maxLength(limit: number, label: string): Rule<string> {
  return (value) => (value.length > limit ? `${label} must be ${limit} characters or fewer` : undefined);
}

/**
 * A bare hostname or address.
 *
 * Mirrors the backend's check so the same paste -- a URL, or a whole connection
 * string out of a password manager -- is caught before a round trip.
 */
export function hostname(): Rule<string> {
  return (value) => {
    const host = value.trim();
    if (host === '') return 'Host is required';
    if (host.includes('://')) return 'Enter just the hostname, without http:// or a driver prefix';
    if (host.includes('/') || host.includes('@')) {
      return 'Enter just the hostname — no username, password or database path';
    }
    if (/\s/.test(host)) return 'Host cannot contain spaces';
    return undefined;
  };
}

export function port(): Rule<number> {
  return (value) => {
    if (!Number.isInteger(value) || Number.isNaN(value)) return 'Port must be a whole number';
    if (value < 1 || value > 65535) return 'Port must be between 1 and 65535';
    return undefined;
  };
}

/** Run a field's rules, returning the first complaint. */
export function firstError<T>(value: T, rules: Array<Rule<T>>): string | undefined {
  for (const rule of rules) {
    const message = rule(value);
    if (message) return message;
  }
  return undefined;
}
