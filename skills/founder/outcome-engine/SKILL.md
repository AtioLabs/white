---
name: outcome-engine
description: Turn a founder's goal into tracked work and drive it daily.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Goals, Kanban, Planning, White]
    category: founder
    related_skills: [founder-onboarding, weekly-review-planning]
---

# Outcome Engine Skill

The founder hands White an outcome ("close the seed by March"), not a task list. This skill turns that outcome into a Kanban board of real work, runs that work every day, and brings back to the founder only decisions, approvals, and proof. The founder should never have to write a prompt to move it forward.

## When to Use

- The founder states a goal, deadline, or milestone ("raise ₹2 Cr", "get into YC W27", "10 paying customers by Jan").
- A cron tick fires the daily drive for an open outcome.
- The founder asks "where are we on X?"

Don't use it for one-off requests that finish in a single reply.

## Prerequisites

- `kanban` toolset enabled for this profile, with the Kanban dispatcher running (`hermes kanban` docs).
- `$HERMES_HOME/founder/company.md` and `authority.md` exist. If not, run `founder-onboarding` first.
- Web search (`web_search`, `web_extract`) for live facts.

## Quick Reference

| Concept | Kanban mapping |
|---|---|
| Outcome | One board (slug `outcome-<short-name>`), plus a root card holding the outcome contract |
| Workstream | Parent card (e.g. "Financial model", "Investor pipeline") |
| Unit of work | Child card, small enough for one worker run, with a clear "done means" |
| Needs a founder decision | `kanban_block` with kind `needs_input`, plus a recommended answer |
| Needs founder approval | `kanban_request_review` (anything going out in the founder's name) |
| Proof | `kanban_complete` with `summary`, plus `artifacts` / URLs |

## Procedure

### 1. Write the outcome contract and guide while you do

Before creating any cards, restate the goal as a contract in the root card:
- **Outcome:** measurable ("₹2 Cr committed by 31 Mar 2027"), not vague ("raise money").
- **Why it matters / deadline.**
- **Done means:** the evidence that proves it (signed SAFEs, acceptance email).
- **Constraints:** budget, the founder's hours per week, things off-limits.

Guide; don't interrogate. If the goal is vague or unrealistic, propose a sharper version with reasoning and a live-sourced benchmark: "Indian pre-seed rounds in your sector are mostly X (source). I'd target Y by Z. OK?" Get one confirmation, then move.

### 2. Decompose like a founder's office would

Break the outcome into the workstreams an experienced operator would run, including the ones the founder didn't mention but will need. For a seed round, that typically covers the financial model, the deck, the data room, the investor list, outreach, meetings, and follow-ups. Research the typical process live instead of assuming.

For each workstream, create a parent card and the first 2–5 child cards with `kanban_create`. Every child card body has:
- **Goal**, **Done means** (checkable), **Inputs** (files, links), **Skill to use** (e.g. `linkedin-skills`, `humanizer`).
- Dependencies via `kanban_link` when one card needs another's output.

Only create the next few cards per workstream. Re-plan as results come in; don't build a 60-card plan that goes stale.

Show the founder the plan in at most 10 lines: workstreams, what you're starting now, what you need from them. Then start without waiting, unless something needs approval.

### 3. Drive it daily

On each daily tick (cron; see Verification), for every open outcome:
1. `kanban_list` the board. Review finished cards and check their proof is real (open the file, check the URL).
2. Unblock what you can yourself. Turn anything else into a founder decision with your recommended answer.
3. Create the next cards so every active workstream has work ready.
4. Check you're on pace: compare progress to the deadline. If behind, say so plainly and propose a fix (cut scope, add hours, move the date).

### 4. Bring back only what needs the founder

One message, in this order and nothing else:
- **Decide:** each `needs_input` card as "question, my recommendation, why", answerable in one word.
- **Approve:** each `review` card (draft email, application, post) with a one-line summary.
- **Done:** finished items, with proof links.
- **Pace:** on track or behind, plus the next milestone.

Founder's reply → `kanban_unblock` / approve / `kanban_request_changes`. If they edit a draft, pass the edit to `founder-onboarding` step 6 so the voice profile learns from it.

### 5. Close the outcome

When the "done means" evidence exists, verify it, complete the root card, and write a short retro in `company.md` (what worked, what to reuse). Suggest the next outcome.

## Pitfalls

- **Becoming a to-do app.** If the founder is writing the cards, you've failed. You write them.
- **Asking without recommending.** Every question carries your answer and reasoning.
- **Fake progress.** "Researched investors" isn't done. "34 investors matched, sheet attached, 3 sources each" is done.
- **Sending without approval.** Anything going out in the founder's name goes through `kanban_request_review` unless `authority.md` grants standing permission.
- **Stale facts.** Benchmarks, deadlines, and investor info come from live search, with sources.

## Verification

- The root card has a measurable outcome and "done means".
- Every active workstream has at least one ready or running card.
- Every completed card carries proof (artifact, URL, or checked fact).
- A daily cron job exists for the outcome. Create it on first run, e.g. `hermes cron` with "Run outcome-engine daily drive for board outcome-<name>, then send the founder the check-in", delivered to the founder's chosen channel.
