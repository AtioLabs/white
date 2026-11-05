---
name: sf-intel
description: Weekly brief on what SF founders ship and what it means.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Intel, Competitors, Trends, White]
    category: founder
    related_skills: [competitor-news-monitor, outcome-engine, distribution]
---

# SF Intel Skill

Keeps a founder outside SF as informed as one inside it. Every week it scans what SF and YC startups, investors, and AI labs shipped and said, filters it down to what matters for this company, and turns it into actions. It's a short brief, not a news dump.

## When to Use

- Weekly cron (default Monday morning, in the founder's timezone).
- "What's happening in SF?", "what are competitors doing?", "am I behind?"

## Prerequisites

- `company.md` (what matters to this company). Web search. Hermes's `competitor-news-monitor` skill for named competitors.

## Quick Reference

Watchlist: `$HERMES_HOME/founder/intel/watchlist.md`, which lists competitors, adjacent startups, key investors, YC batch filters, and model/lab release channels. Propose it from `company.md`, and the founder edits it.

## Procedure

1. **Scan live:** recent YC launches in the space, competitor changelogs and pricing pages, funding news, investor posts and theses, AI model and tool releases that change what's possible, and notable founder threads. Use only items from the last 7 days, each with a source URL.
2. **Filter hard:** keep only items that change something for this company: a threat, an opportunity, a new capability, or a pricing or positioning signal.
3. **Brief:** at most 8 items. For each: what happened (one line plus link), **so what for us**, and the suggested action. End with "one thing to do this week".
4. **Act:** offer to turn actions into `outcome-engine` cards (e.g. "update the positioning page", "post a take", "email investor X who just backed a neighbor").

## Pitfalls

- Volume over signal. 8 items maximum, every one with a "so what".
- Stale or unsourced items.
- Panic. Frame competitor moves with a calm, concrete response.

## Verification

- Every item has a source dated within the last 7 days, plus a "so what" and an action.
- The brief is delivered on schedule to the founder's channel.
