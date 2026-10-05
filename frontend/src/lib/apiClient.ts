import { ApiError, type ErrorDebug } from './ApiError';

const BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

type Body = Record<string, unknown> | undefined;

interface RequestOptions {
  method?: 'GET' | 'POST' | 'DELETE';
  body?: Body;
  signal?: AbortSignal;
}

/**
 * Turn an error body into an ApiError.
 *
 * The backend normalises its own validation failures into the same
 * {code, message, fields, debug} shape as everything else (see
 * app/core/errors.py), so there is one shape to read here. `debug` is only
 * present when the backend is configured to send diagnostics.
 */
function readError(status: number, payload: unknown): ApiError {
  const detail = (payload as { detail?: unknown } | null)?.detail;

  if (detail && typeof detail === 'object' && 'code' in detail) {
    const { code, message, fields, debug } = detail as {
      code: string;
      message?: string;
      fields?: Record<string, string>;
      debug?: ErrorDebug;
    };
    return new ApiError(status, code, message ?? 'Request failed.', fields ?? {}, debug);
  }

  if (typeof detail === 'string') return new ApiError(status, 'ERROR', detail);
  return new ApiError(status, 'ERROR', `Request failed (${status}).`);
}

/**
 * The single place a network call is made.
 *
 * `credentials: 'include'` on every request is what carries the session cookie
 * to the API, which sits on a different origin. Without it there is no session
 * and every call comes back 401.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, signal } = options;

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      credentials: 'include',
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') throw cause;
    throw new ApiError(0, 'NETWORK_ERROR', 'Cannot reach the API. Is the backend running?');
  }

  if (response.status === 204) return undefined as T;

  const payload = await response.json().catch(() => null);
  if (!response.ok) throw readError(response.status, payload);
  return payload as T;
}
