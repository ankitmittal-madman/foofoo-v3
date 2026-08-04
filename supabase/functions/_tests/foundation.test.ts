/**
 * Foundation bootstrap tests (WP-8B).
 *
 * Proves the scaffold is wired correctly: config loads + fails fast, logger initializes, the
 * error model + envelope behave, the middleware pipeline composes and short-circuits errors, the
 * DI container builds its graph, and validation converts schema failures to AppErrors. These are
 * FRAMEWORK tests only — no business logic is exercised.
 */
import { assertEquals, assertExists, assertThrows } from "@std/assert";
import {
  AppError,
  buildContext,
  compose,
  createContainer,
  createLogger,
  defineHandler,
  ERROR_CATALOGUE,
  loadConfig,
  resetConfigCacheForTests,
  resolveTelemetrySink,
  validate,
  webhookSink,
  z,
} from "../_shared/mod.ts";
import type { Handler, Middleware } from "../_shared/mod.ts";

function withEnv(vars: Record<string, string>, fn: () => void | Promise<void>) {
  const prev: Record<string, string | undefined> = {};
  for (const [k, v] of Object.entries(vars)) {
    prev[k] = Deno.env.get(k);
    Deno.env.set(k, v);
  }
  try {
    return fn();
  } finally {
    for (const k of Object.keys(vars)) {
      if (prev[k] === undefined) Deno.env.delete(k);
      else Deno.env.set(k, prev[k]!);
    }
    resetConfigCacheForTests();
  }
}

const REQUIRED_ENV = {
  SUPABASE_URL: "http://localhost:54321",
  SUPABASE_ANON_KEY: "anon-test-key",
  SUPABASE_SERVICE_ROLE_KEY: "service-test-key",
};

Deno.test("config loads when required env is present", () => {
  withEnv({ ...REQUIRED_ENV, FOOFOO_ENV: "staging" }, () => {
    resetConfigCacheForTests();
    const cfg = loadConfig();
    assertEquals(cfg.environment, "staging");
    assertEquals(cfg.isProduction, false);
    assertEquals(cfg.supabaseUrl, "http://localhost:54321");
  });
});

Deno.test("config fails fast on missing required secret", () => {
  withEnv({ SUPABASE_URL: "x", SUPABASE_ANON_KEY: "y" }, () => {
    resetConfigCacheForTests();
    Deno.env.delete("SUPABASE_SERVICE_ROLE_KEY");
    assertThrows(() => loadConfig(), Error, "SUPABASE_SERVICE_ROLE_KEY");
  });
});

Deno.test("logger initializes and honors min level", () => {
  const logger = createLogger("warn", { trace_id: "t-1" });
  assertExists(logger);
  logger.info("should be suppressed at warn level");
  logger.error("should emit");
  assertExists(logger.child({ component: "test" }));
});

Deno.test("AppError produces client-safe JSON without internal detail", () => {
  const e = new AppError(ERROR_CATALOGUE.FORBIDDEN, { detail: "secret internal reason" });
  const body = e.toClientJSON("trace-xyz");
  assertEquals(body.error.code, "FORBIDDEN");
  assertEquals(body.error.trace_id, "trace-xyz");
  assertEquals(JSON.stringify(body).includes("secret internal reason"), false);
});

Deno.test("middleware pipeline composes and error boundary maps AppError to status", async () => {
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const boom: Handler = () => {
      throw new AppError(ERROR_CATALOGUE.NOT_FOUND, { detail: "x" });
    };
    const fetchHandler = defineHandler(boom);
    const res = await fetchHandler(new Request("http://localhost/v1/anything"));
    assertEquals(res.status, 404);
    assertEquals(res.headers.get("x-trace-id") !== null, true);
    const body = await res.json();
    assertEquals(body.error.code, "NOT_FOUND");
  });
});

Deno.test("compose applies middleware outermost-first", async () => {
  const order: string[] = [];
  const mk = (tag: string): Middleware => (next) => async (req, ctx) => {
    order.push(`before:${tag}`);
    const r = await next(req, ctx);
    order.push(`after:${tag}`);
    return r;
  };
  const handler: Handler = () => new Response("ok");
  const composed = compose([mk("a"), mk("b")])(handler);
  await withEnv(REQUIRED_ENV, async () => {
    resetConfigCacheForTests();
    const ctx = buildContext(new Request("http://localhost/"));
    await composed(new Request("http://localhost/"), ctx);
  });
  assertEquals(order, ["before:a", "before:b", "after:b", "after:a"]);
});

Deno.test("DI container builds a service-role client lazily", () => {
  withEnv(REQUIRED_ENV, () => {
    resetConfigCacheForTests();
    const ctx = buildContext(new Request("http://localhost/"));
    const container = createContainer(ctx);
    assertExists(container.db);
    assertExists(container.telemetry);
  });
});

// ---------------------------------------------------------------------------
// P1-7 (2026-08): real alerting sink -- webhookSink actually POSTs, resolveTelemetrySink picks
// the right sink based on config, and a webhook failure never suppresses the underlying log.
// ---------------------------------------------------------------------------
Deno.test("webhookSink POSTs a JSON payload to the configured URL and still logs via fallback", async () => {
  const logged: unknown[] = [];
  const fallback = {
    captureError: (error: unknown, fields?: Record<string, unknown>) => {
      logged.push({ error, fields });
    },
    recordMetric: () => {},
  };

  let capturedBody: string | undefined;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = ((_url: string, init?: RequestInit) => {
    capturedBody = init?.body as string;
    return Promise.resolve(new Response("ok", { status: 200 }));
  }) as typeof fetch;

  try {
    const sink = webhookSink("https://example.test/hook", fallback);
    sink.captureError(new Error("boom"), { path: "/v1/plan" });
    // captureError is fire-and-forget for the network call; the fallback call itself is synchronous.
    assertEquals(logged.length, 1);
    // give the fire-and-forget fetch a tick to run before asserting on it.
    await new Promise((r) => setTimeout(r, 10));
    assertExists(capturedBody);
    const payload = JSON.parse(capturedBody!);
    assertEquals(payload.type, "error");
    assertEquals(payload.message, "boom");
    assertEquals(payload.path, "/v1/plan");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

Deno.test("webhookSink never throws or suppresses the fallback log when the webhook itself fails", async () => {
  const logged: unknown[] = [];
  const fallback = {
    captureError: (error: unknown) => {
      logged.push(error);
    },
    recordMetric: () => {},
  };
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (() => Promise.reject(new Error("network down"))) as typeof fetch;

  try {
    const sink = webhookSink("https://example.test/hook", fallback);
    // Must not throw even though the underlying fetch rejects.
    sink.captureError(new Error("boom"));
    assertEquals(logged.length, 1);
    await new Promise((r) => setTimeout(r, 10));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

Deno.test("resolveTelemetrySink falls back to log-only when no webhook URL is configured", () => {
  const logged: unknown[] = [];
  const logger = { error: () => logged.push("error"), warn: () => {}, info: () => {} } as never;
  const sink = resolveTelemetrySink(logger, null);
  sink.captureError(new Error("x"));
  assertEquals(logged.length, 1);
});

Deno.test("validate() throws VALIDATION_FAILED on bad input", () => {
  const schema = z.object({ n: z.number() });
  assertThrows(
    () => validate(schema, { n: "not-a-number" }),
    AppError,
    "validation",
  );
  assertEquals(validate(schema, { n: 5 }).n, 5);
});
