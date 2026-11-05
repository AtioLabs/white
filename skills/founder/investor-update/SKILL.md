---
name: investor-update
description: Draft the monthly investor update from real progress.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Investors, Updates, White]
    category: founder
    related_skills: [outcome-engine, investor-outreach, founder-onboarding]
---

# Investor Update Skill

Writes the monthly update to investors, angels, and warm prospects from what actually happened, so the founder stays top of mind and gets help without spending a weekend on it. Every number comes from a source, and the asks are specific.

## When to Use

- Monthly cron (default the 3rd business day).
- "Write the investor update."

## Prerequisites

- `company.md`, `voice.md`, the `outcome-engine` boards, and the pipeline files. The recipient list is in `$HERMES_HOME/founder/pipeline/update-list.csv`.

## Quick Reference

Structure: **TL;DR** (3 lines) → **Metrics** (the same set every month, with deltas) → **Wins** → **Lowlights** (honest) → **Asks** (2–3 specific: "intro to the ops head at <company>") → **Thanks**.

## Procedure

1. **Gather:** pull completed outcome-engine cards, pipeline changes, metrics the founder reported, and customer quotes logged that month. Ask only for the metrics you can't find, with last month's value pre-filled.
2. **Draft:** use the structure above, in the founder's voice, at most 300 words. Put lowlights in plainly, because investors trust founders who share bad news. Make the asks concrete and easy to act on.
3. **Approve and send:** send it to `kanban_request_review`. After approval, send it via email to the update list, BCC or individually per `authority.md`.
4. **Follow through:** track replies and offers of help, turn them into cards, and thank people who helped.

## Pitfalls

- Vanity metrics, or changing which metrics appear month to month.
- Vague asks ("any intros appreciated").
- Leaking "Never share" items.

## Verification

- Every metric traces to a source or the founder's confirmation.
- The approval is recorded, and the send confirmation is logged. Help offers become cards.
