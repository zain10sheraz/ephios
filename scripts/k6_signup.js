// k6 load test of the WRITE operation of workflow 2: POST /shifts/<id>/signup/ (sign up, then decline, alternating).
//
// Limits for this workload, set BEFORE the first run (separate from the read workload of scripts/k6_events_list.js,
// justified in docs/team/PERFORMANCE.md section 1b):
//   p95 response time of the signup POST < 500 ms at 5 users (exit criterion EC-04 of the risk register), failed requests < 1 %.
// A "failed request" is a response that is neither 302 (accepted or rejected by a business rule, both redirect) nor 200;
// connection errors and HTTP 5xx count as failures (the SQLite "database is locked" 500 is therefore visible).
// Usage (server running from scripts/serve_seeded.py; synthetic accounts of docs/team/SETUP.md):
//   k6 run -e BASE=http://127.0.0.1:8003 -e SHIFT=1 -e VUS=1 -e DURATION=60s scripts/k6_signup.js
//   k6 run -e BASE=http://127.0.0.1:8003 -e SHIFT=1 -e VUS=5 -e DURATION=60s scripts/k6_signup.js
import http from 'k6/http';
import { check } from 'k6';

const BASE = __ENV.BASE || 'http://127.0.0.1:8000';
const SHIFT = __ENV.SHIFT || '1';
const ACCOUNTS = [
  { username: 'volunteer@sqe.test', password: 'Volunteer#2026' },
  { username: 'volunteer2@sqe.test', password: 'Volunteer#2026' },
];

export const options = {
  vus: Number(__ENV.VUS || 1),
  duration: __ENV.DURATION || '60s',
  thresholds: {
    'http_req_duration{name:signup_post}': ['p(95)<500'],
    'http_req_failed{name:signup_post}': ['rate<0.01'],
  },
};

function login(account) {
  const jar = http.cookieJar();
  http.get(`${BASE}/accounts/login/`);
  const token = jar.cookiesForURL(`${BASE}/`).csrftoken[0];
  const res = http.post(
    `${BASE}/accounts/login/`,
    { username: account.username, password: account.password, csrfmiddlewaretoken: token },
    { headers: { Referer: `${BASE}/accounts/login/` }, redirects: 0 },
  );
  check(res, { 'login redirects': (r) => r.status === 302 });
  const cookies = jar.cookiesForURL(`${BASE}/`);
  return { session: cookies.sessionid[0], csrf: cookies.csrftoken[0] };
}

export function setup() {
  return ACCOUNTS.map(login);
}

let step = 0;

export default function (sessions) {
  const me = sessions[(__VU - 1) % sessions.length];
  const choice = step++ % 2 === 0 ? 'sign_up' : 'decline';
  const res = http.post(
    `${BASE}/shifts/${SHIFT}/signup/`,
    { signup_choice: choice, csrfmiddlewaretoken: me.csrf },
    {
      cookies: { sessionid: me.session, csrftoken: me.csrf },
      headers: { Referer: `${BASE}/shifts/${SHIFT}/signup/` },
      redirects: 0,
      tags: { name: 'signup_post' },
      responseCallback: http.expectedStatuses(200, 302),
    },
  );
  check(res, { 'signup answered 302 or 200': (r) => r.status === 302 || r.status === 200 });
}
