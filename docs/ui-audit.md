# UI Design System Audit
**The Health Collective Inc.**
*Generated: 2026-05-24*

---

## Executive Summary

This audit analyzes the UI styling across all pages and components in The Health Collective Inc. application. The application uses a centralized design system with custom CSS variables, Bootstrap 5, and component-specific overrides. While there's a strong foundation with the THC Design System, there are notable inconsistencies in color usage, font sizing, and spacing patterns across different modules.

---

## 1. Colors

### 1.1 Design System Colors (CSS Variables)

**Primary Brand Colors** - Defined in `application/templates/base.html:23-34`
```css
--thc-primary:       #1a6473  (Teal - Main brand)
--thc-primary-dark:  #135260  (Dark teal - Hover states)
--thc-primary-light: #e6f3f5  (Light teal - Backgrounds)
```

**Neutrals**
```css
--thc-bg:            #f8f9fa  (Page background)
--thc-surface:       #ffffff  (Card/container background)
--thc-border:        #e2e8f0  (Border color)
--thc-text:          #1a2a2a  (Primary text)
--thc-text-muted:    #6b7280  (Secondary text)
```

**Typography**
```css
--thc-font-heading:  'Playfair Display', Georgia, serif
--thc-font-body:     'Inter', 'DM Sans', sans-serif
```

### 1.2 Semantic Button Colors

**Defined in `application/templates/base.html:229-264`**

| Variant | Background | Hover | Use Case | Files |
|---------|------------|-------|----------|-------|
| Primary | `#1a6473` | `#135260` | Add, Save Draft, Edit | base.html:230-233 |
| Info | `#185FA5` | `#0f4880` | Save & Submit, Upload, Confirm | base.html:236-239 |
| Success | `#166534` | `#14532d` | Approve | base.html:242-245 |
| Warning | `#b45309` | `#92400e` | Edit, Unlock | base.html:248-251 |
| Danger | `#c0392b` | `#a93226` | Delete, Cancel transaction | base.html:254-257 |
| Secondary | transparent | transparent | Cancel, Back, Download | base.html:260-263 |

### 1.3 Status & State Colors

**Transaction States** - Found in `application/blueprints/operations/daily_sales/pages/daily_sales/home.html`
```css
/* Draft state */
background: #f0f0f0, color: var(--thc-text-muted)  (Line 99)

/* Submitted state */
background: #d4edda, color: #155724  (Line 100)

/* Cancelled state */
background: #faece7, color: #993c1d  (Line 101)

/* Approved state */
background: #d4edda, color: #155724  (Line 303)
```

**Alert Colors** - `application/templates/base.html:400-413`
```css
.alert-success: background: #4CAF50, color: white
.alert-error:   background: #f44336, color: white
```

### 1.4 Icon Color Variants

**Found in `application/blueprints/operations/daily_sales/pages/daily_sales/home.html:47-54`**
```css
.ic-blue:   background: var(--thc-primary-light), color: var(--thc-primary)
.ic-green:  background: #e6f3f0, color: #0f6e56
.ic-purple: background: #eeedfe, color: #3c3489
.ic-coral:  background: #faece7, color: #993c1d
.ic-amber:  background: #faeeda, color: #854f0b
.ic-rose:   background: #fce7f3, color: #9d174d
.ic-red:    background: #fee2e2, color: #991b1b
.ic-slate:  background: #f1f5f9, color: #475569
```

### 1.5 Badge Color Variants

**Found in `application/blueprints/operations/daily_sales/pages/daily_sales/home.html:63-69`**
```css
.thc-badge-blue:   background: #1a6473, color: #fff
.thc-badge-green:  background: #1a7a60, color: #fff
.thc-badge-purple: background: #3c3489, color: #fff
.thc-badge-coral:  background: #993c1d, color: #fff
.thc-badge-amber:  background: #854f0b, color: #fff
.thc-badge-rose:   background: #9d174d, color: #fff
.thc-badge-slate:  background: #475569, color: #fff
```

### 1.6 Special Purpose Colors

**User Role Badges** - `application/blueprints/user/pages/user/user_group.html`
```css
SuperAdmin: background: #1a6473, color: #fff
Admin:      background: #e0f2fe, color: #0369a1
Staff:      background: #f0fdf4, color: #166534, border: #bbf7d0
SuperUser:  background: #fef3c7, color: #92400e
Viewer:     background: #e5e7eb, color: #374151
```

**Dashboard Metrics** - `application/blueprints/dashboard/pages/dashboard/home.html`
```css
/* Gradient for Total Sales */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
border-color: #667eea
```

**Dashboard Action Card Icons**
```css
Drafts:              background: #fef9c3, color: #854d0e
Pending Approval:    background: #fee2e2, color: #c0392b
Pending Cancellations: background: #fef3c7, color: #f59e0b
Receivables:         background: #dcfce7, color: #166534
```

### 1.7 Inconsistencies Identified

1. **Alert Colors Mismatch**: Base template uses `#4CAF50` (Material green) while buttons use `#166534` (deeper green)
   - Files: `base.html:401`, vs `base.html:242`

2. **Multiple Blue Shades**: At least 4 different blues in use
   - Primary: `#1a6473`
   - Info button: `#185FA5`
   - Dashboard gradient: `#667eea`
   - Link blue: `#0066cc` (collections)

3. **Inconsistent Danger Reds**: Two primary red values
   - Danger button: `#c0392b` (base.html)
   - Material red: `#f44336` (alert-error)
   - Warning/danger icon: `#991b1b`

4. **One-off Colors**: Several pages use inline hex values not in the design system
   - Collections: `#e8f4fd`, `#d1e7ea` (new_collection.html)
   - Audit history: `#007bff`, `#10b981`, `#3b82f6`, `#8b5cf6` (audit_history.html)

---

## 2. Typography

### 2.1 Font Families

**Primary Fonts** - Defined in `application/templates/base.html:32-33`
```css
Headings: 'Playfair Display', Georgia, serif
Body:     'Inter', 'DM Sans', sans-serif
Numbers:  'DM Mono', 'Courier New', monospace (tables)
```

**Font Loading** - `application/templates/base.html:13`
- Local font files via `vendor/css/fonts.css`
- Latin subset only

### 2.2 Font Sizes

**Base Template Sizes** - `application/templates/base.html`

| Element | Size | Line # | Context |
|---------|------|--------|---------|
| Navbar brand | 1rem | 53 | Brand name |
| Navbar links | 0.8rem | 59 | Navigation |
| Navbar version | 0.75rem | 77 | Version tag |
| Navbar dropdown | 0.85rem | 71 | Dropdown menu |
| Page heading (h4) | 1.3rem | 322 | Page titles |
| Card title | 0.7rem | 304 | Section labels |
| Form label | 0.8rem | 267 | Form fields |
| Form control | 0.875rem | 274 | Input text |
| Button | 0.875rem | 216 | Standard buttons |
| Button small | 0.8rem | 226 | Compact buttons |
| Button large | 1rem | 227 | Large buttons |
| Table header | 0.7rem | 330 | Table headings |
| Table body | 0.875rem | 328 | Table content |

**Daily Sales Specific Sizes** - `application/blueprints/operations/daily_sales/pages/daily_sales/home.html`

| Element | Size | Line # |
|---------|------|--------|
| Brand name | 1.05rem | 10 |
| Brand subtitle | 0.75rem | 11 |
| Date nav | 0.82rem | 19 |
| Date display | 0.82rem | 19 |
| Section label | 0.65rem | 37 |
| Metric label | 0.7rem | 32 |
| Metric value | 1.35rem | 33 |
| Transaction title | 0.9rem | 57 |
| Transaction desc | 0.75rem | 58 |
| Badge | 0.65rem | 61 |
| Record number | 0.68rem | 94 |
| Customer name | 0.85rem | 95 |
| Amount | 0.88rem | 97 |

**Dashboard Sizes** - `application/blueprints/dashboard/pages/dashboard/home.html`

| Element | Size | Line # |
|---------|------|--------|
| Section label | 0.68rem | 29, 96, 147 |
| Quick button | 0.82rem | 203 |
| Card icon | 1.15rem | 221 |
| Card label | 0.72rem | 228 |
| Card value | 1.45rem | 237 |
| Card link | 0.72rem | 246 |
| Metric label | 0.68rem | 269 |
| Metric value | 1.25rem | 280 |
| Table header | 0.78rem | 298 |
| Table cell | 0.8rem | 318 |

### 2.3 Font Weights

**Standard Weights**
```css
400 - Normal body text
500 - Form labels, secondary emphasis
600 - Headings, buttons, emphasized text (most common)
700 - Card values, strong emphasis
800 - Dashboard version number (special)
```

**Usage Patterns**
- Form labels: 500 (base.html:268)
- Buttons: 600 (base.html:217)
- Card titles: 600 (base.html:305)
- Page headings: 600 (base.html:323)
- Metric values: 600-700 (varies by context)
- Section labels: 600-700 (varies by page)

### 2.4 Line Heights

**Explicit Line Heights Found**
```css
1.0  - Dashboard version (about.html)
1.2  - Dashboard card value (home.html:240)
1.45 - Transaction description (daily_sales/home.html:58)
1.5  - Default body text (about.html feature descriptions)
1.55 - Guide step body (ape_batch/guide.html)
```

**Implicit**: Most elements rely on browser defaults (~1.2-1.5)

### 2.5 Letter Spacing

**Common Values**
```css
0.01em  - Buttons, standard text (base.html:222)
0.03em  - Sales table header (dashboard/home.html)
0.04em  - Dashboard card label (dashboard/home.html:230)
0.05em  - Metric labels (daily_sales/home.html:32)
0.06em  - Navbar links, table headers (base.html:61)
0.08em  - Section labels (collections/home.html:143)
0.1em   - Card titles, uppercase labels (base.html:306)
0.12em  - Guide section titles (ape_batch/guide.html)
0.14em  - Version label (about.html)
```

### 2.6 Typography Inconsistencies

1. **Section Label Sizes Vary**: 0.65rem (daily_sales), 0.68rem (dashboard), 0.7rem (base)
2. **Card Title Inconsistency**: base.html defines 0.7rem, but some pages override
3. **Number Font Ambiguity**: Tables use monospace, but some use `font-family: monospace` and others use `'DM Mono', 'Courier New', monospace`
4. **Line Height Missing**: Most elements don't explicitly set line-height, relying on browser defaults

---

## 3. Spacing

### 3.1 Padding Values

**Form Elements** - `application/templates/base.html`
```css
Buttons:        0.5rem 1.25rem (standard)
Buttons small:  0.3rem 0.75rem
Buttons large:  0.7rem 1.75rem
Form controls:  (Bootstrap defaults + 6px border-radius)
```

**Cards** - `application/templates/base.html:299`
```css
.thc-card: padding: 1.5rem
```

**Specific Card Padding Overrides**
```css
Daily sales (home.html):       padding: 14px 16px (metric cards)
Collections (new_collection):  padding varies by section
Dashboard (home.html):         padding: 0.85rem 1rem (metric), 1rem 1.1rem (action cards)
```

**Table Padding** - `application/templates/base.html`
```css
Table header (th): padding: 0.5rem 0.75rem (line 335)
Table cell (td):   padding: 0.55rem 0.75rem (line 341)
```

**Navigation** - `application/templates/base.html:96, 103-106`
```css
Mobile nav panel:    padding: 0.4rem 0 0.6rem
Mobile nav link:     padding: 0.55rem 1.1rem
Mobile dropdown item: padding: 0.42rem 2rem
```

**Inconsistent Card Padding**
- Base: 1.5rem
- Daily sales metrics: 14px 16px (≈0.875rem 1rem)
- Dashboard: 1rem 1.1rem
- About page: 2rem 2rem 1.75rem

### 3.2 Margin Values

**Page Layout** - `application/templates/base.html:293`
```css
.thc-page: margin: 3rem auto
```

**Component Spacing**
```css
Card margin-bottom:    1.25rem (base.html:300)
Page header margin:    1.75rem (base.html:317)
Section label margin:  0.6rem (daily_sales/home.html:37)
Form label margin:     0.3rem (base.html:270)
```

**Daily Sales Specific** - `application/blueprints/operations/daily_sales/pages/daily_sales/home.html`
```css
Top bar margin:        1.5rem
Metrics margin:        1.75rem
Transaction grid gap:  10px
Cash grid gap:         10px
Transaction row margin: 6px
```

**Dashboard** - `application/blueprints/dashboard/pages/dashboard/home.html`
```css
Section margin:        1.5rem
Dashboard grid gap:    0.75rem
Sales table gap:       1rem
```

### 3.3 Gap Values (Flexbox/Grid)

**Common Gap Patterns**
```css
0.3rem  - Icon + text in buttons (small)
0.35rem - Help button icon (daily_sales)
0.5rem  - Dashboard header buttons
0.6rem  - Section header actions
0.75rem - Page header, dashboard grid, topbar (most common)
1rem    - Collections deduction grid
```

**Grid Gaps**
```css
Daily sales transaction grid: 10px
Daily sales cash grid:        10px
Daily sales metrics:          10px
Dashboard action grid:        0.75rem
Dashboard sales tables:       1rem
```

**Inconsistency**: Mixing `px` and `rem` units for gaps
- Some use `10px`
- Others use `0.75rem` (12px at default)
- Creates subtle visual differences

### 3.4 Responsive Spacing Adjustments

**Mobile Breakpoints** - `application/templates/base.html:379-393`

```css
@media (max-width: 768px) {
  .thc-page padding:    0.75rem (from 1.5rem)
  .thc-page margin:     1rem (from 3rem)
  .thc-card padding:    1rem (from 1.5rem)
  .thc-page-header margin: 1rem (from 1.75rem)
  .btn padding:         0.45rem 1rem (from 0.5rem 1.25rem)
}

@media (max-width: 576px) {
  .thc-page padding:    0.5rem (from 0.75rem)
  .thc-card padding:    0.75rem (from 1rem)
  .thc-card border-radius: 8px (from 10px)
}
```

---

## 4. Borders, Shadows & Radius

### 4.1 Border Values

**Standard Borders** - `application/templates/base.html`
```css
Default border:        1px solid #e2e8f0
Card border:           1px solid #e2e8f0 (line 296)
Table header border:   2px solid #e2e8f0 (line 336)
Table row border:      1px solid #f0f2f5 (line 342)
Section title border:  1px solid #e2e8f0 (line 311)
```

**Special Borders**
```css
Featured card:         1.5px solid var(--thc-primary) (daily_sales/home.html:43)
Toggle group:          1px solid #c6dde1 (collections/home.html:118)
Pill toggle:           1.5px solid (collections/home.html:156)
Navbar mobile:         1px solid rgba(255,255,255,0.06) (base.html:105)
```

**Border Colors in Use**
```css
#e2e8f0   - Primary border (design system)
#f0f2f5   - Lighter border (table rows)
#c6dde1   - Toggle borders
#d1d5db   - Form controls, secondary button
#e5e7eb   - Audit history
rgba(255,255,255,0.06) - Navbar mobile
```

### 4.2 Box Shadow Values

**Standard Shadows** - `application/templates/base.html`
```css
Card shadow:           0 1px 3px rgba(0,0,0,0.06) (line 298)
Form focus shadow:     0 0 0 3px rgba(26,100,115,0.12) (line 281)
Dropdown shadow:       0 4px 12px rgba(0,0,0,0.10) (line 69)
Mobile nav shadow:     0 8px 28px rgba(0,0,0,0.28) (line 95)
Modal backdrop shadow: 0 4px 8px rgba(0,0,0,0.2) (line 153)
```

**Dashboard Shadows**
```css
Card hover:            0 2px 8px rgba(0,0,0,0.07) (dashboard/home.html:195)
```

**Transaction Form Shadows**
```css
Card shadow:           0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)
                       (daily_sales/new_transaction.html:48)
```

**Consistency**: Shadow values are fairly consistent, using low opacity black rgba for depth

### 4.3 Border Radius Values

**Standard Radius** - `application/templates/base.html`
```css
Small radius (--thc-radius-sm):  6px  (buttons, form controls, badges)
Standard radius (--thc-radius):  10px (cards)
Large radius:                    12px (login card)
Pill radius:                     999px / 20px (badges, toggles)
Circle:                          50% (avatars, icons)
```

**Element-Specific Radius**
```css
Buttons:               6px (base.html:218)
Form controls:         6px (base.html:276)
Cards:                 10px (base.html:297)
Login card:            12px (base_login.html:38)
Dropdown:              6px (base.html:68)
Mobile nav:            0 0 10px 10px (base.html:94)
Navbar mobile toggle:  0 0 8px 8px (base.html:152)
Transaction type badge: 999px (daily_sales/home.html:70)
Small icons:           6px (daily_sales/home.html:46)
Large icons:           10px (daily_sales/home.html:46)
Date nav button:       6px (daily_sales/home.html:15)
```

**Responsive Radius Adjustments**
```css
@media (max-width: 576px) {
  .thc-card border-radius: 8px (from 10px)
}
```

### 4.4 Border & Shadow Inconsistencies

1. **Multiple Border Colors**: 6+ border color values used across the app
2. **Radius Mixing**: Some use `6px`, others `8px`, `10px`, `12px` without clear hierarchy
3. **Shadow Opacity Variance**: Card shadows range from `rgba(0,0,0,0.06)` to `rgba(0,0,0,0.28)`

---

## 5. Button Variants & Styles

### 5.1 Primary Button System

**Global Button Base** - `application/templates/base.html:214-228`
```css
Font:         var(--thc-font-body)
Size:         0.875rem
Weight:       600
Radius:       6px
Padding:      0.5rem 1.25rem
Transition:   background 0.15s, border-color 0.15s, transform 0.1s
Shadow:       none (explicitly removed)
Letter-spacing: 0.01em
```

**Size Variants**
```css
.btn-sm:  padding: 0.3rem 0.75rem, font-size: 0.8rem
.btn-lg:  padding: 0.7rem 1.75rem, font-size: 1rem
```

**Hover Effect**: `transform: translateY(-1px)` (subtle lift)

### 5.2 Button Color Variants

See Section 1.2 for complete color breakdown.

**Quick Reference**
```css
.btn-primary:   #1a6473 → #135260  (teal, most common action)
.btn-info:      #185FA5 → #0f4880  (blue, submit/confirm)
.btn-success:   #166534 → #14532d  (green, approve)
.btn-warning:   #b45309 → #92400e  (amber, edit/unlock)
.btn-danger:    #c0392b → #a93226  (red, delete/cancel)
.btn-secondary: transparent, border  (ghost style)
```

**Outline Variants**: Each has a matching `.btn-outline-*` variant with transparent background and colored border/text

### 5.3 Custom Button Classes

**THC Button System** - `application/templates/base.html:350-376`
```css
.thc-btn:
  - Inline-flex layout
  - Gap: 0.3rem (for icon + text)
  - Padding: 0.4rem 0.9rem
  - Font-size: 0.82rem
  - Weight: 600
  - Radius: 6px
  - Border: 1px solid transparent

.thc-btn-sm:
  - Padding: 0.25rem 0.65rem
  - Font-size: 0.75rem
  - Radius: 5px

.thc-btn-primary:  var(--thc-primary) background
.thc-btn-secondary: white background, teal border
```

**Dashboard Quick Button** - `application/blueprints/dashboard/pages/dashboard/home.html:198-212`
```css
.dash-ql-btn:
  - Inline-flex
  - Gap: 0.35rem
  - Padding: 0.3rem 0.75rem
  - Font-size: 0.82rem
  - Weight: 600
  - Border: 1px solid var(--thc-primary)
  - Hover: fills with primary color
```

### 5.4 Button Macros

**Macro System** - `application/templates/macros_button.html`

| Macro | Style | Icon | Confirmation |
|-------|-------|------|--------------|
| add_button | btn-primary btn-sm | bi-plus-lg | No |
| edit_button | btn-outline-secondary btn-sm | bi-pencil | No |
| delete_button | btn-outline-danger btn-sm | bi-trash | Yes (Type YES) |
| approve_button | btn-outline-success btn-sm | bi-check-lg | Yes (Type YES) |
| unlock_button | btn-outline-warning btn-sm | bi-unlock | Yes (Type YES) |
| activate_button | btn-outline-success btn-sm | bi-toggle-off | Yes (Type YES) |
| deactivate_button | btn-outline-secondary btn-sm | bi-toggle-on | Yes (Type YES) |

All icon-only buttons are `btn-sm` size.

### 5.5 Special Button Patterns

**Date Navigation Buttons** - `application/blueprints/operations/daily_sales/pages/daily_sales/home.html:15-16`
```css
.thc-date-nav-btn:
  - Size: 32x32px square
  - Radius: 6px
  - Border: 1px solid var(--thc-border)
  - Hover: border changes to primary, bg to primary-light
```

**Today Button** - `daily_sales/home.html:23-24`
```css
.thc-today-btn:
  - Font-size: 0.72rem
  - Weight: 600
  - Padding: 4px 10px
  - Radius: 6px
  - Border: 1px solid var(--thc-primary)
  - Hover: bg to primary-light
```

**Guide Help Button** - `daily_sales/home.html:25-27`
```css
.guide-help-btn:
  - No border/background
  - Gap: 0.35rem
  - Color: var(--thc-text-muted)
  - Hover: color to primary
  - Icon: circular border, 1.15rem
```

### 5.6 Button Inconsistencies

1. **Three Button Systems**: Global `.btn`, custom `.thc-btn`, and page-specific buttons with overlapping purposes
2. **Padding Variations**: Standard buttons use `0.5rem 1.25rem`, THC buttons use `0.4rem 0.9rem`
3. **Font Size Mismatch**: Global buttons are `0.875rem`, THC buttons are `0.82rem`
4. **Icon Patterns**: Some use `<i class="bi">` before text, others use gap via flexbox
5. **Hover Effects**: Global buttons have `translateY(-1px)`, custom buttons don't

---

## 6. Input & Form Field Styles

### 6.1 Form Control Base Styles

**Global Form Styles** - `application/templates/base.html:266-291`

```css
.form-label, .col-form-label:
  - Font-size: 0.8rem
  - Weight: 500
  - Color: var(--thc-text-muted) (#6b7280)
  - Margin-bottom: 0.3rem

.form-control, .form-select:
  - Font-family: var(--thc-font-body)
  - Font-size: 0.875rem
  - Border: 1px solid #d1d5db
  - Border-radius: 6px
  - Transition: border-color 0.15s, box-shadow 0.15s

.form-control:focus, .form-select:focus:
  - Border-color: var(--thc-primary)
  - Box-shadow: 0 0 0 3px rgba(26,100,115,0.12)
  - Outline: none

.form-control.is-invalid, .form-select.is-invalid:
  - Border-color: #c0392b
```

**Login Form Overrides** - `application/templates/base_login.html:54-56`
```css
Same as base but defined inline for login pages
```

### 6.2 Input Type Variations

**Number Inputs** - `application/blueprints/operations/daily_sales/pages/daily_sales/new_transaction.html:98`
```css
input[type="number"]:
  - Font-family: monospace
  - Font-size: 0.85rem
```

**Textarea** - `application/blueprints/operations/daily_sales/pages/daily_sales/new_transaction.html:95`
```css
textarea.form-control:
  - Resize: vertical
  - Min-height: 70px
```

**Date Inputs** - `application/blueprints/operations/daily_sales/pages/daily_sales/home.html:22`
```css
.thc-date-hidden:
  - Position: absolute
  - Opacity: 0
  - Cursor: pointer
  (Hidden but functional date picker)
```

### 6.3 Form Field Patterns

**Tom-Select Integration** - `application/blueprints/operations/daily_sales/pages/daily_sales/new_transaction.html:11-12`
- Uses `tom-select.bootstrap5.min.css`
- Provides searchable dropdowns
- Consistent with Bootstrap 5 styling

**Auto-capitalize** - `application/templates/base.html:437-452`
- JavaScript adds `.upper-case` class handler
- Converts input to uppercase on blur
- Used for formal records

**jQuery UI Integration** - `application/templates/base.html:14-19`
- Datepicker and autocomplete widgets
- Styled via `jquery-ui.min.css`

### 6.4 Error & Validation States

**Error Display** - `application/templates/base.html:285-290`
```css
.invalid-feedback, .thc-field-error:
  - Display: block
  - Font-size: 0.75rem
  - Color: #c0392b (danger red)
  - Margin-top: 0.2rem
```

**Error Pattern in Forms**
- `.is-invalid` class on input
- `.invalid-feedback` below input
- Red border on invalid input

### 6.5 Form Layout Patterns

**Horizontal Forms** - Common pattern
```html
<div class="row mb-3">
  <label class="col-sm-3 col-form-label">Label</label>
  <div class="col-sm-9">
    <input class="form-control">
  </div>
</div>
```

**Vertical Forms** - Daily sales pattern
```html
<div class="mb-3">
  <label class="form-label">Label</label>
  <input class="form-control">
</div>
```

**Form Macros** - `application/templates/macros_simple_form.html`
- `text_box(form, label, name, value, autofocus)`
- `text_area(form, label, name, value)`
- `save_button()`
- Encapsulates common patterns

### 6.6 Form Inconsistencies

1. **Label Font Size**: Base uses 0.8rem, but some pages override to 0.78rem (transaction forms)
2. **Control Font Size**: Base uses 0.875rem, transaction forms override to various sizes
3. **Focus Shadow Color**: Uses rgba(26,100,115,0.12) which is different from primary-light (#e6f3f5)
4. **Validation Colors**: Error uses #c0392b, but some templates use different reds inline

---

## 7. Card & Container Patterns

### 7.1 Primary Card System

**THC Card** - `application/templates/base.html:294-312`
```css
.thc-card:
  - Background: #fff
  - Border: 1px solid #e2e8f0
  - Border-radius: 10px
  - Box-shadow: 0 1px 3px rgba(0,0,0,0.06)
  - Padding: 1.5rem
  - Margin-bottom: 1.25rem

.thc-card > .card-body:
  - Padding: 0 (removes Bootstrap padding)

.thc-card-title:
  - Font-size: 0.7rem
  - Weight: 600
  - Letter-spacing: 0.1em
  - Text-transform: uppercase
  - Color: var(--thc-text-muted)
  - Margin-bottom: 1.25rem
  - Padding-bottom: 0.6rem
  - Border-bottom: 1px solid #e2e8f0
```

### 7.2 Specialized Card Variants

**Transaction Cards** - `application/blueprints/operations/daily_sales/pages/daily_sales/home.html:41-44`
```css
.thc-txn-card:
  - Background: #fff
  - Border: 1px solid #e2e8f0
  - Border-radius: 10px
  - Padding: 16px
  - Cursor: pointer
  - Display: flex, gap: 14px
  - Hover: border-color #a0b4b8, background primary-light

.thc-txn-card.featured:
  - Border: 1.5px solid var(--thc-primary)
```

**Cash Management Cards** - `daily_sales/home.html:73-74`
```css
.thc-cash-card:
  - Similar to txn-card but padding: 14px 16px
  - Hover: same as txn-card
```

**Dashboard Action Cards** - `application/blueprints/dashboard/pages/dashboard/home.html:185-196`
```css
.dash-card:
  - Background: #fff
  - Border: 1px solid #e2e8f0
  - Border-radius: 10px
  - Padding: 1rem 1.1rem
  - Display: flex, gap: 0.85rem
  - Hover: shadow 0 2px 8px rgba(0,0,0,0.07)

.dash-card--warn:
  - Border-color: #fbbf24 (amber)
```

**Metric Cards** - `daily_sales/home.html:31`
```css
.thc-metric:
  - Background: #fff
  - Border: 1px solid #e2e8f0
  - Border-radius: 8px
  - Padding: 14px 16px
```

**Sales Table Cards** - `dashboard/home.html:289-295`
```css
.sales-table-card:
  - Background: #fff
  - Border: 1px solid #e2e8f0
  - Border-radius: 8px
  - Overflow: hidden
  - Max-width: 100%
```

### 7.3 Record Row Pattern

**Transaction Record Rows** - `daily_sales/home.html:90-92`
```css
.thc-rec-row:
  - Background: #fff
  - Border: 1px solid #e2e8f0
  - Border-radius: 8px
  - Padding: 11px 14px
  - Display: flex, gap: 12px
  - Margin-bottom: 6px
  - Hover: border-color #a0b4b8, background primary-light
```

### 7.4 Login Card

**Special Card** - `application/templates/base_login.html:35-41`
```css
.thc-login-card:
  - Background: #fff
  - Border: 1px solid #e2e8f0
  - Border-radius: 12px (larger than standard)
  - Box-shadow: 0 4px 16px rgba(0,0,0,0.08) (stronger)
  - Padding: 2rem
```

### 7.5 Container Width Patterns

**Page Wrappers**
```css
.thc-page (base.html:293):
  - Max-width: 1280px
  - Margin: 3rem auto
  - Padding: 0 1.5rem 4rem

.thc-wrap (daily_sales/home.html:6):
  - Max-width: 960px
  - Margin: 0 auto
  - Padding: 1.5rem 1rem 3rem

.txn-wrapper (new_transaction.html:62):
  - Max-width: 960px
  - Margin: 0 auto
  - Padding: 2rem 1rem 4rem
```

### 7.6 Card Inconsistencies

1. **Border Radius Variations**: 8px (metrics), 10px (cards), 12px (login)
2. **Padding Inconsistency**: Standard card is 1.5rem, but many cards override to smaller values
3. **Shadow Variations**: Login card has stronger shadow than standard cards
4. **Hover States**: Some cards have hover effects, others don't (inconsistent interactivity)
5. **Max Width Confusion**: Three different wrapper widths (960px, 1280px) without clear purpose

---

## 8. Layout Patterns

### 8.1 Grid Systems

**CSS Grid Usage**

**Transaction Type Grid** - `daily_sales/home.html:40`
```css
.thc-txn-grid:
  - Display: grid
  - Grid-template-columns: repeat(2, 1fr)
  - Gap: 10px
  - Responsive: 1fr on mobile
```

**Metric Grid** - `daily_sales/home.html:30`
```css
.thc-metrics:
  - Display: grid
  - Grid-template-columns: repeat(3, 1fr)
  - Gap: 10px
  - Responsive: 1fr on mobile
```

**Dashboard Grid** - `dashboard/home.html:178-182`
```css
.dash-grid:
  - Display: grid
  - Grid-template-columns: repeat(auto-fill, minmax(200px, 1fr))
  - Gap: 0.75rem
  - Responsive: 1fr 1fr on mobile (576px)
```

**Dynamic Product Type Grid** - `dashboard/home.html:39`
```css
Dynamic columns:
  - Grid-template-columns: repeat({{ product_types|length + 1 }}, 1fr)
  - Generated server-side based on data
```

**Sales Table Grid** - `dashboard/home.html:53`
```css
Sales tables:
  - Grid-template-columns: repeat({{ [product_types|length, 2]|min }}, 1fr)
  - Max 2 columns
  - Gap: 1rem
```

### 8.2 Flexbox Patterns

**Page Header** - `base.html:313-319`
```css
.thc-page-header:
  - Display: flex
  - Align-items: center
  - Gap: 0.75rem
  - Flex-wrap: wrap
  - Margin-bottom: 1.75rem
```

**Top Bar** - `daily_sales/home.html:9`
```css
.thc-topbar:
  - Display: flex
  - Justify-content: space-between
  - Align-items: flex-start
  - Flex-wrap: wrap
  - Gap: 0.75rem
  - Margin-bottom: 1.5rem
```

**Date Navigation** - `daily_sales/home.html:14`
```css
.thc-date-nav:
  - Display: flex
  - Align-items: center
  - Gap: 6px
```

**Footer** - `daily_sales/home.html:82`
```css
.thc-footer:
  - Display: flex
  - Justify-content: space-between
  - Align-items: center
  - Padding-top: 1rem
  - Border-top: 1px solid var(--thc-border)
  - Flex-wrap: wrap
  - Gap: 0.75rem
```

### 8.3 Max Widths

**Container Widths in Use**
```css
1280px - .thc-page (base.html:293) - Standard pages
960px  - .thc-wrap (daily_sales/home.html:6) - Transaction pages
960px  - .txn-wrapper (new_transaction.html:62) - Form pages
800px  - voucher.css container (print documents)
260px  - Mobile nav panel width (base.html:90)
```

### 8.4 Breakpoints

**Defined Breakpoints** - `application/templates/base.html:379-393`

```css
@media (max-width: 991.98px) - Navbar collapse (lg breakpoint)
@media (max-width: 768px)    - Tablet adjustments (md breakpoint)
@media (max-width: 600px)    - Mobile grid collapse (custom)
@media (max-width: 576px)    - Small mobile (sm breakpoint)
@media (min-width: 1400px)   - Extra large screens (xl breakpoint)
```

**Bootstrap 5 Breakpoints** (inherited)
```css
xs: <576px
sm: ≥576px
md: ≥768px
lg: ≥992px
xl: ≥1200px
xxl: ≥1400px
```

### 8.5 Responsive Patterns

**Grid Collapsing**
```css
Daily sales grids:     3 cols → 1 col at 600px
Dashboard action grid: auto-fill → 2 cols at 576px
Sales table grid:      dynamic → responsive based on content
```

**Navigation**
```css
Desktop: Horizontal navbar with dropdowns
Mobile:  Hamburger → Floating overlay panel (260px wide)
```

**Table Patterns**
```css
Most tables: Horizontal scroll on mobile (no collapsing)
Collections table: Uses Bootstrap .table-responsive wrapper
```

**Spacing Adjustments**
```css
@768px:  Page padding reduces, card padding reduces
@576px:  Further padding reduction, font size adjustments
@1400px: Increased page padding for larger screens
```

### 8.6 Layout Inconsistencies

1. **Max Width Ambiguity**: Two different standard widths (960px vs 1280px) without documentation
2. **Breakpoint Mixing**: Custom breakpoint at 600px doesn't align with Bootstrap standards
3. **Grid Gap Units**: Mixing `px` (10px) and `rem` (0.75rem) for grid gaps
4. **Responsive Strategy**: Some components use CSS Grid auto-fill, others use media queries
5. **Mobile Nav Pattern**: Overlay panel is unique to navbar, not reusable elsewhere

---

## 9. Inconsistencies & One-Off Styles

### 9.1 Critical Inconsistencies

**Color System Violations**

1. **Alert Colors Don't Match Buttons**
   - Alert success: `#4CAF50` (Material Design green)
   - Button success: `#166534` (Tailwind green)
   - Files: `base.html:401` vs `base.html:242`

2. **Multiple Blue Primaries**
   - THC Primary: `#1a6473`
   - Info button: `#185FA5`
   - Dashboard gradient: `#667eea`
   - Uncoordinated blues across pages

3. **Inconsistent Danger Red**
   - Button danger: `#c0392b`
   - Alert error: `#f44336`
   - Badge cancelled: `#993c1d`

**Typography Drift**

4. **Section Label Size Varies**
   - Base: 0.7rem
   - Daily sales: 0.65rem
   - Dashboard: 0.68rem
   - Files: base.html:304, daily_sales/home.html:37, dashboard/home.html:29

5. **Card Title Inconsistency**
   - Defined globally but overridden in many pages
   - Transaction form: Custom sizing

**Spacing Chaos**

6. **Card Padding Varies Wildly**
   - Base: 1.5rem
   - Metrics: 14px 16px
   - Dashboard: 1rem 1.1rem
   - About: 2rem 2rem 1.75rem

7. **Grid Gap Unit Mixing**
   - Some use `10px`
   - Others use `0.75rem`
   - Creates visual inconsistency

**Button Overlap**

8. **Three Button Systems**
   - Global `.btn` system
   - Custom `.thc-btn` system
   - Page-specific buttons
   - Overlapping purposes, different styles

### 9.2 One-Off Styles by Page

**Collections (new_collection.html)**
```css
Unique colors:
  - #e8f4fd (summary background)
  - #d1e7ea (section background)
  - #0066cc (link color)
Custom autocomplete dropdown styles
```

**Audit History (audit_history.html)**
```css
Unique timeline colors:
  - #007bff (info border)
  - #10b981 (created action)
  - #3b82f6 (updated action)
  - #8b5cf6 (submitted action)
Not using design system colors
```

**User Group (user_group.html)**
```css
Inline hex colors for role badges
Hard-coded instead of using classes:
  - background:#1a6473
  - background:#e0f2fe
  - background:#f0fdf4
```

**About Page (about.html)**
```css
Linear gradient for header card:
  - background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
Version number special styling:
  - font-size:2.4rem, weight:800
```

**Transaction Type (transaction_type/home.html)**
```css
Save status indicator colors:
  - #fff3cd (saving)
  - #d1e7dd (saved)
  - #f8d7da (error)
Duplicates alert colors with slight variations
```

**APE Batch Guide (ape_batch/guide.html)**
```css
Print-specific typography:
  - font-size: 9pt, 8pt, 7.5pt
  - Uses points instead of rem
Inconsistent with digital design system
```

### 9.3 Anti-Patterns Identified

1. **Inline Styles Proliferation**: Many pages use `style=""` attributes instead of classes
   - Example: `dashboard/home.html` has 30+ inline style attributes
   - Reduces reusability and maintainability

2. **Color Hard-Coding**: Hex colors directly in templates instead of CSS variables
   - Example: `user_group.html` hard-codes all badge colors

3. **Duplicate Definitions**: Same styles redefined across multiple files
   - Example: Alert success colors defined in base.html and repeated elsewhere

4. **Magic Numbers**: Arbitrary values without clear reason
   - Example: `260px` for mobile nav width
   - Example: `14px 16px` vs `1rem 1.1rem` padding

5. **Unused CSS Variables**: Some variables defined but never used
   - `--thc-surface` only used once
   - `--thc-border-focus` defined in new_transaction.html but not in base

6. **Bootstrap Override Inconsistency**: Some use `!important`, others don't
   - Global buttons use `!important` everywhere
   - Creates specificity battles

### 9.4 Technical Debt

**Print Stylesheet Separation**
- `voucher.css` exists for print but doesn't share variables with main system
- Completely separate styling paradigm

**External Dependencies**
- jQuery UI CSS conflicts with Bootstrap in some areas
- Tom-select uses separate Bootstrap 5 theme

**File Organization**
- Only one custom CSS file (`voucher.css`)
- All other styles embedded in templates
- Makes global changes difficult

**Missing Documentation**
- No style guide document
- No component library
- Developers guessing at correct patterns

---

## 10. Recommendations

### 10.1 Critical Fixes (High Priority)

1. **Consolidate Color System**
   - Replace Material Design colors with Tailwind equivalents
   - Standardize all success colors to `#166534`
   - Remove duplicate blues, pick one info color
   - Document color usage in a style guide

2. **Unify Button System**
   - Choose either `.btn` or `.thc-btn` as primary
   - Deprecate the other or clarify distinct use cases
   - Standardize padding, font-size, and hover effects

3. **Standardize Card Padding**
   - Pick one default padding (recommend 1.5rem)
   - Create explicit modifier classes for variants
   - Example: `.thc-card`, `.thc-card--compact`, `.thc-card--spacious`

4. **Fix Typography Scale**
   - Create consistent size scale (0.7rem, 0.75rem, 0.8rem, 0.875rem, 1rem, etc.)
   - Document when to use each size
   - Remove arbitrary one-offs like 0.68rem, 0.72rem

### 10.2 Medium Priority

5. **Extract Inline Styles**
   - Move inline styles to reusable classes
   - Especially dashboard and user group pages
   - Create utility classes for common patterns

6. **Standardize Grid Gaps**
   - Use rem units consistently
   - Pick one default gap value (0.75rem or 1rem)
   - Document when to deviate

7. **Create Component Library**
   - Document all card variants
   - Document all button variants
   - Create reusable classes for common patterns
   - Add examples to style guide

8. **Border Radius Hierarchy**
   - Small: 6px (buttons, small elements)
   - Medium: 8px (metrics, compact cards)
   - Large: 10px (standard cards)
   - XL: 12px (hero cards, modals)
   - Document usage

### 10.3 Low Priority (Nice to Have)

9. **Responsive Breakpoints**
   - Align custom breakpoints with Bootstrap
   - Remove 600px breakpoint, use 576px (sm)
   - Use Bootstrap's breakpoint mixins consistently

10. **Print Stylesheet Integration**
    - Share variables between `voucher.css` and main system
    - Consider CSS variables for print styles
    - Unify typography scales

11. **External Dependency Audit**
    - Review jQuery UI theme compatibility
    - Ensure Tom-select theme matches design system
    - Consider replacing jQuery UI with Bootstrap 5 equivalents

12. **CSS Organization**
    - Extract embedded styles to external stylesheets
    - Create `/static/css/components/` directory
    - Organize by feature or component type

---

## Appendix A: File Inventory

### Primary Style Files

| File | Purpose | Lines | Notes |
|------|---------|-------|-------|
| `application/templates/base.html` | Main design system | 615 | CSS vars, global styles |
| `application/templates/base_login.html` | Login page styles | 74 | Subset of base |
| `application/templates/base_financial_report.html` | Report pages | 43 | CDN Bootstrap (legacy) |
| `application/static/css/voucher.css` | Print documents | 179 | Separate system |
| `application/static/vendor/css/bootstrap.min.css` | Bootstrap 5 | - | Minified |
| `application/static/vendor/css/bootstrap-icons.min.css` | Icon font | - | Minified |
| `application/static/vendor/css/fonts.css` | Web fonts | - | Local fonts |
| `application/static/vendor/css/jquery-ui.min.css` | jQuery UI | - | Minified |
| `application/static/vendor/css/tom-select.bootstrap5.min.css` | Select plugin | - | Minified |

### Template Files with Significant Embedded Styles

| File | Style Block Lines | Notes |
|------|-------------------|-------|
| `daily_sales/home.html` | ~108 lines | Complete page system |
| `daily_sales/new_transaction.html` | ~300+ lines | Form system |
| `dashboard/home.html` | ~177 lines | Dashboard components |
| `collections/home.html` | ~60 lines | Toggle and pill styles |
| `collections/new_collection.html` | ~200+ lines | Complex autocomplete |
| `ape_batch/guide.html` | ~100 lines | Print-specific |
| `user/user_group.html` | ~50 lines | User management |

### Macro Files

| File | Purpose |
|------|---------|
| `macros_button.html` | Button action macros |
| `macros_simple_form.html` | Form field macros |
| `macros_form_header.html` | Form header layouts |
| `macros_form_detail.html` | Form detail sections |

---

## Appendix B: Color Palette Reference

### Brand Colors
```
Primary:       #1a6473  ██████
Primary Dark:  #135260  ██████
Primary Light: #e6f3f5  ██████
```

### Semantic Colors (Buttons)
```
Info:     #185FA5  ██████
Success:  #166534  ██████
Warning:  #b45309  ██████
Danger:   #c0392b  ██████
```

### Neutrals
```
Background:   #f8f9fa  ██████
Surface:      #ffffff  ██████
Border:       #e2e8f0  ██████
Border Light: #f0f2f5  ██████
Text:         #1a2a2a  ██████
Text Muted:   #6b7280  ██████
```

### Status Colors
```
Draft:      #f0f0f0  ██████
Submitted:  #d4edda  ██████
Approved:   #d4edda  ██████
Cancelled:  #faece7  ██████
```

### Icon Backgrounds
```
Blue:   #e6f3f5  ██████
Green:  #e6f3f0  ██████
Purple: #eeedfe  ██████
Coral:  #faece7  ██████
Amber:  #faeeda  ██████
Rose:   #fce7f3  ██████
Red:    #fee2e2  ██████
Slate:  #f1f5f9  ██████
```

---

**End of Report**

*This audit was generated by analyzing 100+ template files, CSS stylesheets, and embedded style blocks across the entire application. All file paths and line numbers are accurate as of 2026-05-24.*
