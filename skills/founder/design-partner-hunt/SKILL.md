---
name: design-partner-hunt
description: Find, recruit and convert B2B design partners.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, B2B, Design-Partners, Sales, India, White]
    category: founder
    related_skills: [outcome-engine, founder-onboarding, linkedin-skills, humanizer]
---

# Design Partner Hunt Skill

Runs the founder's design-partner program end to end, as an outcome inside `outcome-engine`. It defines who to recruit, finds companies showing the pain right now, gets warm or sharp cold intros in the founder's voice, preps and logs discovery calls, and drives each partner to a paid decision. It does not invent prospects or send anything without approval.

## When to Use

- The founder says "find design partners", "first customers", or "pilot users".
- `outcome-engine` has a design-partner or first-customers workstream.

## Prerequisites

- `founder-onboarding` done (`voice.md`, `company.md`, `authority.md`).
- Web search (`web_search`, `web_extract`). The browser or computer use for LinkedIn.
- Optional: the founder's LinkedIn connections export (CSV), and email access for sending approved messages.

## Quick Reference

Evidence-based defaults (see `references/evidence.md`); adjust with the founder:

| Decision | Default | Why |
|---|---|---|
| Cohort size | 5–8 committed partners | Guides range 3–15. A small cohort stays deep. |
| Program length | 90 days, then a paid decision | Stops it turning into free support |
| Indian minimum | Paid from the start, even small (e.g. ₹50k ACV) | Tests budget, which is a known Indian enterprise blind spot |
| Channels, in order | Warm network → accelerator/alumni → niche communities → targeted LinkedIn → cold email | Warm converts best, but cold LinkedIn has worked alone |
| Who | Can buy, or one step from the buyer. Pain is weekly. Already paying for a bad workaround. | Screens out curious-but-useless partners |

## Procedure

### 1. Define the ideal partner and guide while you do

Draft the profile from `company.md`: industry, size, role of the champion, role of the buyer, the weekly pain, the current workaround. Propose it with reasoning and push back if it's too broad ("'Indian SMBs' is 60M companies. I'd start with 50–200-person logistics firms in Pune and Chennai, because…"). Get one confirmation.

### 2. Build the list from live signals

Find companies showing the pain **now**, and cite the signal for each:
- job posts for the role your product replaces or helps
- public complaints (LinkedIn posts, Reddit, communities, reviews of competitor tools)
- tool switches, funding, new leadership, expansion news

Find the champion and buyer names via `web_search` and the browser. Score each prospect against the ideal-partner profile. Target 40–60 prospects for 5–8 partners. Save the list to `$HERMES_HOME/founder/pipeline/design-partners.csv` (company, person, role, signal, source URL, warm path, score, status).

### 3. Find the warm path first

For each prospect, look for a mutual connection (the founder's LinkedIn export, investors, accelerator alumni, ex-colleagues). If one exists, draft a short forwardable intro request to the connector. Only go cold when there's no warm path.

### 4. Write outreach that sounds like the founder

Each message must name the prospect's specific signal, offer a concrete design-partner deal (what they get, what you ask, how long), and make one small ask (a 20-min call). Use the `voice.md` rules, then run `humanizer`. Use `linkedin-skills` for connection notes and follow-ups. Under 90 words. No templates that look like templates.

Every message goes through `kanban_request_review` for approval unless `authority.md` grants standing permission. Follow up twice at most, 4–6 days apart, each time with new value (an insight or a relevant result) rather than "just bumping".

### 5. Prep and log discovery calls

Before each call, write a one-page brief: the company, the person, their signal, 5 discovery questions about their current workflow and cost of the pain, and what a "yes" looks like. After each call, log pains, quotes, objections, and willingness to pay in `company.md` under customer feedback. Flag patterns across calls to the founder.

### 6. Make the deal and drive to a paid decision

Send a one-page design-partner agreement draft. It lists the commitments (workflow calls, access to one process, feedback on versions, one sponsor meeting), the length, the price or discount, a decision date, and payment terms in writing (deposit or milestones, named approver). Track it to the decision date and push for the paid conversion.

## Pitfalls

- **Inventing prospects or signals.** Every row needs a real source URL.
- **Spray and pray.** 50 sharp, signal-based messages beat 500 generic ones, and the founder's name is on every one.
- **Free forever.** No end date and no price means no learning about budget.
- **Ignoring Indian payment reality.** Get the approver and payment terms in writing before work starts.
- **Founder disappears.** Founder-led selling is the norm early on, so White preps, drafts, and follows up, but the founder takes the calls.

## Verification

- The pipeline CSV exists, and every row has a signal plus a source URL.
- Every sent message was approved, or covered by a standing permission in `authority.md`.
- Every call has a brief before it and a log after it.
- Weekly status in the `outcome-engine` check-in: prospects, intros, calls, agreements, paid.
