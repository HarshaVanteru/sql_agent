import { ApiError } from './ApiError';

const BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

type Body = Record<string, unknown> | undefined;

interface RequestOptions {
  method?: 'GET' | 'POST' | 'DELETE';
  body?: Body;
  signal?: AbortSignal;
}

/** Pull a usable message out of whatever shape the error body arrived in. */
function readError(status: number, payload: unknown): ApiError {
  const detail = (payload as { detail?: unknown } | null)?.detail;

  if (detail && typeof detail === 'object' && 'code' in detail) {
    const { code, message } = detail as { code: string; message?: string };
    return new ApiError(status, code, message ?? 'Request failed.');
  }

  // FastAPI's validation errors arrive as a list of field problems.
  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: string; loc?: unknown[] } | undefined;
    const field = Array.isArray(first?.loc) ? first.loc.at(-1) : undefined;
    const reason = first?.msg ?? 'Check the values and try again.';
    return new ApiError(status, 'VALIDATION_ERROR', field ? `${String(field)}: ${reason}` : reason);
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
