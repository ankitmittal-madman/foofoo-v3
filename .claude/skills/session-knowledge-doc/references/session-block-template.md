# Session Block Template

Use this exact structure for every session. Replace ALL `{{placeholders}}`.
Inject above `<!-- SESSIONS_INJECT -->` in KNOWLEDGE.html.

## Sidebar nav item
Inject above `<!-- NAV_INJECT -->`:

```html
<div class="nav-item" onclick="showPage('s{{N}}')">
  <span class="nav-icon">{{EMOJI}}</span> S{{N}} · {{SHORT_TITLE}}
  <span class="nav-badge">{{DATE_SHORT}}</span>
</div>
```

Choose `{{EMOJI}}` to represent what was built:
- 📦 Setup/scaffold  🔐 Auth  💬 Chat/feed  🔔 Notifications  🗄 Database
- 🧩 New feature  🛠 Bug fix  ⚙️ Config  🔌 Integration  📊 Analytics

---

## Full session page block
Inject above `<!-- SESSIONS_INJECT -->`:

```html
<div id="page-s{{N}}" class="page-content" style="display:none">

  <!-- ── Session header ── -->
  <div class="page-header">
    <div class="page-title">S{{N}} · {{FULL_TITLE}}</div>
    <div class="page-subtitle">{{ONE_SENTENCE_PLAIN_ENGLISH_SUMMARY}}</div>
  </div>

  <!-- ── Summary card ── -->
  <div class="session-card">
    <div class="session-card-header">
      <div class="session-card-title">What was built this session</div>
      <div class="session-card-meta">{{DATE_FULL}}<br>{{N_THINGS}} things touched</div>
    </div>
    <div class="session-card-desc">{{2_3_SENTENCE_PLAIN_ENGLISH_DETAIL}}</div>
    <div class="stat-row">
      <div class="stat"><div class="stat-n" style="color:#1a56db">{{COUNT_SCREENS}}</div><div class="stat-l">Screen{{PLURAL}}</div></div>
      <div class="stat"><div class="stat-n" style="color:#5145b8">{{COUNT_CODE}}</div><div class="stat-l">Code files</div></div>
      <div class="stat"><div class="stat-n" style="color:#0e7a5a">{{COUNT_DB}}</div><div class="stat-l">DB change{{PLURAL}}</div></div>
      <div class="stat"><div class="stat-n" style="color:#92500a">{{COUNT_SERVER}}</div><div class="stat-l">Server fn{{PLURAL}}</div></div>
    </div>
  </div>

  <!-- ── View tabs ── -->
  <div class="view-tabs">
    <div class="view-tab active" onclick="switchView('s{{N}}','swim')">Swim lane flow</div>
    <div class="view-tab" onclick="switchView('s{{N}}','detail')">Detail drill-down</div>
    <div class="view-tab" onclick="switchView('s{{N}}','flows')">Feature flows</div>
  </div>

  <!-- ══ SWIM LANE VIEW ══ -->
  <div id="s{{N}}-swim" class="view-pane active">

    <!-- PHONE LANE — steps the user sees or triggers -->
    <div class="swim-lane lane-blue">
      <div class="swim-label"><div class="swim-label-inner">
        <div class="swim-label-title">Phone</div>
        <div class="swim-label-sub">user sees</div>
      </div></div>
      <div class="swim-body">
        {{REPEAT_FOR_EACH_PHONE_STEP:
        <div class="swim-step" {{onclick="jumpDetail('s{{N}}','{{ITEM_ID}}')" — ONLY if this step maps to one specific item in the Detail view below; omit onclick if the step is purely conceptual (e.g. "user taps Allow")}}>
          <div class="step-num num-blue">{{STEP_N}}</div>
          <div class="step-content">
            <div class="step-title-row">
              <span class="step-title">{{STEP_TITLE}}</span>
              <span class="tag {{TAG_CLASS}}">{{TAG_LABEL}}</span>  <!-- omit if no tag -->
            </div>
            <div class="step-desc">{{PLAIN_ENGLISH_DESCRIPTION}}</div>
          </div>
        </div>
        }}
      </div>
    </div>

    <div class="swim-arrow">↕ {{TRANSITION_DESCRIPTION}}</div>

    <!-- APP LOGIC LANE — hooks, services, business logic -->
    <div class="swim-lane" style="margin-bottom:10px">
      <div class="swim-label"><div class="swim-label-inner">
        <div class="swim-label-title">App logic</div>
        <div class="swim-label-sub">hooks / code</div>
      </div></div>
      <div class="swim-body" style="background:var(--purple-bg);border-color:var(--purple-border)">
        {{REPEAT_FOR_EACH_LOGIC_STEP: same structure as phone lane, use num-purple, same onclick rule}}
      </div>
    </div>

    <div class="swim-arrow">↕ {{TRANSITION_DESCRIPTION}}</div>

    <!-- DATABASE LANE — tables, columns, migrations -->
    <div class="swim-lane lane-teal">
      <div class="swim-label"><div class="swim-label-inner">
        <div class="swim-label-title">Database</div>
        <div class="swim-label-sub">Supabase</div>
      </div></div>
      <div class="swim-body">
        {{REPEAT_FOR_EACH_DB_STEP: same structure, use num-teal, same onclick rule}}
      </div>
    </div>

    <!-- Only include server lane if server functions were touched -->
    <div class="swim-arrow">↕ {{TRANSITION_DESCRIPTION}}</div>

    <!-- SERVER LANE — edge functions, cron jobs, webhooks -->
    <div class="swim-lane lane-amber">
      <div class="swim-label"><div class="swim-label-inner">
        <div class="swim-label-title">Server</div>
        <div class="swim-label-sub">edge functions</div>
      </div></div>
      <div class="swim-body">
        {{REPEAT_FOR_EACH_SERVER_STEP: same structure, use num-amber, same onclick rule}}
      </div>
    </div>

    <!-- Next session box — always present -->
    <div class="next-box">
      <div class="next-label">Next session</div>
      <div class="next-text">{{WHAT_STILL_NEEDS_TO_BE_DONE_PLAIN_ENGLISH}}</div>
    </div>

  </div><!-- /swim -->

  <!-- ══ DETAIL DRILL-DOWN VIEW ══ -->
  <div id="s{{N}}-detail" class="view-pane">

    {{REPEAT_FOR_EACH_TOUCHED_ITEM:
    <div class="detail-item">
      <div class="detail-row" id="row-s{{N}}-{{ITEM_ID}}" onclick="toggleDetail('s{{N}}-{{ITEM_ID}}')">
        <div class="detail-left">
          <span class="tag {{TAG_CLASS}}">{{TAG_LABEL}}</span>
          <span class="detail-name {{plain_if_not_code}}">{{FILENAME_OR_ITEM_NAME}}</span>
        </div>
        <span class="detail-chevron" id="chev-s{{N}}-{{ITEM_ID}}">▾</span>
      </div>
      <div class="detail-drawer" id="draw-s{{N}}-{{ITEM_ID}}">

        <div class="dd-label">What this does</div>
        <div class="dd-text">{{2_3_SENTENCES_PLAIN_ENGLISH_NO_JARGON}}</div>

        <div class="dd-label">Flow through it</div>
        <div class="dd-flow">
          <span class="dd-node">{{STEP_1}}</span><span class="dd-arrow">→</span>
          <span class="dd-node">{{STEP_2}}</span><span class="dd-arrow">→</span>
          <span class="dd-node">{{STEP_N}}</span>
        </div>

        <div class="dd-label">Key line of code</div>
        <div class="dd-code"><span class="dd-hl">{{MOST_IMPORTANT_LINE}}</span>  ← {{PLAIN_ENGLISH_EXPLANATION}}</div>

        {{REPEAT_FOR_EACH_DECISION:
        <div class="dd-why">
          <div class="dd-why-q">{{DECISION_QUESTION}}</div>
          <div class="dd-why-a">{{PLAIN_ENGLISH_ANSWER_WHY_THIS_WAY}}</div>
        </div>
        }}

      </div>
    </div>
    }}

    <div class="next-box">
      <div class="next-label">Next session</div>
      <div class="next-text">{{WHAT_STILL_NEEDS_TO_BE_DONE}}</div>
    </div>

  </div><!-- /detail -->

  <!-- ══ FEATURE FLOWS VIEW ══ -->
  <div id="s{{N}}-flows" class="view-pane"></div>
  <script>
  window.FEATURE_FLOWS_S{{N}} = [
    {{REPEAT_FOR_EACH_FEATURE_BUILT_OR_MODIFIED_THIS_SESSION:
    {
      id: '{{feature-id}}',
      label: '{{Feature label shown on the tab button}}',
      steps: [
        {{REPEAT_FOR_EACH_STEP_IN_REAL_CALL_ORDER:
        {
          layer: '{{Phone|App logic|Middleware|Server|Database|Service}}',
          tag: '{{UI|HOOK|API|DB|SDK|POLICY}}',
          title: '{{Short step title}}',
          desc: '{{Plain English, no jargon, what happens at this step}}',
          codeFlow: [ {chip:'{{verified/real/file/path.ts}}'}, {label:'{{calls|renders|returns}}'}, {chip:'{{next/real/file.ts}}'} ],
          files: [ {path:'{{verified/real/file/path.ts}}', desc:'{{one-line plain-English job}}'} ],
          api: {{null, OR {endpoint:'POST /x', note:'plain English'} if this step makes an API call}},
          db: {{null, OR {table:'table_name', op:'INSERT|UPDATE|SELECT', note:'plain English'} if this step touches a table}}
        }
        }}
      ]
    }
    }}
  ];
  renderFeatureFlows('s{{N}}-flows', window.FEATURE_FLOWS_S{{N}});
  </script>

</div><!-- /page-s{{N}} -->
```

**Before writing any `codeFlow`/`files` entry, verify the path is real:**
```bash
test -f path/to/file.ts && echo EXISTS || echo "MISSING — fix or drop this entry"
```
Never write a plausible-looking path that wasn't checked. If `function renderFeatureFlows`
doesn't already exist anywhere in `KNOWLEDGE.html`'s `<script>` block, copy it in once
from `references/shell-template.md` before adding this session's `<script>` block above —
it must appear exactly once in the whole file, shared by every session.

---

## Architecture map node additions
Inject into the correct layer section above `<!-- ARCH_PHONE_INJECT -->` (screens only) /
`ARCH_APPLOGIC_INJECT` (repositories, hooks, config — the middle layer) / `ARCH_DB_INJECT` /
`ARCH_SERVER_INJECT` / `ARCH_SERVICES_INJECT` (whichever layer fits):

```html
<div class="arch-node {{is-new OR is-mod OR blank}}" onclick="jumpModule('{{MODULE_ID}}')">
  <div class="arch-node-name {{plain if not a filename}}">{{NAME}}</div>
  <div class="arch-node-desc">{{Short desc}} · S{{N}}</div>
</div>
```

Only add the `onclick` if you also wrote a Module Reference entry for `{{MODULE_ID}}`
(see below) — a tile that links to nothing is worse than a tile that's just not clickable.

---

## Module register entry
One entry per module/file/table — explains *what it's for*, not what changed this
session. Append above `<!-- MODULES_INJECT -->` the first time a module is touched;
on later sessions, find and update that module's existing entry in place instead of
adding a duplicate.

```html
<div class="detail-item">
  <div class="detail-row" id="row-mod-{{MODULE_ID}}" onclick="toggleDetail('mod-{{MODULE_ID}}')">
    <div class="detail-left">
      <span class="tag {{TAG_CLASS}}">{{TAG_LABEL}}</span>
      <span class="detail-name {{plain_if_not_code}}">{{MODULE_NAME}}</span>
    </div>
    <span class="detail-chevron" id="chev-mod-{{MODULE_ID}}">▾</span>
  </div>
  <div class="detail-drawer" id="draw-mod-{{MODULE_ID}}">
    <div class="dd-label">What this does</div>
    <div class="dd-text">{{PLAIN_ENGLISH_FROM_HEADER_COMMENT_OR_JSDOC_OR_SQL_COMMENT}}</div>

    <div class="dd-label">Files / tables in this module</div>
    <div class="dd-text">
      {{REPEAT_FOR_EACH_FILE_OR_TABLE:
      <code>{{file_or_table_name}}</code> — {{one_line_plain_english_job_from_its_exported_functions_or_columns}}<br>
      }}
    </div>

    <div class="dd-label">How it helps the app</div>
    <div class="dd-text">{{CONCRETE_USER_OR_BUSINESS_BENEFIT — not "implements X pattern", but what breaks or what users notice if this didn't exist}}</div>

    <div class="dd-label">Last touched</div>
    <div class="dd-text">S{{N}} · {{DATE_SHORT}}</div>
  </div>
</div>
```

---

## System flow diagram
One per major feature flow (not per session) — append above `<!-- FLOWS_INJECT -->` in
`page-flow` the first time this flow is documented; update an existing flow's steps in
place if a later session changes how it works, rather than adding a second diagram for
the same feature. Reuses the same swim-lane markup as a session page, just without the
view-tabs/detail-drilldown wrapper around it — this is a flow, not a session.

```html
<div class="flow-block" style="margin-bottom:32px">
  <div class="step-title" style="font-size:15px;margin-bottom:4px">{{FLOW_TITLE}}</div>
  <div class="step-desc" style="margin-bottom:12px">{{ONE_SENTENCE_WHAT_THIS_FLOW_ACHIEVES}}</div>

  <div class="swim-lane lane-blue">
    <div class="swim-label"><div class="swim-label-inner">
      <div class="swim-label-title">Phone</div><div class="swim-label-sub">user sees</div>
    </div></div>
    <div class="swim-body">
      {{REPEAT_FOR_EACH_PHONE_STEP: same .swim-step structure as a session swim lane,
        onclick="jumpModule('{{MODULE_ID}}')" if that step has a Module Reference entry}}
    </div>
  </div>
  <div class="swim-arrow">↕ {{TRANSITION}}</div>
  <div class="swim-lane" style="margin-bottom:10px">
    <div class="swim-label"><div class="swim-label-inner">
      <div class="swim-label-title">App logic</div><div class="swim-label-sub">hooks / code</div>
    </div></div>
    <div class="swim-body" style="background:var(--purple-bg);border-color:var(--purple-border)">
      {{REPEAT_FOR_EACH_LOGIC_STEP}}
    </div>
  </div>
  <div class="swim-arrow">↕ {{TRANSITION}}</div>
  <div class="swim-lane lane-teal">
    <div class="swim-label"><div class="swim-label-inner">
      <div class="swim-label-title">Database</div><div class="swim-label-sub">Supabase</div>
    </div></div>
    <div class="swim-body">
      {{REPEAT_FOR_EACH_DB_STEP}}
    </div>
  </div>
  <div class="swim-arrow">↕ {{TRANSITION}}</div>
  <div class="swim-lane lane-amber">
    <div class="swim-label"><div class="swim-label-inner">
      <div class="swim-label-title">Server</div><div class="swim-label-sub">edge functions</div>
    </div></div>
    <div class="swim-body">
      {{REPEAT_FOR_EACH_SERVER_STEP}}
    </div>
  </div>
</div>
```

Number steps in real call order — if the flow starts on the server (e.g. a cron job),
its first step can be numbered 1 even though the Server lane is drawn last.

---

## Timeline row
Inject above `<!-- TIMELINE_INJECT -->`:

```html
<div class="timeline-row">
  <div class="tl-date">{{DATE}}</div>
  <div class="tl-spine"><div class="tl-dot" style="background:{{DOT_COLOR}}"></div></div>
  <div class="tl-content">
    <span class="tl-badge" style="background:{{BADGE_BG}};color:{{BADGE_TEXT}}">S{{N}}</span>
    <div class="tl-title">{{SESSION_TITLE}}</div>
    <div class="tl-chips">
      {{REPEAT: <span class="tl-chip" onclick="showPage('s{{N}}')">{{CHIP_LABEL}}</span> }}
    </div>
    <div class="tl-note">{{ONE_LINE_ACHIEVEMENT_AND_WHATS_NEXT}}</div>
  </div>
</div>
```

Session colour palette (use in order, cycling if needed):
- S1: dot `#1a56db` badge `#eff4ff` / `#1a56db`
- S2: dot `#0e7a5a` badge `#e8f8f2` / `#0e7a5a`
- S3: dot `#5145b8` badge `#f0effe` / `#5145b8`
- S4: dot `#92500a` badge `#fef8ec` / `#92500a`
- S5: dot `#166534` badge `#f0fdf4` / `#166534`
- S6: dot `#9a3412` badge `#fff7ed` / `#9a3412`
- S7+: cycle from S1 colours

---

## Files register rows
Inject above `<!-- FILES_INJECT -->`:

```html
<tr>
  <td class="fr-file {{mono}}">{{FILE_PATH}}</td>
  <td><span class="tag {{TAG_CLASS}}">{{TAG}}</span></td>
  <td class="fr-session">S{{N}}</td>
  <td class="fr-desc">{{ONE_LINE_PLAIN_DESCRIPTION}}</td>
</tr>
```

---

## Decisions log items
Inject above `<!-- DECISIONS_INJECT -->`:

```html
<div class="decision-item">
  <div class="decision-q">{{QUESTION_THAT_CAME_UP}}</div>
  <div class="decision-a">{{ANSWER_AND_REASONING}}</div>
  <div class="decision-meta">S{{N}} · {{DATE_SHORT}}</div>
</div>
```
