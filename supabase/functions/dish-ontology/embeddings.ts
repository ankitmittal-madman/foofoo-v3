/** Local, free, no-API-key embeddings via the Supabase Edge Runtime's built-in gte-small model.
 *
 * This is the correct free-local-embedding primitive for a Deno Edge Function (Python
 * sentence-transformers has no runtime home here) -- it runs in-process, has no rate limit, and
 * needs no secret. Used to give migration 128's cosine-similarity vocabulary function real
 * embeddings to compare against, and by the one-time backfill function that populates
 * meal_classes.embedding / cuisines.embedding.
 */

// deno-lint-ignore no-explicit-any -- Supabase is a Deno Edge Runtime global, not an importable type.
declare const Supabase: any;

let session: unknown;

/** Lazily create the shared gte-small inference session (loads the model once per isolate). */
function getSession(): { run(input: string, opts: Record<string, unknown>): Promise<number[]> } {
  if (!session) {
    session = new Supabase.ai.Session("gte-small");
  }
  return session as { run(input: string, opts: Record<string, unknown>): Promise<number[]> };
}

/** Embed one text string into a 384-dim vector. Callers must treat a thrown error as best-effort. */
export async function embedText(text: string): Promise<number[]> {
  const result = await getSession().run(text, { mean_pool: true, normalize: true });
  if (!Array.isArray(result) || result.length !== 384) {
    throw new Error("gte_small_unexpected_output_shape");
  }
  return result;
}

/** Format a 384-dim embedding for a pgvector RPC argument (Postgres vector literal syntax). */
export function toVectorLiteral(embedding: number[]): string {
  return `[${embedding.join(",")}]`;
}
