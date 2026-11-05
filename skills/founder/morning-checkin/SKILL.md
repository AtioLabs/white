---
name: morning-checkin
description: Send the founder one short daily check-in that leads.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Daily, Judgment, White]
    category: founder
    related_skills: [outcome-engine, founder-onboarding]
---

# Morning Check-in Skill

The one message a founder gets from White each morning. It leads: it says what matters most today and why, then asks only for the decisions and approvals that need the founder. It reads like a sharp chief of staff, not a status report.

## When to Use

- The daily cron tick (default 08:30 in the founder's timezone).
- "What should I focus on today?", "where are we?"

## Prerequisites

- The `white-core` plugin (`white_judge`, `white_query`, `white_wiki`). `$HERMES_HOME/founder/charter.yaml`; if it's missing, propose one from `charter.example.yaml` and `company.md`.

## Procedure

1. **Judge first.** Call `white_judge`. Its ranking is code-computed from the charter and world model, so use it rather than re-ranking from memory.
2. **Check the top items.** For the top 3, verify the evidence still holds (`white_query` search, the inbox, the kanban card). Drop or fix anything stale.
3. **Collect the founder queue:** kanban cards in `review` (approvals) and `blocked/needs_input` (decisions). Each decision gets your recommended answer.
4. **Write the message,** at most 12 lines, in this order:
   - **Today's one thing:** what, why (the numbers), and what you'll do versus what you need from them.
   - **Challenge** (only if `white_judge` returned one): say it plainly, with the evidence, as a recommendation.
   - **Decide:** "Q? I recommend X, because Y. Reply 1/2."
   - **Approve:** one line per draft, with a link.
   - **Done since yesterday:** with proof links.
   - **Scorecard:** one line per responsibility (current/target, status).
5. **Send** it to the founder's home channel. Log it with `white_log` kind=action, status=done, proof = the message id.
6. Refresh the wiki with `white_wiki`.

## Pitfalls

- Burying the one thing under a list. It goes first, always.
- Reporting activity instead of outcomes ("researched 40 companies" versus "3 calls booked").
- Softening challenges until they say nothing. Be direct and kind, with numbers.
- Asking open questions. Every question carries your recommendation.

## Verification

- The message starts with one item from `white_judge`'s `one_thing`, or explains why you overrode it.
- Every number in it traces to the world model or a source.
- The action is logged with the message id as proof.
