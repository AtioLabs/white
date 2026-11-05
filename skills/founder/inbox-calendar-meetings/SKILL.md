---
name: inbox-calendar-meetings
description: Triage inbox, guard calendar, run meeting follow-ups.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Email, Calendar, Meetings, White]
    category: founder
    related_skills: [email-inbox-triage, google-workspace, meeting-action-items, outcome-engine]
---

# Inbox, Calendar and Meetings Skill

Takes the daily drag off the founder. It triages email into "needs you" versus "handled", drafts replies in their voice, books and protects time, preps a brief before each meeting, and sends notes and follow-ups after. It builds on Hermes's `email-inbox-triage`, `google-workspace`, and `meeting-action-items` rather than replacing them.

## When to Use

- A daily cron (morning, plus a light afternoon pass).
- "Clear my inbox", "schedule this", "prep me for my 3pm", "send the follow-up".

## Prerequisites

- Email and calendar access (`google-workspace`, or Outlook via `microsoft-office`/MCP). `voice.md`, `authority.md`.
- Meeting notes from a recorder or transcript (`google_meet` plugin, Granola export, or pasted notes).

## Quick Reference

Founder focus rules (propose them, and the founder edits): `$HERMES_HOME/founder/calendar-rules.md`, covering deep-work blocks, max meetings per day, which meetings are auto-accepted, which are declined politely, and buffer times.

## Procedure

1. **Triage:** sort new mail into *Needs you* (decisions, key people), *Drafted* (White wrote a reply for approval), *Handled* (newsletters archived, routine replies within authority), and *FYI*. Use `email-inbox-triage` mechanics.
2. **Reply drafts:** write in the founder's voice. Batch them for one-tap approval in the daily check-in. Send routine replies directly only where `authority.md` allows.
3. **Scheduling:** handle the back-and-forth, propose times per `calendar-rules.md`, and send invites after approval (or directly if allowed). Protect deep-work blocks, and push back on meeting creep in the weekly review.
4. **Before meetings:** 30 minutes before each external meeting, send a brief: who they are (live research), context from past emails, the goal, 3 talking points, and the ask.
5. **After meetings:** from the notes, extract decisions and action items (`meeting-action-items`). Draft the follow-up email for approval. Create outcome-engine cards for our commitments, and log customer feedback in `company.md`.

## Pitfalls

- Archiving something important. When unsure, it goes to *Needs you*.
- Over-sending. Anything outside `authority.md` waits for approval.
- Briefs that recap the obvious. Focus on the goal and the ask.

## Verification

- The daily check-in shows triage counts, drafts waiting, and meetings briefed.
- Every follow-up sent has an approval or a standing permission. Commitments became cards.
