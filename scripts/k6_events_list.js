// k6 load test of ONE operation: GET /api/events/ (event list, WF1 read used by WF2 volunteers).
//
// Limits set BEFORE testing (justified in docs/team/PERFORMANCE.md):
//   p95 response time < 800 ms, failed requests < 1 %.
// Usage (the server must be running; credentials are the synthetic test account):
//   k6 run -e BASE=http://127.0.0.1:8003 -e VUS=1 -e DURATION=60s scripts/k6_events_list.js
import http from 'k6/http';
import { check } from 'k6';

const BASE = __ENV.BASE || 'http://127.0.0.1:8000';

export const options = {
  vus: Number(__ENV.VUS || 1),
  duration: __ENV.DURATION || '60s',
  thresholds: {
    http_req_duration: ['p(95)<800'],
    http_req_failed: ['rate<0.01'],
  },
};

export function setup() {
  // log in once like a browser does; the session cookie is reused by every virtual user
  const jar = http.cookieJar();
  const page = http.get(`${BASE}/accounts/login/`);
  const token = jar.cookiesForURL(`${BASE}/`).csrftoken[0];
  const res = http.post(
    `${BASE}/accounts/login/`,
    { username: 'volunteer@sqe.test', password: 'Volunteer#2026', csrfmiddlewaretoken: token },
    { headers: { Referer: `${BASE}/accounts/login/` }, redirects: 0 },
  );
  check(res, { 'login redirects': (r) => r.status === 302 });
  return { session: jar.cookiesForURL(`${BASE}/`).sessionid[0] };
}

export default function (data) {
  const res = http.get(`${BASE}/api/events/`, { cookies: { sessionid: data.session } });
  check(res, { 'status is 200': (r) => r.status === 200 });
}
