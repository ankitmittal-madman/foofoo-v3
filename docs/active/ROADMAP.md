# Roadmap

Only future work is listed here. Evidence and acceptance detail are in `OPEN_ITEMS.md`.

## P1 — Launch readiness

1. Enable Supabase leaked-password protection.
2. Configure the telemetry webhook and verify alert delivery.
3. Run physical-device E2E journeys for offline reconnect and push delivery.

## P2 — Production improvement

4. Expand nutrition coverage beyond 50 of 810 dishes.
5. Expand comfort-hero coverage beyond 17 of 36 resolved heroes.
6. Populate regional priors for PanIndia and Global zones.
7. Configure staging secrets and the protected production environment.
8. Archive dead `re_engine`-era ETL and validation scripts.
9. Resolve unindexed-foreign-key and duplicate-index findings.
10. Deploy and operationally verify the remaining mobile/operational release candidate.
11. Run production load/soak testing and revisit Fly.io sizing.
12. Monitor the ontology-aware production release and legacy fallback for one verified rollout
    window, then decide whether the fallback can be removed.

## P3 — Product and intelligence evolution

13. Approve and activate the unknown-dish AI classification policy.
14. Add festival-calendar mapping.
15. Add clinically governed health-condition suitability.
16. Activate preference personalization after a real training threshold is met.
17. Expand and safety-review the bounded food graph.
