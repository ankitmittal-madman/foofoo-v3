/**
 * DPDP data-subject-rights API (P0-2, 2026-08) — GET /v1/user/export[/{job_id}] and
 * POST /v1/user/delete. Both Edge Functions already existed and were fully authorized/working;
 * this file is the first mobile-side caller for either (previously unreachable from any screen —
 * see docs/active/OPEN_ITEMS.md P0-2).
 */
import { apiGet, apiPost } from "./client";

export interface ExportJobResponse {
  export_job_id: string;
  status: "queued" | "complete";
  estimated_completion?: string;
  download_url?: string;
  format?: string;
}

/** Start (or, per the backend's synchronous-MVP design, effectively complete) an export job. */
export function requestExport(): Promise<ExportJobResponse> {
  return apiGet<ExportJobResponse>("/user/export");
}

/** Poll a previously-created export job for its signed download URL. */
export function pollExport(exportJobId: string): Promise<ExportJobResponse> {
  return apiGet<ExportJobResponse>(`/user/export/${exportJobId}`);
}

export interface DeleteAccountResponse {
  deletion_job_id: string;
  soft_deleted_at: string;
  hard_delete_estimated_by: string;
}

/** The exact, case-sensitive phrase the backend requires (user-delete/schema.ts) — surfaced here
 * so the UI can show the user precisely what to type, not a paraphrase that would never match. */
export const REQUIRED_CONFIRMATION_PHRASE = "DELETE MY ACCOUNT";

export function deleteAccount(userId: string, confirmationPhrase: string): Promise<DeleteAccountResponse> {
  return apiPost<DeleteAccountResponse>("/user/delete", {
    user_id: userId,
    confirmation_phrase: confirmationPhrase,
  });
}
