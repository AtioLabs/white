---
name: investor-outreach
description: Match investors and send personal outreach as the founder.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Fundraising, Investors, Outreach, White]
    category: founder
    related_skills: [seed-model, white-network, humanizer, outcome-engine]
---

# Investor Outreach Skill

Finds the investors who actually fit, works out why each one would care, and gets the founder in front of them. Warm intros come first, then sharp personal cold emails written in the founder's voice. It tracks every conversation to a decision. Nothing goes out without approval.

## When to Use

- "Find investors", "who should I pitch?", "send investor emails".
- The `outcome-engine` fundraising workstream.

## Prerequisites

- `voice.md`, `company.md`, `authority.md` (`founder-onboarding`).
- Web search. A people-and-company search provider (Exa or Parallel) gives the best results.
- Optional: the founder's LinkedIn export, for warm paths. `white-network` for intros.

## Quick Reference

Pipeline file: `$HERMES_HOME/founder/pipeline/investors.csv` (firm, partner, stage, check size, geography, thesis fit, recent relevant deal plus URL, warm path, status, next step, date).

Statuses: `researched → intro-requested → contacted → replied → meeting → diligence → committed | passed`.

## Procedure

### 1. Define the target with live research

From `company.md`, draft the target: stage, sector, check size, geography. Propose a target list size (e.g. 60–100 for a seed round) with reasoning. Research what similar companies raised from recently, and cite it.

### 2. Match and qualify

For each candidate, verify with live sources that they invested at this stage and sector in the last 12–18 months, that the partner is still active, and that they have no conflicting portfolio company. Record the **reason to care**: one specific link between their recent deal or thesis and this company. Drop anyone without a real reason.

### 3. Warm path first

Look for mutual connections: the founder's network, existing angels, accelerator alumni, `white-network`. Draft forwardable intro blurbs (3–4 lines) for connectors.

### 4. Personal cold emails

Under 120 words, in the founder's voice: the reason to care in line one, one traction proof point, the ask. Run `humanizer` on it. Each one goes to `kanban_request_review`. Send in small batches, and follow up twice with new information (a milestone or a customer), never "just checking in".

### 5. Run the process

Log replies. Book meetings (`inbox-calendar-meetings`). Prep a brief per meeting: the partner's background, their portfolio, likely questions, and the `seed-model` Q&A. Track momentum. Tell the founder when to create urgency, and when a lead is going cold.

## Pitfalls

- **Spray lists.** Generic investor databases without a reason to care get ignored.
- **Stale facts.** Funds close, and partners move. Verify everything live, with a date.
- **Leaking data.** Don't attach the deck or numbers before the founder approves it, per investor.

## Verification

- Every pipeline row has a recent-deal URL and a written reason to care.
- Every sent email was approved, or covered by a standing permission.
- The weekly check-in shows pipeline counts by status.
