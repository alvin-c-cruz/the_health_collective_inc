# The Health Collective Inc. - Claude Development Guide

This guide contains instructions for AI assistants (Claude) working on this codebase.

---

## Design System

### **Rule: All UI must use design system tokens**

Before creating or modifying any UI, read [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md). All UI must use the tokens defined there — **no hardcoded colors, font sizes, spacing values, or radii**. Use semantic token names (e.g. `bg-surface`, not `bg-white`).

**Examples:**

✅ **Good** - Using design tokens:
```html
<div style="background: var(--thc-bg-surface); padding: var(--thc-padding-card);
            border-radius: var(--thc-radius-xl); box-shadow: var(--thc-shadow-sm);">
```

❌ **Bad** - Hardcoded values:
```html
<div style="background: #ffffff; padding: 24px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
```

✅ **Good** - Using utility classes:
```html
<div class="bg-surface rounded-xl shadow-sm">
```

### **Rule: No one-off styles**

If a needed pattern doesn't exist in the design system, **stop and propose an addition to `DESIGN_SYSTEM.md` before implementing it**. Do not invent one-off styles.

**Process:**
1. Check `DESIGN_SYSTEM.md` for existing tokens
2. Check `DESIGN_TOKENS_USAGE.md` for usage examples
3. If pattern doesn't exist, ask the user to approve adding it to the design system
4. Once approved, document the new token/pattern
5. Then implement it

### **Reference Implementation**

Use `application/blueprints/dashboard/pages/dashboard/home.html` as the canonical example of layout density, spacing rhythm, and component composition. New pages should feel like they belong next to it.

**What to match:**
- Layout density (how much content per screen)
- Spacing rhythm (vertical spacing between sections)
- Component composition (how elements are grouped)
- Visual hierarchy (heading sizes, emphasis)
- Interactive patterns (hover states, transitions)

---

## When Building UI

### **1. Reuse Existing Components**

**Always check `application/templates/components/` for existing reusable components before creating new ones.**

**Before creating a new component, check:**
- `application/templates/components/` - **Reusable UI components (CHECK HERE FIRST)**
- `application/templates/` - Base templates and macros
- `application/templates/macros_button.html` - Button macros
- `application/templates/macros_simple_form.html` - Form field macros
- `application/templates/macros_form_header.html` - Form header layouts
- `application/templates/macros_form_detail.html` - Form detail sections
- Blueprint-specific templates in `application/blueprints/*/pages/`

### **2. Create Reusable Components**

If you create a new component, place it in `application/templates/components/` and make it **reusable, not page-specific**.

**Component Guidelines:**
- Make it generic and configurable via parameters
- Use Jinja2 macros for reusable UI components
- Accept design tokens as parameters (don't hardcode)
- Document parameters and usage examples
- Follow existing macro patterns in `application/templates/macros_*.html`

**Example of a good reusable component:**
```jinja2
{% macro card(title, variant="default", size="md") %}
<div class="card card-{{ size }}{% if variant != 'default' %} card-{{ variant }}{% endif %}">
  {% if title %}
  <div class="card-header">{{ title }}</div>
  {% endif %}
  <div class="card-body">
    {{ caller() }}
  </div>
</div>
{% endmacro %}
```

### **3. Match Existing Patterns**

Match the existing patterns for **loading states, empty states, and error states**.

**Loading States:**
```html
<!-- Example: Check existing templates for spinner/loading patterns -->
<div class="loading-spinner">
  <i class="bi bi-hourglass-split"></i> Loading...
</div>
```

**Empty States:**
```html
<!-- Example: Check existing templates for empty state patterns -->
<div class="text-center text-muted py-4">
  No records found.
</div>
```

**Error States:**
```html
<!-- Example: Check existing templates for error patterns -->
<div class="alert alert-danger">
  {{ error_message }}
</div>
```

---

## Technology Stack Reference

This is a Flask application with:
- **Backend**: Flask 3.1.0, SQLAlchemy 2.0.36, Flask-Migrate 4.1.0
- **Frontend**: Bootstrap 5 (local), Bootstrap Icons, Jinja2 templates
- **Fonts**: Playfair Display (headings), Inter (body), DM Mono (numbers)
- **Styling**: CSS variables (design system tokens) + utility classes
- **Database**: SQLite (`the_health_collective_inc.db`)

See [`CLAUDE.md`](CLAUDE.md) in the original instructions for detailed architecture notes.

---

## Key Conventions

### Typography
```css
/* Use semantic tokens */
font-size: var(--thc-body-size);      /* 14px - body text */
font-size: var(--thc-h2-size);        /* 24px - section headings */
font-size: var(--thc-label-size);     /* 12px - labels */
font-family: var(--thc-font-body);    /* Inter */
font-family: var(--thc-font-mono);    /* DM Mono - for numbers */
```

### Colors
```css
/* Use semantic aliases */
background: var(--thc-bg-surface);      /* White - cards */
color: var(--thc-text-primary);         /* Dark gray - main text */
color: var(--thc-text-secondary);       /* Medium gray - muted text */
border-color: var(--thc-border-default);/* Light gray - borders */

/* Use semantic color scales */
background: var(--thc-primary-600);     /* Brand color */
background: var(--thc-success-600);     /* Green - approvals */
background: var(--thc-danger-600);      /* Red - destructive */
```

### Spacing
```css
/* Use spacing scale (4px grid) */
padding: var(--thc-padding-card);       /* 24px - cards */
padding: var(--thc-padding-button);     /* 8px 20px - buttons */
gap: var(--thc-gap-md);                 /* 12px - flexbox/grid gaps */
margin-bottom: var(--thc-stack-md);     /* 20px - vertical spacing */
```

### Components
```css
/* Buttons */
.btn-primary {
  background: var(--thc-primary-600);
  padding: var(--thc-padding-button);
  border-radius: var(--thc-radius-md);
}

/* Cards */
.card {
  background: var(--thc-bg-surface);
  border: 1px solid var(--thc-border-default);
  border-radius: var(--thc-radius-xl);
  padding: var(--thc-padding-card);
  box-shadow: var(--thc-shadow-sm);
}

/* Forms */
.form-control {
  padding: var(--thc-padding-input);
  border: 1px solid var(--thc-border-strong);
  border-radius: var(--thc-radius-md);
}
```

---

## Documentation References

- **[`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md)** - Complete design system specification
- **[`DESIGN_TOKENS_USAGE.md`](DESIGN_TOKENS_USAGE.md)** - How to use design tokens
- **[`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md)** - Token implementation status
- **[`docs/ui-audit.md`](docs/ui-audit.md)** - Original UI audit
- **`application/static/css/design-system.css`** - Token definitions (source of truth)
- **`application/static/css/design-system-test.html`** - Visual token reference

---

## Checklist for New UI

Before submitting UI changes, verify:

- [ ] All colors use design system tokens (no hex values)
- [ ] All spacing uses design system tokens (no arbitrary px/rem)
- [ ] All font sizes use design system tokens
- [ ] All border radius uses design system tokens
- [ ] All shadows use design system tokens
- [ ] Reused existing components where possible
- [ ] New components are generic and reusable
- [ ] Matches existing patterns for loading/empty/error states
- [ ] Matches reference implementation for visual consistency
- [ ] Responsive on mobile (uses Bootstrap breakpoints)
- [ ] Accessible (proper contrast, focus states)

---

## Common Mistakes to Avoid

❌ **Don't**: Use arbitrary spacing
```html
<div style="padding: 18px; margin-bottom: 22px;">
```

✅ **Do**: Use spacing tokens
```html
<div style="padding: var(--thc-space-5); margin-bottom: var(--thc-stack-md);">
```

---

❌ **Don't**: Hardcode colors
```html
<button style="background: #1a6473; color: white;">
```

✅ **Do**: Use color tokens
```html
<button style="background: var(--thc-primary-600); color: var(--thc-text-inverse);">
```

---

❌ **Don't**: Mix units inconsistently
```html
<div style="padding: 16px 1rem; gap: 12px;">
```

✅ **Do**: Use consistent tokens
```html
<div style="padding: var(--thc-space-4); gap: var(--thc-gap-md);">
```

---

❌ **Don't**: Create page-specific components
```jinja2
{% macro dashboard_metric_card_only_for_home_page() %}
```

✅ **Do**: Create generic reusable components
```jinja2
{% macro metric_card(label, value, icon=None, variant="default") %}
```

---

## Questions?

- Check `DESIGN_TOKENS_USAGE.md` for token examples
- View `design-system-test.html` for visual reference
- Ask the user if you need clarification on design patterns
- Propose additions to the design system if patterns are missing

---

**Last Updated**: 2026-05-24
**Design System Version**: 2.0
