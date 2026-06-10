// End-to-end UI suite for StewardPath, driven against the real running app.
// Uses puppeteer-core with the Chrome already installed on the machine.
//
//   Frontend: http://localhost:3434   Backend: http://localhost:8000
//   Run:      node e2e/ui-suite.mjs
//
// It visits every surface, asserts key elements render, captures screenshots,
// and collects signals that predict UX trouble (console errors, failed
// requests, missing titles/h1s, unlabeled buttons, mobile overflow). It also
// runs the real passwordless sign-in by reading the code from the backend log
// and confirms a Buy click reaches Stripe without loading the external page.

import puppeteer from "puppeteer-core";
import fs from "node:fs";
import path from "node:path";

const BASE = process.env.BASE || "http://localhost:3434";
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const LOG = process.env.BACKEND_LOG || "/tmp/sp_backend.log";
const SHOT_DIR = path.join(path.dirname(new URL(import.meta.url).pathname), "screenshots");

const results = [];
const rec = (status, name, note = "") => { results.push({ status, name, note }); };
const pass = (n, note) => rec("PASS", n, note);
const warn = (n, note) => rec("WARN", n, note);
const fail = (n, note) => rec("FAIL", n, note);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function instrument(page) {
  const errors = [];
  const failed = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  page.on("requestfailed", (r) => {
    const u = r.url();
    // Aborting the Stripe navigation ourselves shows as a failed request; ignore.
    if (!u.includes("checkout.stripe.com")) failed.push(`${r.failure()?.errorText || "failed"} ${u}`);
  });
  return { errors, failed };
}

async function gotoSafe(page, url) {
  try {
    const resp = await page.goto(url, { waitUntil: "load", timeout: 20000 });
    await page.waitForNetworkIdle({ idleTime: 600, timeout: 4000 }).catch(() => {});
    return resp;
  } catch (e) {
    return { _error: e.message };
  }
}

async function auditPage(browser, route, label, custom) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });
  const sig = instrument(page);
  const resp = await gotoSafe(page, BASE + route);

  if (resp && resp._error) { fail(`${label}: load`, resp._error); await page.close(); return; }
  if (resp && typeof resp.status === "function" && resp.status() >= 400) fail(`${label}: HTTP ${resp.status()}`);
  else pass(`${label}: loads`);

  const title = await page.title();
  title ? pass(`${label}: has <title>`, title) : warn(`${label}: missing <title>`);

  const h1s = await page.$$eval("h1", (els) => els.map((e) => e.textContent.trim()).filter(Boolean));
  if (h1s.length === 1) pass(`${label}: exactly one h1`, h1s[0]);
  else if (h1s.length === 0) warn(`${label}: no h1 on page`);
  else warn(`${label}: ${h1s.length} h1 elements`, h1s.join(" | "));

  const lang = await page.$eval("html", (el) => el.getAttribute("lang")).catch(() => null);
  lang ? pass(`${label}: <html lang>`, lang) : warn(`${label}: <html> missing lang attribute`);

  const nameless = await page.$$eval("button", (els) =>
    els.filter((b) => !((b.textContent || "").trim() || b.getAttribute("aria-label"))).length);
  nameless === 0 ? pass(`${label}: all buttons have accessible names`) : warn(`${label}: ${nameless} button(s) with no accessible name`);

  if (custom) { try { await custom(page); } catch (e) { fail(`${label}: custom checks`, e.message); } }

  // Mobile overflow
  await page.setViewport({ width: 390, height: 844 });
  await sleep(300);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  overflow > 2 ? warn(`${label}: horizontal overflow on mobile`, `${overflow}px wider than viewport`) : pass(`${label}: no mobile overflow`);

  try { await page.screenshot({ path: path.join(SHOT_DIR, label.replace(/\W+/g, "_") + ".png"), fullPage: true }); } catch {}

  if (sig.errors.length) warn(`${label}: ${sig.errors.length} console error(s)`, sig.errors.slice(0, 3).join(" || "));
  else pass(`${label}: no console errors`);
  if (sig.failed.length) warn(`${label}: ${sig.failed.length} failed network request(s)`, sig.failed.slice(0, 3).join(" || "));
  else pass(`${label}: no failed requests`);

  await page.close();
}

function readCodeFromLog(email) {
  try {
    const text = fs.readFileSync(LOG, "utf8");
    const idx = text.lastIndexOf(`to=${email}`);
    if (idx === -1) return null;
    const after = text.slice(idx);
    const m = after.match(/Your code: (\d{6})/);
    return m ? m[1] : null;
  } catch { return null; }
}

async function clickByText(page, selector, text) {
  const handles = await page.$$(selector);
  for (const h of handles) {
    const t = (await page.evaluate((el) => el.textContent, h)) || "";
    if (t.trim().toLowerCase().includes(text.toLowerCase())) { await h.click(); return true; }
  }
  return false;
}

// Full flow: on the home page, click Buy -> sign in (read code from log) ->
// confirm the browser is sent to Stripe checkout (intercepted, not loaded).
async function testBuyReachesStripe(browser) {
  const label = "flow:buy->signin->stripe";
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });
  const sig = instrument(page);

  let stripeReached = false;
  await page.setRequestInterception(true);
  page.on("request", (req) => {
    if (req.url().includes("checkout.stripe.com")) { stripeReached = true; req.abort(); }
    else req.continue();
  });

  const resp = await gotoSafe(page, BASE + "/");
  if (resp && resp._error) { fail(`${label}: home load`, resp._error); await page.close(); return; }

  const email = `e2e+${Date.now()}@example.com`;
  const clickedBuy = await clickByText(page, "button.offerCta", "start the program");
  if (!clickedBuy) { fail(`${label}: Buy button`, "could not find 'Start the program'"); await page.close(); return; }

  // Sign-in gate
  await page.waitForSelector("#authEmail", { timeout: 8000 }).catch(() => {});
  const hasGate = await page.$("#authEmail");
  if (!hasGate) { fail(`${label}: sign-in gate`, "AuthGate did not open after Buy"); await page.close(); return; }
  pass(`${label}: Buy opens the sign-in gate`);

  await page.type("#authEmail", email);
  await clickByText(page, "button", "send my secure code");

  // Wait for code-entry step and read the code from the backend log.
  await page.waitForFunction(() => !!document.querySelector('input[inputmode="numeric"], #authCode, input[type="text"]'), { timeout: 8000 }).catch(() => {});
  let code = null;
  for (let i = 0; i < 12 && !code; i++) { await sleep(400); code = readCodeFromLog(email); }
  if (!code) { fail(`${label}: code delivery`, "no code found in backend log (is log mode on?)"); await page.close(); return; }
  pass(`${label}: sign-in code issued`, `code ${code}`);

  // Type the code into whatever code field is present.
  const codeSel = (await page.$("#authCode")) ? "#authCode" : 'input[inputmode="numeric"]';
  const codeField = (await page.$(codeSel)) ? codeSel : 'input';
  await page.type(codeField, code).catch(() => {});
  await clickByText(page, "button", "continue to payment");

  // Give startCheckout time to call /checkout and redirect.
  for (let i = 0; i < 15 && !stripeReached; i++) await sleep(500);
  stripeReached ? pass(`${label}: Buy reaches Stripe checkout`) : fail(`${label}: Stripe redirect`, "no navigation to checkout.stripe.com after sign-in");

  if (sig.errors.length) warn(`${label}: console error(s)`, sig.errors.slice(0, 3).join(" || "));
  await page.close();
}

async function main() {
  fs.mkdirSync(SHOT_DIR, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  // Home: pricing band, the three Buy buttons + free, privacy/trust language.
  await auditPage(browser, "/", "home", async (page) => {
    const cards = await page.$$eval(".offerBand article", (els) => els.length);
    cards === 4 ? pass("home: four pricing cards") : warn("home: pricing cards", `${cards} cards (expected 4)`);
    const buys = await page.$$eval(".offerCta", (els) => els.map((e) => e.textContent.trim()));
    const wanted = ["Start free", "Start the program", "Get the concierge package", "Start the advisor pilot"];
    wanted.forEach((w) => buys.some((b) => b.includes(w)) ? pass(`home: CTA '${w}'`) : warn(`home: missing CTA`, w));
    const noReport = await page.evaluate(() => !/buy the report|owner readiness report/i.test(document.body.innerText));
    noReport ? pass("home: $249 tier framed as a Program, not a report") : warn("home: stale 'report' wording for $249 tier");
    const priv = await page.evaluate(() => /private|never used to train|you control/i.test(document.body.innerText));
    priv ? pass("home: privacy language present") : warn("home: no visible privacy cue");
  });

  // Intake: trust step + a visible privacy cue (design law) + begin control.
  await auditPage(browser, "/intake", "intake", async (page) => {
    const begin = await page.evaluate(() => /begin privately|begin/i.test(document.body.innerText));
    begin ? pass("intake: 'Begin' control present") : warn("intake: no Begin control found");
    const priv = await page.evaluate(() => /private|we collect|you control|never used to train/i.test(document.body.innerText));
    priv ? pass("intake: visible privacy cue") : warn("intake: data-entry page lacks a visible privacy cue");
  });

  await auditPage(browser, "/readiness", "readiness");
  await auditPage(browser, "/go-to-market", "go-to-market");
  await auditPage(browser, "/checkout/cancel", "checkout-cancel");

  // Success page with no session id should explain itself, not look broken.
  await auditPage(browser, "/checkout/success", "checkout-success-no-session", async (page) => {
    await sleep(800);
    const txt = await page.evaluate(() => document.body.innerText.toLowerCase());
    /could not confirm|still confirming|no charge|payment/.test(txt)
      ? pass("checkout-success: handles missing session gracefully")
      : warn("checkout-success: unclear state with no session id");
  });

  await auditPage(browser, "/advisor", "advisor");

  await testBuyReachesStripe(browser);

  await browser.close();

  // Report
  const counts = { PASS: 0, WARN: 0, FAIL: 0 };
  results.forEach((r) => { counts[r.status]++; });
  const line = "=".repeat(72);
  console.log("\n" + line + "\nStewardPath UI suite\n" + line);
  for (const r of results) {
    const tag = r.status.padEnd(4);
    console.log(`${tag} ${r.name}${r.note ? "  ->  " + r.note : ""}`);
  }
  console.log(line);
  console.log(`PASS ${counts.PASS}   WARN ${counts.WARN}   FAIL ${counts.FAIL}   (screenshots in e2e/screenshots/)`);
  console.log(line + "\n");
  process.exit(counts.FAIL > 0 ? 1 : 0);
}

main().catch((e) => { console.error("Suite crashed:", e); process.exit(2); });
