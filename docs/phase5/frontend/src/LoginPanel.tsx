import { useState } from 'react'
import { useAuth } from './auth/AuthContext'

export function LoginPanel() {
  const { login } = useAuth()
  const [email, setEmail] = useState('admin@example.com')
  const [workspace, setWorkspace] = useState('default')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(email.trim(), workspace.trim() || 'default')
    } catch (err) {
      setError(String(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="bg-background text-on-surface font-body-md selection:bg-primary-fixed selection:text-on-primary-fixed min-h-screen flex items-center justify-center p-margin-mobile md:p-margin-desktop overflow-x-hidden relative">
      <div className="fixed inset-0 bento-bg opacity-20 pointer-events-none" />
      <div className="fixed top-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary-container/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="fixed bottom-[-10%] left-[-10%] w-[30%] h-[30%] bg-tertiary-container/5 rounded-full blur-[100px] pointer-events-none" />

      <main className="w-full max-w-[440px] z-10">
        <div className="flex flex-col items-center mb-lg">
          <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mb-md shadow-lg shadow-primary/20">
            <span className="material-symbols-outlined text-on-primary text-[28px] filled">analytics</span>
          </div>
          <h1 className="font-headline-md text-headline-md text-on-surface text-center">MeetIQ</h1>
          <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
            Precision insights for high-performance teams
          </p>
        </div>

        <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg md:p-xl shadow-sm">
          {error ? (
            <div className="mb-lg p-md bg-error-container border border-error/20 rounded-lg flex items-center gap-sm">
              <span className="material-symbols-outlined text-error text-[20px]">error</span>
              <p className="font-metadata text-on-error-container">{error}</p>
            </div>
          ) : null}

          <div className="space-y-lg">
            <button
              type="button"
              className="w-full h-12 bg-primary hover:bg-primary-container text-on-primary font-body-md rounded-lg flex items-center justify-center gap-sm transition-all duration-200 active:scale-[0.98] shadow-sm opacity-60 cursor-not-allowed"
              disabled
            >
              <span className="material-symbols-outlined text-[20px]">key</span>
              Sign in with SSO
            </button>

            <div className="relative flex items-center py-sm">
              <div className="flex-grow border-t border-outline-variant" />
              <span className="flex-shrink mx-md font-caption text-caption text-outline uppercase tracking-widest">
                or
              </span>
              <div className="flex-grow border-t border-outline-variant" />
            </div>

            <form className="space-y-md" onSubmit={onSubmit}>
              <div className="space-y-1">
                <label className="font-metadata text-metadata text-on-surface-variant block ml-1" htmlFor="workspace">
                  Workspace Slug
                </label>
                <div className="relative">
                  <input
                    id="workspace"
                    className="w-full h-11 px-md bg-surface border border-outline-variant rounded-lg font-body-sm text-body-sm text-on-surface placeholder:text-outline/50 form-input-focus transition-all"
                    placeholder="acme-corp"
                    value={workspace}
                    onChange={(e) => setWorkspace(e.target.value)}
                  />
                  <div className="absolute right-md top-1/2 -translate-y-1/2 font-metadata text-caption text-outline">
                    .meetiq.ai
                  </div>
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-metadata text-metadata text-on-surface-variant block ml-1" htmlFor="email">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  className="w-full h-11 px-md bg-surface border border-outline-variant rounded-lg font-body-sm text-body-sm text-on-surface placeholder:text-outline/50 form-input-focus transition-all"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>

              <button
                className="w-full h-11 mt-md border border-outline-variant hover:bg-surface-container-low text-on-surface font-metadata text-body-sm rounded-lg transition-all duration-200 active:scale-[0.98] disabled:opacity-60"
                type="submit"
                disabled={busy}
              >
                {busy ? 'Signing in…' : 'Continue with Email'}
              </button>
            </form>
          </div>
        </div>

        <footer className="mt-xl flex flex-col items-center gap-sm">
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Dev login: admin@example.com · workspace <span className="text-primary font-medium">default</span>
          </p>
        </footer>
      </main>

      <div className="hidden lg:block fixed left-12 bottom-12 max-w-[280px]">
        <div className="bg-surface-container-low/50 backdrop-blur-md border border-outline-variant/30 rounded-xl p-md">
          <div className="flex items-center gap-sm mb-sm">
            <div className="w-8 h-8 rounded-full bg-tertiary-fixed-dim flex items-center justify-center">
              <span className="material-symbols-outlined text-on-tertiary-fixed text-[18px]">auto_awesome</span>
            </div>
            <div className="h-2 w-24 bg-outline-variant rounded-full" />
          </div>
          <div className="space-y-1">
            <div className="h-2 w-full bg-outline-variant/40 rounded-full" />
            <div className="h-2 w-4/5 bg-outline-variant/40 rounded-full" />
            <div className="h-2 w-3/4 bg-outline-variant/40 rounded-full" />
          </div>
          <p className="font-caption text-caption text-on-surface-variant mt-md italic">
            &ldquo;Transcribing and analyzing your quarterly review in real-time…&rdquo;
          </p>
        </div>
      </div>
    </div>
  )
}
