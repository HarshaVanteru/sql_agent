import { useAuth } from '../context/AuthContext'
import { apiFetch, toError } from './client'

// Authenticated API calls bound to the current session. On a 401 it refreshes
// the access token once and retries the request; if the refresh fails it logs
// out. Returns the parsed JSON body (or null for an empty response).
//
// Auth endpoints (login/signup/refresh/logout) deliberately do NOT go through
// this -- a failed login is a real 401, not a token to refresh -- so those call
// apiFetch directly in AuthContext.
export function useApi() {
  const { token, refreshAccessToken, logout } = useAuth()

  const request = async (path, options = {}) => {
    let response = await apiFetch(path, { ...options, token })

    if (response.status === 401) {
      const refreshed = await refreshAccessToken()
      if (!refreshed.success) {
        logout()
        throw new Error('Session expired. Please log in again.')
      }
      response = await apiFetch(path, {
        ...options,
        token: localStorage.getItem('auth_token'),
      })
    }

    if (!response.ok) throw await toError(response)
    return response.status === 204 ? null : response.json()
  }

  return {
    get: (path) => request(path, { method: 'GET' }),
    post: (path, body) => request(path, { method: 'POST', body }),
    del: (path) => request(path, { method: 'DELETE' }),
  }
}
