---
name: white-identity
description: Give White its own email inbox and phone number.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Identity, Email, Phone, White]
    category: founder
    related_skills: [agentmail, white-cycle, inbox-calendar-meetings]
---

# White Identity Skill

A real hire has their own email and phone, so people can deal with them directly: scheduling, follow-ups, chasing replies, confirming meetings. This skill gives White an inbox (AgentMail) and a number (AgentPhone). White always says it's an AI working for the founder. It never pretends to be the founder or a human.

## When to Use

- After onboarding, when the founder wants White to handle scheduling or follow-ups under its own name.
- "Give White an email", "can White call them?", "set up White's number".

## Prerequisites

- **Email (AgentMail):** the free tier has 3 inboxes and 3,000 emails/month on an `@agentmail.to` address; custom domains need a paid plan (check agentmail.to/pricing). Install Hermes's optional skill with `hermes skills install official/email/agentmail`. The founder creates the API key at console.agentmail.to and puts `AGENTMAIL_API_KEY` in this profile's `.env` themselves. Never ask for the key in chat.
- **Phone (AgentPhone):** US and Canadian numbers only for now. Outbound calls need billing set up, and outbound SMS needs SMS registration (docs.agentphone.ai). The founder puts `AGENTPHONE_API_KEY` in `.env` and adds to `config.yaml`:

```yaml
mcp_servers:
  agentphone:
    command: npx
    args: ["-y", "agentphone-mcp"]
    env:
      AGENTPHONE_API_KEY: ${AGENTPHONE_API_KEY}
```

- Node.js 18+ for both. The `white-gate` plugin enabled: it treats sends, replies, calls, SMS and number purchases through these tools as outward actions that need approval.

## Procedure

1. **Recommend first.** Propose what White's identity is for, from the week audit (e.g. "scheduling and follow-ups with design-partner prospects"). Propose the display name: **"White, AI founder's office for <Founder> at <Company>"**. Get one confirmation.
2. **Email:** after the founder adds the key, create one inbox with `agentmail inboxes create` (`--format json`). Plain `white@agentmail.to` is taken, so use **`white-<company>`** (e.g. `white-asynarch@agentmail.to`); if that's taken too, try `white.<company>` or `<company>-white`. Long term, recommend a custom domain (`white@<company domain>`, which needs a paid AgentMail plan) because it looks trustworthy to investors and customers. Record the address in `company.md` under "White's identity", and run `white_record` kind=org/person as needed.
3. **Phone (optional):** confirm `account_overview` is visible in the agentphone tools before any paid action. Buying a number costs money, so it goes through approval (the gate enforces this). Record the number in `company.md`.
4. **Signature and disclosure,** in every message and at the start of every call: "This is White, an AI assistant working with <Founder> at <Company>." Add it to `voice.md` under a "White's own voice" section: short, polite, specific, never claiming to be human.
5. **Wire into the loop:** `white-cycle` step 1 also reads White's own inbox (`agentmail` threads) and AgentPhone messages and transcripts. Every reply becomes a signal with source `agentmail:<message-id>` or `agentphone:<call-or-message-id>`.
6. **Authority:** propose standing permissions narrow enough to be safe (e.g. "White may reply from its own inbox to confirm times for meetings the founder already accepted"), and write them to `authority.yaml` only after the founder agrees. Everything else stays approval-only.
7. **Prove it:** send one test email from White's inbox to the founder (approved through the gate), and log it with `white_log` (action, done, proof = the message id).

## Pitfalls

- **Pretending to be human or the founder.** Always disclose. It's both the right thing and what keeps the founder's reputation safe.
- **Keys in chat.** The founder edits `.env` directly; White never sees or repeats keys.
- **Assuming an Indian number.** AgentPhone is US/CA only today. For India, use email plus the founder's WhatsApp through Hermes's gateway.
- **Broad standing permissions.** Keep them narrow and written down in `authority.yaml`.

## Verification

- `company.md` lists White's address (and number, if set up) under "White's identity".
- A test email from White's inbox has a message id logged as proof.
- `white/gate-log.jsonl` shows approvals for the first sends and calls.
