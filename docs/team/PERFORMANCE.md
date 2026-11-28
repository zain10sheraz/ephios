# Performance (k6) and recovery (area 3)

## 1. Operation, limits and justification (set BEFORE testing)
* **Operation:** `GET /api/events/` - the event list a volunteer's client reads before signing up (WF1 data used by WF2). It touches the shared Event/Shift records and is the most frequently repeated read of the two workflows. Logged-in volunteer session (cookie), seeded database.
* **p95 response-time limit: 800 ms.** Interactive responses under about 1 s keep the user's flow of thought (Nielsen); 200 ms of margin is kept for a development server on a laptop with the load generator on the same machine. The median is not used because slow outliers are what users notice.
* **Failure limit: < 1 % failed requests.** A shift-planning tool for a medical service is not safety critical for reads, but a user must be able to rely on 99 % of reads; a failure is any non-2xx/3xx response or connection error (k6 `http_req_failed`).
* Script: `scripts/k6_events_list.js` (the thresholds are in the script and fail the run when broken). Tool: k6 v2.4.0.

## 1b. Second workload: signup (write), own limits (added in the course review, not yet run)

The review noted that one limit was used for both workloads and that signup under load was never measured. The two workloads
have different cost and different consequences, so each gets its own limits, **fixed here before the first signup run**:

| Workload | Operation | p95 limit | Failure limit | Why | Script | Status |
|---|---|---|---|---|---|---|
| Read | `GET /api/events/` (event list) | 800 ms | < 1 % | repeated read, user waits for a page | `scripts/k6_events_list.js` | **run**, limits met (sections 3 and 4b) |
| Write | `POST /shifts/<id>/signup/` (sign up and decline alternating) | **500 ms** at 5 users (the register's EC-04) | **< 1 %**; HTTP 5xx and connection errors count, so SQLite's `database is locked` is visible | a write the volunteer waits for after pressing the button; it must also not lose or duplicate data | `scripts/k6_signup.js` | **run 2026-11-28**: 1 user met, 5 users NOT met (section 1c) |

How the signup run is done: start `scripts/serve_seeded.py`, then `k6 run -e BASE=... -e SHIFT=1 -e VUS=1|5 -e DURATION=60s
scripts/k6_signup.js`, each setup twice, 60 s per run, like the read workload. Two accounts share the 5 users, so
concurrent writes of the same account also exercise the rejection path (302 as well). After the run, read the
participation count back (one record per volunteer) to confirm no duplicate (this read-back was **not** done in the first run).

## 1c. Result of the signup workload (run 2026-11-28, `reports/performance/k6_signup_vus*_run*.json` and `.txt`)

Same machine and the same freshly started seeded server for all four runs (Django `runserver`, SQLite, k6 on the same laptop,
60 s per run). Values are for the tagged signup POST (`http_req_duration{name:signup_post}`); a failed request is anything
other than 200/302.

| VUs | run | signup requests | avg ms | p95 ms | failed % | limits (p95 < 500 ms, < 1 %) |
|---|---|---|---|---|---|---|
| 1 | 1 | 715 | 83 | 138 | 0.00 | met |
| 1 | 2 | 1,039 | 57 | 114 | 0.00 | met |
| 5 | 1 | 824 | 366 | 757 | **27.30** | **NOT met** (both limits) |
| 5 | 2 | 679 | 442 | 1,020 | **28.57** | **NOT met** (both limits) |

Cause of the failures, read from the server log (`server.log` of the run): every failed request is HTTP 500 with
`sqlite3.OperationalError: database is locked` (419 such responses in the log of the whole session, all 5xx). SQLite lets one
writer at a time; with 5 virtual users writing continuously, the writers collide. This is the same behaviour that
`API_TESTING.md` section 6 recorded with two simultaneous signups; the load test shows it at a rate of about 28 %. It is a
property of the test environment (development server and SQLite), not proof of a defect in the signup rules, but it is also not
something to hide: **EC-04 is measured and NOT met in this environment.** Not measured: PostgreSQL/MySQL (the production
databases), where a rerun is the next step; and the data integrity after the 500s (participation read-back not done).
At 1 user the write is fast (p95 114-138 ms in the runs above), so a single volunteer is not affected. The member's own 1-user run on a quiet machine (screenshot `EV-079`, no JSON export) gave p95 45.56 ms, 0.00 % failed, 1,722 requests; as in section 4b the absolute numbers depend strongly on machine load.

The member's own 5-user run (screenshot `EV-079b`, same server and script): **p95 410.32 ms (limit 500 ms met), but 22.33 % of the signup requests failed (297 of 1,330; limit 1 % NOT met)**; the p95 of the successful responses alone was 234.83 ms. So on a quiet machine the time limit can be met while the failure limit is still broken: the failures come from the SQLite write lock, not from slowness. Overall verdict for the 5-user workload in all three runs: **failure limit not met, so EC-04 is not met**.

## 2. Method
1 virtual user and 5 virtual users, **each configuration twice, 60 s per run** (4 runs, one after the other, no other load on the machine). Each virtual user repeats the request in a loop without think time (a worst-case, closed-loop load). Login once in `setup()`.
Environment: Windows 11 laptop, 7.7 GB RAM, Django `runserver` (development server), SQLite, 16 events and 15 shifts in the database (small data set: with more data the list would be slower); k6 on the same machine. Results are therefore **relative indicators for this environment**, not production capacity.

## 3. Results (`reports/performance/k6_vus*_run*.json`, summary `k6_summary.md`)

| VUs | run | requests | req/s | avg ms | p95 ms | max ms | failed % | limits |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 903 | 14.1 | 71 | 104 | 3742 | 0.00 | met |
| 1 | 2 | 902 | 13.9 | 72 | 99 | 4849 | 0.00 | met |
| 5 | 1 | 998 | 15.5 | 305 | 506 | 3961 | 0.00 | met |
| 5 | 2 | 958 | 14.6 | 319 | 505 | 5146 | 0.00 | met |

Comparison with the limits: p95 is 99-104 ms with 1 user (13 % of the limit) and 505-506 ms with 5 users (63 % of the limit); failures are 0 % in every run. **Both limits are met.**

## 4. Observations (not defects)
* **Throughput does not scale:** about 14-15 requests/s whatever the number of users, and the average response time grows about 4.3 times when users go from 1 to 5. The development server handles the requests essentially one at a time (SQLite and the single process), so adding users only adds waiting time. On these first runs the 800 ms limit would be reached at roughly 8-9 simultaneous users (linear extrapolation, **not measured**); the second set of runs below shows far more headroom, so this extrapolation is only valid for a memory-starved machine.
* **Slow outliers:** the maximum is 3.7-5.1 s in every run while p95 is below 0.5 s, so fewer than 5 % of requests are slow. The cause was not investigated (a cold first request after login is a plausible but unverified explanation).
* No performance defect was raised because the limits set beforehand (p95 < 800 ms, < 1 % failures) were met in every run. EC-04 of the risk register (signup, p95 <= 500 ms at 5 users) is **not demonstrated**: the measured operation was the event list, not signup (`RISK_REGISTER.md`, `TEST_COMPLETION_REPORT.md`).

## 4b. Second set of runs on a quiet machine (the member's own runs, screenshots `EV-046`, `EV-046b`)
After closing other applications, the member ran the same script again, one run for each setup, with `scripts/evidence_walkthrough.ps1` (60 s per run, same limits, a freshly started seeded server). These runs have no JSON export; the values below are read from the screenshots.

| VUs | requests | req/s | avg ms | p95 ms | max | failed % | limits |
|---|---|---|---|---|---|---|---|
| 1 | 4000 | 64.2 | 13.45 | 17.8 | 2.2 s | 0.00 | met |
| 5 | 4177 | 67.0 | 72.29 | 115.04 | 2.22 s | 0.00 | met |

Reading: the limits are met again, and **the absolute numbers are about 5 times better than in the first set** (p95 17.8 ms against 99-104 ms with 1 user; 115 ms against 505-506 ms with 5 users; 64-67 requests/s against 14-15). The operation, the code and the limits are the same; what differs is the state of the laptop (the first runs were taken while it had about 600 MB of free memory and Docker running; the cause was not isolated, so this explanation is a likely one, not a proof). The finding that **throughput does not grow with the number of users** holds in both sets (64.2 against 67.0 requests/s, a factor of 1.04), and the average response time grows 5.4 times from 1 to 5 users (13.45 to 72.29 ms). Lesson for the report: single p95 values of this kind depend strongly on machine load, so the limits and the conclusions must be read together with the environment.

## 5. Failure and recovery (S11)
The brief asks for the recovery test to run with the API or integration test runner: `tests/team/api/test_failure_recovery_api.py` (pytest + Requests, real server) makes the database file read-only, sends the signup (HTTP 5xx), reads the persisted state back (row count and REST unchanged), restores the file, retries (302, exactly one CONFIRMED record) and retries once more (still one record). The same scenario is also automated in the browser, `tests/team/e2e/test_failure_recovery.py`:
1. the volunteer opens the event page; 2. the database file is made read-only (the storage dependency fails before the write can complete); 3. the volunteer clicks "sign up": the application cannot write, the user is not told that it worked, and the stored state is read back unchanged (participation count identical, none for the user); 4. the database is restored; 5. the volunteer retries: the signup succeeds and the final state is exactly one participation, CONFIRMED, **no duplicate**.
Result: pass. Limit: the failure is simulated with a read-only SQLite file; other dependency failures (mail server, a second database server) were not simulated.
