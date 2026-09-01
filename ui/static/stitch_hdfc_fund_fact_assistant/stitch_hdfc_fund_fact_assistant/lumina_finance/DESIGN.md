---
name: Lumina Finance
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
  on-surface-variant: '#bec8d2'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#88929b'
  outline-variant: '#3e4850'
  surface-tint: '#89ceff'
  primary: '#89ceff'
  on-primary: '#00344d'
  primary-container: '#0ea5e9'
  on-primary-container: '#003751'
  inverse-primary: '#006591'
  secondary: '#ffb95f'
  on-secondary: '#472a00'
  secondary-container: '#ee9800'
  on-secondary-container: '#5b3800'
  tertiary: '#ffb86e'
  on-tertiary: '#492900'
  tertiary-container: '#de8712'
  on-tertiary-container: '#4d2b00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c9e6ff'
  primary-fixed-dim: '#89ceff'
  on-primary-fixed: '#001e2f'
  on-primary-fixed-variant: '#004c6e'
  secondary-fixed: '#ffddb8'
  secondary-fixed-dim: '#ffb95f'
  on-secondary-fixed: '#2a1700'
  on-secondary-fixed-variant: '#653e00'
  tertiary-fixed: '#ffdcbd'
  tertiary-fixed-dim: '#ffb86e'
  on-tertiary-fixed: '#2c1600'
  on-tertiary-fixed-variant: '#693c00'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  caption:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 16px
  bubble-padding: 16px 20px
  stack-gap-sm: 8px
  stack-gap-md: 16px
  stack-gap-lg: 32px
---

## Brand & Style

This design system is engineered for a premium fintech experience, specifically tailored for high-trust financial advisory and mutual fund exploration. The aesthetic balances the precision of modern SaaS with the gravitas of a traditional wealth management firm. 

The visual narrative is built on **Glassmorphism**, utilizing layered transparency and background blurs to simulate depth and sophistication. The interface feels lightweight and digital-native, yet grounded by a sturdy charcoal foundation. The emotional response should be one of calm confidence, clarity, and technological edge.

- **Primary Style:** Glassmorphism with deep-set background blurs (12px - 20px).
- **Aesthetic Pillars:** High-precision typography, luminous borders, and subtle physical metaphors (frosted glass).
- **Target Audience:** Sophisticated investors, financial advisors, and digitally-literate wealth builders.

## Colors

The palette is anchored in a deep "Midnight Naval" spectrum, providing a high-contrast backdrop that reduces eye strain during long reading sessions.

- **Background Palette:** A gradient from `#0F172A` to `#1E293B` creates a sense of infinite depth.
- **Primary Accent (Teal/Cyan):** Used for actionable intent, progress indicators, and user-initiated chat states.
- **Secondary Accent (Financial Gold):** Reserved exclusively for disclaimers, high-risk fund categories, and cautionary guidance.
- **Border Treatments:** Use a semi-transparent white (10-15% opacity) or a faint teal glow to define glass edges against the dark background.

## Typography

This design system utilizes **Plus Jakarta Sans** across all levels to maintain a contemporary, optimistic feel while ensuring maximum legibility in data-dense financial contexts.

- **Weight Strategy:** Use Bold (700) for displays, SemiBold (600) for headlines and labels, and Regular (400) for long-form assistant responses.
- **Readability:** Paragraphs within chat bubbles should use `body-md` with generous line-height (1.5x) to ensure financial terminology is easily digestible.
- **Hierarchy:** Use `label-md` for metadata like "Source" or "Timestamp" to distinguish them clearly from the primary conversational text.

## Layout & Spacing

The layout follows a **fluid-to-fixed** model. On desktop, the assistant interface is centered with a max-width of 900px to maintain focus. On mobile, elements take the full width minus a 16px safe-area margin.

- **The 4px Rhythm:** All spacing and sizing must be multiples of 4px to ensure a rigid, professional grid.
- **Chat Flow:** Assistant messages are left-aligned; user queries are right-aligned. A 32px gap separates distinct conversational turns, while a 8px gap groups related content (e.g., a response followed by a disclaimer).
- **Responsive Behavior:** On mobile devices, complex data tables within responses should transition to a horizontally scrollable card format or a simplified list view.

## Elevation & Depth

Hierarchy is established through **translucency levels** rather than traditional shadows.

- **Layer 0 (Background):** Solid `#0F172A` or a very subtle linear gradient.
- **Layer 1 (Chat Bubbles):** Glassmorphism with `background: rgba(30, 41, 59, 0.7)`, a 1px border of `rgba(255, 255, 255, 0.1)`, and a `backdrop-filter: blur(12px)`.
- **Layer 2 (Popovers/Modals):** Increased opacity `rgba(30, 41, 59, 0.9)` with a 1px border glow using the primary teal color at 20% opacity.
- **Shadows:** Avoid heavy black shadows. Use "Ambient Glows" where the shadow color matches the surface color but with lower saturation and higher spread (e.g., 0px 8px 24px rgba(0,0,0,0.3)).

## Shapes

The shape language is consistently rounded to evoke a modern, approachable fintech persona.

- **Base Radius:** 16px (`rounded-lg`) is the standard for chat bubbles and cards.
- **Interactive Elements:** Buttons and input fields use 12px or 16px to match the container language.
- **Chips & Badges:** Use a pill-shape (full radius) to differentiate them from structural content containers.
- **Border Width:** Keep borders thin (1px) to maintain a refined, high-end feel.

## Components

### Chat Bubbles
- **Assistant:** Layer 1 glass style with a subtle white border. Use `body-md` for text.
- **User:** Primary Teal background (`#0EA5E9`) with white text. High contrast to signify user action.

### Source-Citation Chips
- Small, secondary pill-shaped elements nested at the bottom of messages.
- Style: `rgba(255, 255, 255, 0.05)` background with a 1px border. 
- Hover state: Border color changes to Primary Teal.

### Risk Category Badges
- **Low Risk:** Teal text on a 10% opacity teal background.
- **High Risk:** Gold (`#F59E0B`) text on a 10% opacity gold background.
- Always include a small icon (e.g., a shield or warning triangle) for accessibility.

### Interactive Example Cards
- Featured fund examples or FAQ suggestions.
- Style: Layer 1 glass with a "Border Glow" effect. On hover, the background blur should intensify from 12px to 20px, and the border opacity should increase.

### Input Field
- Fixed at the bottom of the viewport.
- 100% background blur, 1px border.
- The "Send" button should be a circular Primary Teal button with a white icon.