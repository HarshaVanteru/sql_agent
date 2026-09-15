/**
 * An error the API returned.
 *
 * Every failure from this backend has the same shape:
 *
 *   {"detail": {"code": "INVALID_CREDENTIALS", "message": "Invalid hostname ..."}}
 *
 * and a validation failure adds a per-field map:
 *
 *   {"detail": {"code": "VALIDATION_ERROR", "message": "...",
 *               "fields": {"credentials.host": "Host is required"}}}
 *
 * `code` is what callers branch on; `message` is already written for a reader,
 * so it is shown as-is rather than being translated into something vaguer.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  /** Field path -> message, e.g. "credentials.host". Empty for non-validation errors. */
  readonly fields: Record<string, string>;

  constructor(status: number, code: string, message: string, fields: Record<string, string> = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.fields = fields;
  }

  /** The session is gone: expired, ended, or never started in this browser. */
  get isSessionExpired(): boolean {
    return this.status === 401 || this.code === 'NO_SESSION';
  }

  /**
   * The backend is up but cannot serve right now -- its session store is
   * unreachable, or it fell over on its own.
   *
   * Distinct from an expired session on purpose. Both fail the same calls, but
   * one means "start again" and the other means "wait a moment and retry", and
   * sending someone to the start screen during an outage just moves them to a
   * page where starting also fails.
   */
  get isTemporary(): boolean {
    return this.status === 503 || this.status === 0 || this.code === 'NETWORK_ERROR';
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

/** A message safe to put in front of a person, whatever was thrown. */
export function errorMessage(error: unknown, fallback = 'Something went wrong.'): string {
  if (isApiError(error)) return error.message;
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

/** The per-field messages an error carries, or an empty map. */
export function errorFields(error: unknown): Record<string, string> {
  return isApiError(error) ? error.fields : {};
}
