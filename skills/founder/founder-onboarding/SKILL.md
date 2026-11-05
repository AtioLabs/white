---
name: founder-onboarding
description: Learn the founder's voice, company and authority rules.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Onboarding, Voice, Memory, White]
    category: founder
    related_skills: [google-workspace, email-inbox-triage]
---

# Founder Onboarding Skill

White's first conversation with a new founder. It builds three files that every other White skill reads: the founder's voice, the company, and what White may do without asking. It is a conversation led by White, not a form, and it leaves the founder with drafts they can correct rather than blank questions.

## When to Use

- First run, or when `$HERMES_HOME/founder/voice.md` or `company.md` is missing.
- The founder says "learn my voice", "that doesn't sound like me", or "update what you know about the company".
- After a major change: pivot, new round, new co-founder, new milestone.

Don't use it for one-off drafting. Other skills read these files, they don't re-interview.

## Prerequisites

- Optional but much better: email access (`google-workspace` or `himalaya`) to read the founder's **sent** mail.
- Web search (`web_search`, `web_extract`) to read the founder's public writing, site, LinkedIn and X.

## Quick Reference

| File | Holds | Templates |
|---|---|---|
| `$HERMES_HOME/founder/voice.md` | How the founder writes | `templates/voice.md` |
| `$HERMES_HOME/founder/company.md` | What the company is, traction, the next milestone | `templates/company.md` |
| `$HERMES_HOME/founder/authority.md` | What White may do alone vs. with approval | `templates/authority.md` |

## Procedure

### 1. Gather evidence before asking anything

Collect real samples first, so the conversation is about corrections, not blanks:
- Ask for links: company site, LinkedIn, X, blog or essays, the pitch deck if one exists.
- `web_extract` each link. Use `web_search` for the founder's name plus the company, for interviews, posts and launches.
- If email is connected, read 20–40 recent **sent** emails, mixing cold, investor, customer and casual. Skip anything marked confidential.

Done when you have at least 5 pieces of the founder's own writing, or you've told them you couldn't find that many.

### 2. Draft the voice profile from the evidence

Fill `templates/voice.md` from what you actually observed: sentence length, how they open and close, how formal they are, words they use, words they never use, how they ask for things, emoji or none. **Every trait must quote a real line that shows it, with its source URL.** Generic adjectives without quotes ("direct, clear, analytical") are a failure: replace them with specifics ("cuts to the point: '<quote>' (source)"). Don't invent traits you didn't see. Also ask once for permission to read their sent emails, because public writing differs from how they email.

### 3. Run the conversation, leading with drafts

Show the founder your draft and guide them; don't interrogate. Pattern for each point: **your read → why it matters → confirm or correct.**
- "You open cold emails straight with the ask, no small talk. I'll keep that, since investors read fast. Right?"
- "Your site says 'AI-powered'. Your essays never use buzzwords. I'll follow the essays. OK?"

**Hard rule: never ask an open question when the evidence lets you propose an answer.** Bad: "Can you provide a one-line pitch?" Good: "Pitch, from your site: 'River does your accounting as it happens, from a WhatsApp message.' Use it, or sharpen it?" Cite the source for each proposal. Only ask open questions for facts that appear nowhere (e.g. revenue), and even then offer a likely range or an example answer.

Then cover the company the same way. Propose answers from what you found, and ask only for what you couldn't find:
- one-line pitch, problem, who it's for, why now
- traction: users, revenue, growth, notable customers (numbers, with dates)
- team, the round (amount, stage, timing), the next milestone
- what they'd never say publicly (confidential numbers, unannounced customers)

Push back where an investor would: "You say 'growing fast' but haven't given me a number. Investors will ask first thing. What's last month vs. the month before?"

Keep it to about 15 minutes. Batch related questions, and never ask more than 3 at once.

### 4. Set authority

Propose safe defaults from `templates/authority.md`. Anything that goes out in their name needs approval, and research and drafts don't. White never commits money. Let them loosen it.

Also write the machine-readable version that the `white-gate` plugin enforces, `$HERMES_HOME/founder/authority.yaml` (format in the plugin's `authority.example.yaml`): the `never_share` strings (exact phrases: numbers, unannounced customers) and any `standing_permissions` the founder grants. If it's empty, everything outward needs approval, which is the safe default.

### 4b. Propose the charter

Propose 2–3 responsibilities White will own, each with a measurable target and date, from what you learned (default: design partners, follow-ups, plus the round if they're raising). Write `$HERMES_HOME/founder/charter.yaml` (format in `white-core`'s `charter.example.yaml`). Targets must come from the founder or a cited benchmark. If you propose a number, say where it comes from.

### 5. Write the files and prove it

Write `voice.md`, `company.md`, `authority.md`, `authority.yaml` and `charter.yaml` under `$HERMES_HOME/founder/` with `write_file`. Record the key people and orgs you learned about with `white_record` (with sources). Then run `white-cycle` step 0 so White sets up its own schedule. Then show proof the voice works: draft one short real email the founder needs to send this week, in their voice, and ask "Does this sound like you?" Patch `voice.md` with whatever they correct.

### 6. Keep it alive

Whenever the founder edits a draft you wrote, call `white_feedback` (kind=draft_edit, with your draft and their version) to get exactly what they cut and added, then `patch` `voice.md` with the lesson ("cuts sign-offs to just 'A'"). Don't re-ask anything these files already answer.

### 7. Audit the founder's week and propose what to take

Don't ask the founder what to hand over. They don't know what they don't know. Watch, then propose, the way a new founder's office hire does in week one.

1. With approval, read the last 7 days, and keep observing for the next 7: calendar, sent and received email, and Slack/WhatsApp if connected. Use `google-workspace`, the email tools, or computer use.
2. List every recurring piece of work the founder did: follow-ups, scheduling, updates, outreach, research, admin, posting. For each, estimate the time spent and note the evidence (the thread, meeting, or doc).
3. Rank the items by hours saved × how safely White can do them. Mark each as **take now**, **take with approval**, or **founder only** (with a reason).
4. Show the top 10–12 as a short table: "You spent ~X h on Y. I'll do it by Z. First run: <date>." Recommend the top 3 to start.
5. Each accepted item becomes a workstream in `outcome-engine` or a cron routine. Record any new standing permissions in `authority.md`.

Re-run the audit monthly. New hand-offs show up as the company changes.

## Pitfalls

- **Generic voice profiles** ("friendly, professional") are useless. Every trait needs an observed example.
- **Inventing traction.** Only write numbers the founder gave you or a cited source shows, with the date.
- **Interrogating.** A wall of questions is exactly what the founder is trying to escape. Lead with drafts.
- **Leaking confidential items.** Record them under "never share" in `company.md`, and never put them in outreach.

## Verification

- All five files exist (`voice.md`, `company.md`, `authority.md`, `authority.yaml`, `charter.yaml`), and none is a bare template.
- White's cron jobs exist (`white-cycle` step 0).
- `voice.md` contains at least 3 real quoted lines.
- The founder approved one sample email as sounding like them, or the corrections were patched in.
- The week audit produced a ranked hand-off list, with evidence per item and at least 3 items accepted.
