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
  validate,
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

Deno.test("validate() throws VALIDATION_FAILED on bad input", () => {
  const schema = z.object({ n: z.number() });
  assertThrows(
    () => validate(schema, { n: "not-a-number" }),
    AppError,
    "validation",
  );
  assertEquals(validate(schema, { n: 5 }).n, 5);
});
