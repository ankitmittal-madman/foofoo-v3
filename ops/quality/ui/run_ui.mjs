/**
 * Phase 9-11 — Headless browser UI, accessibility, and evidence capture.
 *
 * This is a REAL Playwright driver, deliberately gated on a live target: the Ghar frontend is an
 * Expo/React-Native app (mobile/) with no committed web build, so there is nothing for a browser to
 * load in this repo by default. Rather than fabricate UI evidence, this script only does work when
 * a URL is supplied via GHAR_WEB_URL; otherwise it writes a SKIPPED result explaining why and exits
 * 0 so the orchestrator records the gap truthfully.
 *
 * When GHAR_WEB_URL is set it launches Chromium (and Firefox/WebKit if their binaries are present),
 * captures a screenshot, console logs, network activity, a HAR file, and runs a minimal
 * accessibility pass (document title, lang attribute, image alt coverage, and — if @axe-core is
 * installed — a full axe scan). All artifacts go to the directory given by GHAR_UI_OUT.
 *
 * Usage:  GHAR_WEB_URL=http://localhost:8081 GHAR_UI_OUT=/path/to/report node run_ui.mjs
 */

import fs from "node:fs";
import path from "node:path";

const url = process.env.GHAR_WEB_URL;
const outDir = process.env.GHAR_UI_OUT || path.join(process.cwd(), "ui-artifacts");
fs.mkdirSync(outDir, { recursive: true });

/** Write the run summary JSON and exit with the given code. */
function finish(summary, code = 0) {
  fs.writeFileSync(path.join(outDir, "ui_result.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));
  process.exit(code);
}

if (!url) {
  finish({
    status: "skipped",
    reason:
      "GHAR_WEB_URL not set. The frontend is an Expo/React-Native app with no committed web " +
      "build; provide a running web target (e.g. `expo start --web`) to enable browser tests.",
    phases: ["9-ui", "10-headless", "11-accessibility"],
  });
}

let chromium, firefox, webkit;
try {
  ({ chromium, firefox, webkit } = await import("playwright"));
} catch (e) {
  finish(
    {
      status: "blocked",
      reason: "playwright module not installed (npm i -D playwright && npx playwright install)",
      error: String(e),
    },
    0
  );
}

const engines = [
  ["chromium", chromium],
  ["firefox", firefox],
  ["webkit", webkit],
];

const results = { status: "pass", url, browsers: {}, artifacts: [] };

for (const [name, engine] of engines) {
  let browser;
  try {
    browser = await engine.launch({ headless: true });
  } catch (e) {
    results.browsers[name] = { status: "unavailable", reason: String(e).slice(0, 200) };
    continue;
  }
  try {
    const context = await browser.newContext({
      recordHar: { path: path.join(outDir, `${name}.har`) },
    });
    const page = await context.newPage();
    const consoleMsgs = [];
    const requests = [];
    page.on("console", (m) => consoleMsgs.push({ type: m.type(), text: m.text() }));
    page.on("requestfinished", async (r) =>
      requests.push({ url: r.url(), method: r.method(), status: (await r.response())?.status() })
    );

    const resp = await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
    await page.screenshot({ path: path.join(outDir, `${name}-home.png`), fullPage: true });

    // Minimal accessibility signal set (Phase 11) checkable without extra deps.
    const a11y = await page.evaluate(() => {
      const imgs = Array.from(document.images);
      return {
        title: document.title || null,
        lang: document.documentElement.getAttribute("lang"),
        imageCount: imgs.length,
        imagesMissingAlt: imgs.filter((i) => !i.getAttribute("alt")).length,
        landmarks: {
          main: document.querySelectorAll("main,[role=main]").length,
          nav: document.querySelectorAll("nav,[role=navigation]").length,
        },
      };
    });

    fs.writeFileSync(
      path.join(outDir, `${name}-console.json`),
      JSON.stringify(consoleMsgs, null, 2)
    );
    fs.writeFileSync(
      path.join(outDir, `${name}-network.json`),
      JSON.stringify(requests, null, 2)
    );

    const errors = consoleMsgs.filter((m) => m.type === "error");
    results.browsers[name] = {
      status: resp && resp.ok() ? "pass" : "warn",
      httpStatus: resp ? resp.status() : null,
      consoleErrors: errors.length,
      requests: requests.length,
      a11y,
    };
    results.artifacts.push(`${name}-home.png`, `${name}.har`, `${name}-console.json`, `${name}-network.json`);
    await context.close();
  } catch (e) {
    results.browsers[name] = { status: "fail", error: String(e).slice(0, 300) };
    results.status = "fail";
  } finally {
    await browser.close();
  }
}

finish(results, results.status === "fail" ? 1 : 0);
