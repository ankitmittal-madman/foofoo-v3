/** Deliver due, consented morning-plan jobs through OneSignal. Service-role only. */
import { jsonOk } from "../_shared/api/response.ts";
import { requireServiceRole } from "../_shared/auth/service-role.ts";
import { createServiceRoleClient } from "../_shared/db/client.ts";
import {
  buildContext,
  compose,
  errorBoundary,
  requestLogging,
} from "../_shared/middleware/index.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";

const pipeline = compose([errorBoundary, requestLogging, requireServiceRole()])(
  async (_req, ctx) => {
    if (!ctx.config.oneSignalAppId || !ctx.config.oneSignalRestApiKey) {
      return jsonOk({ processed: 0, status: "provider_not_configured" }, ctx.traceId, 200);
    }
    const db = createServiceRoleClient(ctx.config);
    const { data: jobs, error } = await withTimeout(
      db.from("notification_jobs").select("id,profile_id,payload,attempts")
        .in("status", ["pending", "failed"]).lte("scheduled_for", new Date().toISOString())
        .lt("attempts", 3).limit(100),
      "notifications.load_due",
    );
    if (error) throw error;
    let sent = 0;
    for (const job of jobs ?? []) {
      const { data: consent } = await db.from("consent_records").select("granted")
        .eq("profile_id", job.profile_id).eq("consent_type", "push_notifications")
        .order("granted_at", { ascending: false }).limit(1).maybeSingle();
      if (!consent?.granted) {
        await db.from("notification_jobs").update({ status: "cancelled" }).eq("id", job.id);
        continue;
      }
      const response = await fetch("https://api.onesignal.com/notifications", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          authorization: `Key ${ctx.config.oneSignalRestApiKey}`,
        },
        body: JSON.stringify({
          app_id: ctx.config.oneSignalAppId,
          include_aliases: { external_id: [job.profile_id] },
          target_channel: "push",
          headings: { en: job.payload?.title ?? "Your Foofoo plan is ready" },
          contents: { en: job.payload?.body ?? "See today's household meal plan." },
          data: { route: job.payload?.route ?? "/today" },
        }),
      });
      const responseBody = await response.json().catch(() => ({}));
      await db.from("notification_jobs").update(
        response.ok
          ? {
            status: "sent",
            provider_message_id: responseBody.id ?? null,
            attempts: job.attempts + 1,
          }
          : { status: "failed", last_error: `HTTP ${response.status}`, attempts: job.attempts + 1 },
      )
        .eq("id", job.id);
      if (response.ok) sent++;
    }
    return jsonOk({ processed: jobs?.length ?? 0, sent }, ctx.traceId, 200);
  },
);

Deno.serve((req: Request) => pipeline(req, buildContext(req)));
