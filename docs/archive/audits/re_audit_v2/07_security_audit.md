STATUS: ARCHIVED
Reason: Superseded by docs/active/ (2026-08-04 documentation restructure). This audit remains the evidentiary source for docs/active/CURRENT_STATUS.md, OPEN_ITEMS.md, ROADMAP.md, and LAUNCH_BLOCKERS.md.

# Security Audit (fresh, 2026-08-04) — live-verified via Supabase advisors this session

| Area | Status | Evidence |
|---|---|---|
| RLS coverage | Implemented correctly | Every user-facing table has RLS + a real ownership policy; internal-only tables' "RLS enabled, no policy" state is reviewed/intentional (no client grants exist) |
| Auth model | Implemented | Supabase JWT (gateway `verify_jwt=true`) + in-function `authenticate()` re-check on every non-cron function; cron functions require service_role key instead of a user JWT |
| Secrets handling | Implemented | HMAC shared secret lives only in Fly's/Supabase's encrypted stores, never committed; `FOOFOO_ENV=production` arms a fail-closed guard that refuses to start without the real secret |
| Secret leaks in source | **None found** | Grepped for key/secret/password/token literal patterns across all source files — zero hits outside placeholder/example values. `mobile/.env` (real anon key + URL) is untracked (`.gitignore`'d, confirmed via `git ls-files`) and Supabase anon keys are designed to be public client-side — not a leak. |
| DPDP data-subject rights | **Real gap, not a security hole but a legal-compliance gap** | `user-export`/`user-delete` Edge Functions are implemented and correctly authorized, but have zero mobile UI callers — users cannot exercise export/delete rights today |
| Leaked-password protection | **Disabled** | Supabase Auth setting, one-click fix, currently off |
| RLS performance pattern | Minor, not urgent | Several policies call `auth.uid()` per-row instead of `(select auth.uid())` — real fix, low urgency at current table sizes |
| HMAC trust boundary (RE service) | Implemented, deliberate design | Public ingress is a documented, founder-confirmed decision since Edge Functions can't join Fly's private mesh; HMAC-SHA256 over raw bytes, constant-time compare, replay window >5 min rejected, checked before body parse |
| Docker image pinning | Pinned by tag, not digest | Explicitly noted as a known, not-yet-hardened gap in the Dockerfile's own comment |
| Auto-deploy on push to main | No staging/approval gate | `fly_deploy.yml` deploys on every push to `main` with no separate review step |

## Overall
No P0 security vulnerabilities found (no leaked secrets, RLS is correctly enforced, auth is real).
The two real findings that matter are legal/compliance (DPDP export/delete unreachable) and
operational hygiene (leaked-password-protection off, no deploy gate) rather than exploitable
security holes.
</content>
