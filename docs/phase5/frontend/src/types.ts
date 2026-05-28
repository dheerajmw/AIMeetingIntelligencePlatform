export type MeetingListItem = {
  id: number
  title: string | null
  created_at: string
  status: string
  original_filename: string
}

export type MeetingDetail = {
  id: number
  title: string | null
  created_at: string
  status: string
  original_filename: string
  meeting_start: string | null
  timezone: string | null
  error_message: string | null
}

export type MeetingResults = {
  status: string
  transcript: { segments?: TranscriptSegment[] } | null
  insights: MeetingInsights | null
}

export type TranscriptSegment = {
  start_s?: number
  end_s?: number
  text?: string
  speaker_id?: string
}

export type MeetingInsights = {
  executive_summary?: string
  key_discussion_points?: string[]
  decisions_made?: InsightDecision[]
  action_items?: InsightAction[]
  prompt_version?: string
  schema_version?: string
}

export type InsightDecision = {
  decision?: string
  owner?: string
  due_date?: string
  evidence_quote?: string
  timestamp_range?: { start_s?: number; end_s?: number }
  confidence?: number
}

export type InsightAction = {
  title?: string
  action?: string
  description?: string
  owner?: string
  due_date?: string
  deadline?: string
  priority?: string
  evidence_quote?: string
  timestamp_range?: { start_s?: number; end_s?: number }
  confidence?: number
}

export type SearchHit = {
  meeting_id: number
  title: string
  score: number
  snippet: string
  mode: string
}

export type ExportRecord = {
  id: number
  provider: string
  export_kind: string
  status: string
  external_ref: string | null
  error_message: string | null
  created_at: string
}
