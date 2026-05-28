import { useState } from 'react'
import type { ExportRecord, MeetingDetail, MeetingResults } from '../types'
import { formatConfidence, formatMeetingDate } from '../lib/format'
import { StatusBadge } from './StatusBadge'

type Tab = 'summary' | 'transcript' | 'actions' | 'integrations'

type Props = {
  meeting: MeetingDetail
  results: MeetingResults | null
  exports: ExportRecord[]
  exportBusy: boolean
  onBack: () => void
  onExport: (
    provider: 'jira' | 'linear' | 'trello' | 'slack' | 'email',
    exportKind: 'action_items' | 'summary',
    emailTo?: string,
  ) => void
}

export function MeetingDetailView({ meeting, results, exports, exportBusy, onBack, onExport }: Props) {
  const [tab, setTab] = useState<Tab>('summary')
  const [emailTo, setEmailTo] = useState('')
  const insights = results?.insights
  const segments = results?.transcript?.segments || []

  const tabs: { id: Tab; label: string }[] = [
    { id: 'summary', label: 'Summary' },
    { id: 'transcript', label: 'Transcript' },
    { id: 'actions', label: 'Actions & Decisions' },
    { id: 'integrations', label: 'Integrations' },
  ]

  return (
    <>
      <button
        type="button"
        className="flex items-center gap-1 text-primary font-metadata text-metadata mb-4 hover:underline"
        onClick={onBack}
      >
        <span className="material-symbols-outlined text-[18px]">arrow_back</span>
        Back to meetings
      </button>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div className="space-y-1">
          <div className="flex items-center gap-3 flex-wrap">
            <h2 className="font-display text-display text-on-surface">{meeting.title || meeting.original_filename}</h2>
            <StatusBadge status={meeting.status} />
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">calendar_today</span>
            {formatMeetingDate(meeting.meeting_start || meeting.created_at)} · #{meeting.id}
          </p>
        </div>
      </div>

      {meeting.error_message ? (
        <div className="mb-6 p-md bg-error-container border border-error/20 rounded-lg flex items-center gap-sm">
          <span className="material-symbols-outlined text-error">error</span>
          <p className="font-body-sm text-on-error-container">{meeting.error_message}</p>
        </div>
      ) : null}

      <nav className="flex border-b border-outline-variant mb-8 overflow-x-auto scrollbar-hide">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`px-6 py-3 border-b-2 font-metadata text-body-sm whitespace-nowrap transition-colors ${
              tab === t.id
                ? 'border-primary text-primary'
                : 'border-transparent text-on-surface-variant hover:text-primary'
            }`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === 'summary' ? (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          <section className="md:col-span-8 p-6 bg-surface-container-lowest border border-outline-variant rounded-xl">
            <div className="flex items-center gap-2 mb-4 text-primary">
              <span className="material-symbols-outlined">auto_awesome</span>
              <h3 className="font-headline-md text-headline-md">Executive Summary</h3>
            </div>
            {insights?.executive_summary ? (
              <div className="font-body-md text-body-md text-on-surface leading-relaxed space-y-4">
                {insights.executive_summary.split('\n').map((p, i) => (
                  <p key={i}>{p}</p>
                ))}
              </div>
            ) : (
              <p className="font-body-sm text-on-surface-variant">
                {meeting.status === 'READY' ? 'Summary not available.' : 'Processing… summary will appear when ready.'}
              </p>
            )}
          </section>

          <section className="md:col-span-4 p-6 bg-surface-container-lowest border border-outline-variant rounded-xl flex flex-col">
            <h3 className="font-headline-md text-headline-md mb-4">Discussion Points</h3>
            {(insights?.key_discussion_points || []).length ? (
              <ul className="space-y-4 flex-1">
                {insights!.key_discussion_points!.map((p, i) => (
                  <li key={i} className="flex gap-3 group">
                    <span className="w-1.5 h-1.5 rounded-full bg-primary mt-2 group-hover:scale-125 transition-transform shrink-0" />
                    <p className="font-body-sm text-body-sm text-on-surface">{p}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="font-body-sm text-on-surface-variant">No discussion points detected.</p>
            )}
          </section>
        </div>
      ) : null}

      {tab === 'transcript' ? (
        <section className="p-6 bg-surface-container-lowest border border-outline-variant rounded-xl">
          <h3 className="font-headline-md text-headline-md mb-4">Transcript</h3>
          {segments.length ? (
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {segments.map((s, i) => (
                <div key={i} className="flex gap-3 font-body-sm leading-relaxed">
                  <span className="text-caption text-on-surface-variant shrink-0 font-code">
                    [{s.start_s?.toFixed?.(1)}–{s.end_s?.toFixed?.(1)}]
                  </span>
                  {s.speaker_id ? (
                    <span className="font-metadata text-primary shrink-0">{s.speaker_id}</span>
                  ) : null}
                  <span className="text-on-surface">{s.text}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="font-body-sm text-on-surface-variant">Transcript not available yet.</p>
          )}
        </section>
      ) : null}

      {tab === 'actions' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <section className="space-y-4">
            <div className="flex items-center gap-2 px-2">
              <span className="material-symbols-outlined text-primary">gavel</span>
              <h3 className="font-headline-md text-headline-md">Decisions Made</h3>
            </div>
            {(insights?.decisions_made || []).length ? (
              insights!.decisions_made!.map((d, i) => (
                <div
                  key={i}
                  className="p-6 bg-surface-container-lowest border border-outline-variant rounded-xl relative overflow-hidden"
                >
                  <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500" />
                  <h4 className="font-headline-md text-headline-md text-on-surface mb-3">{d.decision}</h4>
                  <div className="flex flex-wrap gap-2 text-caption text-on-surface-variant mb-3">
                    <span>Owner: {d.owner || 'Not identified'}</span>
                    <span>·</span>
                    <span>Confidence: {formatConfidence(d.confidence)}</span>
                  </div>
                  {d.evidence_quote ? (
                    <div className="p-4 bg-surface-container-low rounded-lg border-l-4 border-outline-variant italic font-body-sm text-on-surface-variant">
                      &ldquo;{d.evidence_quote}&rdquo;
                    </div>
                  ) : null}
                </div>
              ))
            ) : (
              <p className="font-body-sm text-on-surface-variant px-2">No decisions detected.</p>
            )}
          </section>

          <section className="space-y-4">
            <div className="flex items-center gap-2 px-2">
              <span className="material-symbols-outlined text-primary">checklist</span>
              <h3 className="font-headline-md text-headline-md">Action Items</h3>
            </div>
            {(insights?.action_items || []).length ? (
              insights!.action_items!.map((a, i) => (
                <div
                  key={i}
                  className="p-6 bg-surface-container-lowest border border-outline-variant rounded-xl relative overflow-hidden"
                >
                  <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
                  <h4 className="font-headline-md text-headline-md text-on-surface">{a.title || a.action}</h4>
                  {a.description ? (
                    <p className="font-body-sm text-on-surface-variant mt-1">{a.description}</p>
                  ) : null}
                  <div className="flex flex-wrap gap-2 mt-2 text-caption text-on-surface-variant">
                    <span>Owner: {a.owner || 'Not identified'}</span>
                    <span>·</span>
                    <span>Due: {a.due_date || a.deadline || 'Not identified'}</span>
                    <span>·</span>
                    <span>Priority: {a.priority || 'Not identified'}</span>
                  </div>
                  {a.evidence_quote ? (
                    <div className="mt-3 p-4 bg-surface-container-low rounded-lg border-l-4 border-outline-variant italic font-body-sm text-on-surface-variant">
                      &ldquo;{a.evidence_quote}&rdquo;
                    </div>
                  ) : null}
                </div>
              ))
            ) : (
              <p className="font-body-sm text-on-surface-variant px-2">No action items detected.</p>
            )}
          </section>
        </div>
      ) : null}

      {tab === 'integrations' ? (
        <section className="p-6 bg-surface-container-lowest border border-outline-variant rounded-xl space-y-4">
          <h3 className="font-headline-md text-headline-md">Export to integrations</h3>
          {meeting.status === 'READY' ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
                <div className="space-y-1">
                  <label className="font-metadata text-metadata text-on-surface-variant ml-1">
                    Email recipient (optional)
                  </label>
                  <input
                    className="w-full h-11 px-md bg-surface border border-outline-variant rounded-lg font-body-sm form-input-focus"
                    placeholder="Leave blank to send to your login email"
                    value={emailTo}
                    onChange={(e) => setEmailTo(e.target.value)}
                    disabled={exportBusy}
                  />
                </div>
                <div className="font-body-sm text-on-surface-variant flex items-end">
                  If blank, MeetIQ sends to the signed-in user’s email. Non-admin users can’t send to other recipients.
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {(
                  [
                    ['jira', 'action_items', 'Export → Jira'],
                    ['linear', 'action_items', 'Export → Linear'],
                    ['trello', 'action_items', 'Export → Trello'],
                    ['slack', 'summary', 'Send → Slack'],
                    ['email', 'summary', 'Send → Email'],
                  ] as const
                ).map(([provider, kind, label]) => (
                  <button
                    key={provider}
                    type="button"
                    disabled={exportBusy}
                    className="flex items-center gap-2 px-4 py-2 bg-surface-container-low text-primary font-body-sm rounded-lg border border-primary hover:bg-primary hover:text-on-primary transition-all disabled:opacity-50"
                    onClick={() => onExport(provider, kind, provider === 'email' ? emailTo : undefined)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              {exports.length ? (
                <ul className="space-y-2 mt-4">
                  {exports.map((ex) => (
                    <li
                      key={ex.id}
                      className="flex items-center gap-2 p-3 bg-surface-container-low rounded-lg font-body-sm"
                    >
                      <span className="material-symbols-outlined text-primary text-[18px]">sync</span>
                      <span>
                        <b>{ex.provider}</b> · {ex.export_kind} · {ex.status}
                        {ex.external_ref ? ` · ${ex.external_ref}` : ''}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="font-body-sm text-on-surface-variant">No exports yet for this meeting.</p>
              )}
            </>
          ) : (
            <p className="font-body-sm text-on-surface-variant">Exports available when meeting status is Ready.</p>
          )}
        </section>
      ) : null}
    </>
  )
}
