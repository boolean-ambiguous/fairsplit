# Tasks: add-design-system

## Styles

- [x] 1.1 Rewrite `app/static/style.css`: `:root` token set, `@media (prefers-color-scheme: dark)` override block
- [x] 1.2 `.btn`, `.field-row`, `.fieldset-plain`, `.legend`, `.badge-positive/negative/muted`, `.share-input` + `.is-visible` classes with `:hover`/`:focus-visible` states

## Templates

- [x] 2.1 `<meta name="color-scheme" content="light dark">` in `base.html`
- [x] 2.2 Remove all inline `style="..."` attributes from `_expenses.html`, replace with the new classes
- [x] 2.3 Swap `.positive/.negative/.muted` usages for `.badge-*` where they denote balance status

## Tests

- [x] 3.1 `tests/test_design_system.py`: WCAG contrast formula implemented locally; parse tokens from `style.css`; assert every (text, background) pair in both themes ≥ 4.5:1
- [x] 3.2 Assert `:root` declares the full minimum token set; assert a dark media block redefines every color token
- [x] 3.3 Assert every rendered page/partial has zero `style="` occurrences
- [x] 3.4 Assert `color-scheme` meta tag present; assert `:focus-visible` rule exists in the stylesheet
- [x] 3.5 Full existing suite (71 tests) still passes unchanged

## Verification

- [x] 4.1 Browser check: light and dark rendering (emulate `prefers-color-scheme`), screenshot both
