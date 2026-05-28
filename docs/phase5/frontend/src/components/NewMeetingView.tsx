import { useEffect, useState } from 'react'
import type { SampleItem } from '../SampleShowcase'
import type { ApiClient } from '../api'

type Props = {
  api: ApiClient
  busy: boolean
  file: File | null
  setFile: (f: File | null) => void
  title: string
  meetingStart: string
  timezone: string
  enableDiarization: boolean
  onTitleChange: (v: string) => void
  onMeetingStartChange: (v: string) => void
  onTimezoneChange: (v: string) => void
  onDiarizationChange: (v: boolean) => void
  onUpload: (e: React.FormEvent) => void
  onTrySample: (sample: SampleItem) => Promise<void>
  error: string | null
}

export function NewMeetingView({
  api,
  busy,
  file,
  setFile,
  title,
  meetingStart,
  timezone,
  enableDiarization,
  onTitleChange,
  onMeetingStartChange,
  onTimezoneChange,
  onDiarizationChange,
  onUpload,
  onTrySample,
  error,
}: Props) {
  const [dragOver, setDragOver] = useState(false)
  const [samples, setSamples] = useState<SampleItem[]>([])
  const [sampleBusy, setSampleBusy] = useState<string | null>(null)

  useEffect(() => {
    api
      .apiFetch('/samples')
      .then(async (r: Response) => {
        if (!r.ok) throw new Error(await r.text())
        const data = (await r.json()) as { samples: SampleItem[] }
        setSamples(data.samples.filter((s) => s.available))
      })
      .catch(() => {})
  }, [api])

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) setFile(f)
  }

  async function handleSample(sample: SampleItem) {
    setSampleBusy(sample.id)
    try {
      await onTrySample(sample)
    } finally {
      setSampleBusy(null)
    }
  }

  return (
    <>
      <section className="mb-8">
        <h2 className="font-display text-display mb-2">New Meeting</h2>
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          Upload a recording or try a bundled sample to process intelligence.
        </p>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-xl">
        <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg">
          <h3 className="font-headline-md text-headline-md mb-md">Upload recording</h3>
          <form onSubmit={onUpload} className="space-y-md">
            <div
              className={`border-2 border-dashed rounded-xl p-xl flex flex-col items-center justify-center text-center transition-colors ${
                dragOver ? 'border-primary bg-surface-container-low drag-active' : 'border-outline-variant'
              }`}
              onDragOver={(e) => {
                e.preventDefault()
                setDragOver(true)
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
            >
              <span className="material-symbols-outlined text-primary text-[48px] mb-md">cloud_upload</span>
              <p className="font-body-md text-on-surface mb-1">
                {file ? file.name : 'Drag & drop your recording here'}
              </p>
              <p className="font-caption text-caption text-on-surface-variant mb-md">MP3, WAV, M4A, MP4 supported</p>
              <label className="cursor-pointer px-md py-2 bg-primary text-on-primary rounded-lg font-body-sm hover:opacity-90 transition-opacity">
                Browse files
                <input
                  type="file"
                  className="hidden"
                  accept=".mp3,.wav,.m4a,.mp4,.mov,audio/*,video/*"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                />
              </label>
            </div>

            <div className="space-y-1">
              <label className="font-metadata text-metadata text-on-surface-variant ml-1">Meeting title</label>
              <input
                className="w-full h-11 px-md bg-surface border border-outline-variant rounded-lg font-body-sm form-input-focus"
                placeholder="Sprint planning"
                value={title}
                onChange={(e) => onTitleChange(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
              <div className="space-y-1">
                <label className="font-metadata text-metadata text-on-surface-variant ml-1">Meeting start (ISO)</label>
                <input
                  className="w-full h-11 px-md bg-surface border border-outline-variant rounded-lg font-body-sm form-input-focus"
                  placeholder="2026-05-27T10:00:00+05:30"
                  value={meetingStart}
                  onChange={(e) => onMeetingStartChange(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="font-metadata text-metadata text-on-surface-variant ml-1">Timezone</label>
                <input
                  className="w-full h-11 px-md bg-surface border border-outline-variant rounded-lg font-body-sm form-input-focus"
                  placeholder="Asia/Kolkata"
                  value={timezone}
                  onChange={(e) => onTimezoneChange(e.target.value)}
                />
              </div>
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={enableDiarization}
                onChange={(e) => onDiarizationChange(e.target.checked)}
                className="rounded border-outline-variant text-primary focus:ring-primary"
              />
              <span className="font-body-sm text-on-surface">Enable speaker labeling</span>
            </label>

            <button
              type="submit"
              disabled={busy || !file}
              className="w-full h-11 bg-primary text-on-primary rounded-lg font-body-sm hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined text-[20px]">upload</span>
              {busy ? 'Uploading…' : 'Upload & Process'}
            </button>

            {error ? (
              <div className="p-md bg-error-container border border-error/20 rounded-lg flex items-center gap-sm">
                <span className="material-symbols-outlined text-error text-[20px]">error</span>
                <p className="font-body-sm text-on-error-container">{error}</p>
              </div>
            ) : null}
          </form>
        </section>

        <section className="bg-surface-container-lowest border border-outline-variant rounded-xl p-lg">
          <h3 className="font-headline-md text-headline-md mb-md">Try sample meetings</h3>
          <p className="font-body-sm text-on-surface-variant mb-md">
            One-click demos from AMI and ICSI research corpora — no upload needed.
          </p>
          <div className="space-y-3 max-h-[480px] overflow-y-auto">
            {samples.length === 0 ? (
              <p className="font-body-sm text-on-surface-variant">Loading samples…</p>
            ) : (
              samples.map((s) => (
                <div
                  key={s.id}
                  className="p-md bg-surface-container-low border border-outline-variant/30 rounded-xl"
                >
                  <div className="flex justify-between items-start gap-2 mb-2">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-primary bg-primary-fixed px-2 py-0.5 rounded">
                        {s.dataset}
                      </span>
                      <h4 className="font-body-md font-semibold text-on-surface mt-1">{s.title}</h4>
                    </div>
                  </div>
                  <p className="font-caption text-caption text-on-surface-variant mb-3">{s.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="font-caption text-on-surface-variant">
                      {s.duration_s}s · {s.language}
                    </span>
                    <button
                      type="button"
                      disabled={busy || sampleBusy === s.id}
                      className="px-md py-1.5 bg-primary text-on-primary rounded-lg font-caption hover:opacity-90 disabled:opacity-50"
                      onClick={() => handleSample(s)}
                    >
                      {sampleBusy === s.id ? 'Processing…' : 'Try sample'}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </>
  )
}
