// Browser suite for the discovery surfaces: the three-question read, the
// public sample report, the moment pages, and the advisor door.
//
// It drives the real app in real Chrome. Everything here is an assertion about
// something a visitor can see or click, not about markup that happens to be
// present, so a pass means the path works rather than that the HTML compiled.
//
//   Run:  BASE=http://localhost:3000 node e2e/discovery-suite.mjs
//
// Separate from ui-suite.mjs on purpose: that suite exercises sign-in and
// Stripe, which need live keys and a backend log. This one needs only the app.

import puppeteer from "puppeteer-core";
import fs from "node:fs";
import path from "node:path";

const BASE = process.env.BASE || "http://localhost:3000";
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const SHOT_DIR = path.join(path.dirname(new URL(import.meta.url).pathname), "screenshots");

const results = [];
const pass = (name, note = "") => results.push({ status: "PASS", name, note });
const fail = (name, note = "") => results.push({ status: "FAIL", name, note });

// Assert, but never let one broken expectation stop the rest of the run.
function expect(condition, name, note = "") {
  condition ? pass(name, note) : fail(name, note);
}

const MOMENT_SLUGS = [
  "offer-on-the-table",
  "no-one-to-hand-it-to",
  "cannot-step-away",
  "three-years-out"
];

// Click the option whose visible text starts with `text`, then wait for the
// question counter to move. Waiting on the real target rather than a timer is
// what makes this suite trustworthy on a slow machine.
async function answer(page, text) {
  const before = await page.$eval(".quickPrompt", (el) => el.textContent);
  const clicked = await page.evaluate((wanted) => {
    const button = [...document.querySelectorAll(".quickOptions button")]
      .find((b) => b.textContent.trim().startsWith(wanted));
    if (!button) return false;
    button.click();
    return true;
  }, text);
  if (!clicked) throw new Error(`no option starting with "${text}"`);
  await page.waitForFunction(
    (prev) => {
      const prompt = document.querySelector(".quickPrompt");
      return !prompt || prompt.textContent !== prev;
    },
    { timeout: 5000 },
    before
  );
}

async function newPage(browser, width = 1280, height = 900) {
  const page = await browser.newPage();
  await page.setViewport({ width, height });
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  page.errors = errors;
  return page;
}

async function run() {
  fs.mkdirSync(SHOT_DIR, { recursive: true });
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });

  // ---- 1. The three-question read, clicked all the way through ----
  {
    const page = await newPage(browser);
    await page.goto(`${BASE}/`, { waitUntil: "load", timeout: 25000 });
    await page.waitForSelector(".quickOptions button", { timeout: 10000 });

    const count = await page.$$eval(".quickOptions button", (b) => b.length);
    expect(count === 4, "quick read: first question offers four answers", `found ${count}`);

    await answer(page, "It limps along");
    await answer(page, "Not next week");

    // The third answer ends the card, so wait for the result, not the prompt.
    await page.evaluate(() => {
      [...document.querySelectorAll(".quickOptions button")]
        .find((b) => b.textContent.trim().startsWith("No one"))?.click();
    });
    await page.waitForSelector(".quickHeadline", { timeout: 8000 });

    const headline = await page.$eval(".quickHeadline", (el) => el.textContent.trim());
    // Answers scored 2, 2 and 1. The 1 is succession, so that is the pressure.
    expect(
      headline === "Nobody knows who comes next, including you.",
      "quick read: names the weakest area as the pressure point",
      headline
    );

    const rows = await page.$$eval(".quickAreas li", (els) => els.length);
    const marked = await page.$$eval(".quickAreas li.isPressure", (els) => els.length);
    expect(rows === 3, "quick read: shows all three answers back", `${rows} rows`);
    expect(marked === 1, "quick read: marks exactly one pressure area", `${marked} marked`);

    const limits = await page.$$eval(".quickLimits li", (els) => els.length);
    expect(limits === 4, "quick read: lists what it cannot see", `${limits} items`);

    const body = await page.evaluate(() => document.body.innerText);
    expect(!/\b\d{1,3}\s*\/\s*100\b/.test(body), "quick read: never shows a score out of 100");

    await page.screenshot({ path: path.join(SHOT_DIR, "quickread_result.png"), fullPage: false });

    // Start over returns to question one.
    await page.click(".quickRestart");
    await page.waitForSelector(".quickPrompt", { timeout: 5000 });
    const prompt = await page.$eval(".quickPrompt", (el) => el.textContent);
    expect(prompt.startsWith("You are out for a month"), "quick read: start over returns to question one", prompt.slice(0, 40));

    // Back steps to the previous question rather than clearing the card.
    await answer(page, "It limps along");
    await page.click(".quickBack");
    await page.waitForSelector(".quickPrompt", { timeout: 5000 });
    const back = await page.$eval(".quickPrompt", (el) => el.textContent);
    expect(back.startsWith("You are out for a month"), "quick read: back returns to the previous question", back.slice(0, 40));

    // Three answers of equal weight: the tie goes to the first question.
    // The back button left the card on question one, so answer from here.
    await answer(page, "It limps along");
    await answer(page, "Not next week");
    await page.evaluate(() => {
      [...document.querySelectorAll(".quickOptions button")]
        .find((b) => b.textContent.trim().startsWith("I have a name in mind"))?.click();
    });
    await page.waitForSelector(".quickHeadline", { timeout: 8000 });
    const tie = await page.$eval(".quickHeadline", (el) => el.textContent.trim());
    expect(
      tie === "Most of this business is still you.",
      "quick read: a tie goes to how much runs through you",
      tie
    );

    expect(page.errors.length === 0, "homepage: no console errors", page.errors.join(" | ").slice(0, 160));
    await page.close();
  }

  // ---- 2. The sample report ----
  {
    const page = await newPage(browser);
    await page.goto(`${BASE}/sample`, { waitUntil: "load", timeout: 25000 });
    await page.waitForSelector(".sampleOverall strong", { timeout: 10000 });

    const overall = await page.$eval(".sampleOverall strong", (el) => Number(el.textContent.trim()));
    expect(overall > 0 && overall <= 100, "sample: renders a readiness score", String(overall));

    const areas = await page.$$eval(".sampleScore .sampleRows li", (els) => els.length);
    expect(areas === 5, "sample: shows all five readiness areas", `${areas} rows`);

    const pathRows = await page.$$eval(".sampleTable tbody tr", (els) => els.length);
    expect(pathRows === 6, "sample: weighs six transfer paths", `${pathRows} rows`);

    const briefs = await page.$$eval(".sampleBriefs article", (els) => els.length);
    expect(briefs === 4, "sample: shows four briefs", `${briefs} briefs`);

    // No internal research label or raw field name may reach the page.
    const text = await page.evaluate(() => document.body.innerText.toLowerCase());
    const leaks = ["buffett", "jtbd", "operational_transferability", "north star", "activation event"]
      .filter((term) => text.includes(term));
    expect(leaks.length === 0, "sample: no internal labels in owner-facing text", leaks.join(", "));

    expect(text.includes("made up"), "sample: says the business is invented");
    expect(page.errors.length === 0, "sample: no console errors", page.errors.join(" | ").slice(0, 160));

    await page.screenshot({ path: path.join(SHOT_DIR, "sample_report.png"), fullPage: true });
    await page.close();
  }

  // ---- 3. The doors feed the moment pages from the live homepage ----
  {
    const page = await newPage(browser);
    await page.goto(`${BASE}/`, { waitUntil: "load", timeout: 25000 });
    await page.waitForSelector(".momentDoors a", { timeout: 10000 });

    const hrefs = await page.$$eval(".momentDoors a", (els) => els.map((a) => a.getAttribute("href")));
    expect(hrefs.length === 4, "homepage: four doors", `${hrefs.length} found`);
    for (const slug of MOMENT_SLUGS) {
      expect(hrefs.includes(`/content/${slug}`), `homepage: links to ${slug}`);
    }

    // Follow one door the way a visitor would, by clicking it.
    await Promise.all([
      page.waitForNavigation({ waitUntil: "load", timeout: 20000 }),
      page.click('.momentDoors a[href="/content/offer-on-the-table"]')
    ]);
    const h1 = await page.$eval("h1", (el) => el.textContent.trim());
    expect(
      h1.startsWith("Someone offered to buy my business"),
      "door: lands on the page written for that moment",
      h1.slice(0, 48)
    );
    await page.waitForSelector(".quickOptions button", { timeout: 8000 });
    pass("moment page: carries the three-question read");
    await page.close();
  }

  // ---- 4. Every moment page stands up on its own ----
  for (const slug of MOMENT_SLUGS) {
    const page = await newPage(browser);
    const resp = await page.goto(`${BASE}/content/${slug}`, { waitUntil: "load", timeout: 25000 });
    const ok = resp && resp.status() === 200;
    const h1 = ok ? await page.$eval("h1", (el) => el.textContent.trim()) : "";
    const sections = ok ? await page.$$eval(".contentSection h2", (els) => els.length) : 0;
    expect(ok && h1.length > 10 && sections >= 5, `moment page ${slug}: renders with its sections`, `${sections} sections`);
    expect(page.errors.length === 0, `moment page ${slug}: no console errors`, page.errors.join(" | ").slice(0, 120));
    await page.close();
  }

  // ---- 5. The advisor door ----
  {
    const page = await newPage(browser);
    await page.goto(`${BASE}/for-advisors`, { waitUntil: "load", timeout: 25000 });
    await page.waitForSelector(".copyText", { timeout: 10000 });

    // The pasteable note must carry a working link, not a placeholder domain.
    const note = await page.$eval(".copyText", (el) => el.textContent);
    expect(note.includes(BASE), "advisors: the note carries this site's own link", note.slice(-40));
    expect(!note.includes("your-domain.example"), "advisors: no placeholder domain in the note");

    const links = await page.$$eval(".advisorsMoments a", (els) => els.length);
    expect(links === 4, "advisors: can forward all four moment pages", `${links} links`);

    expect(page.errors.length === 0, "advisors: no console errors", page.errors.join(" | ").slice(0, 160));
    await page.screenshot({ path: path.join(SHOT_DIR, "for_advisors.png"), fullPage: false });
    await page.close();
  }

  // ---- 6. Nothing spills sideways on a phone ----
  for (const route of ["/", "/sample", "/for-advisors", "/content/cannot-step-away"]) {
    const page = await newPage(browser, 390, 844);
    await page.goto(`${BASE}${route}`, { waitUntil: "load", timeout: 25000 });
    const overflow = await page.evaluate(() =>
      document.documentElement.scrollWidth - document.documentElement.clientWidth
    );
    // The sample report holds a six-column table that scrolls inside its own
    // box, so the page itself must still not scroll sideways.
    expect(overflow <= 1, `mobile ${route}: no sideways scroll`, `${overflow}px over`);
    await page.close();
  }

  await browser.close();

  const counts = { PASS: 0, FAIL: 0 };
  results.forEach((r) => counts[r.status]++);
  const line = "=".repeat(74);
  console.log("\n" + line + "\nStewardPath discovery suite\n" + line);
  for (const r of results) console.log(`${r.status.padEnd(4)} ${r.name}${r.note ? "  ->  " + r.note : ""}`);
  console.log(line);
  console.log(`PASS ${counts.PASS}   FAIL ${counts.FAIL}   (screenshots in e2e/screenshots/)`);
  console.log(line + "\n");
  process.exit(counts.FAIL > 0 ? 1 : 0);
}

run().catch((e) => { console.error("Suite crashed:", e); process.exit(2); });
