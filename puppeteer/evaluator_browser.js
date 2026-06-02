import fs from "node:fs/promises";
import puppeteer from "puppeteer";

const payload = JSON.parse(process.argv[2] || "{}");
const defaultUrl = payload.url || process.env.APP_BASE_URL || "http://localhost:3000";

async function withPage(fn) {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });
  const page = await browser.newPage();
  const consoleErrors = [];
  page.on("console", message => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });
  page.on("pageerror", error => {
    consoleErrors.push(error.message);
  });
  try {
    const result = await fn(page, consoleErrors);
    await browser.close();
    return result;
  } catch (error) {
    await browser.close();
    throw error;
  }
}

async function main() {
  const action = payload.action;
  if (!action) {
    throw new Error("Missing action");
  }

  if (action === "audit") {
    const result = await withPage(async (page, consoleErrors) => {
      const viewports = payload.viewports || [{ name: "default", width: 1280, height: 900 }];
      const results = [];

      for (const viewport of viewports) {
        await page.setViewport({ width: viewport.width, height: viewport.height });
        const response = await page.goto(defaultUrl, { waitUntil: "networkidle0", timeout: 15000 });
        const text = await page.evaluate(() => document.body.innerText);
        let clickedText = "";
        if (payload.clickSelector) {
          await page.click(payload.clickSelector);
          clickedText = await page.evaluate(() => document.body.innerText);
        }
        const metrics = await page.evaluate(() => ({
          title: document.title,
          h1: document.querySelector("h1")?.innerText || "",
          buttonCount: document.querySelectorAll("button, a.button").length,
          featureCount: document.querySelectorAll(".feature").length,
          sectionCount: document.querySelectorAll("section").length,
          hasHorizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
          textLength: document.body.innerText.length
        }));
        const screenshotPath = payload.screenshotPaths?.[viewport.name] || payload.screenshotPath || null;
        if (screenshotPath) {
          await fs.mkdir(new URL(".", `file://${screenshotPath}`).pathname, { recursive: true });
          await page.screenshot({ path: screenshotPath, fullPage: true });
        }
        results.push({
          name: viewport.name,
          width: viewport.width,
          height: viewport.height,
          status: response?.status() || null,
          text,
          clickedText,
          metrics,
          screenshotPath
        });
      }

      return {
        ok: true,
        action,
        url: defaultUrl,
        errors: consoleErrors,
        results,
        text: results[0]?.text || "",
        clickedText: results[0]?.clickedText || "",
        screenshotPath: results[0]?.screenshotPath || null
      };
    });
    console.log(JSON.stringify(result));
    return;
  }

  if (action === "navigate") {
    const result = await withPage(async page => {
      const response = await page.goto(defaultUrl, { waitUntil: "networkidle0", timeout: 15000 });
      return { ok: true, action, url: defaultUrl, status: response?.status() || null };
    });
    console.log(JSON.stringify(result));
    return;
  }

  if (action === "get_page_text") {
    const result = await withPage(async page => {
      await page.goto(defaultUrl, { waitUntil: "networkidle0", timeout: 15000 });
      const text = await page.evaluate(() => document.body.innerText);
      return { ok: true, action, url: defaultUrl, text };
    });
    console.log(JSON.stringify(result));
    return;
  }

  if (action === "get_console_errors") {
    const result = await withPage(async (page, consoleErrors) => {
      await page.goto(defaultUrl, { waitUntil: "networkidle0", timeout: 15000 });
      return { ok: true, action, url: defaultUrl, errors: consoleErrors };
    });
    console.log(JSON.stringify(result));
    return;
  }

  if (action === "screenshot") {
    const result = await withPage(async page => {
      await page.goto(defaultUrl, { waitUntil: "networkidle0", timeout: 15000 });
      await fs.mkdir(new URL(".", `file://${payload.path}`).pathname, { recursive: true });
      await page.screenshot({ path: payload.path, fullPage: true });
      return { ok: true, action, url: defaultUrl, path: payload.path };
    });
    console.log(JSON.stringify(result));
    return;
  }

  if (action === "click") {
    const result = await withPage(async page => {
      await page.goto(defaultUrl, { waitUntil: "networkidle0", timeout: 15000 });
      await page.click(payload.selector);
      const text = await page.evaluate(() => document.body.innerText);
      return { ok: true, action, selector: payload.selector, text };
    });
    console.log(JSON.stringify(result));
    return;
  }

  if (action === "type") {
    const result = await withPage(async page => {
      await page.goto(defaultUrl, { waitUntil: "networkidle0", timeout: 15000 });
      await page.type(payload.selector, payload.text || "");
      return { ok: true, action, selector: payload.selector };
    });
    console.log(JSON.stringify(result));
    return;
  }

  if (action === "wait_for_selector") {
    const result = await withPage(async page => {
      await page.goto(defaultUrl, { waitUntil: "networkidle0", timeout: 15000 });
      await page.waitForSelector(payload.selector, { timeout: 10000 });
      return { ok: true, action, selector: payload.selector };
    });
    console.log(JSON.stringify(result));
    return;
  }

  if (action === "evaluate_dom") {
    const result = await withPage(async page => {
      await page.goto(defaultUrl, { waitUntil: "networkidle0", timeout: 15000 });
      const value = await page.evaluate(payload.script);
      return { ok: true, action, value };
    });
    console.log(JSON.stringify(result));
    return;
  }

  throw new Error(`Unsupported action: ${action}`);
}

main().catch(error => {
  console.error(error.stack || error.message);
  process.exit(1);
});
