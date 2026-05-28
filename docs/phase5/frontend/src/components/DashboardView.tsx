import type { MeetingListItem } from '../types'
import { meetingIcon } from '../lib/format'
import { StatusBadge } from './StatusBadge'

type Props = {
  userName: string
  workspaceName: string
  meetings: MeetingListItem[]
  onSelectMeeting: (id: number) => void
  onViewAll: () => void
  onUpload: () => void
  onLive: () => void
}

export function DashboardView({
  userName,
  workspaceName,
  meetings,
  onSelectMeeting,
  onViewAll,
  onUpload,
  onLive,
}: Props) {
  const ready = meetings.filter((m) => m.status === 'READY').length
  const processing = meetings.filter(
    (m) => !['READY', 'FAILED_TRANSCRIPTION', 'FAILED_ANALYSIS'].includes(m.status),
  ).length
  const recent = meetings.slice(0, 5)
  const firstName = userName.split(' ')[0]

  return (
    <>
      <section className="mb-lg">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <span className="font-metadata text-metadata text-primary uppercase tracking-wider">
              Welcome back, {firstName}
            </span>
            <h2 className="font-display text-display text-on-surface mt-1">{workspaceName}</h2>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              className="flex items-center gap-2 px-md py-2.5 bg-primary text-on-primary rounded-xl font-body-sm hover:opacity-90 active:scale-95 transition-all"
              onClick={onUpload}
            >
              <span className="material-symbols-outlined text-[20px]">upload</span>
              Upload recording
            </button>
            <button
              type="button"
              className="flex items-center gap-2 px-md py-2.5 bg-surface-container-high text-primary rounded-xl border border-primary-fixed-dim font-body-sm hover:bg-surface-container-highest active:scale-95 transition-all"
              onClick={onLive}
            >
              <span className="material-symbols-outlined text-[20px]">sensors</span>
              Start live
            </button>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-gutter mb-xl">
        <div className="bg-surface-container-lowest border border-outline-variant p-md rounded-xl flex flex-col justify-between min-h-[112px]">
          <div className="flex justify-between items-start">
            <span className="material-symbols-outlined text-secondary opacity-60">groups</span>
          </div>
          <div>
            <div className="font-display text-headline-lg text-on-surface">{meetings.length}</div>
            <div className="font-caption text-caption text-on-surface-variant">Total meetings</div>
          </div>
        </div>
        <div className="bg-surface-container-lowest border border-outline-variant p-md rounded-xl flex flex-col justify-between min-h-[112px]">
          <div className="flex justify-between items-start">
            <span className="material-symbols-outlined text-primary">assignment_late</span>
            {ready > 0 ? (
              <span className="bg-primary-container/10 px-1.5 py-0.5 rounded text-[10px] font-bold text-primary">
                ACTIVE
              </span>
            ) : null}
          </div>
          <div>
            <div className="font-display text-headline-lg text-primary">{ready}</div>
            <div className="font-caption text-caption text-on-surface-variant">Ready for review</div>
          </div>
        </div>
        <div className="bg-surface-container-lowest border border-outline-variant p-md rounded-xl flex flex-col justify-between min-h-[112px]">
          <div className="flex justify-between items-start">
            <span className="material-symbols-outlined text-tertiary">gavel</span>
          </div>
          <div>
            <div className="font-display text-headline-lg text-on-surface">{ready}</div>
            <div className="font-caption text-caption text-on-surface-variant">Processed</div>
          </div>
        </div>
        <div className="bg-surface-container-lowest border border-outline-variant p-md rounded-xl flex flex-col justify-between min-h-[112px]">
          <div className="flex justify-between items-start">
            <span className="material-symbols-outlined text-outline">sync</span>
            {processing > 0 ? (
              <div className="w-2 h-2 rounded-full bg-tertiary-fixed-dim animate-pulse" />
            ) : null}
          </div>
          <div>
            <div className="font-display text-headline-lg text-on-surface">{processing}</div>
            <div className="font-caption text-caption text-on-surface-variant">Processing queue</div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-xl">
        <section className="lg:col-span-2">
          <div className="flex items-center justify-between mb-md">
            <h3 className="font-headline-md text-headline-md text-on-surface">Recent Meetings</h3>
            <button type="button" className="text-primary font-metadata text-metadata hover:underline" onClick={onViewAll}>
              View all
            </button>
          </div>
          <div className="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-hidden">
            {recent.length === 0 ? (
              <div className="p-md font-body-sm text-on-surface-variant">
                No meetings yet. Upload a recording or try a sample.
              </div>
            ) : (
              recent.map((m, i) => (
                <button
                  key={m.id}
                  type="button"
                  className={`w-full flex items-center justify-between p-md border-b border-outline-variant hover:bg-surface-container-low transition-colors duration-200 text-left ${
                    i === recent.length - 1 ? 'border-b-0' : ''
                  }`}
                  onClick={() => onSelectMeeting(m.id)}
                >
                  <div className="flex items-center gap-md">
                    <div className="w-12 h-12 rounded-lg bg-surface-container flex items-center justify-center text-primary">
                      <span className="material-symbols-outlined">{meetingIcon(i)}</span>
                    </div>
                    <div>
                      <h4 className="font-body-md font-semibold text-on-surface">
                        {m.title || m.original_filename}
                      </h4>
                      <div className="flex gap-2 items-center mt-0.5">
                        <span className="text-caption font-caption text-on-surface-variant">
                          {new Date(m.created_at).toLocaleString()}
                        </span>
                        <span className="w-1 h-1 rounded-full bg-outline-variant" />
                        <span className="text-caption font-caption text-on-surface-variant">#{m.id}</span>
                      </div>
                    </div>
                  </div>
                  <StatusBadge status={m.status} />
                </button>
              ))
            )}
          </div>
        </section>

        <aside className="space-y-xl">
          <div>
            <h3 className="font-headline-md text-headline-md text-on-surface mb-md">Insights</h3>
            <div className="bg-primary-container text-on-primary-container p-lg rounded-xl relative overflow-hidden">
              <div className="relative z-10">
                <h4 className="font-body-lg font-bold mb-2">Workspace Health</h4>
                <p className="font-body-sm opacity-90 mb-4">
                  {meetings.length > 0
                    ? `${ready} of ${meetings.length} meetings processed and ready for review.`
                    : 'Upload your first meeting to start capturing intelligence.'}
                </p>
                <div className="h-2 w-full bg-white/20 rounded-full">
                  <div
                    className="h-full bg-white rounded-full transition-all"
                    style={{ width: meetings.length ? `${Math.round((ready / meetings.length) * 100)}%` : '0%' }}
                  />
                </div>
              </div>
              <div className="absolute -right-4 -bottom-4 opacity-10">
                <span className="material-symbols-outlined text-[120px]">analytics</span>
              </div>
            </div>
          </div>
          <div className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md">
            <h3 className="font-metadata text-metadata font-bold text-on-surface-variant mb-md uppercase tracking-tight">
              Quick actions
            </h3>
            <div className="space-y-2">
              <button
                type="button"
                className="w-full flex items-center gap-2 px-md py-2 bg-surface-container-low rounded-lg hover:bg-surface-container transition-colors text-left font-body-sm"
                onClick={onUpload}
              >
                <span className="material-symbols-outlined text-primary text-[20px]">upload</span>
                Upload new recording
              </button>
              <button
                type="button"
                className="w-full flex items-center gap-2 px-md py-2 bg-surface-container-low rounded-lg hover:bg-surface-container transition-colors text-left font-body-sm"
                onClick={onLive}
              >
                <span className="material-symbols-outlined text-primary text-[20px]">sensors</span>
                Start live session
              </button>
            </div>
          </div>
        </aside>
      </div>
    </>
  )
}
