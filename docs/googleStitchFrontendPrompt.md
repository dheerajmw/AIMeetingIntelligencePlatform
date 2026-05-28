# Google Stitch Prompt — MeetIQ Frontend

Use the prompt below in [Google Stitch](https://stitch.withgoogle.com/) to generate the full frontend UI. Copy everything inside the **PROMPT START / PROMPT END** block as a single prompt, or split by screen section if Stitch has character limits.

---

## How to use

1. Open Google Stitch and create a new project.
2. Paste the **Master Prompt** first to establish the design system and app shell.
3. Generate screens one section at a time using the **Screen Prompts** at the bottom.
4. Iterate with follow-ups: *“Make the sidebar narrower”*, *“Add empty states”*, *“Use dark mode variant”*.

---

## PROMPT START

Design a complete web application UI for **MeetIQ** — a B2B SaaS product that converts meeting recordings into structured intelligence: executive summaries, key discussion points, decisions, action items, owners, and deadlines.

### Theme & visual direction

**Theme type:** Modern B2B SaaS Dashboard  
**Style:** Minimalist · Professional · Clean · Enterprise-grade  
**Inspiration:** Linear (precision, subtle borders, tight spacing), Notion (readable content blocks, calm hierarchy), Asana (clear task/action-item patterns)

**Design system:**
- **Layout:** Left sidebar navigation (collapsible) + top bar + main content area. Max content width ~1200px for detail views.
- **Color palette:** Neutral grayscale base (slate/zinc). Single accent color: indigo or violet (#6366F1 range). Success green, warning amber, error red used sparingly for status only.
- **Typography:** Inter or similar geometric sans-serif. Clear hierarchy: 24px page titles, 16px body, 13px metadata/captions. Generous line-height for transcript and summary text.
- **Surfaces:** White or near-white cards on light gray (#F8FAFC) app background. 1px subtle borders (#E2E8F0). Soft shadows only on dropdowns/modals.
- **Spacing:** 8px grid. Comfortable padding (16–24px in cards). Avoid visual clutter.
- **Components:** Rounded corners (8px cards, 6px buttons). Pill-shaped status badges. Icon + label buttons. Subtle hover states. No heavy gradients or glassmorphism.
- **Dark mode:** Optional secondary variant — dark slate background (#0F172A), elevated cards (#1E293B), muted text (#94A3B8).

**Tone:** Trustworthy, efficient, calm. Built for PMs, engineering managers, founders, and remote teams who need clarity after every meeting.

---

### Application shell (persistent across all screens)

**Left sidebar:**
- Product logo + name: “MeetIQ”
- Nav items with icons:
  - **Dashboard** (home overview)
  - **Meetings** (all processed recordings)
  - **Live Meeting** (real-time capture)
  - **Search** (global search)
  - **Integrations** (export connections)
  - **Admin** (enterprise settings — visible to admins only)
- Bottom: workspace switcher (workspace name + chevron), user avatar + name + role badge, settings, sign out

**Top bar:**
- Breadcrumb or page title
- Global search input (compact, ⌘K hint)
- Primary CTA button context-aware: “Upload recording” or “Start live session”
- Notification bell (processing complete alerts)

---

### Screen 1 — Dashboard (Home)

Purpose: At-a-glance overview for returning users.

Include:
- Welcome header with user name and workspace name
- **Stats row** (4 compact metric cards): Total meetings · Action items pending · Decisions this week · Processing queue
- **Recent meetings** table/list (5 items): title, date, duration, status badge, action item count
- **Quick actions** card: Upload recording · Try sample meeting · Start live session
- **Sample showcase** section for new users — cards for AMI and ICSI demo clips with “Try this sample” button and corpus description
- Empty state when no meetings: illustration + “Upload your first meeting” CTA

---

### Screen 2 — Upload / New Meeting

Purpose: Ingest audio/video for async processing.

Include:
- Drag-and-drop upload zone (supports .mp3, .wav, .m4a, optional video)
- File preview after selection (filename, size, estimated duration)
- Form fields:
  - Meeting title (optional)
  - Meeting start date/time (ISO picker)
  - Timezone selector
  - Toggle: “Enable speaker labeling” (diarization)
- Submit button: “Upload & Process”
- **Processing status pipeline** visual stepper below after submit:
  `Uploaded → Transcribing → Analyzing → Ready`
  Show spinner on active step; red error state for Failed Transcription / Failed Analysis with error message
- Inline validation errors for unsupported file types

---

### Screen 3 — Meetings List

Purpose: Browse all meetings in the workspace.

Include:
- Filter bar: status (All / Ready / Processing / Failed), date range, sort (newest first)
- Search within list
- Table or card list columns: Title · Filename · Date · Status badge · Duration · # Action items · # Decisions
- Row click opens meeting detail
- Bulk actions (admin): delete selected
- Pagination or infinite scroll
- Empty state: “No meetings yet”

---

### Screen 4 — Meeting Detail (core results page)

Purpose: Primary value screen — structured meeting intelligence.

**Header:**
- Meeting title (editable)
- Metadata row: date, timezone, filename, STT model version, LLM model, schema version
- Status badge + progress if still processing (auto-refresh indicator)
- Actions: Export · Share · Delete · Re-process

**Tab navigation:**
1. **Summary** (default)
2. **Transcript**
3. **Actions & Decisions**
4. **Integrations**
5. **Metadata**

**Summary tab content:**
- **Executive summary** — large readable text block
- **Key discussion points** — bulleted list with subtle dividers
- **Decisions made** — card list; each card shows:
  - Decision text
  - Evidence quote (italic, quoted)
  - Timestamp range (clickable, e.g. “12.4s – 18.2s”)
  - Confidence score badge if available
  - Empty state: “No decisions detected” (not blank)
- **Action items** — task-style cards; each shows:
  - Title
  - Owner (or “Not identified” in muted text)
  - Due date (or “Not identified”)
  - Evidence quote + timestamp range
  - Priority indicator (optional)
  - Checkbox to mark done (UI only)

**Transcript tab:**
- Speaker-labeled segments: `[timestamp] Speaker 1: text`
- Monospace or clean prose layout
- Highlight segment when clicking timestamp from decisions/actions
- Search within transcript
- Scrollable with sticky mini audio timeline bar (optional)

**Integrations tab:**
- Export buttons grid: Jira · Linear · Trello · Slack · Email
- Export kind selector: Action items / Summary
- Export history table: provider, status (success/failed), external link, timestamp, error message
- Idempotent export note: “Retries won’t duplicate tickets”

---

### Screen 5 — Global Search

Purpose: Find knowledge across all meetings (Phase 3).

Include:
- Large search input with placeholder: “Search budgets, launch dates, action owners…”
- Mode toggle: **Keyword (FTS)** | **Semantic (similar meetings)**
- Results list: meeting title, relevance score, highlighted snippet, meeting date
- Click result → opens meeting detail scrolled to match
- Recent searches
- Empty / no results state with suggestions

---

### Screen 6 — Live Meeting (Real-time)

Purpose: In-meeting intelligence with streaming capture (Phase 4).

**Layout:** Two-column split view.

**Left column — Live capture:**
- Session title input
- Meeting start + timezone
- Large “Start session” / “Stop & Finalize” button
- Recording indicator (pulsing red dot when active)
- Connection status: WebSocket connected / reconnecting
- Chunk progress: “Last processed seq: 12 · Audio duration: 4m 32s”

**Right column — Live output (updates in real time):**
- **Draft badge** on all live content (amber pill: “DRAFT”)
- Rolling executive summary (updates as meeting progresses)
- Live transcript feed (auto-scroll, newest at bottom)
- Emerging action items list (updates incrementally)
- Emerging decisions list

**After finalize:**
- Draft badge removed; “Final analysis complete” success banner
- Same structured layout as Meeting Detail (final artifacts)

---

### Screen 7 — Integrations Hub

Purpose: Configure and manage external tool connections (Phase 3).

Include:
- Integration cards grid: Jira, Linear, Trello, Slack, Email
- Each card: logo, connection status (Connected / Not configured), “Configure” button
- OAuth / API key setup modal per provider
- Rate limit and retry policy info (subtle footer text)

---

### Screen 8 — Admin / Enterprise (Phase 5)

Purpose: Workspace governance for admins and owners.

**Sub-sections (left sub-nav or tabs):**

1. **Workspace settings**
   - Workspace name, slug, data region selector
   - Retention policy (days)
   - Monthly quotas: meetings limit, LLM token limit

2. **Usage & billing**
   - Progress bars: meetings used / limit, tokens used / limit
   - Cache hit count (cost savings indicator)

3. **Audit log**
   - Filterable table: timestamp, user, action, resource, IP
   - Actions: upload, delete, export, login, retention purge, settings change

4. **Security**
   - SSO / OIDC status
   - Encryption at rest indicator
   - Role management table: user email, role (Owner / Admin / Member / Viewer)

5. **Data retention**
   - “Preview purge” and “Run retention purge” buttons with confirmation modal
   - List of meetings eligible for purge

---

### Screen 9 — Authentication

Purpose: Enterprise sign-in (Phase 5).

Include:
- Clean centered login card
- “Sign in with SSO” primary button (OIDC/SAML)
- Divider: “or”
- Dev/email login form (for local dev — secondary, muted)
- Workspace slug field
- Error states: invalid credentials, session expired
- Post-login redirect to Dashboard

---

### Screen 10 — Empty & error states (components)

Design reusable patterns for:
- **Processing:** skeleton loaders for summary and transcript
- **Failed transcription:** red alert with retry button and support link
- **Failed analysis:** partial results (transcript available, analysis failed)
- **Quota exceeded:** amber banner with upgrade/contact admin CTA
- **Unauthorized:** 403 page — “You don’t have access to this workspace”
- **Not found:** 404 meeting page

---

### UX rules (must follow in all screens)

1. **No fabrication in UI copy** — when owner or deadline is missing, always show “Not identified” in muted gray, never blank or placeholder guesses.
2. **No empty decisions section** — show “No decisions detected” message.
3. **Async by default** — always show job status; never block the UI during long processing; use polling/progress indicators.
4. **Draft vs final** — live meeting outputs must show a visible DRAFT badge until finalized.
5. **Evidence-first** — decisions and action items always show quote + timestamp when available.
6. **Accessible** — WCAG AA contrast, focus rings, keyboard-navigable tables and modals.

---

### Responsive behavior

- **Desktop (1280px+):** Full sidebar + two-column layouts where specified
- **Tablet (768–1279px):** Collapsible sidebar; stack live meeting columns
- **Mobile (<768px):** Bottom tab bar instead of sidebar; single-column everything; upload via file picker

---

Generate a cohesive, production-ready UI kit and all screens listed above as a connected prototype. Prioritize clarity, scannability, and post-meeting actionability. The product should feel like Linear meets Notion for meeting intelligence.

## PROMPT END

---

## Screen-by-screen prompts (if Stitch limits length)

Use these individually after the master prompt, referencing the established design system.

### Prompt A — App shell + Dashboard
```
Using the MeetIQ design system (Linear/Notion-inspired B2B SaaS, indigo accent, light gray background, Inter font, collapsible left sidebar), generate the application shell and Dashboard home screen with stats cards, recent meetings list, quick actions, and sample meeting showcase for new users.
```

### Prompt B — Upload + processing status
```
Same design system. Upload screen with drag-drop zone, meeting metadata form (title, datetime, timezone, speaker labeling toggle), and a horizontal status stepper: Uploaded → Transcribing → Analyzing → Ready, with error states for failed jobs.
```

### Prompt C — Meeting detail (results)
```
Same design system. Meeting detail page with tabs: Summary, Transcript, Actions & Decisions, Integrations. Summary shows executive summary, key points, decision cards with evidence quotes and timestamps, action item cards with owner/due date or "Not identified". Include export actions in header.
```

### Prompt D — Search + Integrations
```
Same design system. Global search page with keyword/semantic mode toggle and highlighted result snippets. Integrations hub with Jira, Linear, Trello, Slack, Email cards and export history table.
```

### Prompt E — Live meeting
```
Same design system. Live meeting split view: left side session controls and recording indicator, right side DRAFT-labeled rolling summary, live transcript feed, and emerging action items. Finalize button prominent.
```

### Prompt F — Admin + Auth
```
Same design system. Admin panel with workspace settings, usage quotas progress bars, audit log table, retention purge controls. Separate login screen with SSO button and clean centered card layout.
```

---

## Follow-up prompts for refinement

| Goal | Prompt |
|------|--------|
| Dark mode | “Convert all screens to dark mode variant using slate #0F172A background and #1E293B cards.” |
| Mobile | “Create mobile responsive versions with bottom navigation tab bar.” |
| Empty states | “Add illustrated empty states for dashboard, meetings list, and search with clear CTAs.” |
| Loading | “Add skeleton loading states for meeting detail while status is Transcribing or Analyzing.” |
| Status badges | “Design a status badge component set: UPLOADED, TRANSCRIBING, ANALYZING, READY, FAILED (red), DRAFT (amber).” |
| Action items | “Design action item cards similar to Asana tasks with owner avatar, due date, and evidence quote expandable section.” |

---

## Feature ↔ phase mapping (reference)

| UI area | Phase |
|---------|-------|
| Upload, meeting list, detail, status pipeline | Phase 1 |
| Speaker labels, evidence quotes, confidence, diarization toggle | Phase 2 |
| Search, integrations export, integration hub | Phase 3 |
| Live meeting, draft badge, finalize, rolling summary | Phase 4 |
| Auth/SSO, admin, audit log, quotas, retention, RBAC | Phase 5 |

---

## Key data fields to show in UI (from backend schema)

**Meeting metadata:** id, title, created_at, status, original_filename, meeting_start, timezone, error_message

**Status values:** `UPLOADED` · `TRANSCRIBING` · `ANALYZING` · `READY` · `FAILED_TRANSCRIPTION` · `FAILED_ANALYSIS`

**Insights output:** executive_summary, key_discussion_points[], decisions_made[] (decision, evidence_quote, timestamp_range, confidence), action_items[] (title, owner, due_date, evidence_quote, timestamp_range, priority)

**Transcript segment:** start_s, end_s, text, speaker_id (optional)

**Live session:** last_processed_seq, audio_duration_s, is_draft flag on transcript/insights until finalized

**Admin:** retention_days, data_region, max_meetings_per_month, max_llm_tokens_per_month, audit log entries, workspace role
