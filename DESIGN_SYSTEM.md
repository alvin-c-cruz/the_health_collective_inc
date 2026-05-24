# The Health Collective Design System
**Version 2.0 — Unified System Proposal**
*Based on UI Audit dated 2026-05-24*

---

## Philosophy

This design system consolidates the existing THC patterns into a coherent, scalable foundation built on:
- **Consistency**: One source of truth for all design decisions
- **Clarity**: Semantic naming that communicates purpose
- **Flexibility**: Tokens that adapt across contexts
- **Modern Standards**: 4px base grid, rem units, CSS variables

**Decision Rationale**: Where conflicts existed, we chose the most frequently occurring pattern, the most modern approach (rem over px), or the Bootstrap 5-aligned value.

---

## 1. Color Tokens

### 1.1 Brand Colors

```css
/* Primary Brand (Teal) */
--thc-primary-900:  #0d3d47;  /* Darkest - very rare use */
--thc-primary-800:  #105058;  /* Extra dark */
--thc-primary-700:  #135260;  /* Dark - hover states */
--thc-primary-600:  #1a6473;  /* Base brand color - DEFAULT */
--thc-primary-500:  #2d8090;  /* Lighter variant */
--thc-primary-400:  #4d9cad;  /* Light accent */
--thc-primary-300:  #8dbcc5;  /* Very light */
--thc-primary-200:  #c6dde1;  /* Subtle backgrounds */
--thc-primary-100:  #e6f3f5;  /* Lightest - backgrounds */
--thc-primary-50:   #f4f9fa;  /* Near white */
```

**Rationale**: Kept existing `#1a6473` as base (600). Generated a proper scale for flexibility. The `-100` value matches existing `--thc-primary-light` (#e6f3f5).

### 1.2 Semantic Colors

```css
/* Success (Green) - Approvals, positive actions */
--thc-success-900:  #0a3318;
--thc-success-800:  #0f4921;
--thc-success-700:  #14532d;  /* Hover */
--thc-success-600:  #166534;  /* Base - DEFAULT */
--thc-success-500:  #22863a;
--thc-success-400:  #4caf50;  /* Alerts only (legacy) */
--thc-success-300:  #86d895;
--thc-success-200:  #bbf7d0;
--thc-success-100:  #d4edda;  /* Light backgrounds */
--thc-success-50:   #f0fdf4;

/* Info (Blue) - Informational actions, submit */
--thc-info-900:  #0a2f52;
--thc-info-800:  #0f4880;  /* Hover */
--thc-info-700:  #135ba3;
--thc-info-600:  #185fa5;  /* Base - DEFAULT */
--thc-info-500:  #2b7cc4;
--thc-info-400:  #4d9cdb;
--thc-info-300:  #82bef0;
--thc-info-200:  #bddff8;
--thc-info-100:  #e0f2fe;
--thc-info-50:   #f0f9ff;

/* Warning (Amber) - Caution, edit, unlock */
--thc-warning-900:  #6b3608;
--thc-warning-800:  #854309;
--thc-warning-700:  #92400e;  /* Hover */
--thc-warning-600:  #b45309;  /* Base - DEFAULT */
--thc-warning-500:  #d97706;
--thc-warning-400:  #f59e0b;
--thc-warning-300:  #fbbf24;
--thc-warning-200:  #fef3c7;
--thc-warning-100:  #fef9c3;
--thc-warning-50:   #fffbf0;

/* Danger (Red) - Destructive, delete, cancel */
--thc-danger-900:  #7a1e16;
--thc-danger-800:  #991b1b;
--thc-danger-700:  #a93226;  /* Hover */
--thc-danger-600:  #c0392b;  /* Base - DEFAULT */
--thc-danger-500:  #dc4538;
--thc-danger-400:  #ef5350;
--thc-danger-300:  #f88078;
--thc-danger-200:  #fca5a0;
--thc-danger-100:  #fee2e2;
--thc-danger-50:   #fef2f2;
```

**Rationale**:
- **Success**: Chose `#166534` (existing button color) over Material's `#4CAF50`. More professional, better contrast.
- **Info**: Kept `#185FA5` (existing info button). Removed conflicting blues (#667eea, #0066cc).
- **Warning**: Kept `#b45309` (existing).
- **Danger**: Kept `#c0392b` over Material's `#f44336` - appears most frequently.

### 1.3 Neutral Colors

```css
/* Grays - Text, borders, backgrounds */
--thc-gray-900:  #111827;  /* Darkest text */
--thc-gray-800:  #1a2a2a;  /* Primary text - DEFAULT */
--thc-gray-700:  #374151;
--thc-gray-600:  #4b5563;
--thc-gray-500:  #6b7280;  /* Muted text - DEFAULT */
--thc-gray-400:  #9ca3af;
--thc-gray-300:  #d1d5db;  /* Form borders */
--thc-gray-200:  #e2e8f0;  /* Primary border - DEFAULT */
--thc-gray-150:  #f0f2f5;  /* Light borders (table rows) */
--thc-gray-100:  #f1f5f9;
--thc-gray-50:   #f8f9fa;  /* Page background - DEFAULT */
--thc-white:     #ffffff;  /* Surface/cards */
```

**Rationale**: Kept existing values. Added `-800` (existing text color) and `-150` for subtle borders.

### 1.4 Extended Palette (Status & Icons)

```css
/* Extended colors for icons, badges, status */

/* Teal (matches primary) */
--thc-teal-600:  #1a6473;
--thc-teal-100:  #e6f3f5;

/* Green (nature) */
--thc-green-700:  #0f6e56;
--thc-green-100:  #e6f3f0;

/* Purple (special) */
--thc-purple-700:  #3c3489;
--thc-purple-100:  #eeedfe;

/* Coral (warm) */
--thc-coral-700:  #993c1d;
--thc-coral-100:  #faece7;

/* Amber (attention) */
--thc-amber-700:  #854f0b;
--thc-amber-100:  #faeeda;

/* Rose (feminine) */
--thc-rose-700:  #9d174d;
--thc-rose-100:  #fce7f3;

/* Red (urgent) */
--thc-red-700:  #991b1b;
--thc-red-100:  #fee2e2;

/* Slate (neutral) */
--thc-slate-700:  #475569;
--thc-slate-100:  #f1f5f9;
```

**Rationale**: Preserved existing icon color system. These are used for visual variety in transaction types, badges, etc.

### 1.5 Semantic Aliases (Recommended Usage)

```css
/* Background */
--thc-bg-page:      var(--thc-gray-50);
--thc-bg-surface:   var(--thc-white);
--thc-bg-subtle:    var(--thc-gray-100);
--thc-bg-muted:     var(--thc-gray-150);

/* Text */
--thc-text-primary:   var(--thc-gray-800);
--thc-text-secondary: var(--thc-gray-500);
--thc-text-disabled:  var(--thc-gray-400);
--thc-text-inverse:   var(--thc-white);

/* Borders */
--thc-border-default:  var(--thc-gray-200);
--thc-border-light:    var(--thc-gray-150);
--thc-border-strong:   var(--thc-gray-300);
--thc-border-primary:  var(--thc-primary-600);

/* State colors */
--thc-state-draft:      var(--thc-gray-100);
--thc-state-draft-text: var(--thc-gray-500);
--thc-state-submitted:  var(--thc-success-100);
--thc-state-submitted-text: #155724;  /* Legacy, close to success-700 */
--thc-state-approved:   var(--thc-success-100);
--thc-state-approved-text: #155724;
--thc-state-cancelled:  var(--thc-coral-100);
--thc-state-cancelled-text: var(--thc-coral-700);
```

---

## 2. Typography Tokens

### 2.1 Font Families

```css
--thc-font-heading:  'Playfair Display', Georgia, serif;
--thc-font-body:     'Inter', 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
--thc-font-mono:     'DM Mono', 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;
```

**Rationale**:
- Kept existing Playfair Display for headings (elegant serif)
- Kept Inter as primary body font with fallback to DM Sans
- Standardized monospace to DM Mono (for numbers, code) with system fallbacks
- Added modern system font stack for better performance

### 2.2 Font Size Scale (4px base)

```css
/* Base: 1rem = 16px */
--thc-text-xs:    0.75rem;   /* 12px - badges, tiny labels */
--thc-text-sm:    0.875rem;  /* 14px - body text, inputs, buttons */
--thc-text-base:  1rem;      /* 16px - default */
--thc-text-md:    1.125rem;  /* 18px - emphasized body */
--thc-text-lg:    1.25rem;   /* 20px - large metrics */
--thc-text-xl:    1.5rem;    /* 24px - section titles */
--thc-text-2xl:   1.875rem;  /* 30px - page titles */
--thc-text-3xl:   2.25rem;   /* 36px - hero text */
--thc-text-4xl:   3rem;      /* 48px - display */
```

**Rationale**:
- Simplified from dozens of arbitrary values (0.65rem, 0.68rem, 0.72rem, etc.)
- Chose common Bootstrap/Tailwind scale
- `0.875rem` (14px) is most common for body text (appears in forms, buttons, tables)
- Removed one-offs; developers must choose from this scale

### 2.3 Font Weight Scale

```css
--thc-font-normal:     400;
--thc-font-medium:     500;
--thc-font-semibold:   600;
--thc-font-bold:       700;
--thc-font-extrabold:  800;  /* Rare - display only */
```

**Rationale**: Standard scale. Weight 600 is most common for emphasis (buttons, headings, labels).

### 2.4 Line Height Scale

```css
--thc-leading-none:    1.0;
--thc-leading-tight:   1.25;
--thc-leading-snug:    1.375;
--thc-leading-normal:  1.5;
--thc-leading-relaxed: 1.625;
--thc-leading-loose:   1.75;
```

**Rationale**:
- Most text should use `normal` (1.5) for readability
- Headings use `tight` (1.25)
- Metrics/values use `none` (1.0) or `tight`

### 2.5 Letter Spacing Scale

```css
--thc-tracking-tighter:  -0.05em;
--thc-tracking-tight:    -0.025em;
--thc-tracking-normal:   0;
--thc-tracking-wide:     0.025em;  /* 0.01-0.03em range */
--thc-tracking-wider:    0.05em;   /* 0.04-0.06em range */
--thc-tracking-widest:   0.1em;    /* Uppercase labels */
```

**Rationale**: Consolidated from many arbitrary values. Most body text uses `normal` (0). Uppercase labels use `widest` (0.1em).

### 2.6 Semantic Typography Tokens

```css
/* Display (hero sections) */
--thc-display-size:       var(--thc-text-3xl);
--thc-display-weight:     var(--thc-font-extrabold);
--thc-display-line:       var(--thc-leading-tight);
--thc-display-tracking:   var(--thc-tracking-tight);

/* Headings */
--thc-h1-size:       var(--thc-text-2xl);
--thc-h1-weight:     var(--thc-font-semibold);
--thc-h1-line:       var(--thc-leading-tight);

--thc-h2-size:       var(--thc-text-xl);
--thc-h2-weight:     var(--thc-font-semibold);
--thc-h2-line:       var(--thc-leading-tight);

--thc-h3-size:       var(--thc-text-md);
--thc-h3-weight:     var(--thc-font-semibold);
--thc-h3-line:       var(--thc-leading-snug);

--thc-h4-size:       var(--thc-text-base);
--thc-h4-weight:     var(--thc-font-semibold);
--thc-h4-line:       var(--thc-leading-snug);

/* Body */
--thc-body-size:     var(--thc-text-sm);      /* 14px - most common */
--thc-body-weight:   var(--thc-font-normal);
--thc-body-line:     var(--thc-leading-normal);

--thc-body-lg-size:  var(--thc-text-base);    /* 16px - emphasis */
--thc-body-sm-size:  var(--thc-text-xs);      /* 12px - captions */

/* Labels */
--thc-label-size:     var(--thc-text-xs);
--thc-label-weight:   var(--thc-font-semibold);
--thc-label-line:     var(--thc-leading-normal);
--thc-label-tracking: var(--thc-tracking-widest);
--thc-label-transform: uppercase;

/* Caption */
--thc-caption-size:   var(--thc-text-xs);
--thc-caption-weight: var(--thc-font-medium);
--thc-caption-line:   var(--thc-leading-normal);
```

**Rationale**:
- Page headings (`<h4>` in current system) map to h1 tokens
- Body text defaults to 14px (0.875rem) - most common in forms, buttons, tables
- Labels are 12px uppercase with wide tracking (card titles, section headers)
- Removed arbitrary sizes like 1.3rem for h4

---

## 3. Spacing Scale (4px Grid)

### 3.1 Core Spacing Tokens

```css
/* Based on 4px grid system */
--thc-space-0:    0;
--thc-space-1:    0.25rem;   /* 4px */
--thc-space-2:    0.5rem;    /* 8px */
--thc-space-3:    0.75rem;   /* 12px */
--thc-space-4:    1rem;      /* 16px - DEFAULT */
--thc-space-5:    1.25rem;   /* 20px */
--thc-space-6:    1.5rem;    /* 24px */
--thc-space-7:    1.75rem;   /* 28px */
--thc-space-8:    2rem;      /* 32px */
--thc-space-10:   2.5rem;    /* 40px */
--thc-space-12:   3rem;      /* 48px */
--thc-space-16:   4rem;      /* 64px */
--thc-space-20:   5rem;      /* 80px */
--thc-space-24:   6rem;      /* 96px */
```

**Rationale**:
- Replaced arbitrary values (0.3rem, 0.35rem, 0.42rem, 0.55rem, etc.) with 4px grid
- Most common: `space-3` (12px), `space-4` (16px), `space-6` (24px)
- Aligns with Bootstrap and Tailwind conventions

### 3.2 Semantic Spacing Aliases

```css
/* Component padding */
--thc-padding-input:      var(--thc-space-2) var(--thc-space-3);  /* 8px 12px */
--thc-padding-button:     var(--thc-space-2) var(--thc-space-5);  /* 8px 20px */
--thc-padding-button-sm:  var(--thc-space-2) var(--thc-space-3);  /* 8px 12px */
--thc-padding-button-lg:  var(--thc-space-3) var(--thc-space-7);  /* 12px 28px */
--thc-padding-card:       var(--thc-space-6);                      /* 24px */
--thc-padding-card-sm:    var(--thc-space-4);                      /* 16px */
--thc-padding-card-lg:    var(--thc-space-8);                      /* 32px */

/* Component gaps (flexbox/grid) */
--thc-gap-xs:   var(--thc-space-1);  /* 4px */
--thc-gap-sm:   var(--thc-space-2);  /* 8px */
--thc-gap-md:   var(--thc-space-3);  /* 12px - most common */
--thc-gap-lg:   var(--thc-space-4);  /* 16px */
--thc-gap-xl:   var(--thc-space-6);  /* 24px */

/* Stack spacing (vertical rhythm) */
--thc-stack-xs:  var(--thc-space-2);   /* 8px */
--thc-stack-sm:  var(--thc-space-3);   /* 12px */
--thc-stack-md:  var(--thc-space-5);   /* 20px - DEFAULT */
--thc-stack-lg:  var(--thc-space-7);   /* 28px */
--thc-stack-xl:  var(--thc-space-12);  /* 48px */
```

**Rationale**:
- Button padding: Chose `8px 20px` (close to existing `0.5rem 1.25rem`)
- Card padding: `24px` (1.5rem) - most common
- Grid gap: `12px` most common (existing `10px` rounds to `12px` on 4px grid)

---

## 4. Border Radius Scale

```css
--thc-radius-none:  0;
--thc-radius-sm:    0.25rem;  /* 4px - very subtle */
--thc-radius-md:    0.375rem; /* 6px - buttons, inputs, small elements */
--thc-radius-lg:    0.5rem;   /* 8px - compact cards, metrics */
--thc-radius-xl:    0.625rem; /* 10px - standard cards */
--thc-radius-2xl:   0.75rem;  /* 12px - large cards, modals */
--thc-radius-3xl:   1rem;     /* 16px - special elements */
--thc-radius-full:  9999px;   /* Pills, circular badges */
```

**Rationale**:
- `6px` (md) for buttons/inputs - most common
- `10px` (xl) for cards - most common
- `12px` (2xl) for modals/hero cards
- Removed arbitrary `8px` as standalone; use `lg` (8px) for compact cards

---

## 5. Shadow Scale

```css
/* Elevation system */
--thc-shadow-none:  none;
--thc-shadow-xs:    0 1px 2px 0 rgba(0, 0, 0, 0.05);
--thc-shadow-sm:    0 1px 3px 0 rgba(0, 0, 0, 0.06), 0 1px 2px 0 rgba(0, 0, 0, 0.04);
--thc-shadow-md:    0 2px 8px 0 rgba(0, 0, 0, 0.07);
--thc-shadow-lg:    0 4px 12px 0 rgba(0, 0, 0, 0.10);
--thc-shadow-xl:    0 8px 24px 0 rgba(0, 0, 0, 0.12);
--thc-shadow-2xl:   0 16px 48px 0 rgba(0, 0, 0, 0.16);

/* Special shadows */
--thc-shadow-focus:  0 0 0 3px rgba(26, 100, 115, 0.12);  /* Primary color ring */
--thc-shadow-focus-danger: 0 0 0 3px rgba(192, 57, 43, 0.12);
```

**Rationale**:
- Cards use `sm` (most common existing shadow)
- Card hover uses `md`
- Dropdowns use `lg`
- Modals use `xl`
- Focus ring kept existing primary-tinted shadow

---

## 6. Component Patterns

### 6.1 Buttons

**Base Button** (`.btn`)
```css
font-family:     var(--thc-font-body);
font-size:       var(--thc-text-sm);           /* 14px */
font-weight:     var(--thc-font-semibold);     /* 600 */
line-height:     var(--thc-leading-tight);
letter-spacing:  var(--thc-tracking-wide);
padding:         var(--thc-padding-button);    /* 8px 20px */
border-radius:   var(--thc-radius-md);         /* 6px */
border:          1px solid transparent;
cursor:          pointer;
transition:      all 150ms ease;
```

**Size Variants**
```css
.btn-sm:  padding: var(--thc-padding-button-sm);  /* 8px 12px */
          font-size: var(--thc-text-xs);          /* 12px */

.btn-lg:  padding: var(--thc-padding-button-lg);  /* 12px 28px */
          font-size: var(--thc-text-base);        /* 16px */
```

**Color Variants**

```css
/* Primary - Main brand actions */
.btn-primary:
  background:  var(--thc-primary-600);
  color:       var(--thc-text-inverse);
  border-color: var(--thc-primary-600);
  hover: background var(--thc-primary-700)

/* Secondary - Less prominent actions */
.btn-secondary:
  background:  var(--thc-bg-surface);
  color:       var(--thc-gray-700);
  border-color: var(--thc-gray-300);
  hover: background var(--thc-gray-50)

/* Success - Approve, confirm */
.btn-success:
  background:  var(--thc-success-600);
  color:       var(--thc-text-inverse);
  border-color: var(--thc-success-600);
  hover: background var(--thc-success-700)

/* Info - Submit, upload */
.btn-info:
  background:  var(--thc-info-600);
  color:       var(--thc-text-inverse);
  border-color: var(--thc-info-600);
  hover: background var(--thc-info-800)

/* Warning - Edit, caution */
.btn-warning:
  background:  var(--thc-warning-600);
  color:       var(--thc-text-inverse);
  border-color: var(--thc-warning-600);
  hover: background var(--thc-warning-700)

/* Danger - Delete, cancel */
.btn-danger:
  background:  var(--thc-danger-600);
  color:       var(--thc-text-inverse);
  border-color: var(--thc-danger-600);
  hover: background var(--thc-danger-700)

/* Ghost - Tertiary actions */
.btn-ghost:
  background:  transparent;
  color:       var(--thc-primary-600);
  border-color: transparent;
  hover: background var(--thc-primary-100)
```

**Outline Variants**
```css
.btn-outline-{variant}:
  background:  transparent;
  color:       var(--thc-{variant}-600);
  border-color: var(--thc-{variant}-600);
  hover: background var(--thc-{variant}-600)
  hover: color var(--thc-text-inverse)
```

**Icon Buttons**
```css
.btn-icon:
  padding: var(--thc-space-2);  /* 8px square button */
  width:   2rem;                 /* 32px */
  height:  2rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
```

**Rationale**:
- Unified `.btn` system (deprecate `.thc-btn` custom system)
- Removed `translateY(-1px)` hover lift (inconsistent, not accessible)
- Padding: `8px 20px` (close to existing `0.5rem 1.25rem = 8px 20px`)
- Font size: `14px` (most common)

### 6.2 Form Inputs

**Base Input** (`.form-control`, `.form-select`)
```css
font-family:    var(--thc-font-body);
font-size:      var(--thc-text-sm);        /* 14px */
font-weight:    var(--thc-font-normal);
line-height:    var(--thc-leading-normal);
padding:        var(--thc-padding-input);  /* 8px 12px */
border:         1px solid var(--thc-border-strong);  /* gray-300 */
border-radius:  var(--thc-radius-md);      /* 6px */
background:     var(--thc-bg-surface);
color:          var(--thc-text-primary);
transition:     border-color 150ms, box-shadow 150ms;

focus:
  border-color: var(--thc-primary-600);
  box-shadow:   var(--thc-shadow-focus);
  outline:      none;

invalid:
  border-color: var(--thc-danger-600);

disabled:
  background:   var(--thc-bg-muted);
  color:        var(--thc-text-disabled);
  cursor:       not-allowed;
```

**Label** (`.form-label`)
```css
font-size:      var(--thc-text-xs);        /* 12px */
font-weight:    var(--thc-font-medium);    /* 500 */
color:          var(--thc-text-secondary); /* gray-500 */
margin-bottom:  var(--thc-space-1);        /* 4px */
```

**Textarea**
```css
resize:      vertical;
min-height:  5rem;  /* 80px, ~3 lines */
```

**Number Input**
```css
font-family: var(--thc-font-mono);
```

**Select/Dropdown**
```css
/* Uses Tom-Select plugin - inherits form-control styles */
```

**Error Message** (`.invalid-feedback`)
```css
display:    block;
font-size:  var(--thc-text-xs);    /* 12px */
color:      var(--thc-danger-600);
margin-top: var(--thc-space-1);    /* 4px */
```

### 6.3 Cards

**Base Card** (`.card`)
```css
background:     var(--thc-bg-surface);
border:         1px solid var(--thc-border-default);  /* gray-200 */
border-radius:  var(--thc-radius-xl);                 /* 10px */
box-shadow:     var(--thc-shadow-sm);
padding:        var(--thc-padding-card);              /* 24px */
margin-bottom:  var(--thc-stack-md);                  /* 20px */
```

**Size Variants**
```css
.card-compact:
  padding:       var(--thc-padding-card-sm);  /* 16px */
  border-radius: var(--thc-radius-lg);        /* 8px */

.card-spacious:
  padding:       var(--thc-padding-card-lg);  /* 32px */
  border-radius: var(--thc-radius-2xl);       /* 12px */
```

**Interactive Card** (`.card-interactive`)
```css
cursor:     pointer;
transition: border-color 150ms, box-shadow 150ms, background 150ms;

hover:
  border-color: var(--thc-gray-400);
  box-shadow:   var(--thc-shadow-md);
  background:   var(--thc-primary-50);
```

**Featured Card** (`.card-featured`)
```css
border-width: 2px;
border-color: var(--thc-primary-600);
```

**Card Header** (`.card-header`)
```css
font-size:       var(--thc-label-size);        /* 12px */
font-weight:     var(--thc-label-weight);      /* 600 */
letter-spacing:  var(--thc-label-tracking);    /* 0.1em */
text-transform:  var(--thc-label-transform);   /* uppercase */
color:           var(--thc-text-secondary);
margin-bottom:   var(--thc-stack-md);          /* 20px */
padding-bottom:  var(--thc-space-3);           /* 12px */
border-bottom:   1px solid var(--thc-border-default);
```

**Rationale**:
- Default padding: `24px` (1.5rem) - most common
- Compact: `16px` for metrics, tight layouts
- Spacious: `32px` for hero/feature cards
- Border radius: `10px` standard, `8px` compact, `12px` spacious

### 6.4 Badges & Pills

**Badge** (`.badge`)
```css
display:        inline-flex;
align-items:    center;
gap:            var(--thc-gap-xs);           /* 4px */
padding:        var(--thc-space-1) var(--thc-space-2);  /* 4px 8px */
font-size:      var(--thc-text-xs);          /* 12px */
font-weight:    var(--thc-font-semibold);
letter-spacing: var(--thc-tracking-wide);
border-radius:  var(--thc-radius-md);        /* 6px */
```

**Pill** (`.badge-pill`)
```css
border-radius: var(--thc-radius-full);  /* 9999px */
padding:       var(--thc-space-1) var(--thc-space-3);  /* 4px 12px */
```

**Color Variants**
```css
.badge-primary:   bg primary-600, text white
.badge-success:   bg success-100, text success-700
.badge-info:      bg info-100, text info-700
.badge-warning:   bg warning-100, text warning-700
.badge-danger:    bg danger-100, text danger-700
.badge-secondary: bg gray-100, text gray-700
```

**State Badges**
```css
.badge-draft:      bg gray-100, text gray-500
.badge-submitted:  bg success-100, text success-700
.badge-approved:   bg success-100, text success-700
.badge-cancelled:  bg coral-100, text coral-700
```

### 6.5 Tables

**Base Table** (`.table`)
```css
width:           100%;
border-collapse: collapse;
font-size:       var(--thc-text-sm);  /* 14px */

th:
  font-size:       var(--thc-text-xs);       /* 12px */
  font-weight:     var(--thc-font-semibold);
  text-transform:  uppercase;
  letter-spacing:  var(--thc-tracking-wider);
  color:           var(--thc-text-secondary);
  padding:         var(--thc-space-2) var(--thc-space-3);  /* 8px 12px */
  border-bottom:   2px solid var(--thc-border-default);
  text-align:      left;
  background:      var(--thc-bg-subtle);

td:
  padding:       var(--thc-space-2) var(--thc-space-3);  /* 8px 12px */
  border-bottom: 1px solid var(--thc-border-light);
  vertical-align: middle;
  color:         var(--thc-text-primary);

tr:hover:
  background: var(--thc-primary-50);

td.numeric:
  text-align:  right;
  font-family: var(--thc-font-mono);
```

### 6.6 Modals

**Modal Overlay**
```css
background: rgba(0, 0, 0, 0.5);
backdrop-filter: blur(4px);
```

**Modal Container** (`.modal-dialog`)
```css
max-width:      640px;   /* md size - default */
border-radius:  var(--thc-radius-2xl);  /* 12px */
box-shadow:     var(--thc-shadow-2xl);
background:     var(--thc-bg-surface);
```

**Modal Sizes**
```css
.modal-sm:  max-width: 400px;
.modal-md:  max-width: 640px;  /* default */
.modal-lg:  max-width: 800px;
.modal-xl:  max-width: 1200px;
```

**Modal Header**
```css
padding:        var(--thc-space-6);  /* 24px */
border-bottom:  1px solid var(--thc-border-default);
background:     var(--thc-primary-600);
color:          var(--thc-text-inverse);

h5:
  font-size:   var(--thc-text-lg);  /* 20px */
  font-weight: var(--thc-font-semibold);
  margin:      0;
```

**Modal Body**
```css
padding: var(--thc-space-6);  /* 24px */
```

**Modal Footer**
```css
padding:        var(--thc-space-6);
border-top:     1px solid var(--thc-border-default);
display:        flex;
justify-content: flex-end;
gap:            var(--thc-gap-md);  /* 12px */
```

---

## 7. Layout System

### 7.1 Container Widths

```css
--thc-container-sm:   640px;
--thc-container-md:   768px;
--thc-container-lg:   1024px;
--thc-container-xl:   1280px;  /* Default for standard pages */
--thc-container-2xl:  1536px;

/* Semantic aliases */
--thc-container-narrow:   960px;   /* Forms, transactions */
--thc-container-standard: 1280px;  /* Default pages */
--thc-container-wide:     1536px;  /* Dashboards, reports */
```

**Usage**
```css
.container:
  max-width: var(--thc-container-standard);  /* 1280px */
  margin:    var(--thc-space-12) auto;        /* 48px auto */
  padding:   0 var(--thc-space-6) var(--thc-space-16);  /* 0 24px 64px */

.container-narrow:
  max-width: var(--thc-container-narrow);  /* 960px - forms */
```

**Rationale**:
- Standard pages: `1280px` (most common existing)
- Forms/transactions: `960px` (existing pattern for focused content)
- Keep both for flexibility

### 7.2 Breakpoints (Bootstrap 5 Standard)

```css
/* Min-width breakpoints */
--thc-breakpoint-sm:   576px;
--thc-breakpoint-md:   768px;
--thc-breakpoint-lg:   992px;
--thc-breakpoint-xl:   1200px;
--thc-breakpoint-2xl:  1400px;
```

**Rationale**:
- Removed custom `600px` breakpoint - use `576px` (sm)
- Align with Bootstrap 5 for consistency
- Use `@media (max-width: 767.98px)` for max-width queries

### 7.3 Grid System

**Default Grid Gap**
```css
--thc-grid-gap-default: var(--thc-gap-md);  /* 12px */
```

**Common Grid Patterns**
```css
/* 2-column grid */
.grid-2:
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--thc-grid-gap-default);

  @media (max-width: 767.98px):
    grid-template-columns: 1fr;

/* 3-column grid (metrics) */
.grid-3:
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--thc-grid-gap-default);

  @media (max-width: 767.98px):
    grid-template-columns: 1fr;

/* Auto-fill grid (responsive) */
.grid-auto:
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--thc-grid-gap-default);
```

**Rationale**:
- Standardized gap to `12px` (close to existing `10px`, aligns with 4px grid)
- Single breakpoint for mobile collapse (md)

### 7.4 Flexbox Utilities

```css
/* Common flex patterns */
.flex:        display: flex;
.flex-col:    flex-direction: column;
.flex-wrap:   flex-wrap: wrap;
.items-center:   align-items: center;
.items-start:    align-items: flex-start;
.justify-between: justify-content: space-between;
.justify-center:  justify-content: center;
.gap-sm:     gap: var(--thc-gap-sm);   /* 8px */
.gap-md:     gap: var(--thc-gap-md);   /* 12px */
.gap-lg:     gap: var(--thc-gap-lg);   /* 16px */
```

---

## 8. Icon System

### 8.1 Icon Container Variants

**Small Icon** (32px)
```css
.icon-sm:
  width:         2rem;  /* 32px */
  height:        2rem;
  border-radius: var(--thc-radius-md);  /* 6px */
  display:       inline-flex;
  align-items:   center;
  justify-content: center;
  font-size:     0.875rem;  /* 14px icon */
```

**Medium Icon** (40px)
```css
.icon-md:
  width:         2.5rem;  /* 40px */
  height:        2.5rem;
  border-radius: var(--thc-radius-lg);  /* 8px */
  font-size:     1rem;     /* 16px icon */
```

**Large Icon** (48px)
```css
.icon-lg:
  width:         3rem;  /* 48px */
  height:        3rem;
  border-radius: var(--thc-radius-xl);  /* 10px */
  font-size:     1.25rem;  /* 20px icon */
```

### 8.2 Icon Color Variants

```css
.icon-primary:  bg primary-100, color primary-600
.icon-success:  bg success-100, color success-700
.icon-info:     bg info-100, color info-700
.icon-warning:  bg warning-100, color warning-700
.icon-danger:   bg danger-100, color danger-700

/* Extended colors */
.icon-green:    bg green-100, color green-700
.icon-purple:   bg purple-100, color purple-700
.icon-coral:    bg coral-100, color coral-700
.icon-amber:    bg amber-100, color amber-700
.icon-rose:     bg rose-100, color rose-700
.icon-slate:    bg slate-100, color slate-700
```

---

## 9. Z-Index Scale

```css
--thc-z-base:     0;
--thc-z-dropdown: 1000;
--thc-z-sticky:   1020;
--thc-z-fixed:    1030;
--thc-z-modal-backdrop: 1040;
--thc-z-modal:    1050;
--thc-z-popover:  1060;
--thc-z-tooltip:  1070;
--thc-z-toast:    1080;
```

**Rationale**: Bootstrap 5-compatible scale for layering components.

---

## 10. Animation & Transitions

### 10.1 Duration Tokens

```css
--thc-duration-fast:    100ms;
--thc-duration-normal:  150ms;
--thc-duration-slow:    300ms;
--thc-duration-slower:  500ms;
```

### 10.2 Easing Functions

```css
--thc-ease-in:      cubic-bezier(0.4, 0, 1, 1);
--thc-ease-out:     cubic-bezier(0, 0, 0.2, 1);
--thc-ease-in-out:  cubic-bezier(0.4, 0, 0.2, 1);
--thc-ease-default: ease;
```

### 10.3 Common Transitions

```css
--thc-transition-base:   all var(--thc-duration-normal) var(--thc-ease-default);
--thc-transition-colors: background-color var(--thc-duration-normal) var(--thc-ease-default),
                         border-color var(--thc-duration-normal) var(--thc-ease-default),
                         color var(--thc-duration-normal) var(--thc-ease-default);
--thc-transition-shadow: box-shadow var(--thc-duration-normal) var(--thc-ease-default);
```

**Usage**: Most interactive elements use `150ms` transitions.

---

## 11. Implementation Guidelines

### 11.1 CSS Variable Usage

**Define in `:root`**
```css
:root {
  /* Color tokens */
  --thc-primary-600: #1a6473;
  /* ... all tokens ... */
}
```

**Use in components**
```css
.btn-primary {
  background: var(--thc-primary-600);
  color: var(--thc-text-inverse);
}
```

### 11.2 Naming Conventions

**Pattern**: `--{namespace}-{category}-{property}-{variant}`

Examples:
- `--thc-primary-600` (color, variant 600)
- `--thc-text-sm` (typography size)
- `--thc-space-4` (spacing scale)
- `--thc-shadow-md` (shadow size)
- `--thc-radius-lg` (border radius)

### 11.3 Deprecation Strategy

**Phase 1**: Add new tokens alongside old
**Phase 2**: Map old variables to new (aliases)
**Phase 3**: Update templates to use new tokens
**Phase 4**: Remove old variables

Example migration:
```css
/* Phase 1: New system */
--thc-primary-600: #1a6473;

/* Phase 2: Alias old to new */
--thc-primary: var(--thc-primary-600);  /* DEPRECATED */

/* Phase 3: Update usage in templates */
/* OLD: background: var(--thc-primary); */
/* NEW: background: var(--thc-primary-600); */

/* Phase 4: Remove deprecated aliases */
```

---

## 12. Migration Mapping

### 12.1 Color Migrations

| Current Usage | New Token | Notes |
|---------------|-----------|-------|
| `--thc-primary` | `--thc-primary-600` | Base brand |
| `--thc-primary-dark` | `--thc-primary-700` | Hover states |
| `--thc-primary-light` | `--thc-primary-100` | Backgrounds |
| `--thc-bg` | `--thc-gray-50` | Page background |
| `--thc-surface` | `--thc-white` | Card backgrounds |
| `--thc-border` | `--thc-gray-200` | Default borders |
| `--thc-text` | `--thc-gray-800` | Primary text |
| `--thc-text-muted` | `--thc-gray-500` | Secondary text |
| `#4CAF50` (alert success) | `--thc-success-600` | Standardize green |
| `#f44336` (alert error) | `--thc-danger-600` | Standardize red |
| `#185FA5` (info button) | `--thc-info-600` | Keep existing |
| `#166534` (success button) | `--thc-success-600` | Keep existing |
| `#b45309` (warning button) | `--thc-warning-600` | Keep existing |
| `#c0392b` (danger button) | `--thc-danger-600` | Keep existing |
| `#d1d5db` (form border) | `--thc-gray-300` | Strong borders |
| `#f0f2f5` (table border) | `--thc-gray-150` | Light borders |
| `#667eea` (dashboard gradient) | Remove | Use `--thc-primary-*` instead |
| `#0066cc` (link color) | `--thc-primary-600` | Standardize |
| `#e8f4fd`, `#d1e7ea` (collections) | `--thc-primary-100` or `--thc-info-100` | Standardize |

### 12.2 Typography Migrations

| Current Usage | New Token | Notes |
|---------------|-----------|-------|
| `1.3rem` (page heading) | `--thc-h1-size` (1.875rem) | Standardize |
| `1.05rem` (brand name) | `--thc-text-md` (1.125rem) | Round up |
| `0.875rem` (body, buttons) | `--thc-text-sm` | Keep - most common |
| `0.8rem` (labels, nav) | `--thc-text-xs` (0.75rem) | Round down |
| `0.85rem` (dropdown) | `--thc-text-sm` (0.875rem) | Standardize |
| `0.82rem`, `0.78rem`, `0.88rem` | `--thc-text-sm` (0.875rem) | Consolidate |
| `0.7rem`, `0.68rem`, `0.72rem` (labels) | `--thc-text-xs` (0.75rem) | Consolidate |
| `0.65rem` (badges) | `--thc-text-xs` (0.75rem) | Round up |
| `1.35rem`, `1.45rem` (metrics) | `--thc-text-lg` (1.25rem) | Standardize |
| Font weight 600 | `--thc-font-semibold` | Keep - most common |
| Font weight 500 | `--thc-font-medium` | Keep for labels |
| Monospace (tables) | `--thc-font-mono` | Standardize to DM Mono |

### 12.3 Spacing Migrations

| Current Usage | New Token | Notes |
|---------------|-----------|-------|
| `0.5rem 1.25rem` (button) | `--thc-padding-button` (0.5rem 1.25rem) | Keep - 8px 20px |
| `0.3rem 0.75rem` (button-sm) | `--thc-padding-button-sm` (0.5rem 0.75rem) | Adjust to 8px 12px |
| `0.7rem 1.75rem` (button-lg) | `--thc-padding-button-lg` (0.75rem 1.75rem) | Adjust to 12px 28px |
| `1.5rem` (card padding) | `--thc-padding-card` (1.5rem) | Keep - 24px |
| `14px 16px` (metric cards) | `--thc-padding-card-sm` (1rem) | Standardize to 16px |
| `1rem 1.1rem` (dashboard) | `--thc-padding-card-sm` (1rem) | Standardize to 16px |
| `2rem` (about card) | `--thc-padding-card-lg` (2rem) | Keep - 32px |
| `0.5rem 0.75rem` (table cell) | `0.5rem 0.75rem` | Keep - 8px 12px |
| `0.75rem` (gap - common) | `--thc-gap-md` (0.75rem) | Keep - 12px |
| `10px` (grid gap) | `--thc-gap-md` (0.75rem = 12px) | Round to 4px grid |
| `1.25rem` (card margin) | `--thc-stack-md` (1.25rem) | Keep - 20px |
| `1.75rem` (header margin) | `--thc-stack-lg` (1.75rem) | Keep - 28px |
| `3rem` (page margin) | `--thc-space-12` (3rem) | Keep - 48px |

### 12.4 Border Radius Migrations

| Current Usage | New Token | Notes |
|---------------|-----------|-------|
| `6px` (buttons, inputs) | `--thc-radius-md` (6px) | Keep |
| `8px` (compact cards) | `--thc-radius-lg` (8px) | Keep |
| `10px` (standard cards) | `--thc-radius-xl` (10px) | Keep |
| `12px` (login card) | `--thc-radius-2xl` (12px) | Keep |
| `999px` (pills) | `--thc-radius-full` | Keep |

### 12.5 Shadow Migrations

| Current Usage | New Token | Notes |
|---------------|-----------|-------|
| `0 1px 3px rgba(0,0,0,0.06)` | `--thc-shadow-sm` | Keep for cards |
| `0 2px 8px rgba(0,0,0,0.07)` | `--thc-shadow-md` | Keep for hover |
| `0 4px 12px rgba(0,0,0,0.10)` | `--thc-shadow-lg` | Keep for dropdowns |
| `0 8px 28px rgba(0,0,0,0.28)` | Remove | Too strong, use `--thc-shadow-xl` |
| `0 4px 16px rgba(0,0,0,0.08)` | `--thc-shadow-lg` | Consolidate |
| `0 0 0 3px rgba(26,100,115,0.12)` | `--thc-shadow-focus` | Keep |

### 12.6 Layout Migrations

| Current Usage | New Token | Notes |
|---------------|-----------|-------|
| `max-width: 1280px` (.thc-page) | `--thc-container-standard` | Keep |
| `max-width: 960px` (.thc-wrap) | `--thc-container-narrow` | Keep |
| `@media (max-width: 600px)` | `@media (max-width: 767.98px)` | Align with Bootstrap md |
| `@media (max-width: 991.98px)` | Keep | Bootstrap lg breakpoint |
| `@media (max-width: 768px)` | Keep | Bootstrap md breakpoint |
| `@media (max-width: 576px)` | Keep | Bootstrap sm breakpoint |
| `@media (min-width: 1400px)` | Keep | Bootstrap 2xl breakpoint |

### 12.7 Component Class Migrations

| Current Class | New Class | Notes |
|---------------|-----------|-------|
| `.thc-btn` | `.btn` | Unify on Bootstrap base |
| `.thc-btn-primary` | `.btn-primary` | Unify |
| `.thc-btn-secondary` | `.btn-secondary` or `.btn-ghost` | Ghost for tertiary |
| `.thc-btn-sm` | `.btn-sm` | Unify |
| `.thc-card` | `.card` | Keep name, update tokens |
| `.thc-card-title` | `.card-header` | More semantic |
| `.thc-page` | `.container` | Bootstrap alignment |
| `.thc-page-header` | `.page-header` | Simplify |
| `.thc-badge-blue` | `.badge-primary` | Semantic naming |
| `.thc-badge-green` | `.badge-success` | Semantic naming |
| `.ic-blue`, `.ic-green`, etc. | `.icon-{color}` | Clearer naming |

### 12.8 Files Requiring Major Updates

**High Priority** (Heavy inline styles or token usage):
1. `application/templates/base.html` - Core design system definition
2. `application/blueprints/operations/daily_sales/pages/daily_sales/home.html` - ~108 lines embedded styles
3. `application/blueprints/operations/daily_sales/pages/daily_sales/new_transaction.html` - ~300 lines
4. `application/blueprints/dashboard/pages/dashboard/home.html` - ~177 lines
5. `application/blueprints/operations/collections/pages/collections/new_collection.html` - ~200 lines
6. `application/blueprints/user/pages/user/user_group.html` - Inline color hard-coding

**Medium Priority** (Moderate style overrides):
7. `application/blueprints/operations/collections/pages/collections/home.html` - ~60 lines
8. `application/blueprints/operations/ape_batch/pages/ape_batch/guide.html` - ~100 lines
9. `application/blueprints/operations/daily_sales/pages/daily_sales/audit_history.html` - Timeline colors
10. `application/templates/base_login.html` - Login styles

**Low Priority** (Inherit from base):
11. All other `.html` templates - Should inherit updated tokens automatically

---

## 13. Success Metrics

After migration, the design system should achieve:

✅ **Consistency**: < 5 unique font sizes (down from 20+)
✅ **Simplicity**: All spacing on 4px grid (no arbitrary px values)
✅ **Semantic**: Color names indicate purpose (primary, success, danger)
✅ **Scalable**: New variants can be added without breaking existing
✅ **Maintainable**: Changes to tokens update entire app
✅ **Accessible**: Sufficient contrast ratios (WCAG AA minimum)
✅ **Modern**: Uses CSS variables, rem units, flexbox/grid

---

## 14. Next Steps

1. **Review & Approve**: Stakeholders review this proposal
2. **Prototype**: Create sample page with new tokens
3. **Migration Plan**: Prioritize files for update (see 12.8)
4. **Implementation**: Phase 1 - Add new tokens to base.html
5. **Testing**: Ensure visual parity with existing design
6. **Rollout**: Update templates file-by-file
7. **Cleanup**: Remove deprecated tokens and inline styles
8. **Documentation**: Create living style guide for developers

---

**End of Design System Proposal**

*This unified system consolidates patterns from the 2026-05-24 UI audit into a cohesive, maintainable foundation for The Health Collective application.*
