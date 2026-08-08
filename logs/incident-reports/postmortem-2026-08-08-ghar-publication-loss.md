# Incident Postmortem — Generic Ghar deploy removed the governed catalogue publication
Date: 2026-08-08 | Severity: High | Status: Resolved

## Summary

A direct production deployment used the repository's generic Fly workflow equivalent, which did
not embed or configure the governed 642-row recommendation catalogue publication. Ghar remained
healthy and retained its immutable 810-dish fallback bundle, but the published-catalogue boundary
reported `configured=false` until a publication-preserving deployment restored it.

## Timeline

| Time (UTC) | Event |
|---|---|
| 17:41:20 | Fly release 145 completed from the generic deploy path. |
| Shortly after 17:41 | The `/v1/meta` smoke check detected that published catalogue configuration had disappeared. |
| 17:42:39 | Reusing the prior image as release 146 confirmed that image rollback alone could not restore missing runtime configuration. |
| 17:45:28 | Release 147 completed with the exact governed publication artifact, required build mode and runtime directory. |
| After 17:45 | `/readyz`, machine checks and `/v1/meta` verified the exact 642-row publication version. |
| 18:05:57 | Release 148 deployed the recommendation-quality repair through the same publication-preserving procedure and passed verification. |

## Impact

The affected interval was about four minutes. The exact number of requests during that interval is
not established. There was no outage, data loss, catalogue mutation or feedback corruption: Ghar
could still serve from its immutable fallback bundle. Requests during the interval may have missed
the intended production-published catalogue candidate boundary.

## Root cause

`.github/workflows/fly_deploy.yml` exposed a manual production job that ran a plain `flyctl deploy`.
That path neither downloaded the governed publication artifact nor passed
`GHAR_RE_PUBLICATION_REQUIRED=true` and `GHAR_RE_PUBLISHED_CATALOGUE_DIR`. Fly therefore replaced the
machine configuration with a valid but publication-unaware release. The dedicated
`recommendation-catalogue-ghar-deploy.yml` already contained the required safeguards, but the
generic workflow provided a second, weaker production path.

## What would have caught this sooner

A static workflow regression requiring a single production deployment path would have prevented
the release. The existing live metadata smoke check caught the condition immediately after deploy,
which bounded the incident, but the generic workflow checked only `/readyz`; readiness alone cannot
prove catalogue identity.

## Action items

| Item | Owner | Status |
|---|---|---|
| Remove production from the generic Fly workflow so it can target staging only. | Recommendation platform | Complete |
| Add the deployment-path regression to recommendation CI. | Recommendation platform | Complete |
| Keep exact publication version and row-count checks in every production Ghar deployment. | Recommendation platform | Complete |
| Reduce the oversized Fly build context to shorten recovery and deployment time. | Recommendation platform | Open |

## Blameless note

This postmortem documents a system gap, not an individual mistake. The goal is preventing
recurrence, not assigning fault.
