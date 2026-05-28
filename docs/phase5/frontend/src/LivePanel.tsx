import { useEffect, useRef, useState } from 'react'
import type { ApiClient } from './api'

type LiveSessionDetail = {
  id: number
  title: string | null
  status: string
  last_processed_seq: number
}

type LiveResults = {
  status: string
  is_draft: boolean
  transcript: { segments?: Array<{ start_s?: number; end_s?: number; text?: string; speaker_id?: string }> } | null
  insights: { executive_summary?: string } | null
}

export function LivePanel({ api }: { api: ApiClient }) {
  const apiBase = api.apiBase
  const [title, setTitle] = useState('Live meeting')
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [status, setStatus] = useState<string>('idle')
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<LiveResults | null>(null)
  const [recording, setRecording] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const seqRef = useRef(1)
  const recorderRef = useRef<MediaRecorder | null>(null)

  async function refreshResults(id: number) {
    const r = await api.apiFetch(`/live/sessions/${id}/results`)
    if (!r.ok) throw new Error(await r.text())
    setResults((await r.json()) as LiveResults)
  }

  useEffect(() => {
    if (!sessionId) return
    const handle = window.setInterval(() => {
      refreshResults(sessionId).catch((e) => setError(String(e)))
    }, 3000)
    return () => window.clearInterval(handle)
  }, [sessionId, api])

  async function createSession(): Promise<number> {
    setError(null)
    const r = await api.apiFetch('/live/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, timezone: 'Asia/Kolkata' }),
    })
    if (!r.ok) throw new Error(await r.text())
    const data = (await r.json()) as LiveSessionDetail
    setSessionId(data.id)
    setStatus(data.status)
    seqRef.current = data.last_processed_seq + 1
    return data.id
  }

  async function startStreaming() {
    const id = sessionId ?? (await createSession())
    const url = apiBase.replace(/^http/, 'ws') + `/live/sessions/${id}/stream`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data)
      if (msg.type === 'draft_update') {
        setResults({
          status: 'ACTIVE',
          is_draft: true,
          transcript: msg.transcript,
          insights: msg.insights,
        })
      }
      if (msg.type === 'session_state') {
        seqRef.current = (msg.last_processed_seq ?? 0) + 1
      }
      if (msg.type === 'ack') {
        seqRef.current = Math.max(seqRef.current, (msg.last_processed_seq ?? 0) + 1)
      }
      if (msg.type === 'error') setError(msg.message)
    }

    ws.onopen = async () => {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      recorderRef.current = recorder
      recorder.ondataavailable = async (evt) => {
        if (!evt.data.size || ws.readyState !== WebSocket.OPEN) return
        const buf = await evt.data.arrayBuffer()
        const bytes = new Uint8Array(buf)
        let binary = ''
        for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i])
        const b64 = btoa(binary)
        ws.send(
          JSON.stringify({
            type: 'audio_chunk',
            seq: seqRef.current,
            format: 'wav',
            data_base64: b64,
          }),
        )
      }
      recorder.start(5000)
      setRecording(true)
      setStatus('ACTIVE')
    }

    ws.onerror = () => setError('WebSocket error')
  }

  function stopRecording() {
    recorderRef.current?.stop()
    wsRef.current?.close()
    setRecording(false)
  }

  async function finalize() {
    if (!sessionId) return
    stopRecording()
    const r = await api.apiFetch(`/live/sessions/${sessionId}/finalize`, { method: 'POST' })
    if (!r.ok) throw new Error(await r.text())
    const data = (await r.json()) as LiveResults
    setResults(data)
    setStatus(data.status)
  }

  const segments = results?.transcript?.segments || []

  return (
    <>
      <section className="mb-md">
        <h2 className="font-display text-display text-on-surface flex items-center gap-2 flex-wrap">
          Live Meeting
          {results?.is_draft ? (
            <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 dark:bg-amber-500/10 dark:text-amber-400 text-caption font-bold uppercase border border-amber-200">
              Draft
            </span>
          ) : null}
        </h2>
        <p className="font-body-sm text-on-surface-variant mt-1">
          Stream microphone audio in chunks. Draft outputs update until you finalize.
        </p>
      </section>

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-md bg-surface-container-lowest p-md rounded-xl border border-outline-variant mb-md">
        <div>
          <p className="font-metadata text-metadata text-on-surface-variant uppercase tracking-wider mb-1">
            Session status
          </p>
          <div className="flex items-center gap-2">
            {recording ? (
              <div className="flex items-center bg-surface-container-low px-sm py-1 rounded-xl border border-outline-variant">
                <div className="w-2 h-2 rounded-full bg-error pulse-red mr-2" />
                <span className="text-caption font-metadata uppercase tracking-wider text-on-surface-variant">
                  Live
                </span>
              </div>
            ) : (
              <span className="font-body-md text-on-surface">{status}</span>
            )}
            {sessionId ? (
              <span className="font-caption text-on-surface-variant">· Session #{sessionId}</span>
            ) : null}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {!sessionId ? (
            <button
              type="button"
              className="flex items-center gap-2 px-md py-2 bg-primary text-on-primary rounded-xl font-body-sm hover:opacity-90 transition-all"
              onClick={() => createSession().catch((e) => setError(String(e)))}
            >
              <span className="material-symbols-outlined text-[20px]">add</span>
              Create session
            </button>
          ) : null}
          {sessionId && !recording ? (
            <button
              type="button"
              className="flex items-center gap-2 px-md py-2 bg-primary text-on-primary rounded-xl font-body-sm hover:opacity-90 transition-all"
              onClick={() => startStreaming().catch((e) => setError(String(e)))}
            >
              <span className="material-symbols-outlined text-[20px]">sensors</span>
              Start streaming
            </button>
          ) : null}
          {recording ? (
            <button
              type="button"
              className="flex items-center gap-2 px-md py-2 border border-outline-variant rounded-xl font-body-sm hover:bg-surface-container-low"
              onClick={stopRecording}
            >
              Stop stream
            </button>
          ) : null}
          {sessionId ? (
            <button
              type="button"
              className="flex items-center gap-2 px-md py-2 bg-surface-container-high text-primary rounded-xl border border-primary-fixed-dim font-body-sm hover:bg-surface-container-highest"
              onClick={() => finalize().catch((e) => setError(String(e)))}
            >
              Finalize meeting
            </button>
          ) : null}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-md">
        <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md">
          <h3 className="font-headline-md text-headline-md mb-md">Session controls</h3>
          <div className="space-y-1 mb-md">
            <label className="font-metadata text-metadata text-on-surface-variant ml-1">Session title</label>
            <input
              className="w-full h-11 px-md bg-surface border border-outline-variant rounded-lg form-input-focus font-body-sm"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={!!sessionId}
            />
          </div>
          {error ? (
            <div className="p-md bg-error-container border border-error/20 rounded-lg flex items-center gap-sm">
              <span className="material-symbols-outlined text-error">error</span>
              <p className="font-body-sm text-on-error-container">{error}</p>
            </div>
          ) : null}
        </section>

        <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md">
          <h3 className="font-headline-md text-headline-md mb-md flex items-center gap-2">
            Live output
            {results?.is_draft ? (
              <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 text-[10px] font-bold uppercase">
                Draft
              </span>
            ) : null}
          </h3>
          {results?.insights ? (
            <div className="space-y-md">
              <div>
                <p className="font-metadata text-metadata text-primary mb-2">
                  {results.is_draft ? 'Rolling summary' : 'Final summary'}
                </p>
                <p className="font-body-md text-on-surface leading-relaxed">{results.insights.executive_summary}</p>
              </div>
              <div>
                <p className="font-metadata text-metadata text-primary mb-2">
                  Transcript ({segments.length} segments)
                </p>
                <div className="space-y-2 max-h-[320px] overflow-y-auto">
                  {segments.slice(-40).map((s, i) => (
                    <div key={i} className="flex gap-2 font-body-sm">
                      <span className="text-caption text-on-surface-variant shrink-0 font-code">
                        [{s.start_s?.toFixed?.(1)}–{s.end_s?.toFixed?.(1)}]
                      </span>
                      {s.speaker_id ? (
                        <span className="font-metadata text-primary shrink-0">{s.speaker_id}</span>
                      ) : null}
                      <span>{s.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="font-body-sm text-on-surface-variant">Start a session to see draft transcript and summary here.</p>
          )}
        </section>
      </div>
    </>
  )
}
