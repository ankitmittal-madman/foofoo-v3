/** Authenticated longitudinal meal-diary API for explicitly enrolled research participants. */
import { jsonContract } from "../_shared/api/response.ts";
import { requireAuth } from "../_shared/auth/authorize.ts";
import { authenticate } from "../_shared/auth/authenticate.ts";
import { createServiceRoleClient } from "../_shared/db/client.ts";
import { defineHandler } from "../_shared/api/handler.ts";

Deno.serve(defineHandler(async (req, ctx) => {
  const claims = requireAuth(ctx.claims);
  const body = await req.json() as Record<string, unknown>;
  const action = String(body.action ?? "status");
  const db = createServiceRoleClient(ctx.config);
  const { data: participants, error: participantError } = await db.rpc(
    "research_participation_status",
    { p_user_id: claims.userId },
  );
  if (participantError) throw participantError;

  if (action === "status") {
    return jsonContract(
      { kind: "research_participation", enrollments: participants ?? [] },
      ctx.traceId,
    );
  }
  if (action === "submit_diary") {
    const studyId = String(body.study_id ?? "");
    const participant = Array.isArray(participants)
      ? participants.find((row) => String(row.study_id) === studyId)
      : null;
    if (!participant) throw new Error("research_enrollment_required");
    const { data, error } = await db.rpc("research_submit_meal_diary", {
      p_user_id: claims.userId,
      p_payload: body,
    });
    if (error) throw error;
    return jsonContract({ kind: "meal_diary", diary_id: data }, ctx.traceId, 201);
  }
  throw new Error("unsupported_research_panel_action");
}, { middleware: [authenticate()] }));
