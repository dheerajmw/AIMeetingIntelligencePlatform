import type { ReactNode } from 'react'
import { userInitials } from '../lib/format'
import { useTheme } from '../theme/ThemeProvider'

export type AppView =
  | 'dashboard'
  | 'meetings'
  | 'meeting-detail'
  | 'new-meeting'
  | 'live'
  | 'integrations'
  | 'settings'

export type NavView = 'dashboard' | 'meetings' | 'live' | 'integrations' | 'settings'

type Props = {
  view: AppView
  onNavigate: (view: NavView) => void
  workspaceName: string
  userName: string
  userRole: string
  onLogout: () => void
  children: ReactNode
  showFab?: boolean
  onFabClick?: () => void
}

const NAV: { id: NavView; label: string; icon: string }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
  { id: 'meetings', label: 'Meetings', icon: 'event_note' },
  { id: 'live', label: 'Live', icon: 'sensors' },
  { id: 'integrations', label: 'Integrations', icon: 'extension' },
  { id: 'settings', label: 'Settings', icon: 'settings' },
]

function navFromView(view: AppView): NavView {
  if (view === 'meeting-detail' || view === 'new-meeting') return 'meetings'
  return view
}

export function AppLayout({
  view,
  onNavigate,
  workspaceName,
  userName,
  userRole,
  onLogout,
  children,
  showFab,
  onFabClick,
}: Props) {
  const { theme, toggleTheme } = useTheme()
  const activeNav = navFromView(view)
  const initials = userInitials(userName)

  return (
    <div className="bg-background text-on-surface font-body-md min-h-screen pb-20 md:pb-0">
      {/* TopAppBar */}
      <header className="fixed top-0 left-0 w-full z-50 flex justify-between items-center px-margin-mobile md:pl-[calc(16rem+1rem)] h-16 bg-surface border-b border-outline-variant">
        <div className="flex items-center gap-3 md:hidden">
          <span className="material-symbols-outlined text-on-surface cursor-pointer">menu</span>
          <h1 className="font-headline-md text-headline-md font-bold text-on-surface">MeetIQ</h1>
        </div>
        <h1 className="hidden md:block font-headline-md text-headline-md font-bold text-on-surface">MeetIQ</h1>
        <div className="flex items-center gap-2 md:gap-4">
          <div className="hidden md:flex items-center gap-2 px-md py-1 bg-surface-container rounded-lg border border-outline-variant">
            <span className="material-symbols-outlined text-on-surface-variant text-sm">search</span>
            <input
              className="bg-transparent border-none focus:ring-0 text-body-md text-on-surface placeholder:text-on-surface-variant w-48 outline-none"
              placeholder="Search insights..."
              readOnly
            />
          </div>
          <button
            type="button"
            className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface-container-low transition-colors"
            onClick={toggleTheme}
            title="Toggle theme"
          >
            <span className="material-symbols-outlined text-primary">
              {theme === 'light' ? 'dark_mode' : 'light_mode'}
            </span>
          </button>
          <button
            type="button"
            className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface-container-low transition-colors"
            title="Notifications"
          >
            <span className="material-symbols-outlined text-primary relative">
              notifications
              {theme === 'dark' ? (
                <span className="absolute top-0 right-0 w-2 h-2 bg-tertiary rounded-full" />
              ) : null}
            </span>
          </button>
          <div className="hidden md:flex items-center gap-2 border-l pl-4 border-outline-variant">
            <div className="w-8 h-8 rounded-full bg-primary-container flex items-center justify-center text-on-primary-container font-bold text-xs">
              {initials}
            </div>
            <span className="font-metadata text-metadata text-on-surface-variant">{workspaceName}</span>
          </div>
          <div className="md:hidden w-8 h-8 rounded-full bg-primary-container flex items-center justify-center text-on-primary-container text-xs font-bold">
            {initials}
          </div>
        </div>
      </header>

      {/* Desktop sidebar (light + dark) */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden md:flex flex-col p-md gap-sm bg-surface-container-low border-r border-outline-variant w-64">
        <div className="flex items-center gap-3 h-16 shrink-0 px-sm">
          <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center">
            <span className="material-symbols-outlined text-on-primary text-[20px] filled">analytics</span>
          </div>
          <span className="font-headline-md text-headline-md font-bold text-on-surface">MeetIQ</span>
        </div>

        <div className="flex items-center gap-md p-md mb-sm bg-surface-container-lowest rounded-xl border border-outline-variant/50">
          <div className="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center text-on-primary-container font-bold text-sm shrink-0">
            {initials}
          </div>
          <div className="min-w-0">
            <p className="font-body-md text-body-md font-semibold text-on-surface truncate">{userName}</p>
            <p className="font-caption text-caption text-on-surface-variant truncate">
              {userRole} · {workspaceName}
            </p>
          </div>
        </div>

        <nav className="flex flex-col gap-1 flex-1">
          {NAV.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`flex items-center gap-md px-md py-sm rounded-lg transition-all duration-200 font-body-md text-body-md ${
                activeNav === item.id
                  ? 'bg-primary-container text-on-primary-container font-semibold'
                  : 'text-on-surface-variant hover:bg-surface-container-high'
              }`}
              onClick={() => onNavigate(item.id)}
            >
              <span className={`material-symbols-outlined ${activeNav === item.id ? 'filled' : ''}`}>
                {item.icon}
              </span>
              {item.label}
            </button>
          ))}
        </nav>

        <button
          type="button"
          className="flex items-center gap-md px-md py-sm rounded-lg text-on-surface-variant hover:bg-surface-container-high transition-colors"
          onClick={onLogout}
        >
          <span className="material-symbols-outlined">logout</span>
          Sign out
        </button>
      </aside>

      <main className="pt-20 px-margin-mobile md:pl-[calc(16rem+2rem)] md:pr-margin-desktop max-w-[1600px] md:mx-auto pb-8">
        {children}
      </main>

      {/* FAB for new meeting on meetings views */}
      {showFab && onFabClick ? (
        <button
          type="button"
          className="fixed right-6 bottom-20 md:bottom-8 w-14 h-14 bg-primary-container text-on-primary-container rounded-2xl shadow-xl flex items-center justify-center hover:scale-105 active:scale-95 transition-all z-40"
          onClick={onFabClick}
          aria-label="New meeting"
        >
          <span className="material-symbols-outlined text-[28px]">add</span>
        </button>
      ) : null}

      {/* Bottom nav (mobile only) */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center h-16 bg-surface border-t border-outline-variant px-2 pb-safe">
        {NAV.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`flex flex-col items-center justify-center flex-1 h-full active:scale-95 transition-transform duration-150 ${
              activeNav === item.id ? 'text-primary font-medium' : 'text-on-surface-variant'
            }`}
            onClick={() => onNavigate(item.id)}
          >
            <span className={`material-symbols-outlined ${activeNav === item.id ? 'filled' : ''}`}>
              {item.icon}
            </span>
            <span className="font-caption text-caption">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}
