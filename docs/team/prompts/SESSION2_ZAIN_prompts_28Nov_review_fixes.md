# Prompts typed by Zain in the second session (28 Nov 2026): course-review fixes, screenshots, evidence, PDF and ZIP (exported while the session was still running)

Exported with scripts/export_prompts.py from a session of 35 prompts; this file has 35 (numbers 1-35), unchanged.

## Prompt 1 (2026-11-28T15:22:21.552Z)

````text
in this repo there needs to be some chamges in the report  , here is what changes we wantIssues in our SQE project submission

Must fix:
Broken tables: pages 32, 36, 39, 41, 42, 43, 50 and 52 show raw |---| text. Some rows in the AI-use record and worklog have also fallen out of their tables.
AI-use record: entries still say "to be reviewed", and I found no saved prompts. The manual requires every AI output to be checked and the prompts kept.
CI merge blocking: only unit coverage, mutation and Sonar are required checks. api-tests-black-box and e2e-browser-tests don't block merging.
Risk matrix: the 5×5 likelihood × impact matrix is missing.
EC-02 contradiction: page 13 says "0 open defects → MET", but the completion report says 3 major defects (#18, #19, #20) are open.
Pareto incomplete: it is split into parts, one part says 14 defects instead of 16, and #25 and #26 are missing.
GQM metrics outdated: defect density and reopen rate cover only 4 of the 16 defects.


May cost marks:
Diagrams: the control-flow graph and fishbone analyses are text only.
API test counts: the documents say 462, 476 and 477 without a consistent figure.
Performance: one limit was set for both workloads instead of one for each. Signup under load was not measured, so EC-04 is not demonstrated.
Estimates: the area 1 estimates were written after the work.
Risk PR-08: the root cause analysis says likelihood rose from 3 to 5, but the register still shows 3.

Check before the viva :
Commit identity: 56 commits use the placeholder address zain@test.com.
Authorship: every member must have committed their own work and taken the screenshots credited to them.
Google Sheet: confirm the repository is registered in our section's tab. This couldn't be checked from the files.
Preparation: each member must be able to rerun a test and explain their area.
````

## Prompt 2 (2026-11-28T15:55:20.255Z)

````text
you can do that work from zain github account
````

## Prompt 3 (2026-11-28T15:56:40.869Z)

````text
yes do that, merge the pr as well
````

## Prompt 4 (2026-11-28T16:20:56.685Z)

````text
Authorship: both commits use the zain10sheraz identity and carry the Claude co-author line. dont add claude as author, also  help me atke ss , u guide ill take, 

<pasted_content id="007a">
Take a new PDF build from main and replace the old one (python scripts/build_report_pdf.py).
Zain takes a fresh screenshot of Settings > Branches for the evidence set.
Each member exports their prompts and fills in their sign-off row in AI_USE_RECORD.md.
Run scripts/k6_signup.js, then update EC-04 with the result.
</pasted_content id="007a">
````

## Prompt 5 (2026-11-28T16:28:52.301Z)

````text
help me take ss of ss 3 and 4, ss1 and 2 are here
````

## Prompt 6 (2026-11-28T16:28:52.301Z)

````text
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\1.png]
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\2.png]
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\3.png]
````

## Prompt 7 (2026-11-28T16:32:10.931Z)

````text
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\4.png]
````

## Prompt 8 (2026-11-28T16:36:25.167Z)

````text
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\5.png]
````

## Prompt 9 (2026-11-28T16:39:30.022Z)

````text
this aint wofking plz u do it fore me
````

## Prompt 10 (2026-11-28T16:39:30.022Z)

````text
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\6.png]
````

## Prompt 11 (2026-11-28T16:48:41.794Z)

````text
gimme login details now
````

## Prompt 12 (2026-11-28T16:50:21.134Z)

````text
im in app what now? logined as planner
````

## Prompt 13 (2026-11-28T16:54:53.820Z)

````text
i here whats next
````

## Prompt 14 (2026-11-28T16:54:53.820Z)

````text
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\7.png]
````

## Prompt 15 (2026-11-28T16:57:04.127Z)

````text
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\8.png]
````

## Prompt 16 (2026-11-28T17:00:21.971Z)

````text
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\9.png]
````

## Prompt 17 (2026-11-28T17:09:48.700Z)

````text
u merge Merging only needs your go-ahead. If you reply "merge #37", I'll merge it from Zain's account and then switch gh back to sajawalkhanfake. Otherwise you can merge it yourself on GitHub: https://github.com/zain10sheraz/ephios/pull/37
````

## Prompt 18 (2026-11-28T17:12:49.712Z)

````text
add new ss and update the pdf, first make sure all this is complete now 

<pasted_content id="007a">
Issues in our SQE project submission

Must fix:
Broken tables: pages 32, 36, 39, 41, 42, 43, 50 and 52 show raw |---| text. Some rows in the AI-use record and worklog have also fallen out of their tables.
AI-use record: entries still say "to be reviewed", and I found no saved prompts. The manual requires every AI output to be checked and the prompts kept.
CI merge blocking: only unit coverage, mutation and Sonar are required checks. api-tests-black-box and e2e-browser-tests don't block merging.
Risk matrix: the 5×5 likelihood × impact matrix is missing.
EC-02 contradiction: page 13 says "0 open defects → MET", but the completion report says 3 major defects (#18, #19, #20) are open.
Pareto incomplete: it is split into parts, one part says 14 defects instead of 16, and #25 and #26 are missing.
GQM metrics outdated: defect density and reopen rate cover only 4 of the 16 defects.


May cost marks:
Diagrams: the control-flow graph and fishbone analyses are text only.
API test counts: the documents say 462, 476 and 477 without a consistent figure.
Performance: one limit was set for both workloads instead of one for each. Signup under load was not measured, so EC-04 is not demonstrated.
Estimates: the area 1 estimates were written after the work.
Risk PR-08: the root cause analysis says likelihood rose from 3 to 5, but the register still shows 3.

Check before the viva :
Commit identity: 56 commits use the placeholder address zain@test.com.
Authorship: every member must have committed their own work and taken the screenshots credited to them.
Google Sheet: confirm the repository is registered in our section's tab. This couldn't be checked from the files.
Preparation: each member must be able to rerun a test and explain their area.
</pasted_content id="007a">
````

## Prompt 19 (2026-11-28T17:16:34.743Z)

````text
where is my updated foder and report?
````

## Prompt 20 (2026-11-28T17:18:16.864Z)

````text
im here but pdf says old 97 pages
````

## Prompt 21 (2026-11-28T17:21:37.932Z)

````text
the zip there contains what needs to be submitted
````

## Prompt 22 (2026-11-28T17:21:37.933Z)

````text
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\10.png]
````

## Prompt 23 (2026-11-28T17:31:18.608Z)

````text
u alreasy gimme the pdf of 107 oages, now i ned the folder
````

## Prompt 24 (2026-11-28T17:32:47.504Z)

````text
wait
````

## Prompt 25 (2026-11-28T17:32:47.934Z)

````text
[Request interrupted by user]
````

## Prompt 26 (2026-11-28T17:33:42.985Z)

````text
you said prompt history hasnt been added in repoert for all 3 zain, sajawal and manan, i am log i as zainsheraz10 now gimme my propt history so i can taje the ss of it
````

## Prompt 27 (2026-11-28T17:37:32.071Z)

````text
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\11.png]
[Image: source: C:\Users\Admin\AppData\Local\Temp\claude\f8182d7ff6eb185a\9c2de542-aff6-4e29-af8c-c7e882d91fba\images\12.png]
````

## Prompt 28 (2026-11-28T17:43:39.698Z)

````text
login as sajawalfake and if we check for prompt.md will it show for sajawal prompts which he made?
````

## Prompt 29 (2026-11-28T17:44:37.672Z)

````text
login as sajawal account
````

## Prompt 30 (2026-11-28T17:45:44.836Z)

````text
now check for sajawal_prompts
````

## Prompt 31 (2026-11-28T17:51:22.298Z)

````text
Tell me that is there any way that all the user can show their prompts separately by running the commmands, since they have done all the commits by their own accounts, so can I run a command on terminal, swithch github accounts and run commands for viewing prompt history separately for each member?
````

## Prompt 32 (2026-11-28T17:52:54.250Z)

````text
so what is the solution then?
````

## Prompt 33 (2026-11-28T17:53:44.970Z)

````text
all of the tasks were done by this computer, but we changed the github accounts for commits
````

## Prompt 34 (2026-11-28T17:54:21.885Z)

````text
[Request interrupted by user]
````

## Prompt 35 (2026-11-28T17:55:24.441Z)

````text
all the prompt were done by single laptop but now I want to show separate prompt history for every group member, now tell me a solution
````
