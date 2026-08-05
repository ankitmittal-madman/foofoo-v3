/** Service-only annotation operations for governed research and ontology review batches. */
import { jsonOk } from "../_shared/api/response.ts";
import { requireServiceRole } from "../_shared/auth/service-role.ts";
import { createServiceRoleClient } from "../_shared/db/client.ts";
import {
  buildContext,
  compose,
  errorBoundary,
  requestLogging,
} from "../_shared/middleware/index.ts";

const pipeline = compose([errorBoundary, requestLogging, requireServiceRole()])(
  async (req, ctx) => {
    const body = await req.json() as Record<string, unknown>;
    const action = String(body.action ?? "");
    const db = createServiceRoleClient(ctx.config);

    if (action === "create_batch") {
      const { data, error } = await db.rpc("research_create_annotation_batch", { p_payload: body });
      if (error) throw error;
      return jsonOk({ batch_id: data }, ctx.traceId, 201);
    }

    if (action === "queue_items") {
      const batchId = String(body.batch_id ?? "");
      const items = Array.isArray(body.items) ? body.items as Record<string, unknown>[] : [];
      const { data, error } = await db.rpc("research_queue_annotation_items", {
        p_batch_id: batchId,
        p_items: items,
      });
      if (error) throw error;
      return jsonOk({ queued: data ?? 0 }, ctx.traceId, 201);
    }

    if (action === "claim") {
      const { data, error } = await db.rpc("research_claim_annotation_items", {
        p_batch_id: String(body.batch_id ?? ""),
        p_annotator_token: String(body.annotator_token ?? ""),
        p_limit: Math.max(1, Math.min(50, Number(body.limit ?? 10))),
      });
      if (error) throw error;
      return jsonOk({ items: data ?? [] }, ctx.traceId);
    }

    if (action === "annotate") {
      const annotationItemId = String(body.annotation_item_id ?? "");
      const { data, error } = await db.rpc("research_record_annotation", {
        p_payload: { ...body, annotation_item_id: annotationItemId },
      });
      if (error) throw error;
      return jsonOk({ annotation_id: data }, ctx.traceId, 201);
    }

    throw new Error("unsupported_research_annotation_action");
  },
);

Deno.serve((req: Request) => pipeline(req, buildContext(req)));
