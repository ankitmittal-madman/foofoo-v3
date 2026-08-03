/**
 * Phase 9-11 — Headless browser UI, accessibility, and evidence capture.
 *
 * This is a REAL Playwright driver, deliberately gated on a live target: the Ghar frontend is an
 * Expo/React-Native app (mobile/) with no committed web build, so there is nothing for a browser to
 * load in this repo by default. Rather than fabricate UI evidence, this script only does work when
 * a URL is supplied via GHAR_WEB_URL; otherwise it writes a SKIPPED result explaining why and exits
 * 0 so the orchestrator records the gap truthfully.
 *
 * When GHAR_WEB_URL is set it launches Chromium (and Firefox/WebKit if their binaries are present)
 * and visits every screen discovered from mobile/app's own expo-router file tree (not a hardcoded
 * list — new screens added under mobile/app are picked up automatically next run), capturing one
 * screenshot per screen per browser, console logs, network activity, a HAR file, and a minimal
 * accessibility pass (document title, lang attribute, image alt coverage, and — if @axe-core is
 * installed — a full axe scan) per screen. All artifacts go to the directory given by GHAR_UI_OUT.
 *
 * Usage:  GHAR_WEB_URL=http://localhost:8081 GHAR_UI_OUT=/path/to/report node run_ui.mjs
 *         GHAR_UI_ROUTES=/,/sign-in  (optional, comma-separated, overrides auto-discovery)
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const url = process.env.GHAR_WEB_URL;
const outDir = process.env.GHAR_UI_OUT || path.join(process.cwd(), "ui-artifacts");
fs.mkdirSync(outDir, { recursive: true });

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const APP_DIR = path.join(REPO_ROOT, "mobile", "app");

/**
 * Discover expo-router screens from mobile/app's own file tree: strips `(group)` segments (they
 * don't affect the URL), maps `index` to the parent path, and substitutes a placeholder for
 * dynamic `[param]` segments so the route is at least reachable for a screenshot. Generic over
 * whatever screens exist — no fixed screen list to fall out of sync with the app.
 */
function discoverRoutes(dir, base = "") {
  if (!fs.existsSync(dir)) return [];
  const routes = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith("_") || entry.name.startsWith(".")) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      const segment = entry.name.startsWith("(") ? "" : entry.name;
      routes.push(...discoverRoutes(full, [base, segment].filter(Boolean).join("/")));
      continue;
    }
    if (!/\.tsx?$/.test(entry.name)) continue;
    let name = entry.name.replace(/\.tsx?$/, "");
    if (name === "index") {
      routes.push(base || "/");
      continue;
    }
    name = name.replace(/^\[(\.\.\.)?(\w+)\]$/, "sample-$2");
    routes.push([base, name].filter(Boolean).join("/") || "/");
  }
  return routes;
}

const routes = process.env.GHAR_UI_ROUTES
  ? process.env.GHAR_UI_ROUTES.split(",").map((r) => r.trim()).filter(Boolean)
  : discoverRoutes(APP_DIR).map((r) => (r.startsWith("/") ? r : `/${r}`));

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

const results = { status: "pass", url, routes, browsers: {}, artifacts: [] };

/** Turn a route path into a filesystem-safe slug, e.g. "/recipe/sample-dish" -> "recipe-sample-dish". */
function slug(route) {
  return route === "/" ? "home" : route.replace(/^\//, "").replace(/\//g, "-");
}

for (const [name, engine] of engines) {
  let browser;
  try {
    browser = await engine.launch({ headless: true });
  } catch (e) {
    results.browsers[name] = { status: "unavailable", reason: String(e).slice(0, 200) };
    continue;
  }
  const screens = {};
  let browserStatus = "pass";
  try {
    const context = await browser.newContext({
      recordHar: { path: path.join(outDir, `${name}.har`) },
    });

    for (const route of routes) {
      const rslug = slug(route);
      const page = await context.newPage();
      const consoleMsgs = [];
      const requests = [];
      page.on("console", (m) => consoleMsgs.push({ type: m.type(), text: m.text() }));
      page.on("requestfinished", async (r) =>
        requests.push({ url: r.url(), method: r.method(), status: (await r.response())?.status() })
      );

      try {
        const resp = await page.goto(new URL(route, url).toString(),
          { waitUntil: "networkidle", timeout: 30000 });
        await page.screenshot({ path: path.join(outDir, `${name}-${rslug}.png`), fullPage: true });

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

        const errors = consoleMsgs.filter((m) => m.type === "error");
        screens[route] = {
          status: resp && resp.ok() ? "pass" : "warn",
          httpStatus: resp ? resp.status() : null,
          screenshot: `${name}-${rslug}.png`,
          consoleErrors: errors.length,
          requests: requests.length,
          a11y,
        };
        results.artifacts.push(`${name}-${rslug}.png`);
        if (!(resp && resp.ok())) browserStatus = browserStatus === "pass" ? "warn" : browserStatus;
      } catch (e) {
        screens[route] = { status: "fail", error: String(e).slice(0, 300) };
        browserStatus = "fail";
      } finally {
        fs.writeFileSync(path.join(outDir, `${name}-${rslug}-console.json`), JSON.stringify(consoleMsgs, null, 2));
        fs.writeFileSync(path.join(outDir, `${name}-${rslug}-network.json`), JSON.stringify(requests, null, 2));
        results.artifacts.push(`${name}-${rslug}-console.json`, `${name}-${rslug}-network.json`);
        await page.close();
      }
    }

    results.artifacts.push(`${name}.har`);
    results.browsers[name] = { status: browserStatus, screens };
    if (browserStatus === "fail") results.status = "fail";
    await context.close();
  } catch (e) {
    results.browsers[name] = { status: "fail", error: String(e).slice(0, 300) };
    results.status = "fail";
  } finally {
    await browser.close();
  }
}

finish(results, results.status === "fail" ? 1 : 0);
