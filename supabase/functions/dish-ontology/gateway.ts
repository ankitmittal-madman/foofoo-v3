import type { FoodOntologyReadMode } from "../_shared/config/config.ts";
import type { TelemetrySink } from "../_shared/telemetry/telemetry.ts";

export type OntologyRead =
  | { action: "meal_classes" }
  | {
    action: "candidates";
    classCode: string;
    role: string;
    limit: number;
    slot?: string;
    diet?: string;
  }
  | { action: "ontology_record"; dishId?: string; name?: string };

export interface GatewayOptions {
  mode: FoodOntologyReadMode;
  serviceUrl: string | null;
  serviceToken: string | null;
  redisUrl: string | null;
  redisToken: string | null;
  cacheSeconds: number;
  traceId: string;
  traceParent?: string;
  telemetry: TelemetrySink;
  fetcher?: typeof fetch;
}

function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${
      Object.entries(value as Record<string, unknown>).sort(([a], [b]) => a.localeCompare(b))
        .map(([key, child]) => `${JSON.stringify(key)}:${stable(child)}`).join(",")
    }}`;
  }
  return JSON.stringify(value);
}

async function digest(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(stable(value));
  return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)))
    .map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export class RedisRestCache {
  constructor(
    private readonly url: string,
    private readonly token: string,
    private readonly fetcher: typeof fetch = fetch,
  ) {}

  private async command(command: unknown[]): Promise<unknown> {
    const response = await this.fetcher(this.url, {
      method: "POST",
      headers: { authorization: `Bearer ${this.token}`, "content-type": "application/json" },
      body: JSON.stringify(command),
    });
    if (!response.ok) throw new Error(`ontology_cache_http_${response.status}`);
    const body = await response.json() as { result?: unknown; error?: string };
    if (body.error) throw new Error("ontology_cache_command_failed");
    return body.result;
  }

  async get(namespace: string, identity: unknown): Promise<unknown | null> {
    const version = String(await this.command(["GET", `foofoo:ontology:v:${namespace}`]) ?? "0");
    const key = `foofoo:ontology:${namespace}:${version}:${await digest(identity)}`;
    const result = await this.command(["GET", key]);
    return typeof result === "string" ? JSON.parse(result) : null;
  }

  async set(namespace: string, identity: unknown, value: unknown, seconds: number): Promise<void> {
    const version = String(await this.command(["GET", `foofoo:ontology:v:${namespace}`]) ?? "0");
    const key = `foofoo:ontology:${namespace}:${version}:${await digest(identity)}`;
    await this.command(["SET", key, JSON.stringify(value), "EX", seconds]);
  }

  async invalidate(namespace: string): Promise<void> {
    await this.command(["INCR", `foofoo:ontology:v:${namespace}`]);
  }
}

export class FoodOntologyGateway {
  private readonly fetcher: typeof fetch;
  private readonly cache: RedisRestCache | null;

  constructor(private readonly options: GatewayOptions) {
    this.fetcher = options.fetcher ?? fetch;
    this.cache = options.redisUrl && options.redisToken
      ? new RedisRestCache(options.redisUrl, options.redisToken, this.fetcher)
      : null;
  }

  private namespace(read: OntologyRead): string {
    return read.action === "meal_classes" ? "classes" : "dish";
  }

  private serviceRequest(read: OntologyRead): { path: string; shape: (value: any) => unknown } {
    if (read.action === "meal_classes") {
      return {
        path: "/v1/meal-classes",
        shape: (value) =>
          (value.items ?? []).map((item: Record<string, unknown>) => ({
            ...item,
            slot: [item.slot],
            is_addon: item.planning_role === "addon",
            planning_role: item.planning_role === "primary"
              ? "MAIN_PRIMARY"
              : item.planning_role === "addon"
              ? "ADDON_ONLY_NOT_PRIMARY"
              : "COMBO_TEMPLATE_NOT_PRIMARY",
          })),
      };
    }
    if (read.action === "candidates") {
      const params = new URLSearchParams({ role: read.role, limit: String(read.limit) });
      if (read.slot) params.set("slot", read.slot);
      if (read.diet) params.set("diet", read.diet);
      return {
        path: `/v1/meal-classes/${encodeURIComponent(read.classCode)}/dishes?${params}`,
        shape: (value) =>
          (value.items ?? []).map((item: Record<string, unknown>) => ({
            ...item,
            dish_id: item.id,
            name: item.canonical_name,
            item_role: read.role,
            class_code: read.classCode,
          })),
      };
    }
    const shapeRecord = (value: Record<string, unknown>) => ({
      schema_version: "1",
      dish: {
        id: value.id,
        name: value.canonical_name,
        description: value.description,
        status: value.status,
      },
      aliases: value.aliases ?? [],
      ingredients: [],
      meal_classes: value.class_memberships ?? [],
      taxonomy: Object.entries((value.fields ?? {}) as Record<string, unknown>).map(
        ([field_key, field]) => ({ field_key, ...(field as Record<string, unknown>) }),
      ),
      constraints: [],
      regional_affinities: [],
      nutrition: [],
      recipes: [],
      meal_episodes: [],
      relationships: value.relationships ?? [],
      images: value.images ?? [],
      evidence: [],
    });
    if (read.dishId) {
      return { path: `/v1/dishes/${encodeURIComponent(read.dishId)}`, shape: shapeRecord };
    }
    const params = new URLSearchParams({ name: read.name ?? "" });
    return { path: `/v1/dishes:resolve?${params}`, shape: shapeRecord };
  }

  private async service(read: OntologyRead): Promise<unknown> {
    if (!this.options.serviceUrl || !this.options.serviceToken) {
      throw new Error("food_ontology_service_not_configured");
    }
    const namespace = this.namespace(read);
    if (this.cache) {
      try {
        const cached = await this.cache.get(namespace, read);
        if (cached !== null) {
          this.options.telemetry.recordMetric("ontology.gateway.cache_hit", 1, { namespace });
          return cached;
        }
      } catch {
        this.options.telemetry.recordMetric("ontology.gateway.cache_error", 1, {
          operation: "get",
        });
      }
    }
    const request = this.serviceRequest(read);
    const start = performance.now();
    const response = await this.fetcher(
      `${this.options.serviceUrl.replace(/\/$/, "")}${request.path}`,
      {
        headers: {
          authorization: `Bearer ${this.options.serviceToken}`,
          "x-request-id": this.options.traceId,
          ...(this.options.traceParent ? { traceparent: this.options.traceParent } : {}),
        },
        signal: AbortSignal.timeout(1500),
      },
    );
    this.options.telemetry.recordMetric(
      "ontology.gateway.origin_latency_ms",
      Math.round(performance.now() - start),
      {
        action: read.action,
        status: response.status,
      },
    );
    if (!response.ok) throw new Error(`food_ontology_service_http_${response.status}`);
    const value = request.shape(await response.json());
    if (this.cache) {
      try {
        await this.cache.set(namespace, read, value, this.options.cacheSeconds);
      } catch {
        this.options.telemetry.recordMetric("ontology.gateway.cache_error", 1, {
          operation: "set",
        });
      }
    }
    return value;
  }

  async read(read: OntologyRead, legacy: () => Promise<unknown>): Promise<unknown> {
    if (this.options.mode === "legacy") return await legacy();
    if (this.options.mode === "service") {
      const value = await this.service(read);
      this.options.telemetry.recordMetric("ontology.gateway.route", 1, {
        route: "service",
        action: read.action,
      });
      return value;
    }
    const legacyValue = await legacy();
    try {
      const serviceValue = await this.service(read);
      const matched = await digest(legacyValue) === await digest(serviceValue);
      this.options.telemetry.recordMetric("ontology.gateway.shadow_match", matched ? 1 : 0, {
        action: read.action,
      });
    } catch (error) {
      this.options.telemetry.captureError(error, {
        component: "food_ontology_gateway",
        mode: "shadow",
        action: read.action,
      });
    }
    return legacyValue;
  }
}
