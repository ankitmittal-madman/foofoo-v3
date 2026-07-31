/**
 * Deterministic id derivation (Phase F, user-delete wiring).
 *
 * DOC-P3-06 §08: "Repeated calls [to POST /v1/user/delete] on an already-soft-deleted profile
 * should return the existing deletion_job_id, not create a second one." No job-tracking table
 * exists in the live schema (would need a migration — flagged separately, out of this task's
 * scope), so instead of persisting a job id anywhere, this derives the SAME id every time from
 * `profile_id` (a stable input the caller already provides) — a repeat call naturally reproduces
 * the identical answer without needing storage. SHA-256-based, RFC 4122 §4.3 name-based (v5-style)
 * construction: deterministic, not guessable from the profile_id alone (needs the salt too), and
 * collision-safe in the same sense any content hash is.
 */
const encoder = new TextEncoder();

/** A deterministic, UUID-shaped id derived from `salt:seed` — same inputs always produce the same
 * output; different salts produce unrelated ids from the same seed (so this can be reused for more
 * than one job-id namespace without cross-namespace collisions). */
export async function deterministicUuid(salt: string, seed: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(`${salt}:${seed}`));
  const bytes = new Uint8Array(digest).slice(0, 16);
  // RFC 4122 §4.3: set version (5) and variant (RFC 4122) bits so this is a syntactically valid UUID.
  bytes[6] = (bytes[6] & 0x0f) | 0x50;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${
    hex.slice(20)
  }`;
}
