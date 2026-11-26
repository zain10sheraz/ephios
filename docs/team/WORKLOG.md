# Worklog (actual effort, for estimate-vs-actual comparison)

| Date | Area | Activity | Approx. actual effort (h) |
|---|---|---|---|
| 2026-11-23 | Zain / setup | repo inspection, install, seed/reset, run app | 1.0 |
| 2026-11-23 | Zain / white-box | unit tests BR1-BR4, coverage to 100 %, MCC/MC-DC, DEFECT-001 | 2.5 |
| 2026-11-23 | Zain / static analysis | SonarQube (Docker memory problems, 2 runs), complexity | 2.5 |
| 2026-11-23/24 | Zain / mutation | Cosmic Ray setup, 3 custom operators, 3 modules run (415 mutants), 52 survivors analysed, killer tests | 4.0 |
| 2026-11-24 | Zain / mutation round 2 | killer tests for stats.py, survivors-only rerun of 92 mutants, analysis table | 2.0 |
| 2026-11-24 | Zain / CI runs | DEFECT-001 fix branch, PR #2 (red then green), demo PR #3 (blocked), branch protection, Sonar smell cleanup, ruff cleanup | 2.5 |
| 2026-11-24 | Zain / CI | quality-gate workflow + check scripts (not yet run on GitHub) | 1.0 |
| 2026-11-24 | Shared | risk register + exit criteria draft | 0.5 |

Efforts are approximate (reconstructed from session time) and will be marked as such in the report.
| 2026-11-24 | Zain / WF1 unit tests | forms and models tests, 100 % on 2 more modules, DEFECT-002 found | 2.0 |
| 2026-11-24 | Zain / DEFECT-002 | live probe, fix, PR #5 with 2 real Sonar blocks, merge | 2.0 (incl. ~0.5 h GitHub outage) |
| 2026-11-24 | Shared docs | RCA, test plan, RTM, progress report | 1.5 |
| 2026-11-24 | Zain / complete MCC-MC/DC | enumerate decisions, tables, 17 tests | 1.5 |
| 2026-11-24 | Zain / signup-path HTTP tests + coverage scope | 11 modules to 100 %, fallbacks, scope document | 4.0 (incl. long stalls from memory pressure) |
| 2026-11-24 | Zain / WF1 HTTP tests, cross-workflow tests | 32 + 29 + 6 tests; DEFECT-003/004 found, fixed, PR #8 | 3.5 |
| 2026-11-26 | Manan / OpenAPI + generator | spec of 14 operations, EP/BVA generator, regeneration demo | 2.0 (approximate) |
| 2026-11-26 | Manan / API test harness and tests | real-server harness, 462 tests, 29 first-run failures analysed and corrected, post-conditions | 5.0 (approximate, includes long server runs) |
| 2026-11-26 | Manan / API docs, issues #12-#14, coverage | `API_TESTING.md`, viva notes, coverage script | 1.5 (approximate) |
| 2026-11-26 | Manan / follow-up tests | REST filters, concurrency, combined invalid values, state transitions (14 tests), rerun 476 passed | 2.0 (approximate, includes a 14 min suite run) |
