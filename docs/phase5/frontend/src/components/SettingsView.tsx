import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext'

type SettingsTab = 'workspace' | 'usage' | 'audit' | 'security' | 'retention'

type WorkspaceSettings = {
  id: number
  slug: string
  name: string
  data_region: string
  retention_days: number
  max_meetings_per_month: number
  max_llm_tokens_per_month: number
}

type Usage = {
  period: string
  meetings_created: number
  llm_tokens_estimated: number
  cache_hits: number
  max_meetings_per_month: number
  max_llm_tokens_per_month: number
}

type AuditLogItem = {
  id: number
  action: string
  resource_type: string
  resource_id: string | null
  user_id: number | null
  created_at: string
}

export function SettingsView() {
  const { api, user } = useAuth()
  const [tab, setTab] = useState<SettingsTab>('workspace')
  const [settings, setSettings] = useState<WorkspaceSettings | null>(null)
  const [usage, setUsage] = useState<Usage | null>(null)
  const [logs, setLogs] = useState<AuditLogItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [retentionDays, setRetentionDays] = useState('90')
  const [dataRegion, setDataRegion] = useState('us-east-1')

  const isAdmin = user?.workspace.role === 'OWNER' || user?.workspace.role === 'ADMIN'

  async function load() {
    const [sRes, uRes, lRes] = await Promise.all([
      api.apiFetch('/admin/workspace'),
      api.apiFetch('/admin/usage'),
      api.apiFetch('/admin/audit-logs?limit=30'),
    ])
    if (!sRes.ok) throw new Error(await sRes.text())
    if (!uRes.ok) throw new Error(await uRes.text())
    if (!lRes.ok) throw new Error(await lRes.text())
    const s = (await sRes.json()) as WorkspaceSettings
    setSettings(s)
    setRetentionDays(String(s.retention_days))
    setDataRegion(s.data_region)
    setUsage((await uRes.json()) as Usage)
    setLogs((await lRes.json()) as AuditLogItem[])
  }

  useEffect(() => {
    if (isAdmin) load().catch((e) => setError(String(e)))
  }, [isAdmin])

  async function saveSettings(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const r = await api.apiFetch('/admin/workspace', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          retention_days: Number(retentionDays),
          data_region: dataRegion,
        }),
      })
      if (!r.ok) throw new Error(await r.text())
      await load()
    } catch (err) {
      setError(String(err))
    } finally {
      setBusy(false)
    }
  }

  async function runPurge(dryRun: boolean) {
    setBusy(true)
    setError(null)
    try {
      const r = await api.apiFetch(`/admin/retention/purge?dry_run=${dryRun ? 'true' : 'false'}`, {
        method: 'POST',
      })
      if (!r.ok) throw new Error(await r.text())
      const data = (await r.json()) as { purged_meeting_ids: number[]; dry_run: boolean }
      alert(
        dryRun
          ? `Dry run: ${data.purged_meeting_ids.length} meeting(s) would be purged.`
          : `Purged ${data.purged_meeting_ids.length} meeting(s).`,
      )
      await load()
    } catch (err) {
      setError(String(err))
    } finally {
      setBusy(false)
    }
  }

  const tabs: { id: SettingsTab; label: string }[] = [
    { id: 'workspace', label: 'Workspace' },
    { id: 'usage', label: 'Usage' },
    { id: 'audit', label: 'Audit Log' },
    { id: 'security', label: 'Security' },
    { id: 'retention', label: 'Data Retention' },
  ]

  if (!isAdmin) {
    return (
      <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg">
        <h2 className="font-headline-md text-headline-md mb-2">Settings</h2>
        <p className="font-body-sm text-on-surface-variant">
          Admin or owner role required. You are signed in as {user?.workspace.role}.
        </p>
      </div>
    )
  }

  return (
    <>
      <div className="mb-gutter overflow-x-auto scrollbar-hide">
        <nav className="flex gap-2 p-1 bg-surface-container-low rounded-xl border border-outline-variant inline-flex min-w-max">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`px-md py-sm rounded-lg font-metadata text-metadata transition-all ${
                tab === t.id
                  ? 'bg-primary-container text-on-primary-container'
                  : 'text-on-surface-variant hover:bg-surface-container-high'
              }`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {error ? (
        <div className="mb-md p-md bg-error-container border border-error/20 rounded-lg flex items-center gap-sm">
          <span className="material-symbols-outlined text-error">error</span>
          <p className="font-body-sm text-on-error-container">{error}</p>
        </div>
      ) : null}

      {tab === 'workspace' ? (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter">
          <section className="md:col-span-8 bg-surface-container-lowest border border-outline-variant rounded-xl p-lg shadow-sm">
            <h2 className="font-headline-md text-headline-md mb-md">Workspace Identity</h2>
            <div className="space-y-md">
              <div className="flex flex-col md:flex-row md:items-center justify-between p-md bg-surface-container-low rounded-lg border border-outline-variant/30">
                <div>
                  <p className="font-metadata text-metadata text-outline">Workspace Slug</p>
                  <p className="font-body-md text-body-md font-medium">{settings?.slug || user?.workspace.slug}</p>
                </div>
              </div>
              <div className="flex flex-col md:flex-row md:items-center justify-between p-md bg-surface-container-low rounded-lg border border-outline-variant/30">
                <div>
                  <p className="font-metadata text-metadata text-outline">Display Name</p>
                  <p className="font-body-md text-body-md font-medium">{settings?.name || user?.workspace.name}</p>
                </div>
              </div>
              <form onSubmit={saveSettings} className="space-y-md pt-md border-t border-outline-variant">
                <div className="space-y-1">
                  <label className="font-metadata text-metadata text-on-surface-variant">Retention (days)</label>
                  <input
                    className="w-full h-11 px-md bg-surface border border-outline-variant rounded-lg form-input-focus font-body-sm"
                    value={retentionDays}
                    onChange={(e) => setRetentionDays(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-metadata text-metadata text-on-surface-variant">Data region</label>
                  <input
                    className="w-full h-11 px-md bg-surface border border-outline-variant rounded-lg form-input-focus font-body-sm"
                    value={dataRegion}
                    onChange={(e) => setDataRegion(e.target.value)}
                  />
                </div>
                <button
                  type="submit"
                  disabled={busy}
                  className="px-lg py-2 bg-primary text-on-primary rounded-lg font-body-sm hover:opacity-90 disabled:opacity-50"
                >
                  Save settings
                </button>
              </form>
            </div>
          </section>
        </div>
      ) : null}

      {tab === 'usage' ? (
        <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg">
          <h2 className="font-headline-md text-headline-md mb-md">Usage & Quotas ({usage?.period})</h2>
          {usage ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-md">
              <div className="p-md bg-surface-container-low rounded-xl border border-outline-variant">
                <p className="font-metadata text-outline mb-1">Meetings</p>
                <p className="font-headline-md text-headline-md">
                  {usage.meetings_created} / {usage.max_meetings_per_month}
                </p>
              </div>
              <div className="p-md bg-surface-container-low rounded-xl border border-outline-variant">
                <p className="font-metadata text-outline mb-1">LLM tokens (est.)</p>
                <p className="font-headline-md text-headline-md">
                  {usage.llm_tokens_estimated.toLocaleString()} / {usage.max_llm_tokens_per_month.toLocaleString()}
                </p>
              </div>
              <div className="p-md bg-surface-container-low rounded-xl border border-outline-variant">
                <p className="font-metadata text-outline mb-1">Cache hits</p>
                <p className="font-headline-md text-headline-md">{usage.cache_hits}</p>
              </div>
            </div>
          ) : (
            <p className="font-body-sm text-on-surface-variant">Loading…</p>
          )}
        </section>
      ) : null}

      {tab === 'audit' ? (
        <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg overflow-x-auto">
          <h2 className="font-headline-md text-headline-md mb-md">Audit Log</h2>
          {logs.length === 0 ? (
            <p className="font-body-sm text-on-surface-variant">No audit events yet.</p>
          ) : (
            <table className="w-full font-body-sm">
              <thead>
                <tr className="border-b border-outline-variant text-left">
                  <th className="py-2 font-metadata text-on-surface-variant">Action</th>
                  <th className="py-2 font-metadata text-on-surface-variant">Resource</th>
                  <th className="py-2 font-metadata text-on-surface-variant">Time</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-outline-variant/30">
                    <td className="py-3 font-code text-primary">{log.action}</td>
                    <td className="py-3 text-on-surface-variant">
                      {log.resource_type}
                      {log.resource_id ? ` #${log.resource_id}` : ''}
                    </td>
                    <td className="py-3 text-on-surface-variant">{new Date(log.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      ) : null}

      {tab === 'security' ? (
        <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg">
          <h2 className="font-headline-md text-headline-md mb-md">Security</h2>
          <div className="space-y-md">
            <div className="p-md bg-surface-container-low rounded-lg flex gap-md">
              <span className="material-symbols-outlined text-primary">lock</span>
              <div>
                <p className="font-metadata text-metadata">Encryption at rest</p>
                <p className="font-body-sm text-on-surface-variant">Meeting artifacts encrypted with workspace keys.</p>
              </div>
            </div>
            <div className="p-md bg-surface-container-low rounded-lg flex gap-md">
              <span className="material-symbols-outlined text-primary">verified_user</span>
              <div>
                <p className="font-metadata text-metadata">RBAC</p>
                <p className="font-body-sm text-on-surface-variant">
                  Your role: {user?.workspace.role}. Workspace isolation enforced on all API routes.
                </p>
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {tab === 'retention' ? (
        <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg">
          <h2 className="font-headline-md text-headline-md mb-md">Data Retention</h2>
          <p className="font-body-sm text-on-surface-variant mb-md">
            Current retention policy: {settings?.retention_days ?? retentionDays} days.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={busy}
              className="px-md py-2 border border-outline-variant rounded-lg font-body-sm hover:bg-surface-container-low disabled:opacity-50"
              onClick={() => runPurge(true)}
            >
              Preview retention purge
            </button>
            <button
              type="button"
              disabled={busy}
              className="px-md py-2 bg-error-container text-on-error-container rounded-lg font-body-sm hover:opacity-90 disabled:opacity-50"
              onClick={() => runPurge(false)}
            >
              Run retention purge
            </button>
          </div>
        </section>
      ) : null}
    </>
  )
}
