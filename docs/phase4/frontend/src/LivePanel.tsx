import { useEffect, useRef, useState } from 'react'

type LiveSessionDetail = {
  id: number
  title: string | null
  status: string
  last_processed_seq: number
}

type LiveResults = {
  status: string
  is_draft: boolean
  transcript: any | null
  insights: any | null
}

export function LivePanel({ apiBase }: { apiBase: string }) {
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
    const r = await fetch(`${apiBase}/live/sessions/${id}/results`)
    if (!r.ok) throw new Error(await r.text())
    setResults((await r.json()) as LiveResults)
  }

  useEffect(() => {
    if (!sessionId) return
    const handle = window.setInterval(() => {
      refreshResults(sessionId).catch((e) => setError(String(e)))
    }, 3000)
    return () => window.clearInterval(handle)
  }, [sessionId, apiBase])

  async function createSession(): Promise<number> {
    setError(null)
    const r = await fetch(`${apiBase}/live/sessions`, {
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
    const r = await fetch(`${apiBase}/live/sessions/${sessionId}/finalize`, { method: 'POST' })
    if (!r.ok) throw new Error(await r.text())
    const data = (await r.json()) as LiveResults
    setResults(data)
    setStatus(data.status)
  }

  const segments = results?.transcript?.segments || []

  return (
    <section className="card full">
      <h2>Live meeting (Phase 4)</h2>
      <p className="muted">
        Stream microphone audio in chunks over WebSocket. Draft transcript and summary update during the meeting.
      </p>

      <div className="row">
        <label className="field">
          <span>Session title</span>
          <input value={title} onChange={(e) => setTitle(e.target.value)} disabled={!!sessionId} />
        </label>
      </div>

      <div className="exportGrid">
        {!sessionId ? (
          <button className="btn" onClick={() => createSession().catch((e) => setError(String(e)))}>
            Create live session
          </button>
        ) : null}
        {sessionId && !recording ? (
          <button className="btn" onClick={() => startStreaming().catch((e) => setError(String(e)))}>
            Start streaming
          </button>
        ) : null}
        {recording ? (
          <button className="btnGhost" onClick={stopRecording}>
            Stop stream
          </button>
        ) : null}
        {sessionId ? (
          <button className="btnGhost" onClick={() => finalize().catch((e) => setError(String(e)))}>
            Finalize meeting
          </button>
        ) : null}
      </div>

      {sessionId ? (
        <div className="muted">
          Session #{sessionId} · status {status} · draft updates marked <b>Draft</b>
        </div>
      ) : null}
      {error ? <div className="error">{error}</div> : null}

      {results?.insights ? (
        <div className="results">
          <div className="block">
            <h3>{results.is_draft ? 'Draft summary' : 'Final summary'}</h3>
            <p>{results.insights.executive_summary}</p>
          </div>
          <div className="block">
            <h3>Live transcript ({segments.length} segments)</h3>
            <div className="transcript">
              {segments.slice(-40).map((s: any, i: number) => (
                <div key={i} className="transcriptLine">
                  <span className="ts">
                    [{s.start_s?.toFixed?.(1)}-{s.end_s?.toFixed?.(1)}]
                  </span>
                  {s.speaker_id ? <span className="speaker">{s.speaker_id}</span> : null}
                  <span>{s.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  )
}
