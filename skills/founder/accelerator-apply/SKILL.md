---
name: accelerator-apply
description: Find accelerators, track deadlines, draft applications.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Accelerators, Applications, White]
    category: founder
    related_skills: [founder-onboarding, outcome-engine, humanizer]
---

# Accelerator Apply Skill

Finds the accelerators, grants, and programs that fit the company, tracks every deadline, and drafts applications in the founder's voice. It reuses `company.md` so the founder never retypes the same answers. It submits only with approval.

## When to Use

- "Apply to accelerators", "what programs should I apply to?", "YC application".
- A cron tick for deadline tracking.

## Prerequisites

- `voice.md`, `company.md` (`founder-onboarding`). Web search and the browser (to fill forms).

## Quick Reference

Tracker: `$HERMES_HOME/founder/pipeline/accelerators.csv` (program, location/remote, terms (equity/cash), fit, deadline plus source URL, status, answers file).

Answer bank: `$HERMES_HOME/founder/answers/`, one file per common question (what you do, traction, why now, competitors, team, the founder video script).

## Procedure

1. **Find:** `web_search` for current cohorts that fit sector, stage, and geography (global, India, remote), plus grants and government schemes. Verify each deadline and term on the official page, and cite it. Rank by fit and terms, and recommend the top 5 with reasons.
2. **Track:** create a cron reminder 10 days and 3 days before each deadline. Re-check deadlines weekly, since they change.
3. **Draft:** answer each question from `company.md` and the answer bank, in the founder's voice, at the program's word limits. Push back on weak answers the way a partner reading 10,000 applications would ("'We use AI' says nothing. Say what changes for the customer."). Run `humanizer`.
4. **Review and submit:** send the full application to `kanban_request_review`. After approval, fill the form via the browser. Screenshot the confirmation as proof.
5. **Learn:** save the final answers to the answer bank. Log the outcomes.

## Pitfalls

- **Missed or wrong deadlines.** Always verify on the official page.
- **Copy-paste answers** that ignore what each program asks.
- **Submitting without approval.** Never.

## Verification

- Every tracked program has an official-source deadline URL.
- Every submission has an approval record and a confirmation screenshot.
