# White core: design

_Status (2026-11-06): sections 3.1–3.10 and the bench are implemented in `plugins/` and `bench/`, with tests. Open questions in §6 are partly answered: White now has its own inbox, an optional phone, WhatsApp check-ins, and Composio for the founder's apps. Not yet validated over real founder weeks._

## 1. What White is

White is an AI founder's office: a worker that owns parts of a founder's job, decides what matters, does most of it, and brings back only decisions, approvals, and proof. It is **not** a skill pack. Skills are its training. The worker is a running system with its own state, loop, judgment, and enforced authority.

```
 Founder ─── check-ins, approvals, decisions ───┐
                                                │
 ┌──────────────────── WHITE CORE (plugin) ─────┴────────────────────┐
 │ Charter → World model → Event loop → Judgment → Specialists      │
 │                   ↑           │                     │             │
 │             Supervisor ← Authority gate ← every action            │
 │                       Scorecard / learning                        │
 └──────────────────────────────┬────────────────────────────────────┘
                                │ uses
 ┌──────────── HERMES (body, unchanged) ─────────────────────────────┐
 │ model routing · tools · browser · Bot Screen (own computer)      │
 │ gateway (email/WhatsApp/Telegram) · cron · kanban · memory · A2A │
 └───────────────────────────────────────────────────────────────────┘
 Skills (training): founder-onboarding, seed-model, design-partner-hunt, …
```

### The test: a colleague, not a tool

Every design choice must pass this test: **does this make White behave like a founder's office hire, or like a tool the founder operates?**

| A tool the founder uses | A founder's office colleague (White) |
|---|---|
| Waits for a prompt | Shows up every day with a plan, unasked (3.3) |
| Does the task asked | Owns an outcome and its number (3.1, 3.8) |
| Executes instructions | Says what matters and pushes back with evidence (3.4) |
| Forgets between sessions | Knows the company's people, deals, and promises (3.2) |
| Works through the founder's hands | Has its own computer and, later, its own email and number (3.9, Bot Screen) |
| Output must be checked by the founder | Checks its own work before showing it (3.7) |
| Same quality forever | Gets better at the job from feedback and practice (3.8, 3.10) |
| Can do anything it's told | Knows the limits of its authority and respects them in code (3.6) |

Rejected: features that only make White a better tool (more slash commands, more manual routines, prompt templates the founder must fill in).

## 2. Lessons from the field (researched 2026-11-05)

| Product | Pattern we adopt |
|---|---|
| **Town** (Townies) | Memory is an editable wiki about the user's world, refreshed nightly. It comes to the user with a briefing right after tools are connected. It tracks commitments. |
| **Okara** (AI CMO) | A team of specialist agents, one per channel or workstream, running on a daily cycle. Its weakness, no performance proof, is our opening. |
| **Sierra / Decagon** | Procedures in plain language, but sensitive steps in deterministic code. Supervisor agents check live work. Tests before every change. Pricing per outcome. |
| **Anthropic / Google long-running harnesses** | State lives outside the model in structured stores, with progress artifacts per session and wake-on-event. |
| **Harness²** (Google Research) | Improve the harness, not the model: try harness variants on the same task, keep what works, and store evidence-backed lessons for later tasks. Showed gains on workplace benchmarks with Flash-class models. |
| **Nobody** | Judgment: telling the founder what matters most, unprompted. **This is White's edge.** |

## 3. Components

### 3.1 Charter: the job description, as data

`founder/charter.yaml`. What White owns, with a target metric for each. It is created in onboarding and edited by the founder.

```yaml
responsibilities:
  - id: design-partners
    outcome: "5 paying design partners"
    metric: signed_design_partners
    target: 5
    due: 2027-01-31
    authority: approval_required        # for outbound
  - id: follow-ups
    outcome: "No commitment older than 48h without action"
    metric: overdue_commitments
    target: 0
    authority: standing_permission       # internal reminders only
```

### 3.2 World model: state outside the model

SQLite at `$HERMES_HOME/white/world.db`. Every row carries a source (email id, URL, call log) and a timestamp.

| Table | Holds |
|---|---|
| `people`, `orgs` | Who they are, their relationship to the founder, last contact, warm paths |
| `pipeline` | Deals of any kind (design partner, investor, customer, accelerator) with stage, next step, and owner |
| `commitments` | Every promise made by the founder or White: who, what, due date, status |
| `signals` | Raw events: new email, reply, calendar change, web signal, customer quote |
| `decisions` | What was decided, by whom, why, with links |
| `runway` | Cash, burn, and runway months (from the founder or `seed-model`) |
| `actions` | Every action White took or proposed: status, approval, proof |

**Wiki view (the Town lesson):** a nightly job renders readable, editable pages (`founder/wiki/*.md`: company, each key person, each pipeline) from the database. Founder edits sync back as corrections.

### 3.3 Event loop: works without prompts

Inputs: Hermes gateway events (email, WhatsApp, Telegram), calendar webhooks, kanban completions, A2A messages, and cron ticks (morning drive, evening wrap, weekly review).

Each cycle:
1. **Ingest:** turn the event into `signals`, then update the entities and commitments (extraction by a cheap model, validated in code).
2. **Triage:** decide whether it matters to a charter responsibility. If not, file it.
3. **Judge:** rank the open work (3.4).
4. **Dispatch:** top items become kanban cards for specialists (3.5), and decisions go into the founder queue.
5. **Verify:** the supervisor checks the results (3.7) before anything counts as done.
6. **Log:** write `actions`, the scorecard, and a progress note. The next cycle resumes from state, not chat history.

### 3.4 Judgment engine: White's edge

Runs every cycle, plus a deeper weekly review. It scores open work in code, then has the model reason over the top ones:

`priority = charter_weight × deadline_pressure × runway_pressure × stall_penalty × founder_neglect`

The model's job is reasoning, not bookkeeping. It produces:
- **Today's one thing:** the highest-leverage item, with why.
- **Challenges:** where the founder's time or plans and the data disagree ("60% of your week went to the model; the round depends on design partners").
- **Risks:** stalled deals, cold leads, missed commitments, runway versus plan.

A challenge is always phrased as a recommendation with evidence. The founder can accept, reject, or override it, and every response is logged to `decisions` and fed back into the weights.

### 3.5 Specialists: the Okara lesson

One Hermes profile or kanban lane per workstream: `white-outreach`, `white-research`, `white-content`, `white-finance`, `white-ops`. Each runs with the matching skills and only the tools it needs. White core is the orchestrator. Specialists never talk to the founder directly; everything goes through White.

### 3.6 Authority gate: code, not prompt (the Decagon/Sierra lesson)

A Hermes plugin `pre_tool_call` hook (a blocking hook in `agent/agent_runtime_helpers.py`) checks every outward action against `authority.md`, compiled to `authority.yaml`:
- **Outward actions** (email send, post, DM, form submit, payment, calendar invite to externals, `computer_use` clicks on Send/Submit/Pay, A2A messages containing "never share" data) are blocked unless there's a matching approval or standing permission.
- Blocked calls become approval requests in the founder queue. Approval yields a single-use token tied to the exact content hash, so the model can't send something different from what was approved.
- "Never share" items are checked by string and entity match before any outbound call.
- **Fail closed:** if the gate errors, the action does not happen.

### 3.7 Supervisor: checks the work (the Sierra lesson)

A separate model call, ideally a different model from the worker, reviews each output before it reaches the founder or counts as done. It checks:
- **Facts:** every claim has a source, and the sources are fetched and actually say it.
- **Voice:** matches `voice.md`, with no AI tells (`humanizer` rubric).
- **Contract:** the card's "done means" is met, and the proof exists (file opens, URL resolves, email id exists).
- **Authority:** no "never share" leaks.

Fail → back to the specialist with reasons, up to 2 retries, then escalate to White with what's wrong.

### 3.8 Scorecard and learning

- A scorecard per charter responsibility (metric versus target, trend), shown in the weekly review.
- Misses are reported with a reason and a fix. White doesn't hide them.
- **Founder corrections become policy:** edits to drafts update `voice.md`, rejected recommendations adjust the judgment weights, and new rules go to `authority.yaml`. Each change is logged.

### 3.10 Getting better at the job (the Harness² lesson)

A good hire improves through feedback and practice. White does both:
- **Lessons with evidence:** after each closed outcome or rejected draft, White writes a lesson ("ops heads in logistics reply to signal-first openers, 9/40 vs 2/40") with links to the actions behind it, stored in `world.db` → `lessons`. Planning and specialists read the relevant lessons before acting. Lessons without evidence aren't stored.
- **Practice runs, sandboxed only:** weekly, White proposes changes to its own harness (a skill's wording, judgment weights, supervisor rubric) and runs the current and candidate versions on the bench (section 4). It adopts a change only if it scores better **and** doesn't lower the authority or no-leak scores. Practice never touches real email, accounts, or people. It runs only on bench fixtures, with network restricted.
- **The founder sees the change log:** "This week I changed how I open design-partner emails; the bench score went from 61 to 68."

### 3.9 Founder interface

- **Morning check-in** (WhatsApp or Telegram): Decide, Approve, Done (with proof), Pace, Today's one thing.
- **One-tap replies:** approve, edit, reject, or "do what you recommend".
- **Live view:** Bot Screen in Hermes Desktop shows White's own computer, with take-over for logins and 2FA.

## 4. Evidence: Founder's Office Bench

Start from public workplace benchmarks that Harness² reports on (JobBench and WorkBuddy-Bench; check what they cover before relying on them), so White has a number outsiders recognize. On top of those, add a founder's-office bench of 25 scripted scenarios with a simulated founder and inbox (seeded `world.db`, fake email, web fixtures). For example:
- "Plan a seed raise with 9 months of runway."
- "Find 5 logistics design partners in India."
- "Three customers complained about X this week."
- "Investor replied asking for the model."
- "A follow-up promised Friday is overdue."

Scored on: correct priority picked, facts sourced, nothing sent without approval, outcome reached, and founder minutes needed. Run **plain Hermes against White** and publish both. Run it in CI before every change (the Sierra lesson).

## 5. Build order (week one)

1. **Authority gate plugin** (3.6). Safety first, and the clearest answer to "it's just prompts".
2. **World model plus ingest** (3.2, 3.3 steps 1–2) for email and calendar.
3. **Judgment engine v0 plus morning check-in** (3.4, 3.9). This is the visible "it tells me what matters" moment.
4. **Supervisor** (3.7) on drafts.
5. **Bench v0**, 10 scenarios (section 4).
6. Specialists and the scorecard follow in week two. Self-improvement (3.10) comes once the bench is stable.

## 6. Open questions

1. **Model budget:** which models power the worker and the supervisor until credits arrive? The free tier is rate-limited.
2. **White's identity:** its own email address and number now, or act only through the founder's accounts at first?
3. **Where White runs:** the laptop with a Docker Bot Screen, or a small cloud VM so it works while the laptop is off?
4. **Charter v1:** which 3 responsibilities do we start with? Proposed: design partners, follow-ups/commitments, investor pipeline.
