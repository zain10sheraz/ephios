| Role | Action | Expected | Observed | Result | Evidence |
|---|---|---|---|---|---|
| anonymous | open create-event page (redirected to login) | 200 | 200 | PASS | `test_access_decision[anonymous-open create-event page]`, HTTP 200, final URL `/accounts/login/?next=/events/create/1/` |
| volunteer | open create-event page (denied) | 403 | 403 | PASS | `test_access_decision[volunteer-open create-event page]`, HTTP 403, final URL `/events/create/1/` |
| planner | open create-event page (allowed) | 200 | 200 | PASS | `test_access_decision[planner-open create-event page]`, HTTP 200, final URL `/events/create/1/` |
| volunteer | open edit-shift page (denied) | 403 | 403 | PASS | `test_access_decision[volunteer-open edit-shift page]`, HTTP 403, final URL `/shifts/5/edit/` |
| planner | open edit-shift page (allowed) | 200 | 200 | PASS | `test_access_decision[planner-open edit-shift page]`, HTTP 200, final URL `/shifts/6/edit/` |
| volunteer | open delete-shift page (denied) | 403 | 403 | PASS | `test_access_decision[volunteer-open delete-shift page]`, HTTP 403, final URL `/shifts/7/delete/` |
| volunteer | open the event list (allowed) | 200 | 200 | PASS | `test_access_decision[volunteer-open the event list]`, HTTP 200, final URL `/events/` |
