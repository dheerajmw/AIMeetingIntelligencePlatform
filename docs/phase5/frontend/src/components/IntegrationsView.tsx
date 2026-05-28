import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext'

type IntegrationMeta = {
  id: string
  name: string
  subtitle: string
  icon: string
  description: string
}

const INTEGRATIONS: IntegrationMeta[] = [
  {
    id: 'jira',
    name: 'Jira',
    subtitle: 'Ticket automation',
    icon: 'task',
    description: 'Create Jira tasks from meeting action items.',
  },
  {
    id: 'linear',
    name: 'Linear',
    subtitle: 'Modern issue tracking',
    icon: 'rebase_edit',
    description: 'Sync action items to Linear issues.',
  },
  {
    id: 'slack',
    name: 'Slack',
    subtitle: 'Team communication',
    icon: 'forum',
    description: 'Post meeting summaries to a Slack channel.',
  },
  {
    id: 'trello',
    name: 'Trello',
    subtitle: 'Visual board sync',
    icon: 'dashboard_customize',
    description: 'Create Trello cards from action items.',
  },
  {
    id: 'email',
    name: 'Email',
    subtitle: 'Inbox automation',
    icon: 'mail',
    description: 'Email the executive summary and action items.',
  },
]

type ProviderStatus = { configured: boolean; ready: boolean }

export function IntegrationsView() {
  const { api } = useAuth()
  const [stubMode, setStubMode] = useState(true)
  const [providers, setProviders] = useState<Record<string, ProviderStatus>>({})

  useEffect(() => {
    api
      .apiFetch('/integrations/status')
      .then(async (r) => {
        if (!r.ok) return
        const data = (await r.json()) as { stub_mode: boolean; providers: Record<string, ProviderStatus> }
        setStubMode(data.stub_mode)
        setProviders(data.providers)
      })
      .catch(() => {})
  }, [api])

  return (
    <>
      <div className="mb-xl">
        <h2 className="font-display text-display text-on-surface mb-1">Integrations Hub</h2>
        <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
          Export meeting summaries and action items to your workflow tools from each meeting&apos;s Integrations
          tab.
        </p>
        {stubMode ? (
          <p className="mt-2 font-body-sm text-primary bg-primary-fixed/30 border border-primary-fixed-dim rounded-lg px-md py-sm max-w-2xl">
            <strong>Demo mode:</strong> Integrations are simulated locally (no Jira/Slack API keys required).
            Set <code className="font-code text-caption">INTEGRATIONS_STUB_MODE=false</code> and add credentials in{' '}
            <code className="font-code text-caption">backend/.env</code> for real exports.
          </p>
        ) : null}
      </div>

      <div className="integration-grid">
        {INTEGRATIONS.map((item) => {
          const status = providers[item.id]
          const configured = status?.configured ?? false
          const ready = status?.ready ?? false
          const label = stubMode && !configured ? 'Simulated' : configured ? 'Connected' : 'Not configured'

          return (
            <div
              key={item.id}
              className="bg-surface-container-lowest border border-outline-variant rounded-xl p-md flex flex-col justify-between hover:border-primary transition-colors duration-200"
            >
              <div className="flex justify-between items-start mb-lg">
                <div className="flex items-center gap-md">
                  <div className="w-12 h-12 bg-surface-container-low rounded-xl flex items-center justify-center border border-outline-variant">
                    <span className="material-symbols-outlined text-primary text-[32px]">{item.icon}</span>
                  </div>
                  <div>
                    <h3 className="font-headline-md text-headline-md">{item.name}</h3>
                    <p className="font-caption text-caption text-on-surface-variant">{item.subtitle}</p>
                  </div>
                </div>
                <div
                  className={`flex items-center gap-1 rounded-full px-sm py-1 ${
                    ready
                      ? 'text-on-secondary-container bg-surface-container'
                      : 'text-outline bg-surface-container-low'
                  }`}
                >
                  {ready ? (
                    <span className="material-symbols-outlined text-[16px]">check_circle</span>
                  ) : null}
                  <span className="font-metadata text-metadata">{label}</span>
                </div>
              </div>
              <div className="space-y-md">
                <p className="font-body-sm text-body-sm text-on-surface-variant">{item.description}</p>
                <p className="font-caption text-caption text-on-surface-variant">
                  {item.id === 'jira' || item.id === 'linear' || item.id === 'trello'
                    ? 'Export kind: action items'
                    : 'Export kind: summary'}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      <footer className="mt-xl pt-lg border-t border-outline-variant">
        <div className="flex items-start gap-2 opacity-80 max-w-3xl">
          <span className="material-symbols-outlined text-[18px] text-primary shrink-0">info</span>
          <p className="font-caption text-caption text-on-surface-variant">
            Open a <strong>Ready</strong> meeting → <strong>Integrations</strong> tab → choose Jira/Linear/Trello
            (action items) or Slack/Email (summary). Failed exports from before demo mode was enabled can be
            retried with the export buttons.
          </p>
        </div>
      </footer>
    </>
  )
}
