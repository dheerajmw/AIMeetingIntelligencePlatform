const MEETING_ICONS = ['description', 'payments', 'rocket_launch', 'map', 'trending_up', 'event_repeat', 'groups', 'mic']

export function meetingIcon(index: number): string {
  return MEETING_ICONS[index % MEETING_ICONS.length]
}

export function formatTimestampRange(range: { start_s?: number; end_s?: number } | null | undefined) {
  if (!range || range.start_s == null || range.end_s == null) return 'Not identified'
  return `${range.start_s.toFixed(1)}s – ${range.end_s.toFixed(1)}s`
}

export function formatConfidence(value: number | null | undefined) {
  if (value == null) return 'Not identified'
  return `${Math.round(value * 100)}%`
}

export function userInitials(name: string): string {
  return name
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

export function formatMeetingDate(iso: string | null | undefined): string {
  if (!iso) return 'Date not set'
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

export function isProcessingStatus(status: string): boolean {
  const s = status.toUpperCase()
  return !['READY', 'FAILED_TRANSCRIPTION', 'FAILED_ANALYSIS', 'FAILED'].some((f) => s.includes(f))
}

export function isFailedStatus(status: string): boolean {
  return status.toUpperCase().includes('FAILED')
}
