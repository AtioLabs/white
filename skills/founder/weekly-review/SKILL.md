---
name: weekly-review
description: "White's Monday review: scorecard, misses, and next week."
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Review, Accountability, White]
    category: founder
    related_skills: [morning-checkin, outcome-engine, sf-intel, white-cycle]
---

# Weekly Review Skill

White reports to the founder the way a good hire does in a 1:1: what it owned, what moved, what it missed and why, what it learned, and what it will do next week. It doesn't spin the numbers.

## When to Use

- Monday cron (`white-weekly`), or "how did last week go?"

## Procedure

1. Call `white_scorecard` and `white_judge`.
2. Run `sf-intel` and keep only the 1–2 items that change next week's plan.
2b. **Growth partner.** `white_gaps` action=gather, then decide what the founder and company lack to hit the charter (skills, tools, people, process, numbers, focus). Write at most 5 gaps with `white_gaps` action=write, each with evidence, the fix and who owns it; do the "white" ones yourself. Add `white_mastery` action=report (lowest tool usage first) and `white_scout` action=scan (owned but unused). Monthly: `white_models` (hardware, open_models, routing). Explain one open-weight model that fits the founder's machine or needs in plain words, and propose a change to White's own models only with cost, speed and quality numbers.
3. Write the review, at most 20 lines:
   - **Outcomes:** one line per responsibility (current/target, on track, behind, or met).
   - **Done:** the 3–5 actions that mattered, with proof links. Outcomes, not activity.
   - **Missed:** every miss, with the reason and the fix. Don't hide or soften them.
   - **Learned:** the lessons added this week (with their evidence), plus what changed from the founder's feedback (e.g. "you rejected 3 content recommendations, so I've ranked content lower").
   - **What's missing:** the top 2–3 gaps from step 2b, each with its fix (link the full report).
   - **Next week:** the plan from `white_judge`, the 1–2 SF intel items, and decisions needed from the founder (each with a recommendation).
   - **Question for you:** one thing the founder should change (target, date, or authority), if the data says so.
4. Run `white_review` (kind=report), then send to the founder's channel. Log it with `white_log` (action, done, proof = the message id).
5. When the founder reacts to a recommendation, call `white_feedback` (accepted/rejected).

## Pitfalls

- Activity theatre ("researched 50 companies"). Report what moved.
- Hiding misses. A miss with a fix builds trust, and a hidden one destroys it.
- A plan that ignores `white_judge` without saying why.

## Verification

- Every responsibility in the charter appears in Outcomes.
- Every miss in `white_scorecard` appears in Missed, with a fix.
