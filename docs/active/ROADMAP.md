# Roadmap

Only future work, strictly ordered. Full detail/evidence for every item:
`docs/active/OPEN_ITEMS.md`. Source audit: `docs/archive/audits/re_audit_v2/`.

## P0
1. Investigate the recommendation-events vs. plan-persistence gap (P0-1)
2. Decide the fate of the two parallel recommendation surfaces (P0-3)
3. Feedback UI on the actively-routed screens (P0-4, depends on #2)
4. Wire DPDP export/delete into the mobile app (P0-2)

## P1
5. Recommendation-explanation UI (P1-2, depends on #2)
6. Profile/preferences-edit screen (P1-4)
7. History/past-plans view (P1-3)
8. Enable Supabase leaked-password-protection (P1-1)
9. Real monitoring/alerting (P1-7)
10. Mobile automated test coverage (P1-5, highest value once #2-7 stabilize)
11. Wire IDF-cosine distance into pairing/scoring (P1-6, needs a Founder decision)

## P2
12. Expand nutrition data coverage
13. Expand comfort-hero mapping coverage
14. Populate PRIOR table for PanIndia/Global zones
15. Fix per-row RLS `auth.uid()` re-evaluation
16. Add a staging/approval gate before auto-deploy
17. Pin Docker image by digest
18. Archive dead `re_engine`-era ETL/validation scripts
19. Resolve unindexed-FK/duplicate-index findings

## P3
20. Festival calendar mapping
21. Disease/health-condition dish suitability
22. Activate `s_pref` personalization (gated on real feedback volume)
23. Build a real multi-hop knowledge graph
24. Load-test at full catalogue scale, re-size Fly.io machine
</content>
