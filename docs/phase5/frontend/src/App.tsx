import { useEffect, useMemo, useState } from 'react'
import { LoginPanel } from './LoginPanel'
import { LivePanel } from './LivePanel'
import type { SampleItem } from './SampleShowcase'
import { AuthProvider, useAuth } from './auth/AuthContext'
import { DashboardView } from './components/DashboardView'
import { IntegrationsView } from './components/IntegrationsView'
import { MeetingDetailView } from './components/MeetingDetailView'
import { MeetingsView } from './components/MeetingsView'
import { NewMeetingView } from './components/NewMeetingView'
import { SettingsView } from './components/SettingsView'
import { AppLayout, type AppView, type NavView } from './layout/AppLayout'
import { ThemeProvider } from './theme/ThemeProvider'
import type { ExportRecord, MeetingDetail, MeetingListItem, MeetingResults } from './types'

function AppShell() {
  const { api, user, loading, logout } = useAuth()

  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState('')
  const [meetingStart, setMeetingStart] = useState('')
  const [timezone, setTimezone] = useState('Asia/Kolkata')
  const [enableDiarization, setEnableDiarization] = useState(true)

  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [meetings, setMeetings] = useState<MeetingListItem[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [selected, setSelected] = useState<MeetingDetail | null>(null)
  const [results, setResults] = useState<MeetingResults | null>(null)
  const [exports, setExports] = useState<ExportRecord[]>([])
  const [exportBusy, setExportBusy] = useState(false)
  const [view, setView] = useState<AppView>('dashboard')

  async function refreshMeetings() {
    const r = await api.apiFetch('/meetings')
    if (!r.ok) throw new Error(await r.text())
    const data = (await r.json()) as MeetingListItem[]
    setMeetings(data)
  }

  async function loadMeeting(id: number) {
    const [mRes, rRes, eRes] = await Promise.all([
      api.apiFetch(`/meetings/${id}`),
      api.apiFetch(`/meetings/${id}/results`),
      api.apiFetch(`/meetings/${id}/integrations/exports`),
    ])
    if (!mRes.ok) throw new Error(await mRes.text())
    if (!rRes.ok) throw new Error(await rRes.text())
    setSelected((await mRes.json()) as MeetingDetail)
    setResults((await rRes.json()) as MeetingResults)
    if (eRes.ok) setExports((await eRes.json()) as ExportRecord[])
  }

  async function exportMeeting(
    provider: 'jira' | 'linear' | 'trello' | 'slack' | 'email',
    exportKind: 'action_items' | 'summary',
    emailTo?: string,
  ) {
    if (selectedId == null) return
    setExportBusy(true)
    setError(null)
    try {
      const r = await api.apiFetch(`/meetings/${selectedId}/integrations/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          export_kind: exportKind,
          force: true,
          ...(provider === 'email' && emailTo?.trim() ? { email_to: emailTo.trim() } : {}),
        }),
      })
      if (!r.ok) {
        const text = await r.text()
        try {
          const parsed = JSON.parse(text) as { detail?: string }
          throw new Error(parsed.detail || text)
        } catch (e) {
          if (e instanceof Error && e.message !== text) throw e
          throw new Error(text)
        }
      }
      await loadMeeting(selectedId)
    } catch (err) {
      setError(String(err))
    } finally {
      setExportBusy(false)
    }
  }

  async function submitMeeting(fd: FormData) {
    const r = await api.apiFetch('/meetings', { method: 'POST', body: fd })
    if (!r.ok) throw new Error(await r.text())
    const created = (await r.json()) as { id: number }
    await refreshMeetings()
    setSelectedId(created.id)
    return created
  }

  async function onUpload(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (!file) {
      setError('Please choose an audio file.')
      return
    }

    const fd = new FormData()
    fd.append('file', file)
    if (title.trim()) fd.append('title', title.trim())
    if (meetingStart.trim()) fd.append('meeting_start', meetingStart.trim())
    if (timezone.trim()) fd.append('timezone', timezone.trim())
    fd.append('enable_diarization', enableDiarization ? 'true' : 'false')

    setBusy(true)
    try {
      await submitMeeting(fd)
      setFile(null)
      setTitle('')
      setMeetingStart('')
      setView('meeting-detail')
    } catch (err) {
      setError(String(err))
    } finally {
      setBusy(false)
    }
  }

  async function trySample(sample: SampleItem) {
    setError(null)
    setBusy(true)
    try {
      const r = await api.apiFetch(`/samples/${sample.id}/process`, { method: 'POST' })
      if (!r.ok) throw new Error(await r.text())
      const created = (await r.json()) as { id: number }
      await refreshMeetings()
      setSelectedId(created.id)
      setView('meeting-detail')
      if (sample.meeting_start) setMeetingStart(sample.meeting_start)
      if (sample.timezone) setTimezone(sample.timezone)
    } catch (err) {
      setError(String(err))
      throw err
    } finally {
      setBusy(false)
    }
  }

  function navigate(nav: NavView) {
    setView(nav)
    if (nav !== 'meetings') setError(null)
  }

  function openMeeting(id: number) {
    setSelectedId(id)
    setView('meeting-detail')
  }

  useEffect(() => {
    if (!user) return
    refreshMeetings().catch((e) => setError(String(e)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  useEffect(() => {
    if (!user || selectedId == null || view !== 'meeting-detail') return
    let cancelled = false

    const tick = async () => {
      try {
        await loadMeeting(selectedId)
        if (!cancelled) setError(null)
      } catch (e) {
        if (!cancelled) setError(String(e))
      }
    }

    tick()
    const handle = window.setInterval(tick, 4000)
    return () => {
      cancelled = true
      window.clearInterval(handle)
    }
  }, [selectedId, api, user, view])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-on-surface font-body-md">
        Loading session…
      </div>
    )
  }

  if (!user) {
    return <LoginPanel />
  }

  const showFab = view === 'meetings'

  return (
    <AppLayout
      view={view}
      onNavigate={navigate}
      workspaceName={user.workspace.name}
      userName={user.display_name}
      userRole={user.workspace.role}
      onLogout={logout}
      showFab={showFab}
      onFabClick={() => setView('new-meeting')}
    >
      {view === 'dashboard' ? (
        <DashboardView
          userName={user.display_name}
          workspaceName={user.workspace.name}
          meetings={meetings}
          onSelectMeeting={openMeeting}
          onViewAll={() => setView('meetings')}
          onUpload={() => setView('new-meeting')}
          onLive={() => setView('live')}
        />
      ) : null}

      {view === 'meetings' ? (
        <MeetingsView
          meetings={meetings}
          onSelectMeeting={openMeeting}
          onRefresh={() => refreshMeetings().catch((e) => setError(String(e)))}
        />
      ) : null}

      {view === 'new-meeting' ? (
        <NewMeetingView
          api={api}
          busy={busy}
          file={file}
          setFile={setFile}
          title={title}
          meetingStart={meetingStart}
          timezone={timezone}
          enableDiarization={enableDiarization}
          onTitleChange={setTitle}
          onMeetingStartChange={setMeetingStart}
          onTimezoneChange={setTimezone}
          onDiarizationChange={setEnableDiarization}
          onUpload={onUpload}
          onTrySample={trySample}
          error={error}
        />
      ) : null}

      {view === 'meeting-detail' && selected ? (
        <MeetingDetailView
          meeting={selected}
          results={results}
          exports={exports}
          exportBusy={exportBusy}
          onBack={() => setView('meetings')}
          onExport={exportMeeting}
        />
      ) : null}

      {view === 'meeting-detail' && !selected && selectedId != null ? (
        <div className="font-body-sm text-on-surface-variant">Loading meeting…</div>
      ) : null}

      {view === 'live' ? <LivePanel api={api} /> : null}
      {view === 'integrations' ? <IntegrationsView /> : null}
      {view === 'settings' ? <SettingsView /> : null}
    </AppLayout>
  )
}

function App() {
  const apiBase = useMemo(
    () => (import.meta.env.VITE_API_BASE as string) || 'http://127.0.0.1:8002',
    [],
  )
  return (
    <ThemeProvider>
      <AuthProvider apiBase={apiBase}>
        <AppShell />
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
