import { useEffect, useState } from 'react'
import { useAuth } from './auth/AuthContext'

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

export function AdminPanel() {
  const { api, user } = useAuth()
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

  if (!isAdmin) {
    return (
      <section className="card full">
        <h2>Admin</h2>
        <p className="muted">Admin or owner role required. You are signed in as {user?.workspace.role}.</p>
      </section>
    )
  }

  return (
    <section className="panel full adminPanel">
      <section className="pageHeader">
        <div>
          <span className="kicker">Enterprise</span>
          <h2 className="displayTitle">Workspace settings</h2>
        </div>
      </section>
      <p className="muted">
        Governance for <strong>{settings?.name || user?.workspace.name}</strong> ({user?.workspace.slug}) — retention,
        quotas, audit trail, data residency.
      </p>
      {error ? <div className="error">{error}</div> : null}

      <div className="adminGrid">
        <div className="adminBlock">
          <h3>Settings</h3>
          <form onSubmit={saveSettings} className="form">
            <label className="field">
              <span>Retention (days)</span>
              <input value={retentionDays} onChange={(e) => setRetentionDays(e.target.value)} />
            </label>
            <label className="field">
              <span>Data region</span>
              <input value={dataRegion} onChange={(e) => setDataRegion(e.target.value)} />
            </label>
            <button className="btn btnPrimary" type="submit" disabled={busy}>
              Save settings
            </button>
          </form>
          <div className="row" style={{ marginTop: 12 }}>
            <button className="btnGhost" type="button" disabled={busy} onClick={() => runPurge(true)}>
              Preview retention purge
            </button>
            <button className="btnGhost" type="button" disabled={busy} onClick={() => runPurge(false)}>
              Run retention purge
            </button>
          </div>
        </div>

        <div className="adminBlock">
          <h3>Usage & quotas ({usage?.period})</h3>
          {usage ? (
            <ul className="sampleMeta">
              <li>
                Meetings: {usage.meetings_created} / {usage.max_meetings_per_month}
              </li>
              <li>
                LLM tokens (est.): {usage.llm_tokens_estimated.toLocaleString()} /{' '}
                {usage.max_llm_tokens_per_month.toLocaleString()}
              </li>
              <li>Analysis cache hits: {usage.cache_hits}</li>
            </ul>
          ) : (
            <div className="muted">Loading…</div>
          )}
        </div>
      </div>

      <div className="adminBlock" style={{ marginTop: 16 }}>
        <h3>Audit log (recent)</h3>
        <div className="auditTable">
          {logs.length === 0 ? (
            <div className="muted">No audit events yet.</div>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="auditRow">
                <code>{log.action}</code>
                <span>
                  {log.resource_type}
                  {log.resource_id ? ` #${log.resource_id}` : ''}
                </span>
                <span className="muted">{new Date(log.created_at).toLocaleString()}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  )
}
