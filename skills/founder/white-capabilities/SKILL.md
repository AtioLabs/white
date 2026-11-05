---
name: white-capabilities
description: "Find, vet and master the tools and skills a task needs."
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Skills, Tools, Mastery, White]
    category: founder
    related_skills: [white-cycle, white-computer, weekly-review]
---

# White Capabilities Skill

The founder doesn't know every tool they own or every skill that exists, and shouldn't have to. You do. Your job: bring expert-level use of the right tool to every task, unasked.

## When to Use

- After setup and every Monday (inside `weekly-review`): scan and report gaps.
- A task needs something you can't do well yet: find a skill.
- You use any tool (Ploy, Stripe, Notion, Excel, anything): keep its mastery pack.

## Procedure

### 1. Know what the founder has
`white_scout` action=scan. Compare with `founder/charter.yaml`: which owned tools serve a goal but sit unused? Which goals have no tool at all?

### 2. Find a missing skill (no need to ask)
1. `white_scout` action=search need=`<what the task needs>`. Only repos with ≥1000 stars, a license and recent commits come back.
2. Pick the best fit by description, not just stars. `white_scout` action=fetch repo=`owner/name`: it downloads into quarantine and inspects the code.
3. If inspection passed: action=install with `why` = the task, and `only` = the skill folders you need. Then load and use it.
4. If blocked: don't work around it. Tell the founder in one line what was found and offer an alternative.

### 3. Master every tool you use
1. Before first real use, learn the tool from **live** sources: official docs, API reference, changelog, expert guides. `white_mastery` action=learn with each feature, what it does, which founder goal it serves ('' if none) and its source URL. Set `how_to_drive` (API/Composio → CLI → `white_desktop`).
2. After each use: action=use with the outcome and a lesson if you learned one.
3. Weekly: action=report. For the lowest usage %, tell the founder: "You use 20% of Ploy. I'll start running these 3 features for your goal X." Then do it (risky steps still go through approval).
4. Re-check changelogs monthly; add new features.

## Pitfalls

- Never install system software (apps, drivers, packages outside skills) this way: ask the founder.
- Stars aren't safety: the inspection result decides, and it re-runs at install.
- Don't learn features from memory: every feature needs a source URL.
