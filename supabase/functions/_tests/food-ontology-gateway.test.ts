import { assertEquals } from "@std/assert";
import { FoodOntologyGateway, RedisRestCache } from "../dish-ontology/gateway.ts";

class Telemetry {
  metrics: Array<{ name: string; value: number; fields?: Record<string, unknown> }> = [];
  errors: unknown[] = [];
  captureError(error: unknown): void {
    this.errors.push(error);
  }
  recordMetric(name: string, value: number, fields?: Record<string, unknown>): void {
    this.metrics.push({ name, value, fields });
  }
}

Deno.test("legacy gateway does not contact the ontology service", async () => {
  let calls = 0;
  const gateway = new FoodOntologyGateway({
    mode: "legacy",
    serviceUrl: null,
    serviceToken: null,
    redisUrl: null,
    redisToken: null,
    cacheSeconds: 300,
    traceId: "trace-legacy",
    telemetry: new Telemetry(),
    fetcher: () => {
      calls += 1;
      throw new Error("unexpected fetch");
    },
  });
  assertEquals(await gateway.read({ action: "meal_classes" }, () => Promise.resolve(["legacy"])), [
    "legacy",
  ]);
  assertEquals(calls, 0);
});

Deno.test("service gateway forwards trace and translates the class response", async () => {
  const telemetry = new Telemetry();
  const gateway = new FoodOntologyGateway({
    mode: "service",
    serviceUrl: "https://ontology.example",
    serviceToken: "secret-token",
    redisUrl: null,
    redisToken: null,
    cacheSeconds: 300,
    traceId: "trace-service",
    telemetry,
    fetcher: (input, init) => {
      assertEquals(String(input), "https://ontology.example/v1/meal-classes");
      assertEquals(new Headers(init?.headers).get("x-request-id"), "trace-service");
      return Promise.resolve(Response.json({
        items: [{ class_code: "BF_POHA", slot: "breakfast", planning_role: "primary" }],
      }));
    },
  });
  assertEquals(
    await gateway.read({ action: "meal_classes" }, () => Promise.resolve([])),
    [{
      class_code: "BF_POHA",
      slot: ["breakfast"],
      is_addon: false,
      planning_role: "MAIN_PRIMARY",
    }],
  );
  assertEquals(telemetry.metrics.some((item) => item.name === "ontology.gateway.route"), true);
});

Deno.test("shadow failure is observed but legacy remains authoritative", async () => {
  const telemetry = new Telemetry();
  const gateway = new FoodOntologyGateway({
    mode: "shadow",
    serviceUrl: "https://ontology.example",
    serviceToken: "secret-token",
    redisUrl: null,
    redisToken: null,
    cacheSeconds: 300,
    traceId: "trace-shadow",
    telemetry,
    fetcher: () => Promise.resolve(new Response(null, { status: 503 })),
  });
  assertEquals(
    await gateway.read({ action: "meal_classes" }, () => Promise.resolve(["legacy"])),
    ["legacy"],
  );
  assertEquals(telemetry.errors.length, 1);
});

Deno.test("Redis cache keys are namespace-versioned and invalidated with INCR", async () => {
  const commands: unknown[][] = [];
  const cache = new RedisRestCache(
    "https://redis.example",
    "redis-token",
    (_input, init) => {
      const command = JSON.parse(String(init?.body)) as unknown[];
      commands.push(command);
      const result = command[0] === "GET" ? null : "OK";
      return Promise.resolve(Response.json({ result }));
    },
  );
  await cache.set("dish", { id: "1" }, { name: "Poha" }, 300);
  await cache.invalidate("dish");
  assertEquals(commands[0], ["GET", "foofoo:ontology:v:dish"]);
  assertEquals(commands[1][0], "SET");
  assertEquals(commands[2], ["INCR", "foofoo:ontology:v:dish"]);
});
