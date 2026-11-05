---
name: seed-model
description: Build a seed-stage financial model that guides the founder.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Fundraising, Financial-Model, Seed, White]
    category: founder
    related_skills: [excel-author, 3-statement-model, outcome-engine, investor-outreach]
---

# Seed Model Skill

Builds the financial model a seed investor expects: a driver-based monthly plan, hiring, burn, runway, and the raise amount. It works the way a good CFO-for-hire guides a founder who has never built one: it proposes every assumption with a live-sourced benchmark, explains why it matters, pushes back on weak numbers, and gets the founder ready to defend the model in a meeting. Banker-grade 3-statement depth is out of scope; use `3-statement-model` for that.

## When to Use

- "Build my financial model", "how much should I raise?", "what's my runway?"
- The `outcome-engine` fundraising workstream needs a model.
- Investors asked for a model, or questioned an assumption.

## Prerequisites

- `company.md` from `founder-onboarding` (traction, team, round).
- The `excel-author` optional skill, for workbook conventions and recalculation (`hermes skills install official/finance/excel-author`).
- Web search, for benchmarks. Never use benchmark numbers from memory.

## Quick Reference

Workbook tabs: `Assumptions` (every input, with a source and a note) → `Revenue` (driver-based) → `Team` (hiring plan) → `Costs` → `Monthly P&L + Cash` (36 months) → `Raise & Runway` → `Scenarios` (base/bear/bull) → `Investor Q&A`.

Inputs are blue, formulas black, and no hardcoded numbers live outside `Assumptions` (`excel-author` conventions).

## Procedure

### 1. Pick the model shape

From `company.md`, choose the revenue engine (SaaS seats, usage, transactional, services-led, or marketplace take rate) and say why in one line. Wrong shape means a wrong model.

### 2. Propose assumptions; don't ask for them

For each driver (pricing, conversion, sales cycle, churn, expansion, CAC, salaries by city and role, tools, and so on):
- `web_search` for current benchmarks for this sector, stage, and geography (e.g. Indian SaaS salaries in 2026, B2B churn at seed).
- Propose a value: "Churn 3%/mo. Seed B2B benchmarks run 2–4% (source). You have no data yet, so 3% won't look naive."
- Flag the drivers investors attack most (growth rate, CAC payback, hiring speed) and default to conservative ones.

Batch the proposals into one table for the founder: driver, proposed value, benchmark plus source, and why. They confirm or edit in one pass.

### 3. Build it

Generate the workbook with `excel-author` conventions, then recalculate. Every assumption cell's note carries its source URL.

### 4. Pressure-test like an investor

Compute and comment on runway, burn multiple, CAC payback, the month when revenue covers cost, and what breaks first. Push back plainly: "With 6 hires you run out in month 14, before the Series A milestone. Raise ₹X more, or cut to 4 hires. My pick is Y, because…" Build the bear case and say what it means.

### 5. Teach the founder to defend it

Write the `Investor Q&A` tab: the 10 questions investors will most likely ask about this model, each with a crisp answer grounded in the assumptions. Offer a 10-minute mock grilling.

## Pitfalls

- **Hockey sticks with no driver.** Every revenue number traces to a driver.
- **Benchmarks without sources, or stale ones.** Cite every one, and note the date.
- **Too much precision.** Seed investors want sane drivers and runway, not 400 rows.
- **Raising too little.** Size the raise to milestones plus a buffer, and show the math.

## Verification

- The workbook recalculates with no errors, and `Assumptions` has a source for every benchmark.
- Runway, burn, and the raise amount are on `Raise & Runway`, and they're consistent with the scenarios.
- The founder has the `Investor Q&A` tab. The file is attached via `kanban_complete` artifacts.
