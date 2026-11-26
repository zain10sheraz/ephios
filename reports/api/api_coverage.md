# API coverage against test_specs/openapi.yaml

| Operation | Method path | Documented | Observed | Missing |
|---|---|---|---|---|
| activateEvent | POST /events/{pk}/activate/ | 302, 403, 404 | 302, 403, 404 | - |
| createEvent | POST /events/create/{type}/ | 200, 302, 403, 404 | 200, 302, 403, 404 | - |
| createShift | POST /events/{pk}/createshift/ | 200, 302, 403, 404 | 200, 302, 403, 404 | - |
| deleteEvent | POST /events/{pk}/delete/ | 302, 403, 404 | 302, 403, 404 | - |
| deleteShift | POST /shifts/{pk}/delete/ | 302, 403, 404 | 302, 403, 404 | - |
| editShift | POST /shifts/{pk}/edit/ | 200, 302, 403, 404 | 200, 302, 403, 404 | - |
| getEvent | GET /api/events/{id}/ | 200, 403, 404 | 200, 403, 404 | - |
| getParticipation | GET /api/participations/{id}/ | 200, 403, 404 | 200, 403, 404 | - |
| getShift | GET /api/shifts/{id}/ | 200, 403, 404 | 200, 403, 404 | - |
| listEvents | GET /api/events/ | 200, 400, 403 | 200, 400, 403 | - |
| listOwnParticipations | GET /api/users/me/participations/ | 200, 400, 403 | 200, 400, 403 | - |
| listParticipations | GET /api/participations/ | 200, 400, 403 | 200, 400, 403 | - |
| listShifts | GET /api/shifts/ | 200, 400, 403 | 200, 400, 403 | - |
| signup | POST /shifts/{pk}/signup/ | 200, 302, 403, 404 | 200, 302, 403, 404, 500 | - |

- Operation coverage: 14/14 = 100 %
- Status-code coverage: 46/46 = 100 % of the documented responses
- Input coverage: 80/80 inputs have generated EP/BVA cases (409 cases: 324 EP, 85 BVA)
