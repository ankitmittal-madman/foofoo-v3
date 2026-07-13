# Foofoo — Product Roadmap
**PM-SUPP-01 · Version 1.0 · June 2026**

> Phases are gates, not timelines. A phase begins only when the previous phase passes its go/no-go criteria.

---

## Phase overview

| Phase | Timeline | Goal | DAU target | Revenue |
|---|---|---|---|---|
| **MVP — Soft launch** | Weeks 1–14 build + 90-day test | Validate: do users come back daily? | 0 → 500 | ₹0 — fully free |
| **Phase 0.5 — Full product** | Weeks 15–20 | Full feature set on both stores | 500 → 2,000 | ₹0 — free period |
| **Phase TBD — Deferred features** | TBD | F-24, F-27, F-28, F-46, F-50, F-57 assigned | TBD | TBD |
| **Phase 1 — Public launch** | Weeks 21–28 | Public launch + content marketing | 2,000 → 10,000 | Ads + Premium visible |
| **Phase 1.5 — Monetisation** | Weeks 29–36 | Paywall activates (Day 90+) | 10,000 → 30,000 | Premium + Ads active |
| **Phase 2 — Depth** | Weeks 37–50 | Health profiles + RE v3 + cluster | 30,000 → 75,000 | All subscription tiers |
| **Phase 3 — Partnerships** | Year 2 | Zomato/Swiggy + grocery integration | 75,000 → 200,000 | Affiliate + subscriptions |
| **Year 2+ — Scale** | Year 2+ | Full ML + B2B exploration | 200,000+ | All streams |

---

## Phase detail

### MVP — Soft launch (Weeks 1–14 build + 90 days)
**Goal:** Prove one thing — daily habit formation. 500 DAU is the verdict.

| | |
|---|---|
| **Key features** | F-01 to F-23, F-25, F-30–F-31, F-33–F-34, F-37, F-39, F-55–F-56, F-58, F-59 |
| **RE version** | classfirst_v1 (rule-based, cohort priors, MMR variety, bandit) |
| **Unlock trigger** | 5 of 8 MVP metrics hit at Day 90. Zero RE constraint violations. |
| **Revenue** | ₹0. All users free. |

### Phase 0.5 (Weeks 15–20)
**Goal:** Full product depth. iOS + Android. Recipes. Pantry.

| | |
|---|---|
| **Key features** | F-26 (recipes), F-29 (smart grocery), F-38 (evening notification), F-51 (social login), F-54 (pantry) |
| **RE version** | classfirst_v1 continued |
| **Unlock trigger** | 500 DAU sustained 14 consecutive days |
| **Revenue** | ₹0. Free period continues. |

### Phase TBD — Deferred features
**Goal:** F-24, F-27, F-28, F-46, F-50, F-57 assigned to a specific phase by founder.

> ⚠️ These features are ready to implement. They require a phase assignment decision at the next planning session.

### Phase 1 — Public launch (Weeks 21–28)
**Goal:** Open to public. Content marketing. Mood selector. Calorie targeting.

| | |
|---|---|
| **Key features** | F-32 (explore), F-35 (diary), F-40 (RE v2 personal learning), F-41 (mood selector), F-42 (calorie targeting), F-43 (fitness mode) |
| **RE version** | classfirst_v2 (+ personal history learning) |
| **Unlock trigger** | D7 retention > 30%, acceptance > 40% |
| **Revenue** | Ads go live (free tier). Premium visible. |

### Phase 1.5 — Monetisation (Weeks 29–36)
**Goal:** Paywall activates. Family profiles. Full freemium model.

| | |
|---|---|
| **Key features** | F-36 (family profiles), F-47 (Premium ₹99), F-48 (Premium Plus ₹149), F-49 (ads optimised) |
| **RE version** | classfirst_v2 continued |
| **Unlock trigger** | 1,000 DAU. D30 retention > 25%. |
| **Revenue** | Premium ₹99 + Premium Plus ₹149 + Ads |

### Phase 2 — Depth (Weeks 37–50)
**Goal:** Health profiles. Festival calendar. RE cluster mode at 5K+ DAU.

| | |
|---|---|
| **Key features** | F-44 (RE v3 cluster), F-45 (festival calendar), health profiles, meal insights dashboard |
| **RE version** | cluster_v1 (cluster-based cold start when base > 5K DAU) |
| **Unlock trigger** | ₹1L MRR. 5,000 DAU. |
| **Revenue** | All subscription tiers. Affiliate prep. |

### Phase 3 — Partnerships (Year 2)
**Goal:** Zomato/Swiggy API. Grocery delivery. Social features.

| | |
|---|---|
| **Key features** | F-52 (Blinkit/Zepto), F-53 (Zomato/Swiggy API), social/sharing features |
| **RE version** | ltr_v1 (Learning-to-Rank) — if 10K+ labeled events |
| **Unlock trigger** | 10,000 DAU. Product-market fit confirmed. |
| **Revenue** | Affiliate commissions + all subscriptions |

---

## RE evolution by phase

| RE version | Phase | What changes |
|---|---|---|
| classfirst_v1 | MVP | Rule-based. Cohort priors. MMR variety. Bandit exploration. |
| classfirst_v2 | Sprint 6 | + Personal history learning. Weights auto-adjust per user. |
| classfirst_v3 | Phase 1 | + Dish embeddings (Word2Vec). Better cross-cuisine match. |
| cluster_v1 | Phase 2 | + Cluster-based cold start. New users matched to clusters. |
| ltr_v1 | Phase 3 | Learning-to-Rank replaces hand-tuned weights. New API /v2. |
| ml_v1 | Year 2+ | Two-tower + neural ranking + CF (ALS). Full ML stack. |

---

## Revenue milestones

| Phase | Revenue event | Target |
|---|---|---|
| MVP | ₹0. Build the product. | 500 DAU at Day 90 |
| Phase 0.5 | ₹0. Extend the product. | 2,000 MAU |
| Phase 1 | Ads go live (free tier). | ₹8–15/free user/month |
| Phase 1.5 | Paywall activates. | 3–5% conversion → ₹60K–2L MRR |
| Phase 2 | Subscriptions scale. | ₹4L–12.5L MRR |
| Phase 3 | Affiliate commissions. | ₹12.5L–30L MRR |
| Year 2+ | All streams + B2B. | ₹30L+ MRR |

---

## Phase TBD features — pending founder decision

| Feature | What it is |
|---|---|
| F-24 | Order Instead CTA (Swiggy/Zomato deeplink) |
| F-27 | Auto-generated grocery list |
| F-28 | Ingredient check-off |
| F-46 | Freemium tier visible (₹0 during trial) |
| F-50 | Referral programme |
| F-57 | Daily email digest (13 metrics) |

---

*Source documents: DOC-04 PRD v1.1, DOC-08 Revenue, RE-DOC-05*
