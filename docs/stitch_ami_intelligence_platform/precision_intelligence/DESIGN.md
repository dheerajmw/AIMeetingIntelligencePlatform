---
name: Precision Intelligence
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#464554'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#767586'
  outline-variant: '#c7c4d7'
  surface-tint: '#494bd6'
  primary: '#4648d4'
  on-primary: '#ffffff'
  primary-container: '#6063ee'
  on-primary-container: '#fffbff'
  inverse-primary: '#c0c1ff'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#904900'
  on-tertiary: '#ffffff'
  tertiary-container: '#b55d00'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#ffdcc5'
  tertiary-fixed-dim: '#ffb783'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#703700'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  metadata:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
---

## Brand & Style

The design system is engineered for high-performance B2B workflows, prioritizing clarity and cognitive ease. The brand personality is **Trustworthy, Efficient, and Calm**, reflecting the platform's role in distilling complex human interactions into actionable intelligence.

The visual style is a fusion of **Enterprise Minimalism** and **Systematic Utility**. It draws inspiration from the precision of developer tools (tight spacing, subtle borders) and the readability of modern knowledge bases (calm hierarchy, intentional whitespace). The UI should feel like a sophisticated instrument—quiet when idle, but hyper-focused and legible during analysis.

Key stylistic pillars:
- **Precision:** 1px strokes define the structure without adding visual noise.
- **Clarity:** Generous line-heights and whitespace for dense meeting transcripts.
- **Utility:** Function-first aesthetics where every element serves a data-driven purpose.

## Colors

The palette is anchored in a professional grayscale (Slate/Zinc) to ensure a neutral environment for content analysis. 

- **Primary (Indigo):** Reserved for primary actions, focus states, and key brand moments.
- **Neutral Base:** Uses Slate-50 for backgrounds and Slate-900 for primary text to maintain a soft, high-contrast readability.
- **Semantic Accents:** Emerald (Success), Amber (Warning), and Rose (Error) are used sparingly for status indicators and data visualization.
- **Borders:** A consistent 1px stroke (#E2E8F0) is the primary method for defining containers, replacing heavy shadows.

## Typography

This design system utilizes **Inter** exclusively to leverage its geometric clarity and exceptional legibility at small sizes.

- **Transcripts & Summaries:** Use `body-md` with an increased line-height (1.6x) to facilitate scanning long-form text.
- **Metadata:** Captions and timestamps use `metadata` (13px) with a medium weight to maintain visibility without competing with primary content.
- **Hierarchy:** Maintain a tight scale. Most interface text stays between 13px and 16px to maximize data density while ensuring accessibility.

## Layout & Spacing

The layout follows a **Mobile-First** philosophy with a focus on single-column content streams on smaller screens and multi-pane orchestration on desktop.

- **Mobile:** Uses a persistent bottom navigation bar (64px height) for primary app sections. Margins are fixed at 16px.
- **Desktop:** Features a collapsible sidebar (240px width) for navigation and workspace switching. Content views utilize a flexible grid that caps at 1200px for optimal reading length.
- **Spacing Rhythm:** Based on a 4px baseline grid. Components generally use 8px (sm) or 16px (md) internal padding to maintain a "tight" but breathable feel.

## Elevation & Depth

Hierarchy is established primarily through **Tonal Layering** and **Subtle Outlines** rather than dramatic shadows.

- **Base Level:** The background is Slate-50.
- **Surface Level:** Content cards and containers are White with a 1px border (#E2E8F0).
- **Elevated Level:** Modals, dropdowns, and active tooltips use a very soft, diffused shadow (0px 4px 12px rgba(15, 23, 42, 0.05)) to separate them from the content plane.
- **Active States:** Subtle 1px inset shadows or slight background shifts (Slate-100) indicate interactivity.

## Shapes

The shape language is precise and professional.
- **Cards & Containers:** 8px radius provides a modern, soft feel without appearing overly casual.
- **Interactive Elements:** Buttons and Input fields use a tighter 6px radius to signify utility.
- **Status Indicators:** Badges and chips are fully pill-shaped (round) to distinguish them from actionable buttons and structural cards.

## Components

- **Buttons:** 6px radius. Primary buttons use Indigo background with white text. Ghost buttons use a 1px Slate-200 border and Slate-700 text.
- **Cards:** 8px radius, white background, 1px #E2E8F0 border. No shadow by default.
- **Status Badges:** Pill-shaped. Use low-saturation background tints (e.g., Success: Emerald-50 background, Emerald-700 text).
- **Input Fields:** 6px radius, 1px #E2E8F0 border. Focus state: 1px Indigo-500 border with a 2px Indigo-100 outer glow.
- **Lists:** Clean rows with 1px bottom borders. Hover state uses Slate-50 background shift.
- **Navigation:**
    - **Mobile:** Fixed bottom bar with 24px icons and 12px labels.
    - **Desktop Sidebar:** Minimalist icons with `body-sm` text; active state indicated by an Indigo vertical bar (2px) on the left edge.
- **Transcript Blocks:** Use systematic indentation for speakers and generous `line-height` for the text body.