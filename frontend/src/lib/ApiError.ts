/**
 * An error the API returned, carrying the machine-readable code the backend
 * sends alongside its message (`{"detail": {"code": ..., "message": ...}}`).
 *
 * The code is what callers branch on -- NO_SESSION sends someone back to the
 * start, everything else is shown as written.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }

  /** The session is gone: expired, ended, or never started in this browser. */
  get isSessionExpired(): boolean {
    return this.status === 401;
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
