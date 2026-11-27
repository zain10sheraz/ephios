// Full axe-core scan with @axe-core/playwright of the key screen of each use case, logged in through the real login form.
//
// Usage: node scripts/axe_scan.mjs <base_url> <phase>        e.g.  node scripts/axe_scan.mjs http://127.0.0.1:8003 before
// Needs: npm install playwright @axe-core/playwright (in SQE_TOOLS, default C:/sqe_tools) and a running seeded server
// (scripts/serve_seeded.py). Writes reports/accessibility/axe_<screen>_<phase>.json (the full axe result).
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const tools = process.env.SQE_TOOLS || 'C:/sqe_tools';
const require = createRequire(path.join(tools, 'package.json'));
const { chromium } = require('playwright');
const AxeBuilder = require('@axe-core/playwright').default;

const [base, phase] = process.argv.slice(2);
const out = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'reports', 'accessibility');
fs.mkdirSync(out, { recursive: true });

const ACCOUNTS = {
  planner: ['planner@sqe.test', 'Planner#2026'],
  volunteer: ['volunteer@sqe.test', 'Volunteer#2026'],
};

async function login(browser, role) {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(`${base}/accounts/login/`);
  await page.fill('#id_username', ACCOUNTS[role][0]);
  await page.fill('#id_password', ACCOUNTS[role][1]);
  await page.click('button[type=submit]');
  await page.waitForURL((url) => !url.pathname.includes('/accounts/login'));
  return page;
}

async function createEventWithShift(page, title, day) {
  await page.goto(`${base}/events/create/1/`);
  await page.fill('#id_title', title);
  await page.fill('#id_location', 'Test hall');
  await page.click('button[type=submit]');
  await page.waitForURL(/\/events\/\d+\/createshift\//);
  await page.fill('#id_date', day);
  await page.fill('#id_meeting_time', '09:00');
  await page.fill('#id_start_time', '10:00');
  await page.fill('#id_end_time', '16:00');
  await page.fill('#id_maximum_number_of_participants', '5');
  await page.click("button[type=submit]:has-text('Save')");
  await page.waitForURL(/\/events\/\d+-/);
  return page.url();
}

async function scan(page, name) {
  await page.waitForLoadState('networkidle');
  const results = await new AxeBuilder({ page }).analyze();
  fs.writeFileSync(path.join(out, `axe_${name}_${phase}.json`), JSON.stringify(results, null, 1));
  const rules = results.violations.map((v) => `${v.id}(${v.nodes.length})`).join(', ');
  console.log(`${name} ${phase}: ${results.violations.length} violated rules: ${rules}`);
}

const browser = await chromium.launch();
const planner = await login(browser, 'planner');
const volunteer = await login(browser, 'volunteer');
const eventUrl = await createEventWithShift(planner, 'Axe scan event', '2095-05-05');
const shiftId = (await planner.locator("[id^='shift-']").first().getAttribute('id')).replace('shift-', '');

await planner.goto(`${base}/shifts/${shiftId}/edit/`);
await scan(planner, 'uc1_shift_form');
await volunteer.goto(eventUrl);
await scan(volunteer, 'uc2_event_page');
// UC5 key screen (planner): the confirmation page of a shift deletion
await planner.goto(`${base}/shifts/${shiftId}/delete/`);
await scan(planner, 'uc5_shift_delete');
// UC6 key screen (volunteer): the "customize signup times" page
await volunteer.goto(`${base}/shifts/${shiftId}/signup/`);
await scan(volunteer, 'uc6_customize_page');
await browser.close();
