const TOKEN_KEY = 'ami_access_token'

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setStoredToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export function createApiClient(apiBase: string) {
  async function apiFetch(path: string, init: RequestInit = {}) {
    const headers = new Headers(init.headers)
    const token = getStoredToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
    const response = await fetch(`${apiBase}${path}`, { ...init, headers })
    return response
  }

  return { apiBase, apiFetch }
}

export type ApiClient = ReturnType<typeof createApiClient>

export type AuthTokenResponse = {
  access_token: string
  workspace_id: number
  workspace_slug: string
  role: string
  user_email: string
  user_display_name: string
}

export type MeResponse = {
  user_id: number
  email: string
  display_name: string
  workspace: {
    id: number
    slug: string
    name: string
    data_region: string
    role: string
  }
  workspaces: Array<{
    id: number
    slug: string
    name: string
    data_region: string
    role: string
  }>
}
