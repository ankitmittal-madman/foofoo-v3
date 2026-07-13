# Foofoo — Consolidated Risk Register
**PM-SUPP-02 · Version 1.0 · June 2026**

> All risks consolidated from DOC-01, DOC-02, DOC-04, DOC-07, DOC-08, DOC-09, and RE-DOC-05.

**Scoring:** Likelihood × Impact. Score ≥ 15 = Critical 🔴 | 8–14 = High 🟠 | < 8 = Manageable 🟢

**Release blockers:** R-007, R-011, R-018 — cannot launch without resolution.

---

## Product risks

| ID | Risk | Like | Impact | Score | Mitigation | Trigger | Owner |
|---|---|---|---|---|---|---|---|
| R-001 | Cold-start plan quality fails Day 0 | 4 | 4 | **16** 🔴 | RE v1 class-first pipeline. Unit test all 5 cohorts. Monitor Day-0 acceptance daily for first 14 days. | Day-0 acceptance < 20% for 3 consecutive days | Engineering |
| R-002 | Onboarding drop-off > 30% at any single screen | 4 | 3 | **12** 🟠 | Test each OB screen in beta. Cut any screen with > 30% drop-off. OB-00 (no skip) is highest risk. | Funnel analytics show > 30% drop at any step | Product |
| R-003 | Never rate > 25% in first 30 days | 3 | 4 | **12** 🟠 | Monitor cohort-level never rates. Recalibrate cohort class matrix manually if any cohort elevated. | Never rate > 25% for any cohort for 7 consecutive days | Engineering |
| R-004 | Habit loop fails — Day-7 retention < 20% | 3 | 5 | **15** 🔴 | A/B test notification copy. Investigate plan quality vs notification as drop driver. | Day-7 retention < 20% across all cohorts | Product |
| R-005 | OB-08b plan preview creates wrong expectation | 3 | 3 | **9** 🟠 | Preview uses real RE v1 output — no mock plans. Improve RE before showing preview. | Preview rated 'not relevant' > 40% of the time | Product |
| R-006 | Dish database incomplete at launch | 4 | 4 | **16** 🔴 | Content audit gate: 500 dishes fully tagged with photo, ingredients, class code. 2 weeks before launch. | Content audit finds > 50 dishes with missing data | Content + Engineering |

---

## Technical / RE risks

| ID | Risk | Like | Impact | Score | Mitigation | Trigger | Owner |
|---|---|---|---|---|---|---|---|
| R-007 | Hard constraint violation — allergen/diet fails 🚫 | 1 | 5 | **5** 🟢 | SQL safety-gate queries — release blocker. Integer allergen matching. Automated. | Any safety-gate query returns > 0 rows | Engineering |
| R-008 | RE response time > 3 seconds on budget Android | 3 | 4 | **12** 🟠 | Load test on reference device before launch. Cache plan for morning notification. | P95 plan generation > 3 seconds for 2+ consecutive days | Engineering |
| R-009 | App crash rate > 1% | 2 | 4 | **8** 🟠 | Sentry from Day 1. Zero known P0 crashes before launch. Test on physical Android 8, 10, 12 + iOS 14, 16. | Crash rate > 0.5% per session for 48h | Engineering |
| R-010 | RE confidence score consistently < 0.4 | 3 | 3 | **9** 🟠 | Monitor confidence score distribution. If median < 0.5 at Day 7, investigate onboarding and cohort matrix. | Median confidence < 0.5 at Day 7 for onboarding-complete users | Engineering |
| R-011 | Allergen violation reaches user with severe allergy 🚫 | 1 | 5 | **5** 🟢 | Allergen disclaimer in onboarding. Safety gate as release blocker. Duplicate of R-007 for severity awareness. | User reports seeing allergen-containing dish | Engineering + Founder |
| R-012 | Free tier infrastructure hits limits before 500 DAU | 2 | 3 | **6** 🟢 | Capacity model before launch. Alert at 70% of free tier. Supabase Pro = $25/month as fallback. | Usage exceeds 70% of free tier limits before 500 DAU | Engineering |

---

## Market / competitive risks

| ID | Risk | Like | Impact | Score | Mitigation | Trigger | Owner |
|---|---|---|---|---|---|---|---|
| R-013 | Zomato/Swiggy builds 'what to eat' feature | 3 | 4 | **12** 🟠 | Accelerate. Their feature will be restaurant-centric. Double down on household intelligence moat. | Zomato/Swiggy announces meal planning feature | Founder |
| R-014 | HealthifyMe pivots to household meal planning | 2 | 3 | **6** 🟢 | Different positioning (health goals, ₹999+/month). We own everyday household utility. | HealthifyMe launches household planning product | Founder |
| R-015 | New funded startup enters meal decision space | 2 | 3 | **6** 🟢 | Dish genome + 41-persona cohort model not replicable quickly. Execute faster. User data is compounding moat. | Competitor raises funding for meal decision product | Founder |
| R-016 | App store discovery too slow — organic installs insufficient | 4 | 3 | **12** 🟠 | ASO Day 1. Personal network launch (100+ direct WhatsApp). Housing society groups. | Month 2 install rate < 50/week organic | Founder |
| R-017 | Meera persona underrepresented in early users | 3 | 3 | **9** 🟠 | Target housing society WhatsApp groups, homemaker forums. Personal recommendation is primary mechanic. | Beta users predominantly Riya or Vikram persona | Founder |

---

## Legal / compliance risks

| ID | Risk | Like | Impact | Score | Mitigation | Trigger | Owner |
|---|---|---|---|---|---|---|---|
| R-018 | App store rejection at submission 🚫 | 3 | 4 | **12** 🟠 | Review Apple guidelines 5.1 + 3.1.1 before submission. No health claims. Test IAP sandbox. 2-week buffer. | App store returns rejection notice | Engineering + Founder |
| R-019 | DPDP Act 2023 compliance gap post-launch | 2 | 5 | **10** 🟠 | Privacy Policy + ToS + DPDP consent mechanism complete before launch. Legal review before submission. | Regulatory enquiry or user data complaint | Founder + Legal |
| R-020 | Allergen liability — user claims product caused harm | 1 | 5 | **5** 🟢 | Allergen disclaimer in onboarding. Medical disclaimer on health features. Safety gate prevents violations. | User complaint or legal notice re: allergen | Founder + Legal |
| R-021 | Dish content IP violation | 2 | 4 | **8** 🟠 | All photos: original, licensed stock, or CC commercial. Ingredient lists not copyrightable. Document every photo licence. | DMCA takedown or IP dispute | Content + Founder |
| R-022 | Trademark dispute over 'Foofoo' name | 2 | 3 | **6** 🟢 | File trademark application (Class 42 + 35) before public launch. Check IP India database. ~₹10,000–15,000. | Cease and desist from existing trademark holder | Founder + Legal |

---

## Financial risks

| ID | Risk | Like | Impact | Score | Mitigation | Trigger | Owner |
|---|---|---|---|---|---|---|---|
| R-023 | Premium conversion rate < 2% at Day 90 | 3 | 4 | **12** 🟠 | 90-day habit. Personalised conversion message. Referral rewards. If < 2%: extend free period 30 days. | Conversion < 2% at Day 90 with > 500 DAU | Founder |
| R-024 | Users churn at Day 90 paywall | 3 | 4 | **12** 🟠 | Non-negotiable 90-day free period. Personalised message. Referral stacking path to free Premium. | D90→D120 retention drops > 30% when paywall activates | Founder |
| R-025 | Apple 30% commission erodes margin | 5 | 3 | **15** 🔴 | Certain risk. Mitigation: annual subscription option, UPI payment via website where legal. Accept as iOS cost. | n/a — certain | Founder |
| R-026 | Infrastructure costs escalate before revenue | 2 | 3 | **6** 🟢 | Alert at 70% free tier. Supabase Pro = $25/month if needed. Affordable at 500+ DAU with 2% conversion. | Monthly infra cost exceeds ₹2,000 before ₹2,000 revenue | Engineering + Founder |

---

## Operational risks

| ID | Risk | Like | Impact | Score | Mitigation | Trigger | Owner |
|---|---|---|---|---|---|---|---|
| R-027 | Dish content quality insufficient at launch | 4 | 4 | **16** 🔴 | Pre-launch content audit: photo quality, ingredient accuracy, class code verification. 2 weeks before launch. | Audit fails > 10% of dishes in any category | Content + Founder |
| R-028 | Claude Code produces incorrect RE implementation | 3 | 4 | **12** 🟠 | Every RE build references RE-DOC non-negotiable rules. Safety gate after every RE change. Human review. | Safety gate violations OR dishes appear in wrong meal slots | Engineering + Founder |
| R-029 | Both founders unavailable simultaneously | 2 | 4 | **8** 🟠 | All decisions in ADRs. Prompts self-contained per DOC-24. Claude Code can continue from documented state. | Both founders unavailable > 5 consecutive working days | Founder |
| R-030 | User support volume overwhelms founders | 3 | 2 | **6** 🟢 | Support email + FAQ before launch. WhatsApp group for beta users. At MVP scale (< 300 users) manageable directly. | > 20 support requests/day requiring individual responses | Founder |

---

## Heat map summary

| Score | Risk IDs | Requires immediate action? |
|---|---|---|
| 🔴 Critical (≥ 15) | R-001, R-004, R-006, R-025, R-027 | Yes — address before or at launch |
| 🟠 High (8–14) | R-002, R-003, R-005, R-008, R-009, R-010, R-013, R-016, R-017, R-018, R-019, R-021, R-023, R-024, R-028, R-029 | Yes — mitigation plan ready before launch |
| 🟢 Manageable (< 8) | R-007, R-011, R-012, R-014, R-015, R-020, R-022, R-026, R-030 | Monitor. Activate mitigation if trigger fires. |

**Release blockers:** R-007 (allergen safety gate) · R-011 (allergen violation) · R-018 (app store rejection)

---

## Review schedule

| Frequency | Action |
|---|---|
| Before every sprint closes | Review Critical + High risks. Check safety gate status. |
| Before every phase gate | Full register review. Update likelihood/impact. Do not proceed if Critical risk unmitigated. |
| Monthly post-launch | Full register. Update status. Add new risks. |
| On trigger event | Execute mitigation plan immediately. Document outcome. |

---

*Source documents: DOC-01, DOC-02, DOC-04, DOC-07, DOC-08, DOC-09, RE-DOC-05*
