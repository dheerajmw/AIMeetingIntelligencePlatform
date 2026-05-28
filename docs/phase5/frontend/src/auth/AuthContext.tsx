import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  createApiClient,
  getStoredToken,
  setStoredToken,
  type ApiClient,
  type AuthTokenResponse,
  type MeResponse,
} from '../api'

type AuthState = {
  api: ApiClient
  user: MeResponse | null
  loading: boolean
  login: (email: string, workspaceSlug?: string) => Promise<void>
  logout: () => void
  refreshMe: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ apiBase, children }: { apiBase: string; children: ReactNode }) {
  const api = useMemo(() => createApiClient(apiBase), [apiBase])
  const [user, setUser] = useState<MeResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshMe = useCallback(async () => {
    const r = await api.apiFetch('/auth/me')
    if (!r.ok) throw new Error(await r.text())
    setUser((await r.json()) as MeResponse)
  }, [api])

  const login = useCallback(
    async (email: string, workspaceSlug = 'default') => {
      const r = await fetch(`${apiBase}/auth/dev-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, workspace_slug: workspaceSlug }),
      })
      if (!r.ok) throw new Error(await r.text())
      const data = (await r.json()) as AuthTokenResponse
      setStoredToken(data.access_token)
      await refreshMe()
    },
    [apiBase, refreshMe],
  )

  const logout = useCallback(() => {
    setStoredToken(null)
    setUser(null)
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        if (getStoredToken()) await refreshMe()
      } catch {
        setStoredToken(null)
        setUser(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [refreshMe])

  const value = useMemo(
    () => ({ api, user, loading, login, logout, refreshMe }),
    [api, user, loading, login, logout, refreshMe],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
