---
name: session-knowledge-doc
description: >
  Maintains a living HTML knowledge book for a software project built with AI assistance.
  MUST be used at the end of every Claude Code session — no exceptions — to record what
  was built, changed, touched, or decided. Also use at the start of a session when the
  user says "catch me up", "what did we build", "what's the current state", or opens the
  knowledge book. Multiple developers or AI sessions on the same project all write to the
  same HTML file, so the knowledge book is always the single source of truth.

  Trigger on any of: "end of session", "session done", "wrap up", "document what we built",
  "update the knowledge book", "what did we build", "catch me up", "show me the project state",
  or automatically at natural session close when significant code/DB/config work was done.
---

# Session Knowledge Doc Skill

A living HTML file that grows with every session. Every developer or AI agent working on
the project appends to the same file — it never gets replaced, only extended.

## The one rule above all others

**Never skip this. Never say "I'll do it next time."**
If code was written, a file was changed, a DB column was added, a config was touched,
a decision was made — it goes in the knowledge book. Every session. No exceptions.
This is the non-technical PM's only reliable window into what is being built.

**This includes changes to the knowledge book and skill themselves.** If you edited
`KNOWLEDGE.html` directly, or edited any file under `.claude/skills/session-knowledge-doc/`
(this skill's own templates), that is still "code/files touched" — log it as its own
session before ending your turn, the same as an app feature. Don't wait for the user to
notice it's missing and ask. The fact that the change was to the documentation tool
itself doesn't exempt it from being documented.

## Skill Authority
This skill provides reusable engineering practices.

It must never override:

- Project Documentation
- Architecture
- Governance
- Founder Decisions
- Project Workflow (APDF)

If the project already defines an approach, the project takes precedence.

## Activation
- Activation Type: Automatic
- Recommended Phase: Every Session

---

## Step 1 — Find or create the knowledge book

```bash
# Check if it exists in the project root
ls KNOWLEDGE.html 2>/dev/null && echo "EXISTS" || echo "NEW"
```

- If it **exists**: read it, locate the `<!-- SESSIONS -->` and `<!-- NAV -->` injection
  points, then append. Do NOT rewrite the whole file.
- If it **does not exist**: generate the full shell from the template in
  `assets/shell.html`, then write it as `KNOWLEDGE.html` in the project root.

---

## Step 2 — Gather everything that was touched this session

Before writing a single word of documentation, run these commands to get the facts:

```bash
# All files modified since session start (adjust timeframe as needed)
git diff --name-status HEAD 2>/dev/null || git status --short

# New files added
git ls-files --others --exclude-standard 2>/dev/null

# Recent commits by this session
git log --oneline -10 2>/dev/null

# Supabase migrations added this session
ls supabase/migrations/ 2>/dev/null | tail -5

# Package.json changes (new dependencies)
git diff HEAD package.json 2>/dev/null | grep "^[+-]" | grep -v "^---\|^+++" 2>/dev/null
```

Do not document from memory. Always verify from actual file state.

For every file touched that doesn't already have a Module Reference entry (see Step 4a),
read its actual source before writing anything about it:
```bash
# Header comment / JSDoc block at the top of a touched file
head -20 path/to/file.ts

# Exported functions, to see what the module's surface area actually is
grep -n "^export " path/to/file.ts

# SQL doc comments on a touched migration
grep -n "^--\|COMMENT ON" path/to/migration.sql
```
The plain-English module description must come from what the code/SQL comments actually
say, not be invented. If a file has no header comment, infer purpose from its exported
function names and a skim of the function bodies — don't guess at intent the code doesn't support.

---

## Step 3 — Classify every touched item

Classify each item before writing:

| Type | What it is | Tag to use |
|------|-----------|------------|
| Screen / UI | A page or component the user sees | `tag-new` or `tag-mod` |
| Hook / logic | Reusable code, utility, helper | `tag-new` or `tag-mod` |
| DB migration | New table, column, index, RLS rule | `tag-db` |
| Edge function | Server-side function | `tag-new` or `tag-mod` |
| Config | env, app.config, .json config files | `tag-cfg` |
| Service | Third-party integration added | `tag-new` |
| Modified | Any existing file changed | `tag-mod` |

---

## Step 4 — Write the session block

Read `references/session-block-template.md` for the exact HTML structure to inject.

Key rules for writing each section:

### Session header (one-liner)
Write a single sentence a non-technical PM can read in 5 seconds and understand
what changed in the app. NOT technical. NOT a list. One sentence.

**Good:** "Built the ability to send push notifications — devices register after signup and the server can now target individual users."
**Bad:** "Implemented OneSignal SDK integration with Supabase player_id persistence via useOneSignal hook."

### Swim lane flow
- 4 fixed lanes: Phone (what user sees), App logic (hooks/code), Database, Server
- Number each step sequentially across ALL lanes (step 3 in DB follows step 2 in logic)
- Every step gets a tag (New / Modified / DB / Config)
- Steps that aren't built yet (future sessions) go in the relevant lane greyed out
- Write step descriptions in plain English — no file names, no jargon in the description
- If a step corresponds to exactly one item in the Detail Drill-down, add
  `onclick="jumpDetail('s{{N}}','{{ITEM_ID}}')"` on that `.swim-step` so clicking it
  jumps to and expands the matching detail row (F13). Leave purely conceptual steps
  (e.g. "user taps Allow") without an onclick.

### Detail drill-down
For every item in the touched register, write:
1. **What it does** — plain English, 2–3 sentences max. What does a PM need to know?
2. **Flow through it** — the sequence of events as simple nodes joined by arrows
3. **Key line of code** — one highlighted line with a plain English explanation of what it does
4. **Why this way** — the decision. Why this approach and not another? This is the validation layer for the PM.

Each `.detail-row` must carry `id="row-s{{N}}-{{ITEM_ID}}"` — `jumpDetail()` scrolls to
this id when a swim-step links here. Do not add a "sequence strip" inside the drawer —
that was an earlier design idea that never shipped; the drawer goes straight from the
detail-row into the four `dd-label` sections above.

### Architecture map update
- 5 layers, each its own `arch-grid`/injection point: **Phone** (screens only — what
  the user actually sees), **App Logic** (repositories, hooks, config, utilities — the
  "middle layer" between screens and the server/DB), **Database** (tables), **Server**
  (edge functions/APIs), **Services** (third-party integrations). Screens and
  repositories are NOT the same layer — don't lump them into one "Phone" bucket.
- Mark `is-new` for created this session, `is-mod` for modified
- Do NOT remove old nodes — the map is cumulative
- **Every node should end up with a Module Reference entry eventually** — when you add
  or touch a node, write its module entry (Step 4a) in the same pass rather than leaving
  it as a dead tile. A tile with no `onclick` looks identical to a clickable one (same
  hover/cursor styling otherwise), so an undocumented tile is a silent UX bug, not a
  harmless gap — treat "every tile is wired" as the target state, not an optional extra.
- Add `onclick="jumpModule('{{MODULE_ID}}')"` to the `.arch-node` div once its module
  entry exists (F24). Multiple tiles may point at the same module id when they're one
  cohesive unit (e.g. 3 tables from one migration).

### Step 4a — Module Reference (what each piece of code/DB is *for*)
This is the layer that explains *why* a file or table exists, not just that it changed.
It's a separate, cumulative register from the per-session Detail Drill-down — one entry
per module, updated in place (not duplicated) whenever a later session touches it again.

For every file or DB table you read in Step 2's source-inspection commands, write one
module entry using `references/session-block-template.md`'s "Module register entry"
block:
1. **What it does** — plain English, drawn from the file's header comment/JSDoc or the
   migration's SQL comments. If the source has no comment, summarise from its exported
   functions/columns — never invent a purpose the code doesn't support.
2. **Files / tables in this module** — list each file or table with a one-line plain-English
   job description (e.g. "fetchTodayDishCandidates() — picks today's meal suggestions
   for a household, ranked by how well they match this household's taste").
3. **How it helps the app** — the concrete benefit to the end user or the business, in
   one or two sentences. Not "implements X pattern" — "this is what makes sure a brand
   new user doesn't see an empty screen."
- Group related files into one module when they're part of the same feature (e.g. all
  six `re-*.repository.ts` files could be one module each, or grouped by feature area —
  use judgement, but never bundle unrelated files into one entry).
- Append to the Module Reference register above `<!-- MODULES_INJECT -->`. Never remove
  or rewrite another session's module entries — if a later session changes a module,
  update that module's existing drawer content in place and note which session last
  touched it, rather than creating a duplicate entry.
- Update the `<span class="nav-badge">` count on the "Modules" sidebar nav-item to the
  new total module count.

### Step 4a-2 — Feature flows tab (per-session, code-level walkthrough)
A third tab on every session page, alongside "Swim lane flow" and "Detail drill-down" —
not a separate page like Modules/System Flow. One button per feature built or modified
*this session*; each feature is a stack of collapsible steps across up to 6 possible
layers, in this fixed order when present: **Phone → App logic → Middleware → Server →
Database → Service**. This is the most granular view in the book — it's where a PM
can see the actual file-to-file call chain for one feature without reading code.

**Identify features first.** A "feature" here is a user-facing capability, not a file —
"User login," "Place order," not "LoginScreen.tsx." Group this session's touched files
by which feature they serve; a feature with only 1-2 files is fine, don't force-merge
unrelated work into one feature button.

**Verify every file path before writing it down.** This is non-negotiable:
```bash
test -f path/to/file.tsx && echo "EXISTS" || echo "MISSING — do not include"
```
Every file path named in a step's "Code flow" or "Files touched" must be a real path in
the actual repo, checked with `test -f` (or equivalent) before it goes in the data. Do
not invent a plausible-looking file. If a step's logic genuinely isn't in a separate
file (e.g. inline in the same component), say so in the description rather than naming
a file that doesn't exist.

**Data shape** — one `flows[]` array per session, each entry one feature:
```js
{
  id: 'user-login',              // unique within this session
  label: 'User login',           // shown on the tab button
  steps: [
    {
      layer: 'Phone',            // Phone | App logic | Middleware | Server | Database | Service
      tag: 'UI',                 // UI | HOOK | API | DB | SDK | POLICY
      title: 'Login screen mounts',
      desc: 'Plain English, no jargon — what actually happens at this step.',
      codeFlow: [                 // the real call chain, verified to exist
        {chip:'screens/LoginScreen.tsx'}, {label:'renders'},
        {chip:'components/EmailInput.tsx'}, {label:'local state'},
        {chip:'hooks/useLoginForm.ts'}
      ],
      files: [                    // every file in this step, one plain-English job each
        {path:'screens/LoginScreen.tsx', desc:'Renders the visible form'},
        {path:'hooks/useLoginForm.ts', desc:'Holds form state, error messages'}
      ],
      api: null,                  // {endpoint:'POST /auth/login', note:'...'} — omit entirely if this step makes no API call
      db: null                    // {table:'users', op:'SELECT', note:'...'} — omit entirely if this step touches no table
    }
    // ... more steps, in real call order, across whichever layers this feature actually uses
  ]
}
```
- `api`/`db` are `null` (or omitted) on steps that don't have that surface — the renderer
  skips those sections entirely rather than showing an empty one.
- Not every feature uses all 6 layers. A pure front-end interaction might only have
  Phone + App logic steps. Don't pad with fake Middleware/Server/Database steps to fill
  the layer list.

**Injection mechanics** — see `references/session-block-template.md`'s "Feature flows
tab" section for the exact markup and the one-time global JS (`renderFeatureFlows`,
`toggleFeatureStep`, `deepDiveFeature`). The renderer function itself goes in the
shared `<script>` block **once** — if `function renderFeatureFlows` isn't already in
the file, copy it in from `references/shell-template.md` before adding any session's
flows data. Each session then just adds a third `.view-tab`, an empty `<div id="s{{N}}-flows">`
view-pane, and a small inline `<script>` defining that session's `flows[]` array and
calling `renderFeatureFlows('s{{N}}-flows', flows)`.

**Script ordering — critical.** The shared `<script>` block (containing `showPage`,
`switchView`, `jumpDetail`, `jumpModule`, `toggleDetail`, `renderFeatureFlows`,
`toggleFeatureStep`, `deepDiveFeature`) MUST appear immediately after `<body>` opens,
**before** `<!-- SESSIONS_INJECT -->` and before any per-session inline `<script>`.
Browsers execute non-deferred `<script>` tags synchronously in document order — if a
session's inline script calls `renderFeatureFlows(...)` before that function has been
defined further down the document, it throws `ReferenceError: renderFeatureFlows is
not defined`. Never append the shared script block at the bottom of `<body>`. When
validating (Step 6), check that the shared script's `<script>` opening tag's line
number is lower than every per-session call site's line number — `node --check` on an
extracted block alone will NOT catch this, since it only validates syntax, not
cross-block execution order.

### Step 4b — System Flow (front-end → back-end sequence diagrams)
A separate page, cumulative like Modules, showing how a major user-facing flow actually
travels through the layers — e.g. "Onboarding → persona assignment" or "Daily plan
generation." This is what answers "what calls what" for a non-coder.

- One flow diagram per major feature flow, not one per session — only add a new flow
  diagram when a session introduces a flow that doesn't have one yet, or update an
  existing flow's diagram if this session changed the sequence of an existing flow.
- Reuse the swim-lane markup (`.swim-lane`/`.swim-step`, same 4 lanes: Phone, App Logic,
  Database, Server) — a flow diagram looks exactly like a session's swim lane view, just
  scoped to one feature instead of one session, and living on its own page so it doesn't
  get buried under session history.
- Number steps in actual chronological/call order, even if that means the Server lane
  has step 1 (e.g. a flow that starts with a cron job calling into the server first).
- Every step that has a Module Reference entry gets `onclick="jumpModule('{{MODULE_ID}}')"`
  — this is what makes the flow diagram a clickable map instead of a static picture.
- Append above `<!-- FLOWS_INJECT -->` in `page-flow`.

### Timeline row
- Append one row to the timeline
- Chips = every major thing touched (short labels, clickable)
- Note = one sentence on what this session achieved and what's still pending

### Files register
- Append every touched file with: path, type tag, session number, one-line description
- Never remove entries — register is append-only
- Update the `<span class="nav-badge">` count on the "Files register" sidebar nav-item
  to the new total row count

### Decisions log
- Extract every "why" from the session — decisions that aren't obvious
- Format: Question → Answer (see reference template)
- 3–8 decisions per session is normal

### Default open page
- The session you just documented becomes the page that's open when the file loads:
  remove `style="display:none"` from its `page-s{{N}}` div and add `active` to its
  sidebar `nav-item`.
  Add `style="display:none"` to whichever page was previously the default (the
  prior latest session, or `page-arch-full` if this is session 1), and remove
  `active` from that page's nav-item.
- This means the file always opens on the most recent work, not on the architecture
  overview — the architecture/timeline/files/decisions pages are reference material
  reached via the sidebar, not the landing page.

---

## Step 5 — Inject into the HTML file

```bash
# Verify injection points exist
grep -n "SESSIONS_INJECT\|NAV_INJECT\|ARCH_.*_INJECT\|TIMELINE_INJECT\|FILES_INJECT\|MODULES_INJECT\|FLOWS_INJECT\|DECISIONS_INJECT" KNOWLEDGE.html
```

Replace each injection comment with new content + the comment (so it stays injectable
for next session). Pattern:

```
<!-- SESSIONS_INJECT -->
```
becomes:
```
[new session HTML block]
<!-- SESSIONS_INJECT -->
```

Do the same for NAV_INJECT, ARCH_PHONE_INJECT / ARCH_APPLOGIC_INJECT / ARCH_DB_INJECT /
ARCH_SERVER_INJECT / ARCH_SERVICES_INJECT (update nodes), TIMELINE_INJECT (append row),
FILES_INJECT (append rows), MODULES_INJECT (append module entries), FLOWS_INJECT (append
flow diagrams), DECISIONS_INJECT (append items).

---

## Step 6 — Validate before finishing

```bash
# Confirm the file is valid and readable
wc -l KNOWLEDGE.html
grep -c 'id="page-s' KNOWLEDGE.html   # should equal number of sessions
grep "SESSIONS_INJECT\|MODULES_INJECT" KNOWLEDGE.html   # should still be present for next session
grep -c "function renderFeatureFlows" KNOWLEDGE.html   # must be exactly 1 — never duplicated across sessions
node --check /tmp/extracted-script.js   # extract the <script>...</script> contents and syntax-check before committing

# Confirm every onclick-called function actually has a real `function NAME(` definition —
# not just mentioned in a documentation code-sample string. This is how jumpModule shipped
# broken once: it was referenced in 31 onclick attributes but never implemented.
for fn in showPage switchView jumpDetail jumpModule toggleDetail renderFeatureFlows toggleFeatureStep deepDiveFeature; do
  grep -q "function $fn(" KNOWLEDGE.html || echo "MISSING IMPLEMENTATION: $fn"
done

# Confirm every onclick="jumpModule('X')" / jumpDetail('s','X') target has a matching drawer.
# A call with no matching draw-mod-X or draw-sN-X id will silently no-op or throw at click time.
comm -23 \
  <(grep -o "jumpModule('[^']*')" KNOWLEDGE.html | sed -E "s/jumpModule\('([^']*)'\)/\1/" | sort -u) \
  <(grep -o 'id="draw-mod-[^"]*"' KNOWLEDGE.html | sed -E 's/id="draw-mod-([^"]*)"/\1/' | sort -u)
# ^ any output here = a jumpModule call with no matching drawer — fix before committing

# Confirm the shared <script> block (showPage/jumpModule/renderFeatureFlows/etc.) is
# positioned BEFORE any per-session inline <script> that calls those functions — i.e.
# its opening <script> line number must be lower than every session's call-site line.
# It must sit right after <body> opens, before <!-- SESSIONS_INJECT -->.
grep -n "^<script>\|SESSIONS_INJECT" KNOWLEDGE.html | head -3
```

Tell the user:
- How many sessions are now documented
- What was added this session (summary)
- The file path to open in browser: `KNOWLEDGE.html`

---

## Multi-developer and multi-agent rules

When multiple people or multiple Claude Code instances work on the same project:

1. **Always pull before documenting** — run `git pull` before injecting to avoid
   overwriting another session's additions.
2. **Use session numbers, not dates, as IDs** — `page-s5`, `s5` etc. Check the highest
   existing session number before assigning yours.
3. **Each agent documents only its own session** — do not modify another session's block.
   The swim lane and detail sections are append-only per session.
4. **The architecture map and files register are shared** — update these carefully,
   preserving all existing nodes and entries.
5. **Commit the knowledge book with every session** — treat `KNOWLEDGE.html` like
   code. It should be in version control and committed at the end of every session.

```bash
git add KNOWLEDGE.html
git commit -m "docs: session S[N] knowledge book update — [one-line summary]"
```

---

## Reference files

- `references/session-block-template.md` — full HTML template for one session block
- `references/shell-template.md` — full HTML for a brand-new knowledge book
- `assets/` — colour tokens, tag styles (referenced by both templates)

Read these before writing any HTML. Do not invent structure — follow the templates exactly
so all sessions look consistent regardless of who wrote them.
