---
name: white-cycle
description: "White's work loop: take in events, judge, act, verify, log."
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Loop, Autonomy, White]
    category: founder
    related_skills: [morning-checkin, outcome-engine, inbox-calendar-meetings, founder-onboarding]
---

# White Cycle Skill

The loop that makes White a worker instead of a chatbot. It runs on a schedule without anyone prompting it: take in what changed, decide what matters, do the work, check it, and record everything. A cycle that finds nothing important says nothing. It doesn't message the founder just to report that it ran.

## When to Use

- A cron tick (default every 2 hours, 08:00–20:00 in the founder's timezone).
- Right after onboarding, to set up White's own schedule.
- The founder says "catch up", "what's new?", or "go".

## Prerequisites

- `white-core` and `white-gate` plugins enabled. `founder/charter.yaml` and `founder/authority.yaml` exist (`founder-onboarding` writes them).
- Email/calendar access if connected (`google-workspace`, `himalaya`, or MCP). Without them, the cycle runs on the world model and kanban only.

## Procedure

### 0. First run: set up your own schedule

If `cronjob_manage` shows no White jobs for this profile, create them (founder's timezone from `company.md`):

| Name | Schedule | What it runs |
|---|---|---|
| `white-cycle` | every 2h, 08:00–20:00 | this skill |
| `white-morning` | 08:30 daily | `morning-checkin` |
| `white-weekly` | Monday 09:00 | `weekly-review` (includes `sf-intel`) |
| `white-wiki` | 23:30 daily | `white_wiki` |

Deliver to the founder's home channel. Log the setup with `white_log` (kind=action, status=done, proof = the job ids).

### 1. Take in events

**Inbox first.** Call `white_inbox` action=scan. The founder drops anything there (local `founder/inbox/` or the Google Drive folder in `founder/inbox.yaml`) and never explains it: work out what it is and what it implies yourself. For each new item: record its people, orgs, deals, commitments and numbers with `source` = the item's `source`; then do the work it implies (a new deck → update the seed model and pipeline notes; a term sheet → summarise terms and flag the decisions). No-risk work: just do it. Risky work (outward, money, irreversible, reputation, never-share): prepare it and ask the founder for one decision. Then call action=file with a one-line summary and the work done. If no text was extracted, open the file with your own tools.

Read what changed since the last cycle: new email (inbox and sent), calendar changes, replies on kanban cards, A2A messages, and, if `white-identity` is set up, White's own inbox (AgentMail) and calls and texts (AgentPhone). With `white-connect`, read the founder's apps through Composio using read-only slugs (e.g. `GMAIL_FETCH_EMAILS`, `GOOGLECALENDAR_LIST_EVENTS`). For each **meaningful** item, call `white_log` kind=signal with `source` = the stable id (e.g. `gmail:<message-id>`, `cal:<event-id>`). Re-ingesting the same id is a no-op, so re-scanning is safe. Skip newsletters and notifications.

From each meaningful item, also update the world model:
- new or known people and orgs: `white_record` (with source)
- deal movement: `white_record` kind=pipeline (stage, next step, due)
- promises made in the thread by the founder or the other side: `white_log` kind=commitment (with due date)

### 1b. Infer intent (no prompt needed)

Call `white_intent` action=context. Ask yourself: *what is the founder trying to get done this week?* Look for patterns across signals (an essay dropped + two investor emails = "preparing a fundraise story"), not single events. For each real pattern (max 3), call action=propose with the signal ids as evidence, your honest confidence, and risk (`risky` if the next step is outward, money, irreversible, reputation, or touches never-share). Then follow the returned decision exactly:
- **act**: do the next step now and log it.
- **ask**: prepare the work, then ask the founder ONE question with your recommended answer.
- **wait**: do nothing; it stays open for more evidence.

If nothing forms a pattern, call action=quiet with why. Doing nothing is a correct answer; inventing work is not. When the founder reacts to a guess, record it with action=feedback so White learns which signals to trust. Close finished intents (`close`, status done) and stale ones (status expired).

### 2. Judge

Call `white_judge`. Treat its ranking as the plan unless you can see evidence it's wrong; if you override it, say why in the log.

### 3. Act on the top items, within authority

For each of the top 3 items:
- If it takes a few minutes (updating the world model, a reminder, a short reply draft), do it now.
- If it's bigger, hand it to a specialist: `white_dispatch` (role outreach | research | content | finance | ops, goal, checkable done_means), then `kanban_create` with exactly the payload it returns. White orchestrates and checks; specialists do the work.
- If it needs the founder (a decision, or an approval to send), prepare everything first (draft, recommendation, evidence), then queue it: `kanban_request_review` for approvals, `kanban_block` with kind `needs_input` for decisions.
- Never try to send outward and "see if the gate allows it". Drafts go to review.

### 4. Verify

Run `white_review` on every draft and result before it's queued or marked done. Fix and recheck up to 2 times.

### 5. Record

- Mark handled signals: `white_log` kind=signal_handled.
- Every action: `white_log` kind=action, with status and proof.
- Promises kept: `white_log` kind=commitment_status, status=done.
- If something urgent appeared (a person waiting with a near deadline, a never-share risk, a broken promise), message the founder now with one short line and the recommended action. Otherwise stay quiet until the morning check-in.

## Pitfalls

- **Noise.** Don't message the founder every cycle. Urgent only; everything else waits for the check-in.
- **Duplicate work.** Check the world model and kanban before starting something; it may already be in progress.
- **Unsourced facts.** Every record needs a source id, and the plugin rejects it otherwise.
- **Silent overrides.** If you ignore `white_judge`'s top item, log why.

## Verification

- Every meaningful new email or calendar change from this cycle has a signal row with its source id.
- The top `white_judge` items have an action, a queued approval, or a logged reason for deferring.
- No outward action happened without approval or a standing permission (check `white/gate-log.jsonl`).
