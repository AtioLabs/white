---
name: distribution
description: Pick channels and post steadily in the founder's voice.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Distribution, Content, LinkedIn, X, White]
    category: founder
    related_skills: [linkedin-skills, marketingskills, humanizer, xurl, founder-onboarding]
---

# Distribution Skill

Gets the founder and the company seen without a big name behind them. It picks the 1–2 channels that fit the buyer, turns real progress and customer stories into posts in the founder's voice, keeps a steady cadence, and learns from what performs. Real receipts beat hype.

## When to Use

- "Post for me", "grow my audience", "distribution", "build in public".
- A cron tick for the weekly content plan or daily posting.

## Prerequisites

- `voice.md`, `company.md`. Vetted skills: `linkedin-skills` (sergebulaev) and `marketingskills` (Corey Haines), installed after a SkillSpector scan, plus `humanizer`. X via `xurl`.

## Quick Reference

Content sources, in order of strength: customer results and quotes (with permission) → real receipts and metrics → lessons from building → opinions grounded in the founder's essays → industry news reactions.

Files: `$HERMES_HOME/founder/content/plan.md` (weekly plan), `log.csv` (post, channel, date, metrics).

## Procedure

1. **Channel choice:** research where the buyer actually spends time (B2B India: usually LinkedIn, plus niche communities). Propose 1–2 channels with reasoning, not everywhere.
2. **Weekly plan:** every Monday, draft 3–5 posts from the week's real material (outcome-engine progress, call logs, customer feedback). Mix formats: receipts, lessons, contrarian takes.
3. **Write:** use the `linkedin-skills` hooks and structures, with `voice.md` rules, then `humanizer`. No engagement bait or fake stories.
4. **Approve and publish:** posts go to `kanban_request_review` in one batch. Publish on schedule via the channel's tool or the browser.
5. **Engage:** draft replies to comments and thoughtful comments on relevant creators' posts, for approval.
6. **Learn:** log metrics after 48h, tell the founder what worked, and adapt next week.

## Pitfalls

- Generic AI-sounding posts, which ruin trust. Always run voice plus `humanizer`.
- Sharing customer names or numbers without permission.
- Chasing virality over buyers. Measure inbound leads, not just likes.

## Verification

- Every published post has an approval record and a log entry with metrics.
- The weekly report shows posts, reach, and inbound leads or DMs attributed to them.
