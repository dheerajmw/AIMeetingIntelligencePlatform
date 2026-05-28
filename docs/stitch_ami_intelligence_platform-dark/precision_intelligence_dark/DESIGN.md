---
name: Precision Intelligence Dark
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#7bd0ff'
  on-secondary: '#00354a'
  secondary-container: '#00a6e0'
  on-secondary-container: '#00374d'
  tertiary: '#ffb2b7'
  on-tertiary: '#67001b'
  tertiary-container: '#ff516a'
  on-tertiary-container: '#5b0017'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c0c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2f2ebe'
  secondary-fixed: '#c4e7ff'
  secondary-fixed-dim: '#7bd0ff'
  on-secondary-fixed: '#001e2c'
  on-secondary-fixed-variant: '#004c69'
  tertiary-fixed: '#ffdadb'
  tertiary-fixed-dim: '#ffb2b7'
  on-tertiary-fixed: '#40000d'
  on-tertiary-fixed-variant: '#92002a'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  code:
    fontFamily: jetbrainsMono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  margin: 24px
---

## Brand & Style
The design system is a high-performance, technical framework designed for data-intensive applications and developer tools. It emphasizes clarity, focus, and a "heads-up display" aesthetic.

The style is **Corporate Modern** with a lean toward **Minimalism**. It utilizes deep spatial depth to organize complex information hierarchies without visual clutter. The emotional response is one of reliability, precision, and sophisticated control. The UI recedes to let data and actionable insights take center stage, using light only where attention is required.

## Colors
The palette is rooted in a deep slate foundation to reduce eye strain during prolonged technical work.

- **Surface (Background):** `#0F172A` — A deep slate that provides a stable base for the interface.
- **Surface-Container (Cards/Layers):** `#1E293B` — Used for elevated elements, providing subtle contrast against the base.
- **Primary Accent:** `#6366F1` (Indigo) — Used for primary actions, active states, and critical branding moments.
- **Typography:** 
    - High-contrast headings: `#F8FAFC` (Zinc-50).
    - Secondary/Body text: `#94A3B8` (Slate-400) to ensure hierarchy and readability.
- **Status Colors:** Optimized for dark mode luminosity to ensure "Ready" (Green), "Processing" (Amber), and "Failed" (Red) remain distinct and accessible.

## Typography
The typography system uses **Inter** for its exceptional legibility in UI contexts and its systematic, utilitarian feel. 

- **Headlines:** Use tighter letter-spacing and heavier weights to create a strong visual anchor.
- **Body Text:** Scaled for high readability with generous line heights.
- **Labels:** Small caps or uppercase labels are used for metadata and category headers to differentiate from body content.
- **Monospace:** Use JetBrains Mono for data strings, IDs, and code snippets to maintain the technical character of the design system.

## Layout & Spacing
This design system utilizes a **12-column fluid grid** for desktop and a **4-column fluid grid** for mobile. 

- **Spacing Rhythm:** Based on a strict 4px/8px incremental scale. All padding and margins must be multiples of 4.
- **Grid Layout:** 24px gutters provide significant breathing room between data modules.
- **Responsive Behavior:** On tablet, gutters shrink to 16px. On mobile, side margins are reduced to 16px to maximize screen real estate.

## Elevation & Depth
In this dark mode environment, depth is conveyed through **Tonal Layering** and **Subtle Outlines** rather than heavy shadows.

- **Level 0 (Base):** `#0F172A` — The canvas.
- **Level 1 (Cards):** `#1E293B` — Slightly lighter than the base. Used for primary content containers.
- **Level 2 (Modals/Popovers):** `#334155` (Slate-700) with a subtle 1px border (`#475569`). 
- **Outlines:** Use low-contrast borders (`#1E293B` or `#334155`) to define boundaries. Avoid drop shadows unless used for floating elements like dropdown menus, where a 25% black shadow with a 15px blur is permitted.

## Shapes
The shape language is precise and disciplined. 

- **Standard Elements:** 4px (`0.25rem`) corner radius for buttons, input fields, and small UI widgets.
- **Containers:** 8px (`0.5rem`) corner radius for cards and larger content sections.
- **Status Indicators:** Use the "Pill" style for badges to differentiate them from interactive buttons.

## Components

### Buttons
- **Primary:** Solid Indigo (`#6366F1`) with white text. 4px radius.
- **Secondary:** Ghost style with a 1px slate-700 border and Zinc-50 text.
- **States:** Hover states should involve a subtle lightening of the background color (e.g., Indigo-500).

### Status Badges
- **Ready:** Background `rgba(16, 185, 129, 0.1)`, Text `#10B981`.
- **Processing:** Background `rgba(245, 158, 11, 0.1)`, Text `#F59E0B`.
- **Failed:** Background `rgba(239, 68, 68, 0.1)`, Text `#EF4444`.
- All badges use a full pill radius and uppercase label-md typography.

### Input Fields
- **Default:** Background `#1E293B`, Border 1px `#334155`, Text Zinc-50.
- **Focus:** Border 1px Indigo (`#6366F1`), with a subtle outer glow (0px 0px 0px 2px rgba(99, 102, 241, 0.2)).

### Cards
- Background `#1E293B`. No shadow. Use a 1px border of `#334155` for additional definition if multiple cards are adjacent.

### Data Tables
- Row lines should be subtle (`#1E293B`).
- Header row background should be slightly darker or use a specific label-md style for column titles.