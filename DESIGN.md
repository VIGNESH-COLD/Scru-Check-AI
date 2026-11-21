---
name: ScruCheckAI
description: Institutional Question Paper Scrutiny Platform • Anna University Compliance
colors:
  primary: "#0d6b5c"
  primary-hover: "#0b594d"
  primary-surface: "#f0f9f6"
  primary-line: "#b9ddd4"
  accent: "#ea8c00"
  accent-hover: "#d47f00"
  accent-surface: "#fffbeb"
  accent-line: "#fde68a"
  accent-ink: "#9a4e00"
  canvas: "#eef4f1"
  surface: "#ffffff"
  surface-subtle: "#f9fbfa"
  surface-muted: "#f0f5f3"
  line: "#dbe7e2"
  line-subtle: "#e6ede9"
  track: "#e2ede8"
  ink: "#111827"
  ink-muted: "#4b5563"
  ink-faint: "#6b7280"
  danger: "#dc2626"
  danger-surface: "#fef2f2"
  success: "#0d6b5c"
typography:
  display:
    fontFamily: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 800
    lineHeight: "2.5rem"
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: "1.75rem"
    letterSpacing: "-0.025em"
  title:
    fontFamily: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: "1.5rem"
    letterSpacing: "0em"
  body:
    fontFamily: "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: "1.25rem"
    letterSpacing: "0em"
  label:
    fontFamily: "'JetBrains Mono', monospace"
    fontSize: "0.6875rem"
    fontWeight: 600
    lineHeight: "1rem"
    letterSpacing: "0.05em"
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
  full: "9999px"
spacing:
  xs: "6px"
  sm: "8px"
  md: "16px"
  lg: "20px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "10px 20px"
  button-accent:
    backgroundColor: "{colors.accent}"
    textColor: "#0f172a"
    rounded: "{rounded.md}"
    padding: "14px 24px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "24px"
  badge:
    backgroundColor: "{colors.primary-surface}"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    padding: "2px 10px"
---

# Design System: ScruCheckAI

## Overview

**Creative North Star: "The Academic Sanctuary"**

ScruCheckAI is an authoritative, serene, and disciplined examination studio designed for educators and scrutiny committees. Rather than imposing the sterile tension of an audit or the chaotic noise of consumer AI tools, the interface provides a calm, focused environment that balances institutional prestige with modern technological clarity. It gives faculty the confidence of working within an official academic council chamber while delivering instantaneous, actionable scrutiny and automated remediation.

The density is calibrated for high-stakes operational review: generous whitespace around core cards keeps cognitive fatigue low, while compact, monospace tables and data strips present forensic mark breakdowns and Bloom's Taxonomy analytics with mathematical precision. The aesthetic is clean, intentional, and dignified—rejecting decorative gradients, floating novelty bubbles, and gratuitous micro-illustrations in favor of crisp typography, structural hairline borders, and purposeful contrast.

**Key Characteristics:**
- **Sovereign Color Anchor:** Imperial Institutional Teal provides grounding authority, while Academic Amber drives intentional forward progress.
- **Tonal Layering:** Spatial depth is established by surface contrast and whispering 1px borders rather than heavy drop-shadows.
- **Mathematical Typography Pairing:** Warm, contemporary geometric sans (`Plus Jakarta Sans`) paired with tabular monospace (`JetBrains Mono`) for all examination calculations and criteria numbers.
- **Bimodal Harmony:** Seamless transitions between a high-legibility Mint Paper Light mode and a low-glare Abyssal Teal Dark mode for prolonged grading cycles.

## Colors

The color palette reflects institutional gravitas and academic optimism: deep botanical teals evoke institutional credibility, balanced by radiant ambers that signal high-value forward actions and critical scrutiny highlights.

### Primary
- **Imperial Institutional Teal** (`#0d6b5c` in Light mode / `#2dd4bf` in Dark mode): The primary brand anchor. Applied to institutional banners, primary navigation capsules, active pattern selection rings, and verified compliance badges.
- **Teal Surface Tint** (`#f0f9f6` in Light mode / `rgba(45, 212, 191, 0.12)` in Dark mode): Used for active badge fills, table highlight rows, and verified criteria cards.
- **Teal Line** (`#b9ddd4` in Light mode / `rgba(45, 212, 191, 0.28)` in Dark mode): Delimits selected cards and provides active focus rings.

### Secondary
- **Scholarly Gold / Academic Amber** (`#ea8c00` in Light mode / `#f59e0b` in Dark mode): The primary action and remediation catalyst. Reserved for primary submission triggers ("Check Question Paper"), Syllabus ingestion zones, and Part B mark distribution indicators.
- **Amber Surface** (`#fffbeb` in Light mode / `rgba(245, 158, 11, 0.14)` in Dark mode): Container fill for remediation warnings and syllabus upload zones.
- **Amber Line** (`#fde68a` in Light mode / `rgba(245, 158, 11, 0.32)` in Dark mode): Dashed borders on syllabus drop areas and warning callouts.

### Neutral
- **Mint Paper Canvas** (`#eef4f1` in Light mode / `#061512` in Dark mode): The serene backdrop upon which all evaluation cards rest.
- **Crisp Card Surface** (`#ffffff` in Light mode / `#0c201c` in Dark mode): Elevated white and deep charcoal containers holding specific inspection modules.
- **Subtle Surface** (`#f9fbfa` in Light mode / `#102924` in Dark mode): Hover states and nested container fills.
- **Hairline Border Line** (`#dbe7e2` in Light mode / `#1c453d` in Dark mode): 1px structural separator defining card perimeters.
- **Deep Ink Text** (`#111827` in Light mode / `#f0fdf9` in Dark mode): High-contrast primary headings and regulatory text.
- **Muted Ink** (`#4b5563` in Light mode / `#94b9b0` in Dark mode): Subtitles, descriptions, and table metadata.
- **Faint Ink** (`#6b7280` in Light mode / `#5d877e` in Dark mode): Placeholders, file sizes, and secondary notes.

### Feedback
- **Academic Red / Critical Alert** (`#dc2626` in Light mode / `#ef4444` in Dark mode): Used strictly for blocking scrutiny errors (e.g. mark mismatches, missing compulsory fields).
- **Red Alert Surface** (`#fef2f2` in Light mode / `rgba(239, 68, 68, 0.16)` in Dark mode): Banner background for blocking reasons and validation failure summaries.

### Named Rules
**The Amber Action Rule.** Amber is strictly reserved for primary forward-momentum triggers (e.g., "Check Question Paper", syllabus attachment) and Part B balance indicators. It must never be applied to passive chrome, generic cards, or decorative borders.

**The Rarity Rule.** High-saturation brand colors occupy less than 15% of the viewport at rest. The interface lets clean white/charcoal document surfaces and clear typography dominate, ensuring faculty can review 50+ questions without visual saturation.

## Typography

The typography unites humanistic modern sans-serif headings with forensic tabular monospace numerals, ensuring examination figures, part subdivisions, and regulation codes align with mathematical certainty.

**Display Font:** `Plus Jakarta Sans` (fallback: `system-ui, -apple-system, sans-serif`)  
**Body Font:** `Plus Jakarta Sans` (fallback: `system-ui, -apple-system, sans-serif`)  
**Label/Mono Font:** `JetBrains Mono` (fallback: `monospace`)

**Character:** Scholarly, authoritative, modern, and impeccably legible. Geometric letterforms prevent visual fatigue, while tabular figures eliminate layout jitter during live calculations.

### Hierarchy
- **Display** (800 ExtraBold, `2.25rem` / `36px`, line-height `2.5rem`, tracking `-0.025em`): Prominent mark figures (e.g. "50 marks"), percentage compliance scores.
- **Headline** (700 Bold, `1.25rem` / `20px`, line-height `1.75rem`, tracking `-0.025em`): Primary section headings ("Exam Pattern", "ScruCheckAI", "Question Paper Scrutiny Approved").
- **Title** (700 Bold, `1rem` / `16px`, line-height `1.5rem`): Card titles, modal headers, criteria module titles.
- **Body** (400 Regular / 500 Medium, `0.875rem` / `14px`, line-height `1.25rem`): Instructional text, question descriptions, criteria feedback notes. Max line length: 65–75ch.
- **Label / Tag** (600 SemiBold, `0.6875rem` / `11px`, line-height `1rem`, tracking `0.05em`, uppercase monospace): Badges ("SELECTED", "ALTERNATE", "APPROVED", "PASS"), mark formulas ("5×2=10"), and timestamp stamps.

### Named Rules
**The Tabular Precision Rule.** Every numeric calculation, question identifier (e.g. "Q14.a"), mark breakdown formula ("10×2=20"), and regulation year ("Regulations 2023") must render in `JetBrains Mono` with tabular figure spacing.

## Layout

The layout uses a centered single-column spine (`max-w-[860px]` to `max-w-[920px]`) centered within a generous canvas. This reflects the familiar physical proportion of academic portfolios and examination dossier folders.

- **Vertical Rhythm:** 20px (`gap-5` / `space-y-5`) between primary modules maintains clear task boundaries while keeping the entire setup visible above the fold on desktop viewports.
- **Card Grids:**
  - *Pattern Selection:* 2-column balanced grid (`grid grid-cols-1 md:grid-cols-2 gap-5`).
  - *Document Ingestion & Configuration:* 3-column modular grid (`grid grid-cols-1 md:grid-cols-3 gap-5`).
  - *Execution Action Banner:* Full-width horizontal strip (`rounded-2xl p-6`) anchoring the bottom of the workspace.
- **Responsive Behavior:** On screens `< 768px`, grids collapse gracefully into single-column flows while retaining identical internal padding (`p-5` to `p-6`) and touch-target sizes (minimum 44px height for interactive targets).

## Elevation & Depth

ScruCheckAI adheres to **Tonal Layering with Whispering Borders**. Depth is communicated through subtle lightness deltas between surfaces rather than heavy ambient blur or dramatic drop shadows.

Surfaces rest flat on the canvas. High-fidelity 1px hairline borders (`border border-line`) define containers with clinical precision.

### Shadow Vocabulary
- **Card Rest** (`box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04)`): Baseline ambient separation for white cards resting on the mint canvas.
- **Action Banner / Active Drawer** (`box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08)`): Reserved for primary floating triggers ("Check Question Paper") and active modals.

### Named Rules
**The Flat-at-Rest Rule.** All surfaces and cards remain flat at rest. Elevation changes occur only dynamically as an active response to user input (e.g., hover lift or button click compression).

## Shapes

- **Corner Strategy:** Soft institutional geometry using calibrated concentric rounded corners:
  - Containers & Major Panels: `16px` (`rounded-2xl`)
  - Buttons, Controls & Inputs: `12px` (`rounded-xl`)
  - Badges, Segmented Pills & Indicators: `9999px` (`rounded-full`)
- **Continuous Distribution Bars:** Progress bars for Part A / Part B distribution are housed in a single pill container (`rounded-full h-2.5 overflow-hidden flex`) with zero internal gap, cleanly dividing the teal and amber sections into a seamless physical spectrum.
- **Dashed Upload Boundaries:** Inactive upload zones feature 2px dashed borders (`border-2 border-dashed border-brand-line` or `border-accent-line`) with `16px` curvature, providing an inviting, tactile drop target.

## Components

### Buttons
- **Primary Action (Brand):**
  - Shape: Rounded-xl (`12px`)
  - Colors: Imperial Teal background (`#0d6b5c`), Crisp White text (`#ffffff`), border 1px solid brand
  - Hover: Darker teal (`#0b594d`), active transform scale-98
- **Catalyst Action (Amber):**
  - Shape: Rounded-xl (`12px`)
  - Colors: Academic Amber background (`#ea8c00` / `#f59e0b`), Deep Charcoal text (`#0f172a` font-extrabold)
  - Hover: Deep amber (`#d47f00`), active scale-98
- **Segmented Control Buttons:**
  - Contained within an outer pill track (`bg-track p-1.5 rounded-2xl`).
  - Active state: Solid teal (`bg-brand text-white shadow-sm font-bold rounded-xl`).
  - Inactive state: Transparent with muted ink hover (`text-ink-muted hover:text-ink font-medium`).

### Cards / Containers
- **Corner Style:** `rounded-2xl` (`16px`)
- **Background:** Crisp White (`#ffffff`) in Light mode; Charcoal Teal (`#0c201c`) in Dark mode.
- **Border:** 1px solid Line token (`#dbe7e2` light / `#1c453d` dark).
- **Selected State:** 2px solid Brand Teal (`#0d6b5c`) with subtle 1px ring expansion.
- **Padding:** 20px to 24px (`p-5` to `p-6`).

### Upload Dropzones
- **Style:** 2px dashed border in brand or accent line color, `rounded-2xl`, internal min-height `155px`.
- **States:** Hover background tint (`bg-surface-subtle`), icon micro-zoom (`group-hover:scale-110`).
- **File Selected:** Green/teal check icon, truncated filename, file size badge in monospace, and dedicated "Change" / "Remove" controls.

### Status Badges & Chips
- **Selected Badge:** Solid brand teal pill, white text `text-[11px] font-semibold`.
- **Alternate Badge:** Light track gray pill, muted ink text `text-[11px] font-semibold`.
- **Verdict Badges:** Solid dark pill (`#0f172a` or `#0d6b5c`) for "APPROVED" / "PASS"; high-visibility warning pill for "REVIEW REQUIRED".

## Do's and Don'ts

### Do:
- **Do** maintain the 100% strict requirement that scrutiny reports export **only as PDF** (`.pdf`).
- **Do** pair every status indicator with explicit textual labels and icons to ensure full accessibility for color-blind faculty.
- **Do** preserve academic, mathematical, and algorithmic vocabulary without triggering grammar or spelling defect warnings.
- **Do** keep the "Check Question Paper" catalyst button solid amber with bold dark text (`text-slate-900`) for maximum legibility.
- **Do** ensure all numerical marks, timestamps, and question identifiers render in `JetBrains Mono`.

### Don't:
- **Don't** use amber for general decorative backgrounds, borders, or non-action elements.
- **Don't** add numerical percentage scores to qualitative linguistic or clarity evaluations; use strict categorical indicators.
- **Don't** add format-selection dropdowns (Word, HTML, CSV) to the report export module.
- **Don't** introduce heavy multi-layered drop shadows; preserve the clean, calm tonal layering.
- **Don't** allow arbitrary color splits in question mark distribution bars; Part A is always Teal, Part B is always Amber.
