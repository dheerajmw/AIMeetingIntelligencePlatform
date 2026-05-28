import { useEffect, useState } from 'react'

export type SampleItem = {
  id: string
  dataset: string
  title: string
  description: string
  filename: string
  duration_s: number
  language: string
  meeting_start: string | null
  timezone: string | null
  source_url: string | null
  available: boolean
}

type Props = {
  apiBase: string
  busy: boolean
  onTrySample: (sample: SampleItem) => Promise<void>
}

export function SampleShowcase({ apiBase, busy, onTrySample }: Props) {
  const [samples, setSamples] = useState<SampleItem[]>([])
  const [loading, setLoading] = useState(true)
  const [activeId, setActiveId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${apiBase}/samples`)
      .then(async (r) => {
        if (!r.ok) throw new Error(await r.text())
        const data = (await r.json()) as { samples: SampleItem[] }
        setSamples(data.samples)
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false))
  }, [apiBase])

  async function handleTry(sample: SampleItem) {
    setError(null)
    setActiveId(sample.id)
    try {
      await onTrySample(sample)
    } catch (e) {
      setError(String(e))
    } finally {
      setActiveId(null)
    }
  }

  const ami = samples.filter((s) => s.dataset.includes('AMI'))
  const icsi = samples.filter((s) => s.dataset.includes('ICSI'))

  return (
    <section className="card full sampleShowcase">
      <h2>Try sample meetings (new here?)</h2>
      <p className="muted">
        One-click demos from public research corpora. No upload needed — uses bundled clips from the{' '}
        <strong>AMI</strong> and <strong>ICSI</strong> meeting datasets (see problem statement).
      </p>

      {loading ? <div className="muted">Loading samples…</div> : null}
      {error ? <div className="error">{error}</div> : null}

      {ami.length ? (
        <div className="sampleGroup">
          <h3>AMI Meeting Corpus</h3>
          <p className="muted small">
            ~100h of recorded meetings; headset mix WAV, 16 kHz. Good for STT + summary testing.
          </p>
          <div className="sampleGrid">
            {ami.map((s) => (
              <SampleCard
                key={s.id}
                sample={s}
                busy={busy || activeId === s.id}
                onTry={() => handleTry(s)}
              />
            ))}
          </div>
        </div>
      ) : null}

      {icsi.length ? (
        <div className="sampleGroup">
          <h3>ICSI Meeting Corpus</h3>
          <p className="muted small">
            ~72h of natural academic meetings; multi-speaker close-talk audio. Tests speaker overlap and
            attribution.
          </p>
          <div className="sampleGrid">
            {icsi.map((s) => (
              <SampleCard
                key={s.id}
                sample={s}
                busy={busy || activeId === s.id}
                onTry={() => handleTry(s)}
              />
            ))}
          </div>
        </div>
      ) : null}

      <div className="sampleGroup">
        <h3>QMSum (text benchmark)</h3>
        <p className="muted small">
          Transcript + human summaries only (no audio). Use for summary-quality benchmarking, not upload.
        </p>
        <a
          className="btnGhost"
          href="https://github.com/Yale-LILY/QMSum"
          target="_blank"
          rel="noreferrer"
        >
          View QMSum on GitHub
        </a>
      </div>
    </section>
  )
}

function SampleCard({
  sample,
  busy,
  onTry,
}: {
  sample: SampleItem
  busy: boolean
  onTry: () => void
}) {
  return (
    <article className="sampleCard">
      <div className="sampleBadge">{sample.dataset}</div>
      <div className="sampleTitle">{sample.title}</div>
      <p className="sampleDesc">{sample.description}</p>
      <ul className="sampleMeta">
        <li>{sample.duration_s}s</li>
        <li>{sample.language}</li>
        <li>{sample.filename}</li>
      </ul>
      {sample.source_url ? (
        <a className="sampleLink" href={sample.source_url} target="_blank" rel="noreferrer">
          Corpus homepage
        </a>
      ) : null}
      <button
        className="btn"
        type="button"
        disabled={busy || !sample.available}
        onClick={onTry}
      >
        {busy ? 'Processing…' : 'Try this sample'}
      </button>
      {!sample.available ? (
        <div className="muted small">Sample file not on disk yet.</div>
      ) : null}
    </article>
  )
}
