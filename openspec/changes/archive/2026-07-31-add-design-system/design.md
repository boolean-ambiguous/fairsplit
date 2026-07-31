# Design: add-design-system

## Context

Four feature changes accreted styling in `style.css` and a handful of inline `style="..."` attributes in `_expenses.html` (fieldset reset, legend size, checkbox-row layout, hidden/visible share inputs). This change formalizes what's there rather than restyling from scratch, and removes the inline styles by giving each of those one-off needs a real class.

## Decisions

### Token values

Verified computationally against WCAG's relative-luminance formula before being adopted — every text/background pairing in the minimum set clears 4.5:1 in both themes (light: 4.68–15.8:1; dark: 6.69–15.4:1).

```
Light                          Dark
--color-bg:        #f7f7f5     #0f1115
--color-surface:   #ffffff     #1a1d23
--color-ink:       #1f2328     #e8e8e6
--color-muted:     #57606a     #9aa4b2
--color-accent:    #0f766e     #5eead4
--color-accent-ink:#ffffff     #08201d
--color-positive:  #15803d     #4ade80
--color-negative:  #b91c1c     #fca5a5
--color-border:    #e5e7eb     #2a2f3a
--space-1..4:      0.25/0.5/1/1.5rem   (unchanged both themes)
--radius:          8px                 (unchanged both themes)
```

`--color-accent-ink` swaps light-on-dark in dark mode because the accent itself flips from a dark teal (needs white text) to a light teal (needs dark text) — same role, different value, which is exactly what tokens are for.

### Contrast as a computed test, not a manual check

`tests/test_design_system.py` implements the WCAG relative-luminance/contrast formula directly (no new dependency) and parses `:root` and the dark media block out of `style.css` with a small regex, so the test fails the moment anyone edits a color without checking contrast — the same "verify the property, don't eyeball it" approach as the balance zero-sum and settlement bound tests from earlier changes.

### Replacing inline styles with classes

- `fieldset[style="border:none;padding:0;margin:0"]` → `.fieldset-plain`
- `legend[style="font-size:0.85rem"]` → reuse `.muted` (already a class) plus new `.legend` for sizing
- `label[style="flex-direction:row;align-items:center"]` → `.field-row`
- `input[style="display:none;width:5.5rem"]` → `.share-input` (already a class; give it the width and a default `display:none`) toggled visible via a `.is-visible` class instead of inline `style.display`, flipped by the existing `onchange` handler (unchanged, since it's behavior not styling)

### Component classes

`.btn` (buttons), `.field` (label+input group, already implicit via `label > input/select`), `.badge-positive/negative/muted` (balance amounts — replaces the existing bare `.positive/.negative/.muted` utility classes with the same visual result but a documented component name), each with `:hover`/`:focus-visible` states defined once in the stylesheet rather than per-element.

## Risks / Trade-offs

- No visual regression tooling (no Percy/Chromatic) — a Playwright screenshot pass after implementation is the manual check, same as previous changes' browser verification step.
