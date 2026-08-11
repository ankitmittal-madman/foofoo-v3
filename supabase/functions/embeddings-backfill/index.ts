/** Service-only, idempotent backfill: populates meal_classes.embedding / cuisines.embedding
 * (migration 128) via the Edge Runtime's local gte-small model, so
 * ai_enrichment_closed_vocabulary_by_embedding has real vectors to compare against.
 *
 * Re-run safe: only rows where embedding IS NULL are processed, so a partial run (timeout,
 * transient gte-small failure) just picks up the remaining rows on the next call rather than
 * redoing completed work. Not on the cron schedule -- run manually (or wire into a low-frequency
 * cron) after schema changes to meal_classes/cuisines display names.
 */
import { jsonOk } from "../_shared/api/response.ts";
import { requireServiceRole } from "../_shared/auth/service-role.ts";
import { createServiceRoleClient } from "../_shared/db/client.ts";
import { buildContext, compose, errorBoundary, requestLogging } from "../_shared/middleware/index.ts";
import { embedText, toVectorLiteral } from "../dish-ontology/embeddings.ts";

const pipeline = compose([errorBoundary, requestLogging, requireServiceRole()])(
  async (_req, ctx) => {
    const db = createServiceRoleClient(ctx.config);
    let classesEmbedded = 0;
    let cuisinesEmbedded = 0;
    const failures: string[] = [];

    const { data: classes, error: classesError } = await db
      .from("meal_classes")
      .select("class_code, display_name")
      .is("embedding", null);
    if (classesError) throw classesError;
    for (const row of classes ?? []) {
      try {
        const embedding = await embedText(String(row.display_name));
        const { error } = await db.from("meal_classes")
          .update({ embedding: toVectorLiteral(embedding) })
          .eq("class_code", row.class_code);
        if (error) throw error;
        classesEmbedded++;
      } catch (error) {
        failures.push(
          `meal_classes:${row.class_code}:${error instanceof Error ? error.message.slice(0, 80) : "error"}`,
        );
      }
    }

    const { data: cuisines, error: cuisinesError } = await db
      .from("cuisines")
      .select("id, display_name")
      .is("embedding", null);
    if (cuisinesError) throw cuisinesError;
    for (const row of cuisines ?? []) {
      try {
        const embedding = await embedText(String(row.display_name));
        const { error } = await db.from("cuisines")
          .update({ embedding: toVectorLiteral(embedding) })
          .eq("id", row.id);
        if (error) throw error;
        cuisinesEmbedded++;
      } catch (error) {
        failures.push(
          `cuisines:${row.id}:${error instanceof Error ? error.message.slice(0, 80) : "error"}`,
        );
      }
    }

    return jsonOk({ classesEmbedded, cuisinesEmbedded, remaining: failures.length, failures }, ctx.traceId);
  },
);

Deno.serve((req: Request) => pipeline(req, buildContext(req)));
