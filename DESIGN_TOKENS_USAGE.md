# Design System Tokens - Usage Guide

## Overview

The Health Collective Design System v2.0 tokens are now available throughout the application via:
- **CSS Variables** - Use in custom CSS
- **Utility Classes** - Use directly in HTML templates

## Quick Start

### 1. Using CSS Variables

All design tokens are available as CSS custom properties with the `--thc-` prefix.

```css
/* Colors */
.my-element {
  background-color: var(--thc-primary-600);
  color: var(--thc-text-inverse);
  border: 1px solid var(--thc-border-default);
}

/* Typography */
.my-heading {
  font-size: var(--thc-h2-size);
  font-weight: var(--thc-h2-weight);
  line-height: var(--thc-h2-line);
}

/* Spacing */
.my-card {
  padding: var(--thc-padding-card);
  margin-bottom: var(--thc-stack-md);
  gap: var(--thc-gap-md);
}

/* Border & Shadow */
.my-container {
  border-radius: var(--thc-radius-xl);
  box-shadow: var(--thc-shadow-sm);
}
```

### 2. Using Utility Classes

Utility classes provide quick styling without writing custom CSS.

```html
<!-- Background Colors -->
<div class="bg-primary text-inverse">Primary background</div>
<div class="bg-success text-inverse">Success background</div>

<!-- Text Colors -->
<span class="text-primary">Primary text</span>
<span class="text-muted">Muted text</span>

<!-- Border Radius -->
<div class="rounded-md">Medium rounded corners</div>
<div class="rounded-xl">Large rounded corners</div>

<!-- Shadows -->
<div class="shadow-sm">Small shadow</div>
<div class="shadow-lg">Large shadow</div>

<!-- Spacing -->
<div class="gap-md">12px gap</div>

<!-- Font Weights -->
<span class="font-semibold">Semibold text</span>
<span class="font-mono">Monospace text</span>
```

## Token Categories

### Colors

#### Semantic Colors (Use These!)
```css
--thc-primary-600    /* Brand teal - buttons, links */
--thc-success-600    /* Green - approvals, success */
--thc-info-600       /* Blue - informational */
--thc-warning-600    /* Amber - caution, edits */
--thc-danger-600     /* Red - destructive actions */
```

Each semantic color has a full scale (50-900):
```css
--thc-primary-900    /* Darkest */
--thc-primary-700    /* Dark - hover states */
--thc-primary-600    /* Base - DEFAULT */
--thc-primary-100    /* Lightest - backgrounds */
--thc-primary-50     /* Near white */
```

#### Neutral Colors
```css
--thc-gray-800       /* Primary text */
--thc-gray-500       /* Secondary text */
--thc-gray-200       /* Borders */
--thc-gray-50        /* Page background */
--thc-white          /* Surface/cards */
```

#### Semantic Aliases (Recommended)
```css
/* Backgrounds */
--thc-bg-page        /* Page background */
--thc-bg-surface     /* Card/container background */

/* Text */
--thc-text-primary   /* Main text color */
--thc-text-secondary /* Muted text */
--thc-text-inverse   /* White text on dark backgrounds */

/* Borders */
--thc-border-default /* Standard border color */
--thc-border-light   /* Lighter borders */
```

### Typography

#### Font Sizes
```css
--thc-text-xs        /* 12px - badges, labels */
--thc-text-sm        /* 14px - body text (most common) */
--thc-text-base      /* 16px - default */
--thc-text-lg        /* 20px - large metrics */
--thc-text-xl        /* 24px - section titles */
--thc-text-2xl       /* 30px - page titles */
```

#### Semantic Typography
```css
--thc-h1-size        /* Page heading size */
--thc-h2-size        /* Section heading size */
--thc-body-size      /* Body text size (14px) */
--thc-label-size     /* Label/caption size (12px) */
```

#### Font Weights
```css
--thc-font-normal    /* 400 - body text */
--thc-font-medium    /* 500 - labels */
--thc-font-semibold  /* 600 - headings, buttons */
--thc-font-bold      /* 700 - emphasis */
```

#### Font Families
```css
--thc-font-heading   /* Playfair Display serif */
--thc-font-body      /* Inter sans-serif */
--thc-font-mono      /* DM Mono monospace (for numbers) */
```

### Spacing

All spacing uses a 4px base grid.

#### Core Spacing Scale
```css
--thc-space-1        /* 4px */
--thc-space-2        /* 8px */
--thc-space-3        /* 12px */
--thc-space-4        /* 16px */
--thc-space-6        /* 24px */
--thc-space-8        /* 32px */
--thc-space-12       /* 48px */
```

#### Semantic Spacing
```css
/* Padding */
--thc-padding-button       /* 8px 20px */
--thc-padding-button-sm    /* 8px 12px */
--thc-padding-card         /* 24px */
--thc-padding-card-sm      /* 16px - compact */

/* Gaps (flexbox/grid) */
--thc-gap-xs               /* 4px */
--thc-gap-sm               /* 8px */
--thc-gap-md               /* 12px - most common */
--thc-gap-lg               /* 16px */

/* Stack (vertical spacing) */
--thc-stack-md             /* 20px - default */
--thc-stack-lg             /* 28px */
```

### Border Radius
```css
--thc-radius-md      /* 6px - buttons, inputs */
--thc-radius-lg      /* 8px - compact cards */
--thc-radius-xl      /* 10px - standard cards */
--thc-radius-2xl     /* 12px - modals */
--thc-radius-full    /* 9999px - pills */
```

### Shadows
```css
--thc-shadow-sm      /* Small - cards */
--thc-shadow-md      /* Medium - hover states */
--thc-shadow-lg      /* Large - dropdowns */
--thc-shadow-xl      /* Extra large - modals */
--thc-shadow-focus   /* Focus ring for inputs */
```

### Layout
```css
--thc-container-standard   /* 1280px - default pages */
--thc-container-narrow     /* 960px - forms */

--thc-breakpoint-sm        /* 576px */
--thc-breakpoint-md        /* 768px */
--thc-breakpoint-lg        /* 992px */
```

## Common Patterns

### Button Styling
```css
.my-button {
  padding: var(--thc-padding-button);
  font-size: var(--thc-text-sm);
  font-weight: var(--thc-font-semibold);
  border-radius: var(--thc-radius-md);
  background: var(--thc-primary-600);
  color: var(--thc-text-inverse);
  transition: var(--thc-transition-colors);
}

.my-button:hover {
  background: var(--thc-primary-700);
}
```

### Card Styling
```css
.my-card {
  background: var(--thc-bg-surface);
  border: 1px solid var(--thc-border-default);
  border-radius: var(--thc-radius-xl);
  padding: var(--thc-padding-card);
  box-shadow: var(--thc-shadow-sm);
}
```

### Form Input Styling
```css
.my-input {
  padding: var(--thc-padding-input);
  font-size: var(--thc-text-sm);
  border: 1px solid var(--thc-border-strong);
  border-radius: var(--thc-radius-md);
  background: var(--thc-bg-surface);
}

.my-input:focus {
  border-color: var(--thc-primary-600);
  box-shadow: var(--thc-shadow-focus);
  outline: none;
}
```

### Typography Hierarchy
```html
<h1 style="font-size: var(--thc-h1-size); font-weight: var(--thc-h1-weight); line-height: var(--thc-h1-line);">
  Page Title
</h1>

<h2 style="font-size: var(--thc-h2-size); font-weight: var(--thc-h2-weight);">
  Section Title
</h2>

<p style="font-size: var(--thc-body-size); line-height: var(--thc-body-line);">
  Body paragraph text goes here.
</p>

<span style="font-size: var(--thc-label-size); font-weight: var(--thc-label-weight);
              letter-spacing: var(--thc-label-tracking); text-transform: uppercase;">
  Label Text
</span>
```

## Migration from Legacy Variables

Legacy variables still work but are deprecated:

| Old (DEPRECATED) | New (USE THIS) |
|-----------------|----------------|
| `--thc-primary` | `--thc-primary-600` |
| `--thc-primary-dark` | `--thc-primary-700` |
| `--thc-primary-light` | `--thc-primary-100` |
| `--thc-bg` | `--thc-bg-page` |
| `--thc-surface` | `--thc-bg-surface` |
| `--thc-border` | `--thc-border-default` |
| `--thc-text` | `--thc-text-primary` |
| `--thc-text-muted` | `--thc-text-secondary` |

## Testing

To verify all tokens are loaded correctly, open:
```
application/static/css/design-system-test.html
```

This test page demonstrates all available tokens with visual examples.

## Documentation

For complete token specifications and rationale, see:
- `DESIGN_SYSTEM.md` - Full design system proposal
- `docs/ui-audit.md` - Original UI audit

## Support

When using tokens:
- ✅ **DO** use semantic tokens (`--thc-primary-600`, `--thc-text-secondary`)
- ✅ **DO** use utility classes for quick prototyping
- ✅ **DO** follow the spacing scale (4px grid)
- ❌ **DON'T** use arbitrary values (use tokens instead)
- ❌ **DON'T** use deprecated variables in new code
- ❌ **DON'T** mix `px` and `rem` - tokens handle units

---

**Design System Version**: 2.0
**Last Updated**: 2026-05-24
