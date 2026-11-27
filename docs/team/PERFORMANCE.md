# Performance (k6) and recovery (area 3)

## 1. Operation, limits and justification (set BEFORE testing)
* **Operation:** `GET /api/events/` - the event list a volunteer's client reads before signing up (WF1 data used by WF2). It touches the shared Event/Shift records and is the most frequently repeated read of the two workflows. Logged-in volunteer session (cookie), seeded database.
* **p95 response-time limit: 800 ms.** Interactive responses under about 1 s keep the user's flow of thought (Nielsen); 200 ms of margin is kept for a development server on a laptop with the load generator on the same machine. The median is not used because slow outliers are what users notice.
* **Failure limit: < 1 % failed requests.** A shift-planning tool for a medical service is not safety critical for reads, but a user must be able to rely on 99 % of reads; a failure is any non-2xx/3xx response or connection error (k6 `http_req_failed`).
* Script: `scripts/k6_events_list.js` (the thresholds are in the script and fail the run when broken). Tool: k6 v2.4.0.

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
* **Throughput does not scale:** about 14-15 requests/s whatever the number of users, and the average response time grows about 4.3 times when users go from 1 to 5. The development server handles the requests essentially one at a time (SQLite and the single process), so adding users only adds waiting time. The 800 ms limit would be reached at roughly 8-9 simultaneous users on this setup (linear extrapolation, **not measured**).
* **Slow outliers:** the maximum is 3.7-5.1 s in every run while p95 is below 0.5 s, so fewer than 5 % of requests are slow. The cause was not investigated (a cold first request after login is a plausible but unverified explanation).
* No performance defect was raised because the limits set beforehand were met; EC-04 of the risk register (performance) is therefore **met for this operation in this environment**, with the limits above.

## 5. Failure and recovery (S11)
Test `tests/team/e2e/test_failure_recovery.py` (real browser, real server):
1. the volunteer opens the event page; 2. the database file is made read-only (the storage dependency fails before the write can complete); 3. the volunteer clicks "sign up": the application cannot write, the user is not told that it worked, and the stored state is read back unchanged (participation count identical, none for the user); 4. the database is restored; 5. the volunteer retries: the signup succeeds and the final state is exactly one participation, CONFIRMED, **no duplicate**.
Result: pass. Limit: the failure is simulated with a read-only SQLite file; other dependency failures (mail server, a second database server) were not simulated.
