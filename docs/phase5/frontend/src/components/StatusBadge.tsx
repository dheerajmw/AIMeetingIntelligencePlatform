import { isFailedStatus, isProcessingStatus } from '../lib/format'

export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toUpperCase()

  if (normalized === 'READY') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400 text-[11px] font-bold uppercase tracking-tighter border border-emerald-100 dark:border-emerald-500/20">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
        Ready
      </span>
    )
  }

  if (isFailedStatus(status)) {
    return (
      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-error-container text-on-error-container text-[11px] font-bold uppercase tracking-wide border border-error/20">
        Failed
      </span>
    )
  }

  if (isProcessingStatus(status)) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400 text-[11px] font-bold uppercase tracking-tighter border border-blue-100 dark:border-blue-500/20">
        <span className="w-1 h-1 rounded-full bg-blue-700 dark:bg-blue-400 animate-pulse" />
        Processing
      </span>
    )
  }

  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-full bg-surface-container-high text-on-surface-variant text-[11px] font-bold uppercase tracking-tighter border border-outline-variant">
      {status.replace(/_/g, ' ')}
    </span>
  )
}
