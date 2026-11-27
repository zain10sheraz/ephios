# Usability and accessibility (area 3)

Screens tested (the key screen of each use case, logged in). The six use cases of the team share four key screens: **UC1 and UC3** the shift form `/shifts/<id>/edit/` (planner), **UC2 and UC4** the event page with the signup buttons (volunteer), **UC5** the shift deletion confirmation page `/shifts/<id>/delete/` (planner), **UC6** the customize-signup-times page `/shifts/<id>/signup/` (volunteer).
Tools: Lighthouse 13.6.0 (accessibility, best practices, SEO; `scripts/run_lighthouse.py`, logged in through a session cookie) and a full axe-core 4.14.0 scan with **`@axe-core/playwright`** (npm, Node Playwright; `scripts/axe_scan.mjs`, which logs in through the real login form and scans the key screen of each use case).
An issue found by both tools is counted once: Lighthouse's accessibility audits are axe-core rules, so issues are merged by rule id (`scripts/compare_accessibility.py` -> `reports/accessibility/comparison.md`).
All numbers below come from the saved reports in `reports/accessibility/`.

## 1. Usability tests (Playwright, `tests/team/e2e/test_usability_keyboard.py`)
| Test | What it does | Result |
|---|---|---|
| WF1 | planner opens the shift form, enters a meeting time **after** the start time, saves; the page must say what is wrong; correct the value; save | error "Meeting time must not be after start time!" names the field and the rule, the entered values are kept, the correction succeeds with the banner "...has been saved" (pass) |
| WF2 | volunteer opens the event page, clicks sign up | banner "You have successfully signed up for ..." (pass) |
| Keyboard (WF1 form) | focus is placed on the first required field and Tab is pressed until the submit button; then Enter | focus reaches date, meeting time, start time, end time in document order, then "Save event"; Enter submits and the success banner appears (pass) |

Usability finding (not an accessibility rule): when a click is rejected by a server rule from a page that was already open (shift filled up, window closed, second tab), the page shows only **"This action is not allowed."** without the reason, while a fresh page shows the reason ("The maximum number of participants is reached."). Reported as an issue (message does not say what to do).

## 2. Findings (axe-core + Lighthouse, each issue once)
| ID | Rule | Impact | Element(s) | User impact | Proposed fix | Status |
|---|---|---|---|---|---|---|
| A11Y-1 | `select-name` | critical | `#id_signup_flow_slug`, `#id_structure_slug` (shift form) | a screen reader announces a combobox without a name; the user cannot tell what the choice is for | give the selects an accessible name (`aria-label`) | **fixed** (before: 2 elements, after: 0) |
| A11Y-2 | `label` | critical | `#id_signup_until_0`, `#id_signup_until_1` (signup deadline date and time) | the two inputs are announced as unnamed edit fields | `aria-label` "Date" / "Time" on the shared split date/time widget | **fixed** (2 -> 0) |
| A11Y-3 | `color-contrast` | serious | shift form 6 elements, e.g. `#id_label_helptext`; event page 5 elements, e.g. `.card-text > p`, `9 a.m. Meetup` | low-vision users cannot read grey secondary text (below 4.5:1) | darken `text-body-secondary` to at least 4.5:1 | open (issue) |
| A11Y-4 | `aria-input-field-name` | serious | `.select2-selection` (qualification multi-select) | combobox without a name | pass an accessible name to the Select2 widget | open (issue) |
| A11Y-5 | `tabindex` | serious | `#signup-form-3 > .d-inline-block` (event page, wrapper of the signup button has `tabindex="1"`) | tab order jumps; positive tabindex breaks the natural order for keyboard users | remove the positive tabindex (use 0 or none) | open (issue) |
| A11Y-6 | `heading-order` | moderate | `.card-title` (shift form), `.card-subtitle` (event page) | headings skip a level; screen reader navigation by headings is confusing | use the correct heading level or a styled non-heading | open (issue) |
| A11Y-7 | `aria-allowed-role` | minor | `textarea` inside the Select2 search | invalid ARIA role on a third-party widget element | upstream widget; report or override | open (not reported separately) |
| A11Y-8 | `aria-dialog-name` | (Lighthouse only) | 1 dialog element | an unnamed dialog | add `aria-label`/`aria-labelledby` | open (not reported separately) |

### Additional key screens (one measurement, not fixed)
| Screen | Lighthouse accessibility / best practices / SEO | axe-core violated rules | Findings |
|---|---|---|---|
| UC5 shift deletion confirmation | 90 / 100 / 91 | `color-contrast` (1 element, `.text-body-secondary`) | same cause as A11Y-3 (issue #18); Lighthouse also lists `aria-dialog-name` and `heading-order` (1 element each, not reported by axe) |
| UC6 customize signup times | 90 / 100 / 91 | `color-contrast` (1 element, `.text-body-secondary`) | same cause as A11Y-3 (issue #18); Lighthouse also lists `aria-dialog-name` and `heading-order` |

## 3. Before and after (one screen fixed: the UC1 shift form)
Fix (source of the MIS, `src/ephios/core/forms/events.py`, `src/ephios/extra/widgets.py`): accessible names for the two selects and the split date/time inputs.
| Screen / tool | Before | After |
|---|---|---|
| UC1 shift form, Lighthouse accessibility score | **80** | **89** |
| UC1 shift form, axe violated rules | 6 (`aria-allowed-role`, `aria-input-field-name`, `color-contrast`, `heading-order`, `label`, `select-name`) | **4** (`label` and `select-name`, both critical, gone) |
| UC2 event page, Lighthouse accessibility score | 86 | 86 (not changed, not in scope of the fix) |
| Lighthouse best practices / SEO (both screens) | 100 / 91 | 100 / 91 |
Regression test `tests/team/e2e/test_accessible_names.py` (Playwright accessible-name assertion on the four controls): **4 of 4 fail before** the fix (run on a worktree of the commit before the fix, `reports/accessibility/regression_before_fix.txt`), **4 of 4 pass after** (`reports/accessibility/regression_after_fix.txt`). The related unit tests (83) still pass.

## 4. Limits
Automated tools find only part of the accessibility problems (axe-core reports about 30-40 % of WCAG issues at best); no manual screen-reader test was done. Lighthouse ran on the logged-in pages through a session cookie. Colour contrast was measured on the rendered default theme only.
Screenshots of the tool results must be taken by the team member himself (course rule); the reports are in `reports/accessibility/`.
