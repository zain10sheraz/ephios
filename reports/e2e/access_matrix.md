| Role | Action | Expected | Observed | Result |
|---|---|---|---|---|
| anonymous | open create-event page (redirected to login) | 200 | 200 | PASS |
| volunteer | open create-event page (denied) | 403 | 403 | PASS |
| planner | open create-event page (allowed) | 200 | 200 | PASS |
| volunteer | open edit-shift page (denied) | 403 | 403 | PASS |
| planner | open edit-shift page (allowed) | 200 | 200 | PASS |
| volunteer | open delete-shift page (denied) | 403 | 403 | PASS |
| volunteer | open the event list (allowed) | 200 | 200 | PASS |
