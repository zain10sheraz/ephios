# Accessibility: before and after (axe-core + Lighthouse, issues found by both counted once)

## uc1_shift_form

| Tool | Phase | Accessibility | Best practices | SEO |
|---|---|---|---|---|
| Lighthouse | before | 80 | 100 | 91 |
| Lighthouse | after | 89 | 100 | 91 |

| Rule | Impact | Found by | Elements before | Elements after | Example element |
|---|---|---|---|---|---|
| aria-allowed-role | minor | axe | 1 | 1 | `['textarea']` |
| aria-dialog-name | - | Lighthouse | 1 | 1 | `-` |
| aria-input-field-name | serious | axe + Lighthouse | 1 | 1 | `['.select2-selection']` |
| color-contrast | serious | axe + Lighthouse | 6 | 6 | `['#id_label_helptext']` |
| heading-order | moderate | axe + Lighthouse | 1 | 1 | `['.card-title']` |
| label | critical | axe + Lighthouse | 2 | 0 | `['#id_signup_until_0']` |
| select-name | critical | axe + Lighthouse | 2 | 0 | `['#id_signup_flow_slug']` |

## uc2_event_page

| Tool | Phase | Accessibility | Best practices | SEO |
|---|---|---|---|---|
| Lighthouse | after | 86 | 100 | 91 |

| Rule | Impact | Found by | Elements before | Elements after | Example element |
|---|---|---|---|---|---|
| aria-dialog-name | - | Lighthouse | - (not fixed, single measurement) | 1 | `-` |
| color-contrast | serious | axe + Lighthouse | - (not fixed, single measurement) | 5 | `['small:nth-child(4) > .d-inline-block']` |
| heading-order | moderate | axe + Lighthouse | - (not fixed, single measurement) | 1 | `['.card-subtitle']` |
| tabindex | serious | axe + Lighthouse | - (not fixed, single measurement) | 1 | `['#signup-form-2 > .d-inline-block']` |

## uc5_shift_delete

| Tool | Phase | Accessibility | Best practices | SEO |
|---|---|---|---|---|
| Lighthouse | after | 90 | 100 | 91 |

| Rule | Impact | Found by | Elements before | Elements after | Example element |
|---|---|---|---|---|---|
| aria-dialog-name | - | Lighthouse | - (not fixed, single measurement) | 1 | `-` |
| color-contrast | serious | axe + Lighthouse | - (not fixed, single measurement) | 1 | `['.text-body-secondary']` |
| heading-order | - | Lighthouse | - (not fixed, single measurement) | 1 | `-` |

## uc6_customize_page

| Tool | Phase | Accessibility | Best practices | SEO |
|---|---|---|---|---|
| Lighthouse | after | 90 | 100 | 91 |

| Rule | Impact | Found by | Elements before | Elements after | Example element |
|---|---|---|---|---|---|
| aria-dialog-name | - | Lighthouse | - (not fixed, single measurement) | 1 | `-` |
| color-contrast | serious | axe + Lighthouse | - (not fixed, single measurement) | 1 | `['.text-body-secondary']` |
| heading-order | - | Lighthouse | - (not fixed, single measurement) | 1 | `-` |

