STATUS: ARCHIVED
Reason: Superseded by docs/active/ (2026-08-04 documentation restructure). This audit remains the evidentiary source for docs/active/CURRENT_STATUS.md, OPEN_ITEMS.md, ROADMAP.md, and LAUNCH_BLOCKERS.md.

# Deployment Audit (fresh, 2026-08-04) — live-verified, not assumed from config

## What was actually verified live (this session)
```
curl https://ghar-re.fly.dev/healthz  → {"status":"alive"}
curl https://ghar-re.fly.dev/readyz   → {"status":"ready"}
curl https://ghar-re.fly.dev/v1/meta  → real bundle_version, engine_version, zero-initialized metrics
```
**The RE service is deployed and healthy right now.** This is a live check, not a config-file
assumption.

## What is merely configured (not independently re-verified live this session)
- Fly.io `min_machines_running=1`, rolling deploy strategy, HMAC-only public ingress — all declared
  in `fly.toml`, consistent with the live health check above, but the specific claims (e.g. "no
  scale-to-zero ever happens," "rollback works") were not separately load-tested.
- `fly_deploy.yml` auto-deploys every push to `main` with no staging/approval gate — confirmed by
  reading the workflow file; not independently tested by triggering a real deploy in this session.
- Docker image pinned by tag, not digest — a real, stated gap in the Dockerfile's own comment.
- Monitoring/alerting: `/v1/meta`'s metrics object exists and returns real (zero) counters, but no
  external alerting on those counters was found anywhere (see security/observability findings) —
  if the service goes down, nothing pages anyone.
- Disaster recovery / rollback: `fly deploy --image <previous-ref>` is documented as the rollback
  mechanism in `ghar_re_service/README.md`; not tested live this session.
- Scaling: single `shared-cpu-1x`/512MB machine, explicitly sized for the smaller golden-sample
  catalogue and flagged in its own comment to be re-measured now that the real 810-dish catalogue
  is live — not load-tested this session.

## Bottom line
Deployment is real and the service is healthy right now — this is the strongest-verified area of
the whole audit precisely because it was checked live rather than inferred. The gaps that remain
(monitoring/alerting, load-testing at 810-dish scale, rollback drill, image digest pinning) are all
real but none of them are "is it deployed" questions — that one is settled: yes.
</content>
