---
name: Professional Decision Intelligence
colors:
  surface: '#faf8ff'
  surface-dim: '#d9d9e5'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3fe'
  surface-container: '#ededf9'
  surface-container-high: '#e7e7f3'
  surface-container-highest: '#e1e2ed'
  on-surface: '#191b23'
  on-surface-variant: '#434655'
  inverse-surface: '#2e3039'
  inverse-on-surface: '#f0f0fb'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#943700'
  on-tertiary: '#ffffff'
  tertiary-container: '#bc4800'
  on-tertiary-container: '#ffede6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#ffdbcd'
  tertiary-fixed-dim: '#ffb596'
  on-tertiary-fixed: '#360f00'
  on-tertiary-fixed-variant: '#7d2d00'
  background: '#faf8ff'
  on-background: '#191b23'
  surface-variant: '#e1e2ed'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  title-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-base:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  metric-lg:
    fontFamily: JetBrains Mono
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 32px
  metric-md:
    fontFamily: JetBrains Mono
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
  metric-sm:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
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
  gutter: 24px
  margin: 32px
  container-max: 1440px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 24px
---

## Brand & Style
The design system is engineered for the high-stakes environment of real estate investment, where clarity equals confidence. The aesthetic follows a **Corporate / Modern** approach, prioritizing functional realism over decorative trends. It evokes "Professional Decision Intelligence"—a state of focused analysis where the UI recedes to highlight actionable data.

The brand personality is authoritative, institutional, and precise. It targets institutional investors and fund managers who require rapid cognitive processing of complex portfolios. The interface utilizes a "flat-plus" philosophy: primarily flat surfaces distinguished by subtle depth markers to establish a clear information hierarchy without visual fatigue.

## Colors
This design system employs a high-trust palette rooted in functional utility. 

- **Primary Blue** is reserved for core intent: primary actions, active navigation states, and focus indicators.
- **Semantic Colors** (Emerald, Amber, Red) are used strictly for performance indicators—ROI growth, risk assessment, and legal alerts. These must maintain high contrast against white surfaces.
- **Surface Strategy**: A slate-tinted background (#f8fafc) provides a soft canvas that makes pure white (#ffffff) card surfaces "pop," indicating interactive or data-rich containers.
- **Text Hierarchy**: Deep slate (#1e293b) ensures maximum legibility for body text, while a secondary slate (#64748b) is used for metadata and labels to reduce visual noise.

## Typography
The system uses a dual-font strategy to separate narrative from empirical data. 

- **Inter** handles all UI chrome, labels, and descriptive text. Its neutral, systematic geometry supports the "Professional" tone.
- **JetBrains Mono** is utilized exclusively for financial metrics, cap rates, and numerical data. This technical precision ensures that digits align vertically in tables, facilitating faster price and percentage comparisons.
- **Hierarchy**: Use `label-caps` for table headers and section overviews to create a distinct structural "anchor" for the eyes.

## Layout & Spacing
This design system utilizes a **12-column fluid grid** designed for high-density data visualization. 

- **Density**: Spacing is tighter than consumer applications to allow for significant data "above the fold." Use an 8px base grid, with 4px increments for internal component spacing.
- **Layout Model**: A fixed left-hand navigation (240px) with a fluid content area. In dashboard views, cards should span 3, 4, 6, or 12 columns depending on the complexity of the chart.
- **Padding**: Large data tables use a "compact" vertical padding (8px or 12px per row) to maximize the visible records without sacrificing touch/click targets.

## Elevation & Depth
Depth is communicated through **Low-contrast outlines** combined with **Ambient shadows**. 

- **Card Definition**: Every data container must use a 1px solid border (#e2e8f0). This provides a hard "legal" boundary for the data.
- **Shadows**: Use a single, soft "Shadow-SM" (0px 1px 2px rgba(0,0,0,0.05)) to lift cards slightly off the Light Slate background.
- **Interaction**: On hover, interactive cards may transition to a "Shadow-MD" (0px 4px 6px rgba(0,0,0,0.07)) to indicate clickability.
- **Layering**: Avoid multiple nested shadows. Depth should feel like layers of physical paper stacked on a desk.

## Shapes
The shape language is conservative and disciplined. A **Soft (0.25rem)** border radius is the standard for primary UI components like buttons, input fields, and small badges.

- **Cards**: Use `rounded-lg` (0.5rem) to provide a slightly softer frame for high-density data, preventing the UI from feeling overly "sharp" or aggressive.
- **Progress Bars**: Use fully rounded ends (pill-shaped) to distinguish linear progress from structural containers.
- **Buttons**: Square corners are avoided to maintain a modern feel, but the radius never exceeds 4px for primary actions to maintain the "Enterprise" look.

## Components
- **Buttons**: Solid #2563eb with white text for primary actions. Ghost buttons with #e2e8f0 borders for secondary actions.
- **Status Badges**: Small, semi-transparent background tints with high-contrast text (e.g., Red 100 bg with Red 800 text). Labels must be concise (e.g., "High Risk", "Underperforming").
- **Opportunity Scoring**: Progress bars should use a tri-color logic: Emerald for 80-100%, Amber for 50-79%, and Red for below 50%.
- **Data Tables**: Use zebra-striping (light slate #f8fafc) on hover only. Table headers are sticky with a subtle bottom shadow to maintain context during long scrolls.
- **Charts**: Use a professional categorical palette (Blue, Slate, Emerald, Indigo). Avoid "rainbow" palettes. Lines should be 2px thick with no area-fill unless comparing volume.
- **Input Fields**: 1px #e2e8f0 border, white background. On focus, a 2px #2563eb ring with 0% offset.
- **Property Cards**: High-resolution thumbnail on the left/top, followed by a JetBrains Mono metric block for the "Asking Price" or "Yield."