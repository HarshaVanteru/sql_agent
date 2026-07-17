// Central API client: one place for the backend base URL and the fetch
// mechanics, so components don't each hardcode http://localhost:8000.
//
// The base URL comes from VITE_API_URL at build time, falling back to the local
// dev server. See .env.example.
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Low-level request. Prefixes the API base, JSON-encodes a `body` (and sets the
// content-type), and attaches a bearer `token` when given. Returns the raw
// Response so callers can inspect the status.
export function apiFetch(path, { token, body, headers, ...rest } = {}) {
  return fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  })
}

// Turn a failed Response into an Error carrying the API's message and status.
export async function toError(response, fallback = 'Request failed') {
  let message = fallback
  try {
    const data = await response.json()
    message = data.detail?.message || fallback
  } catch {
    // Non-JSON error body; keep the fallback message.
  }
  const error = new Error(message)
  error.status = response.status
  return error
}
