# FooFoo Backend (`supabase/`)

Backend engineering foundation (WP-8B), implementing the architecture approved in
**DOC-P4-00** (WP-8A). Runtime: **Supabase Edge Functions (Deno/TypeScript) over PostgreSQL.**

> This folder is the backend code tree. The database schema, migrations, seeds, and validation
> remain the source of truth in the repo's `database/` tree — never duplicated here.

## Layout
- `functions/_shared/` — the shared engineering foundation (this WP). Import surface: `_shared/mod.ts`.
  - `config/` typed env loader · `db/` Supabase client factories · `auth/` JWT + authorization guards
  - `middleware/` compose + context/error/logging · `validation/` zod wrapper · `errors/` AppError + catalogue
  - `logging/` structured logger · `telemetry/` observability hooks · `repositories/` + `services/` base classes
  - `api/` response envelope + handler wrapper · `di/` per-request container · `types/` · `constants/` · `utils/`
- `functions/_tests/` — foundation bootstrap tests.
- `functions/<endpoint>/` — Edge Functions (added WP-8C onward — none yet).
- `scripts/` — `verify.sh` (fmt/lint/check/test), `gen-types.sh` (schema → TS types).
- `config.toml` — local Supabase stack config. `deno.json` — tasks + imports + fmt/lint config.

## What is NOT here yet (later WPs)
No endpoints, no recommendation-engine logic, no auth flows, no CRUD, no business logic. Only the foundation.

## Local development
```bash
# from supabase/
deno task verify      # fmt --check + lint + check + test
supabase start        # local Postgres+Auth+Functions (applies ../database migrations)
```

## Environment (DOC-P3-08 §Env; secrets server-side only, DOC-P3-07 §14)
Required: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
Optional: `SUPABASE_DB_URL`, `OPENWEATHERMAP_API_KEY`, `USDA_FOODDATA_API_KEY`,
`GROQ_API_KEY`, `GROQ_MODEL`, `HF_TOKEN`, `AI_FREE_DAILY_REQUEST_BUDGET`,
`AI_FREE_DAILY_TOKEN_BUDGET`, `AI_MIN_USABLE_CONFIDENCE`,
`AI_DIRECT_PUBLISH_CONFIDENCE`, `ONESIGNAL_REST_API_KEY`, `CLOUDINARY_CLOUD_NAME`,
`FOOFOO_ENV`, `LOG_LEVEL`.

Production ontology defaults are Groq `openai/gpt-oss-120b`, 800 requests/160,000 tokens per UTC
day, candidate retention at 0.65 and direct low-risk publication at 0.80. The model is never an
authority for nutrition, allergens, religious/clinical suitability or other safety-sensitive facts.

## Deploy discipline
Edge Functions deploy via Supabase CLI under the same numbered-migration discipline as the schema
(DOC-P3-08 §14). CI runs fmt/lint/check/test + the DB safety gates; **production deploys are
Founder-approved only** (env map locked: local / `foofoo-staging` / `foofoo-mvp`).
