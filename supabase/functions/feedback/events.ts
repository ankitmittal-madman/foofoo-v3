/**
 * feedback_events writer (WP-15 — POST /v1/feedback, wired to migration 038's table).
 *
 * Unlike recommendations/events.ts's recordRecommendationEvent (best-effort telemetry alongside
 * an already-successful response), a failed write HERE is the entire point of the request failing
 * — the caller needs to know their feedback wasn't recorded so a client can retry, since (per
 * migration 038's own comment) this history "cannot be back-filled retroactively" once the
 * moment passes.
 *
 * Two lookups happen before the insert, both deliberate:
 *   1. The caller supplies `request_id` (RecommendationsResponse.request_id — the ONLY
 *      recommendation identifier the mobile client is ever given; recommendation_events.id, the
 *      DB row's own uuid PK, is never echoed to the client). This is resolved server-side to that
 *      recommendation_events row, scoped to the calling profile (defense-in-depth ownership check
 *      — RLS is bypassed under the service-role client used here, same as every other Edge
 *      Function; see auth/authenticate.ts's own module doc).
 *   2. dish_name (what the mobile client actually has — plate.hero_dish_names, not a
 *      public.dishes uuid) is resolved to dish_id by exact name lookup. A miss is NOT an error:
 *      public.dishes and the RE's own catalogue are two separately-synced data sources (the same
 *      class of gap this session's WP-15 already found and disclosed for the KB comfort-hero
 *      table) — the feedback row is still recorded, with dish_id left null and the miss logged,
 *      rather than rejecting a user's real feedback over a data-sync gap.
 */
import { createServiceRoleClient } from "../_shared/db/client.ts";
import { AppError } from "../_shared/errors/app-error.ts";
import { API_ERRORS } from "../_shared/errors/api-catalogue.ts";
import { ERROR_CATALOGUE } from "../_shared/errors/catalogue.ts";
import type { RequestContext } from "../_shared/types/context.ts";
import { withTimeout } from "../_shared/utils/timeout.ts";
import type { FeedbackEventType } from "../_shared/validation/feedback-schema.ts";
import { recordProductEvent } from "../_shared/analytics/product-events.ts";

export interface FeedbackEventInput {
  /** Authenticated actor who supplied this feedback. */
  actorProfileId: string;
  /** Household whose recommendation/outcome/state is affected. */
  householdId: string;
  /** RecommendationsResponse.request_id — see module doc for why this, not the DB row's uuid PK. */
  requestId: string;
  eventType: FeedbackEventType;
  dishName?: string;
  slot?: string;
  detail?: Record<string, unknown>;
}

export interface FeedbackEventResult {
  id: string;
  createdAt: string;
  dishResolved: boolean;
}

const OUTCOME_BY_FEEDBACK: Partial<Record<FeedbackEventType, string>> = {
  accept: "chosen",
  like: "liked",
  dislike: "disliked",
  never: "disliked",
  make_this: "chosen",
  lock: "locked",
  cooked: "cooked",
  ordered: "ordered",
  replaced: "replaced",
  completed: "completed",
  regretted: "regretted",
};

export function slateItemMatchesDish(
  decisionTrace: unknown,
  requestedDishName: string,
): boolean {
  if (!decisionTrace || typeof decisionTrace !== "object") return false;
  const trace = decisionTrace as Record<string, unknown>;
  const wanted = requestedDishName.trim().toLocaleLowerCase("en-IN");
  const direct = typeof trace.dish_name === "string" ? trace.dish_name : undefined;
  const snapshot = trace.dish_snapshot && typeof trace.dish_snapshot === "object"
    ? trace.dish_snapshot as Record<string, unknown>
    : undefined;
  const episode = trace.episode_snapshot && typeof trace.episode_snapshot === "object"
    ? trace.episode_snapshot as Record<string, unknown>
    : undefined;
  const components = Array.isArray(episode?.components)
    ? episode.components as Array<Record<string, unknown>>
    : [];
  return [direct, snapshot?.name, ...components.map((component) => component.dish_name)]
    .some((name) => typeof name === "string" && name.trim().toLocaleLowerCase("en-IN") === wanted);
}

async function syncTypedIntelligence(
  ctx: RequestContext,
  db: ReturnType<typeof createServiceRoleClient>,
  ev: FeedbackEventInput,
  eventId: string,
  occurredAt: string,
): Promise<void> {
  // Recompute every taste projection from canonical feedback history. This is deliberately an
  // idempotent RPC rather than a client-side read/modify/write delta: retries repair stale state,
  // concurrent member feedback cannot lose an update, and exact-dish evidence generalizes into
  // meal-class and genome dimensions for related-dish discovery.
  const { error: tasteStateError } = await withTimeout(
    db.rpc("refresh_user_taste_vector", { p_profile_id: ev.actorProfileId }),
    "feedback.events.refresh_user_taste_vector",
  );
  if (tasteStateError) {
    throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: tasteStateError.message });
  }

  const outcomeType = OUTCOME_BY_FEEDBACK[ev.eventType];
  if (outcomeType) {
    let episodeHash = typeof ev.detail?.episode_hash === "string" ? ev.detail.episode_hash : null;
    const { data: slateRows, error: slateError } = await withTimeout(
      db.from("slates").select("id").eq("household_id", ev.householdId).eq(
        "request_id",
        ev.requestId,
      ).limit(1),
      "feedback.events.slate_lookup",
    );
    if (slateError) throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: slateError.message });
    const slateId = slateRows?.[0]?.id ?? null;
    // Dish-card feedback usually carries only the canonical display name. Resolve it back to the
    // exact served item so outcome attribution remains point-in-time rather than joining to the
    // user's latest slate later. Older clients need no new payload field for this.
    if (!episodeHash && slateId && ev.dishName) {
      const { data: itemRows, error: itemError } = await withTimeout(
        db.from("slate_items").select("episode_hash,decision_trace").eq("slate_id", slateId)
          .order("rank", { ascending: true }).limit(100),
        "feedback.events.slate_item_lookup",
      );
      if (itemError) {
        throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: itemError.message });
      }
      const matching = itemRows?.find((row) =>
        slateItemMatchesDish(row.decision_trace, ev.dishName!)
      );
      episodeHash = matching?.episode_hash ?? null;
    }
    const { error } = await withTimeout(
      db.from("outcome_events").upsert({
        idempotency_key: eventId,
        household_id: ev.householdId,
        profile_id: ev.actorProfileId,
        slate_id: slateId,
        episode_hash: episodeHash,
        outcome_type: outcomeType,
        value: ev.detail ?? {},
        source: "explicit",
        confidence: 1,
        occurred_at: occurredAt,
        schema_version: "1",
      }, { onConflict: "idempotency_key" }),
      "feedback.events.outcome_upsert",
    );
    if (error) throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: error.message });
  }

  // Missing-item evidence updates pantry state only when the user/client identifies the exact
  // ingredient. A generic rejection must never guess which ingredient was absent.
  if (ev.eventType === "missing_ingredient" && typeof ev.detail?.ingredient_name === "string") {
    const ingredientName = ev.detail.ingredient_name.trim();
    const { data: ingredient, error: lookupError } = await withTimeout(
      db.from("ingredients").select("id").eq("name", ingredientName).maybeSingle(),
      "feedback.events.ingredient_lookup",
    );
    if (lookupError) throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: lookupError.message });
    if (ingredient) {
      const expiry = new Date();
      expiry.setUTCDate(expiry.getUTCDate() + 7);
      const { error } = await withTimeout(
        db.from("pantry_beliefs").upsert({
          household_id: ev.householdId,
          ingredient_id: ingredient.id,
          probability_present: 0.02,
          quantity_range: {},
          last_evidence_at: occurredAt,
          evidence_type: "explicit_missing_ingredient",
          expires_at: expiry.toISOString(),
          feature_version: "pantry-belief-v1",
          updated_at: new Date().toISOString(),
        }, { onConflict: "household_id,ingredient_id" }),
        "feedback.events.pantry_upsert",
      );
      if (error) throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: error.message });
    } else {
      ctx.logger.warn("feedback_event.ingredient_not_found", { ingredient_name: ingredientName });
    }
  }

  // Recompute rather than increment: duplicate retries and concurrent household-member actions
  // converge on the durable feedback history and cannot double-count lifecycle progress.
  const { error: reStateError } = await withTimeout(
    db.rpc("refresh_user_re_state", { p_profile_id: ev.householdId }),
    "feedback.events.refresh_user_re_state",
  );
  if (reStateError) {
    throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: reStateError.message });
  }
}

/**
 * Record one feedback event, after resolving the caller's `request_id` to its
 * recommendation_events row and verifying that row belongs to the authorized household.
 * @throws AppError ERR_RECOMMENDATION_EVENT_NOT_FOUND (404) if request_id matches no row for this household.
 * @throws AppError ERROR_CATALOGUE.INTERNAL (500) if a lookup/the insert itself fails (the caller should retry).
 */
export async function recordFeedbackEvent(
  ctx: RequestContext,
  ev: FeedbackEventInput,
): Promise<FeedbackEventResult> {
  const db = createServiceRoleClient(ctx.config);

  // Scope the served request to the authorized household. Actor identity is intentionally
  // separate so each member's feedback remains attributable without exposing other households.
  const { data: recRows, error: recErr } = await withTimeout(
    db
      .from("recommendation_events")
      .select("id, profile_id, household_id")
      .eq("request_id", ev.requestId)
      .eq("household_id", ev.householdId)
      .order("created_at", { ascending: false })
      .limit(1),
    "feedback.events.lookup_recommendation_event",
  );
  if (recErr) {
    ctx.logger.warn("feedback_event.lookup_recommendation_event_failed", {
      request_id: ev.requestId,
      detail: recErr.message,
    });
    throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: recErr.message });
  }
  const recRow = recRows?.[0];
  if (!recRow) {
    throw new AppError(API_ERRORS.ERR_RECOMMENDATION_EVENT_NOT_FOUND, {
      context: { request_id: ev.requestId },
    });
  }

  let dishId: string | null = null;
  let dishResolved = false;
  let canonicalDishName = ev.dishName;
  if (ev.dishName) {
    const { data: dishRow, error: dishErr } = await withTimeout(
      db.from("dishes").select("id,name").ilike("name", ev.dishName).limit(1).maybeSingle(),
      "feedback.events.lookup_dish",
    );
    if (dishErr) {
      // A dish-lookup failure must not block recording the feedback itself — log and continue
      // with dish_id=null, same "don't lose real signal over a secondary lookup" principle as
      // the miss case below.
      ctx.logger.warn("feedback_event.dish_lookup_failed", {
        dish_name: ev.dishName,
        detail: dishErr.message,
      });
    } else if (dishRow) {
      dishId = dishRow.id as string;
      canonicalDishName = String(dishRow.name);
      dishResolved = true;
    } else {
      // Serving and database catalogues can temporarily disagree on display spelling. Resolve
      // through the governed alias ontology before accepting an identity-less feedback row.
      const { data: aliases, error: aliasError } = await withTimeout(
        db.from("dish_name_synonyms").select("dish_id,confidence,dishes(name)")
          .ilike("synonym", ev.dishName).order("confidence", { ascending: false }).limit(1),
        "feedback.events.lookup_dish_alias",
      );
      if (aliasError) {
        ctx.logger.warn("feedback_event.dish_alias_lookup_failed", {
          dish_name: ev.dishName,
          detail: aliasError.message,
        });
      } else if (aliases?.[0]) {
        const alias = aliases[0] as Record<string, unknown>;
        const joined = alias.dishes as { name?: unknown } | Array<{ name?: unknown }> | null;
        const joinedName = Array.isArray(joined) ? joined[0]?.name : joined?.name;
        dishId = String(alias.dish_id);
        canonicalDishName = typeof joinedName === "string" ? joinedName : ev.dishName;
        dishResolved = true;
      } else {
        // The ingestion pipeline keeps source-derived aliases separate from the curated synonym
        // ontology. Both are identity evidence and must resolve feedback to the same canonical ID.
        const { data: importedAliases, error: importedAliasError } = await withTimeout(
          db.from("dish_aliases").select("dish_id,confidence,dishes(name)")
            .ilike("alias_text", ev.dishName).order("confidence", { ascending: false }).limit(1),
          "feedback.events.lookup_imported_dish_alias",
        );
        if (importedAliasError) {
          ctx.logger.warn("feedback_event.imported_dish_alias_lookup_failed", {
            dish_name: ev.dishName,
            detail: importedAliasError.message,
          });
        }
        if (importedAliases?.[0]) {
          const alias = importedAliases[0] as Record<string, unknown>;
          const joined = alias.dishes as { name?: unknown } | Array<{ name?: unknown }> | null;
          const joinedName = Array.isArray(joined) ? joined[0]?.name : joined?.name;
          dishId = String(alias.dish_id);
          canonicalDishName = typeof joinedName === "string" ? joinedName : ev.dishName;
          dishResolved = true;
        } else {
          ctx.logger.warn("feedback_event.dish_not_found_in_public_dishes", {
            dish_name: ev.dishName,
          });
        }
      }
    }
  }

  // Client retries are safe: one intent per served recommendation/dish/event. Return the original
  // result without applying its affinity delta twice.
  const existingQuery = db.from("feedback_events").select("id,created_at").eq(
    "profile_id",
    ev.actorProfileId,
  ).eq("recommendation_event_id", recRow.id).eq("event_type", ev.eventType);
  const { data: existing, error: existingError } = await withTimeout(
    dishId === null
      ? existingQuery.is("dish_id", null)
        .contains("detail", ev.dishName ? { dish_name: ev.dishName } : {})
        .maybeSingle()
      : existingQuery.eq("dish_id", dishId).maybeSingle(),
    "feedback.events.idempotency_lookup",
  );
  if (existingError) {
    throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: existingError.message });
  }
  if (existing) {
    await syncTypedIntelligence(
      ctx,
      db,
      ev,
      existing.id as string,
      existing.created_at as string,
    );
    return { id: existing.id as string, createdAt: existing.created_at as string, dishResolved };
  }

  const { data: inserted, error } = await withTimeout(
    db
      .from("feedback_events")
      .insert({
        profile_id: ev.actorProfileId,
        household_id: ev.householdId,
        recommendation_event_id: recRow.id,
        dish_id: dishId,
        event_type: ev.eventType,
        slot: ev.slot ?? null,
        detail: {
          ...(ev.detail ?? {}),
          ...(ev.dishName ? { dish_name: ev.dishName } : {}),
          ...(canonicalDishName && canonicalDishName !== ev.dishName
            ? { canonical_dish_name: canonicalDishName }
            : {}),
        },
        data_source: "real",
      })
      .select("id, created_at")
      .single(),
    "feedback.events.insert",
  );
  if (error) {
    ctx.logger.warn("feedback_event.insert_failed", {
      profile_id: ev.actorProfileId,
      household_id: ev.householdId,
      request_id: ev.requestId,
      event_type: ev.eventType,
      detail: error.message,
    });
    throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: error.message });
  }

  // Apply explicit intent and a bounded online preference update synchronously. A successful
  // feedback response therefore guarantees that the next recommendation reads the new state.
  // Values are deliberately small and clamped; explicit Never/Not-Today use hard exclusions.
  if (ev.dishName) {
    if (dishId && ev.eventType === "never") {
      const { error: stateError } = await withTimeout(
        db.from("never_list").upsert({
          profile_id: ev.householdId,
          dish_id: dishId,
          nevered_at: new Date().toISOString(),
          is_active: true,
        }, { onConflict: "profile_id,dish_id" }),
        "feedback.events.never",
      );
      if (stateError) throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: stateError.message });
    } else if (dishId && ev.eventType === "not_today") {
      const effectiveUntil = new Date();
      effectiveUntil.setUTCHours(18, 30, 0, 0); // next IST midnight when still ahead
      if (effectiveUntil <= new Date()) effectiveUntil.setUTCDate(effectiveUntil.getUTCDate() + 1);
      const { error: stateError } = await withTimeout(
        db.from("not_today_suppression").upsert({
          profile_id: ev.householdId,
          dish_id: dishId,
          suppressed_at: new Date().toISOString(),
          effective_until: effectiveUntil.toISOString(),
          is_active: true,
        }, { onConflict: "profile_id,dish_id" }),
        "feedback.events.not_today",
      );
      if (stateError) throw new AppError(ERROR_CATALOGUE.INTERNAL, { detail: stateError.message });
    }
  }

  await syncTypedIntelligence(
    ctx,
    db,
    ev,
    inserted.id as string,
    inserted.created_at as string,
  );

  ctx.logger.info("feedback_event.recorded", {
    id: inserted.id,
    profile_id: ev.actorProfileId,
    household_id: ev.householdId,
    request_id: ev.requestId,
    event_type: ev.eventType,
    dish_resolved: dishResolved,
  });
  await recordProductEvent(ctx, {
    profileId: ev.actorProfileId,
    householdId: ev.householdId,
    eventName: `recommendation_${ev.eventType}`,
    requestId: ev.requestId,
    dishId,
    properties: {
      household_id: ev.householdId,
      slot: ev.slot ?? null,
      dish_name: ev.dishName ?? null,
      canonical_dish_name: canonicalDishName ?? null,
    },
  });

  return { id: inserted.id as string, createdAt: inserted.created_at as string, dishResolved };
}
