import { useEffect, useMemo, useState } from 'react'
import './App.css'

type MeetingListItem = {
  id: number
  title: string | null
  created_at: string
  status: string
  original_filename: string
}

type MeetingDetail = {
  id: number
  title: string | null
  created_at: string
  status: string
  original_filename: string
  meeting_start: string | null
  timezone: string | null
  error_message: string | null
}

type MeetingResults = {
  status: string
  transcript: any | null
  insights: any | null
}

function formatTimestampRange(range: { start_s?: number; end_s?: number } | null | undefined) {
  if (!range || range.start_s == null || range.end_s == null) return 'Not identified'
  return `${range.start_s.toFixed(1)}s – ${range.end_s.toFixed(1)}s`
}

function formatConfidence(value: number | null | undefined) {
  if (value == null) return 'Not identified'
  return `${Math.round(value * 100)}%`
}

function App() {
  const apiBase = useMemo(
    () => (import.meta.env.VITE_API_BASE as string) || 'http://localhost:8000',
    [],
  )

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

  async function refreshMeetings() {
    const r = await fetch(`${apiBase}/meetings`)
    if (!r.ok) throw new Error(await r.text())
    const data = (await r.json()) as MeetingListItem[]
    setMeetings(data)
    if (data.length > 0 && selectedId == null) setSelectedId(data[0].id)
  }

  async function loadMeeting(id: number) {
    const [mRes, rRes] = await Promise.all([
      fetch(`${apiBase}/meetings/${id}`),
      fetch(`${apiBase}/meetings/${id}/results`),
    ])
    if (!mRes.ok) throw new Error(await mRes.text())
    if (!rRes.ok) throw new Error(await rRes.text())
    setSelected((await mRes.json()) as MeetingDetail)
    setResults((await rRes.json()) as MeetingResults)
  }

  useEffect(() => {
    refreshMeetings().catch((e) => setError(String(e)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (selectedId == null) return
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
  }, [selectedId, apiBase])

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
      const r = await fetch(`${apiBase}/meetings`, { method: 'POST', body: fd })
      if (!r.ok) throw new Error(await r.text())
      const created = (await r.json()) as { id: number; status: string }
      await refreshMeetings()
      setSelectedId(created.id)
      setFile(null)
      setTitle('')
      setMeetingStart('')
    } catch (err) {
      setError(String(err))
    } finally {
      setBusy(false)
    }
  }

  const transcriptSegments = results?.transcript?.segments || []

  return (
    <div className="page">
      <header className="header">
        <div>
          <div className="kicker">MeetIQ</div>
          <h1>Phase 2 — Quality Upgrades</h1>
          <p className="subtitle">
            Speaker-labeled transcripts, evidence-backed decisions, and richer action items with due dates and confidence.
          </p>
        </div>
        <div className="api">
          <span className="pill">API</span>
          <code>{apiBase}</code>
        </div>
      </header>

      <main className="grid">
        <section className="card">
          <h2>Upload</h2>
          <form onSubmit={onUpload} className="form">
            <label className="field">
              <span>Recording</span>
              <input
                type="file"
                accept=".mp3,.wav,.m4a,.mp4,.mov,audio/*,video/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </label>

            <label className="field">
              <span>Meeting title (optional)</span>
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Sprint planning" />
            </label>

            <div className="row">
              <label className="field">
                <span>Meeting start ISO (recommended for due dates)</span>
                <input
                  value={meetingStart}
                  onChange={(e) => setMeetingStart(e.target.value)}
                  placeholder="2026-05-27T10:00:00+05:30"
                />
              </label>
              <label className="field">
                <span>Timezone (optional)</span>
                <input value={timezone} onChange={(e) => setTimezone(e.target.value)} placeholder="Asia/Kolkata" />
              </label>
            </div>

            <label className="checkboxField">
              <input
                type="checkbox"
                checked={enableDiarization}
                onChange={(e) => setEnableDiarization(e.target.checked)}
              />
              <span>Enable speaker labeling (pause-based diarization)</span>
            </label>

            <button className="btn" type="submit" disabled={busy}>
              {busy ? 'Uploading…' : 'Upload & Process'}
            </button>

            {error ? <div className="error">{error}</div> : null}
          </form>
        </section>

        <section className="card">
          <div className="cardHeader">
            <h2>Meetings</h2>
            <button className="btnGhost" onClick={() => refreshMeetings().catch((e) => setError(String(e)))}>
              Refresh
            </button>
          </div>
          <div className="list">
            {meetings.length === 0 ? (
              <div className="muted">No meetings yet. Upload one to get started.</div>
            ) : (
              meetings.map((m) => (
                <button
                  key={m.id}
                  className={`listItem ${selectedId === m.id ? 'active' : ''}`}
                  onClick={() => setSelectedId(m.id)}
                >
                  <div className="listTitle">{m.title || m.original_filename}</div>
                  <div className="listMeta">
                    <span className="status">{m.status}</span>
                    <span>#{m.id}</span>
                  </div>
                </button>
              ))
            )}
          </div>
        </section>

        <section className="card full">
          <div className="cardHeader">
            <h2>Results</h2>
            {selected ? <span className="statusBig">{selected.status}</span> : null}
          </div>

          {!selected ? (
            <div className="muted">Select a meeting to view status and results.</div>
          ) : (
            <>
              {selected.error_message ? <div className="error">{selected.error_message}</div> : null}

              <div className="metaGrid">
                <div>
                  <div className="metaLabel">Meeting</div>
                  <div className="metaValue">{selected.title || selected.original_filename}</div>
                </div>
                <div>
                  <div className="metaLabel">Meeting start</div>
                  <div className="metaValue">{selected.meeting_start || 'Not provided'}</div>
                </div>
                <div>
                  <div className="metaLabel">Timezone</div>
                  <div className="metaValue">{selected.timezone || 'Not provided'}</div>
                </div>
              </div>

              {results?.insights ? (
                <div className="results">
                  <div className="block">
                    <h3>Executive summary</h3>
                    <p>{results.insights.executive_summary}</p>
                  </div>

                  <div className="block">
                    <h3>Key discussion points</h3>
                    <ul>
                      {(results.insights.key_discussion_points || []).map((p: string, i: number) => (
                        <li key={i}>{p}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="block">
                    <h3>Decisions made</h3>
                    {(results.insights.decisions_made || []).length ? (
                      <ul className="cards">
                        {results.insights.decisions_made.map((d: any, i: number) => (
                          <li key={i} className="miniCard">
                            <div className="miniTitle">{d.decision}</div>
                            <div className="miniMeta">
                              <span>
                                <b>Owner:</b> {d.owner}
                              </span>
                              <span>
                                <b>Due date:</b> {d.due_date}
                              </span>
                              <span>
                                <b>Confidence:</b> {formatConfidence(d.confidence)}
                              </span>
                              <span>
                                <b>Timestamp:</b> {formatTimestampRange(d.timestamp_range)}
                              </span>
                            </div>
                            <div className="evidence">
                              <b>Evidence:</b> {d.evidence_quote || 'Not identified'}
                            </div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="muted">No decisions detected.</div>
                    )}
                  </div>

                  <div className="block">
                    <h3>Action items</h3>
                    {(results.insights.action_items || []).length ? (
                      <ul className="cards">
                        {results.insights.action_items.map((a: any, i: number) => (
                          <li key={i} className="miniCard">
                            <div className="miniTitle">{a.title || a.action}</div>
                            {a.description ? <div className="miniDesc">{a.description}</div> : null}
                            <div className="miniMeta">
                              <span>
                                <b>Owner:</b> {a.owner}
                              </span>
                              <span>
                                <b>Due date:</b> {a.due_date || a.deadline}
                              </span>
                              <span>
                                <b>Priority:</b> {a.priority || 'Not identified'}
                              </span>
                              <span>
                                <b>Confidence:</b> {formatConfidence(a.confidence)}
                              </span>
                              <span>
                                <b>Timestamp:</b> {formatTimestampRange(a.timestamp_range)}
                              </span>
                            </div>
                            <div className="evidence">
                              <b>Evidence:</b> {a.evidence_quote || 'Not identified'}
                            </div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="muted">No action items detected.</div>
                    )}
                  </div>

                  {transcriptSegments.length ? (
                    <div className="block">
                      <h3>Transcript (speaker-labeled)</h3>
                      <div className="transcript">
                        {transcriptSegments.slice(0, 120).map((s: any, i: number) => (
                          <div key={i} className="transcriptLine">
                            <span className="ts">
                              [{s.start_s?.toFixed?.(1) ?? s.start_s}-{s.end_s?.toFixed?.(1) ?? s.end_s}]
                            </span>
                            {s.speaker_id ? <span className="speaker">{s.speaker_id}</span> : null}
                            <span>{s.text}</span>
                          </div>
                        ))}
                        {transcriptSegments.length > 120 ? (
                          <div className="muted">Showing first 120 segments…</div>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : (
                <div className="muted">
                  {selected.status === 'READY'
                    ? 'Results are ready but not loaded.'
                    : 'Processing… this view auto-refreshes every few seconds.'}
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
