import AsyncStorage from "@react-native-async-storage/async-storage";
import { ApiError, CLIENT_ERROR_CODES, apiPost } from "./client";
import type { FeedbackRequest, FeedbackResponse } from "./types";
import { logger } from "../lib/logger";

const QUEUE_KEY = "foofoo.feedbackQueue.v1";

interface QueuedFeedback {
  body: FeedbackRequest;
  queuedAt: string;
}

async function loadQueue(): Promise<QueuedFeedback[]> {
  const raw = await AsyncStorage.getItem(QUEUE_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

async function saveQueue(queue: QueuedFeedback[]): Promise<void> {
  if (queue.length === 0) await AsyncStorage.removeItem(QUEUE_KEY);
  else await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

function isRetryableTransportFailure(error: unknown): boolean {
  return error instanceof ApiError &&
    (error.code === CLIENT_ERROR_CODES.NETWORK_ERROR || error.code === CLIENT_ERROR_CODES.TIMEOUT);
}

/** Flushes queued feedback in order. Stops at the first transport failure to preserve ordering. */
export async function flushFeedbackQueue(): Promise<number> {
  const queue = await loadQueue();
  let delivered = 0;
  while (queue.length > 0) {
    try {
      await apiPost<FeedbackResponse>("/feedback", queue[0].body);
      queue.shift();
      delivered += 1;
    } catch (error) {
      if (isRetryableTransportFailure(error)) break;
      // A permanent server rejection should not poison every later queued event.
      logger.warn("feedback.queue_drop", {
        event_type: queue[0].body.event_type,
        detail: error instanceof Error ? error.message : String(error),
      });
      queue.shift();
    }
  }
  await saveQueue(queue);
  return delivered;
}

/**
 * POST /v1/feedback (WP-15) — records what the caller actually did with a served plate/dish
 * against the recommendation identified by `request_id` (the id echoed back in
 * RecommendationsResponse, NOT any id the client would have to look up separately). This is the
 * Online dish/class affinities are updated by the backend and loaded on the next plan request.
 * Transport failures are durably queued so kitchen feedback is not lost on poor connectivity.
 */
export function postFeedback(body: FeedbackRequest): Promise<FeedbackResponse> {
  return apiPost<FeedbackResponse>("/feedback", body).catch(async (error: unknown) => {
    if (!isRetryableTransportFailure(error)) throw error;
    const queue = await loadQueue();
    queue.push({ body, queuedAt: new Date().toISOString() });
    await saveQueue(queue);
    logger.info("feedback.queued", { event_type: body.event_type, queue_size: queue.length });
    return {
      id: `queued:${queue.length}`,
      event_type: body.event_type,
      recorded_at: new Date().toISOString(),
      trace_id: "offline",
      queued: true,
    };
  });
}
