import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('auth_token'))
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refresh_token'))
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('auth_token')
      if (storedToken) {
        try {
          // Verify token is still valid
          const response = await fetch('http://localhost:8000/auth/me', {
            headers: { Authorization: `Bearer ${storedToken}` }
          })

          if (response.ok) {
            const data = await response.json()
            setToken(storedToken)
            setUser(data.user)
          } else {
            // Token is invalid, clear it
            localStorage.removeItem('auth_token')
            localStorage.removeItem('refresh_token')
            setToken(null)
            setRefreshToken(null)
          }
        } catch (err) {
          // Error checking token, clear it
          localStorage.removeItem('auth_token')
          localStorage.removeItem('refresh_token')
          setToken(null)
          setRefreshToken(null)
        }
      }
      setLoading(false)
    }

    initializeAuth()
  }, [])

  const signup = async (email, password, firstName, lastName) => {
    setError(null)
    try {
      const response = await fetch('http://localhost:8000/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          first_name: firstName,
          last_name: lastName,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail?.message || 'Signup failed')
      }

      const data = await response.json()
      return { success: true, userId: data.user_id, message: data.message }
    } catch (err) {
      setError(err.message)
      return { success: false, error: err.message }
    }
  }

  const login = async (email, password) => {
    setError(null)
    try {
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail?.message || 'Login failed')
      }

      const data = await response.json()
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      setToken(data.access_token)
      setRefreshToken(data.refresh_token)
      setUser(data.user)
      return { success: true }
    } catch (err) {
      setError(err.message)
      return { success: false, error: err.message }
    }
  }

  const refreshAccessToken = async () => {
    if (!refreshToken) {
      setError('No refresh token available')
      return { success: false }
    }

    try {
      const response = await fetch('http://localhost:8000/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail?.message || 'Token refresh failed')
      }

      const data = await response.json()
      localStorage.setItem('auth_token', data.access_token)
      setToken(data.access_token)
      return { success: true }
    } catch (err) {
      setError(err.message)
      logout()
      return { success: false, error: err.message }
    }
  }

  const logout = async () => {
    const storedToken = localStorage.getItem('auth_token')
    const storedRefresh = localStorage.getItem('refresh_token')

    // Clear locally regardless of whether the server call lands: the refresh
    // session is revoked server-side, but a failed request must not strand the
    // user in a logged-in UI.
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
    setToken(null)
    setRefreshToken(null)
    setUser(null)
    setError(null)

    if (storedToken) {
      try {
        await fetch('http://localhost:8000/auth/logout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${storedToken}`,
          },
          body: JSON.stringify({ refresh_token: storedRefresh }),
        })
      } catch {
        // Already signed out locally; nothing useful to surface.
      }
    }
  }

  const clearError = () => setError(null)

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        error,
        signup,
        login,
        refreshAccessToken,
        logout,
        clearError,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
