import { useMemo, useState } from 'react'
import type { MeetingListItem } from '../types'
import { isFailedStatus, isProcessingStatus, meetingIcon } from '../lib/format'
import { StatusBadge } from './StatusBadge'

type StatusFilter = 'all' | 'ready' | 'processing' | 'failed'

type Props = {
  meetings: MeetingListItem[]
  onSelectMeeting: (id: number) => void
  onRefresh: () => void
}

export function MeetingsView({ meetings, onSelectMeeting, onRefresh }: Props) {
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<StatusFilter>('all')

  const filtered = useMemo(() => {
    let list = meetings
    if (filter === 'ready') list = list.filter((m) => m.status === 'READY')
    else if (filter === 'processing') list = list.filter((m) => isProcessingStatus(m.status))
    else if (filter === 'failed') list = list.filter((m) => isFailedStatus(m.status))

    if (query.trim()) {
      const q = query.trim().toLowerCase()
      list = list.filter(
        (m) =>
          (m.title || '').toLowerCase().includes(q) ||
          m.original_filename.toLowerCase().includes(q) ||
          String(m.id).includes(q),
      )
    }
    return list
  }, [meetings, filter, query])

  const filters: { id: StatusFilter; label: string }[] = [
    { id: 'all', label: 'All' },
    { id: 'ready', label: 'Ready' },
    { id: 'processing', label: 'Processing' },
    { id: 'failed', label: 'Failed' },
  ]

  return (
    <>
      <section className="mb-8">
        <h2 className="font-display text-display mb-2">Meetings</h2>
        <p className="font-body-sm text-body-sm text-on-surface-variant">
          Review your recent intelligence captures and transcriptions.
        </p>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter mb-8">
        <div className="md:col-span-5 relative">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline">
            search
          </span>
          <input
            className="w-full pl-10 pr-4 py-2 bg-surface border border-outline-variant rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-container/20 focus:border-primary transition-all font-body-sm"
            placeholder="Search meetings by title or content..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="md:col-span-7 flex flex-wrap gap-2 items-center">
          <div className="flex bg-surface border border-outline-variant rounded-xl p-1">
            {filters.map((f) => (
              <button
                key={f.id}
                type="button"
                className={`px-3 py-1.5 text-caption font-medium rounded-lg transition-colors ${
                  filter === f.id
                    ? 'bg-primary-container text-on-primary-container'
                    : 'text-on-surface-variant hover:bg-surface-container-low'
                }`}
                onClick={() => setFilter(f.id)}
              >
                {f.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="flex items-center gap-2 px-4 py-2 bg-surface border border-outline-variant rounded-xl text-body-sm text-on-surface-variant hover:bg-surface-container-low transition-colors"
            onClick={onRefresh}
          >
            <span className="material-symbols-outlined text-[18px]">refresh</span>
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {filtered.length === 0 ? (
          <div className="bg-surface border border-outline-variant rounded-xl p-lg text-on-surface-variant font-body-sm">
            No meetings match your filters.
          </div>
        ) : (
          filtered.map((m, i) => {
            const processing = isProcessingStatus(m.status)
            const failed = isFailedStatus(m.status)
            return (
              <div
                key={m.id}
                className={`group bg-surface border border-outline-variant rounded-xl p-md flex flex-col md:flex-row items-start md:items-center justify-between hover:border-primary/40 hover:shadow-sm transition-all duration-300 ${
                  processing ? 'opacity-80' : ''
                }`}
              >
                <div className="flex gap-4 items-center mb-4 md:mb-0">
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      failed
                        ? 'bg-error-container/30 text-error'
                        : processing
                          ? 'bg-surface-container-high text-on-surface-variant'
                          : i % 2 === 0
                            ? 'bg-primary-fixed text-primary'
                            : 'bg-tertiary-fixed text-tertiary'
                    }`}
                  >
                    <span className={`material-symbols-outlined ${processing ? 'animate-spin' : ''}`}>
                      {processing ? 'refresh' : failed ? 'error_outline' : meetingIcon(i)}
                    </span>
                  </div>
                  <div>
                    <h3 className="font-headline-md text-body-lg font-bold text-on-surface leading-tight">
                      {m.title || m.original_filename}
                    </h3>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-caption text-on-surface-variant flex items-center gap-1">
                        <span className="material-symbols-outlined text-[14px]">event</span>
                        {new Date(m.created_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </span>
                      <span className="text-caption text-on-surface-variant flex items-center gap-1">
                        <span className="material-symbols-outlined text-[14px]">tag</span>#{m.id}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="w-full md:w-auto flex items-center justify-between md:justify-end gap-6 border-t md:border-t-0 border-outline-variant/30 pt-4 md:pt-0">
                  <StatusBadge status={m.status} />
                  <button
                    type="button"
                    className={`material-symbols-outlined p-1 rounded transition-colors ${
                      processing
                        ? 'text-outline cursor-not-allowed'
                        : 'text-outline hover:text-primary'
                    }`}
                    disabled={processing}
                    onClick={() => onSelectMeeting(m.id)}
                  >
                    {processing ? 'lock' : 'chevron_right'}
                  </button>
                </div>
              </div>
            )
          })
        )}
      </div>

      {filtered.length > 0 ? (
        <div className="mt-8 flex flex-col md:flex-row items-center justify-between gap-4 py-6 border-t border-outline-variant">
          <p className="text-body-sm text-on-surface-variant">
            Showing {filtered.length} of {meetings.length}
          </p>
        </div>
      ) : null}
    </>
  )
}
