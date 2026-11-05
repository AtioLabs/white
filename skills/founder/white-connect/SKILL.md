---
name: white-connect
description: Connect the founder's apps to White through Composio.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Integrations, Composio, Gmail, LinkedIn, White]
    category: founder
    related_skills: [composio, white-cycle, inbox-calendar-meetings, founder-onboarding]
---

# White Connect Skill

A founder's office needs access to where work happens: email, calendar, LinkedIn, Slack, Notion, Drive, CRM. Composio **For You** connects the founder's own accounts through one MCP server (1,000+ apps) and handles OAuth with connect links, so White never sees passwords. White's authority gate still decides what may go out: reads pass, and sends, posts, invites and remote code need approval.

## When to Use

- After onboarding, or when the week audit shows work in an app White can't reach.
- "Connect my Gmail", "can you see my calendar?", "use my LinkedIn".

## Prerequisites

Two ways in. Use whichever key the founder has.

**A. Platform project key (`ak_…`), the default for White.** The founder puts `COMPOSIO_API_KEY=ak_…` in this profile's `.env`, then runs `hermes -p white white composio-setup`. That creates a Composio session for the founder and writes the MCP server into `config.yaml`, referencing the key as `${COMPOSIO_API_KEY}` (the key itself is never written there; config.yaml is backed up first). Restart the chat. If the tools stop working (for example, the session expired), run the command again.

**B. For You consumer key.**

- A Composio **For You** consumer key (`ck_…`) from dashboard.composio.dev → For You → AI Clients. A Platform project key (`COMPOSIO_API_KEY`, often `ak_…`) is a different product and won't work here; if that's what the founder has, say so and point them to For You. Load the vendored `composio` skill for details.
- The founder puts the key in this profile's `.env` themselves: `COMPOSIO_CONSUMER_KEY=ck_…`. White never asks for it in chat, never prints it, and never writes it into `config.yaml`.
- `config.yaml` references it by name only:

```yaml
mcp_servers:
  composio:
    url: "https://connect.composio.dev/mcp"
    headers:
      x-consumer-api-key: "${COMPOSIO_CONSUMER_KEY}"
```

- The `white-gate` plugin enabled. It reads the action slugs inside `COMPOSIO_MULTI_EXECUTE_TOOL` (e.g. `GMAIL_SEND_EMAIL` needs approval, `GMAIL_FETCH_EMAILS` passes) and always asks before `COMPOSIO_REMOTE_WORKBENCH` / `REMOTE_BASH`.

## Procedure

1. **Recommend which apps, from evidence.** Use the week audit and `company.md` to propose the 3–5 apps that matter (typically Gmail, Google Calendar, LinkedIn, plus where the team works: Slack or WhatsApp, Notion or Drive). Don't connect everything.
2. **Verify the server.** Run `hermes -p white white doctor` (it checks the Composio entry and that no raw key is in `config.yaml`). Confirm the Composio tools appear (`COMPOSIO_SEARCH_TOOLS` and the others).
3. **Connect each app** when a task first needs it: `COMPOSIO_MANAGE_CONNECTIONS` returns a connect link. Send the founder the link, then `COMPOSIO_WAIT_FOR_CONNECTIONS`. Links expire, so request a new one rather than reusing an old one.
4. **Prove each connection with one safe read,** e.g. `GMAIL_FETCH_EMAILS` (5 newest) or `GOOGLECALENDAR_LIST_EVENTS` (today). Record the connection in `company.md` under "Connected apps", and log it with `white_log` (action, done, proof = the Composio log id).
5. **Discover; never invent.** Find tool slugs with `COMPOSIO_SEARCH_TOOLS` and get schemas with `COMPOSIO_GET_TOOL_SCHEMAS` before executing. Never guess a slug.
6. **Feed the loop.** `white-cycle` step 1 now reads new mail, calendar changes and messages through these tools, and records signals with stable sources (`gmail:<id>`, `gcal:<id>`, `slack:<ts>`).
7. **Outward actions** (sending, posting, inviting, commenting) go through the gate. Prepare the draft, then queue it for approval. Drafts inside the founder's own account (e.g. `GMAIL_CREATE_EMAIL_DRAFT`) are allowed and are a good way to hand off ready-to-send emails.

## Pitfalls

- **Wrong key type.** `ck_` (For You) versus Platform keys. Check the prefix the founder reports; never ask for the key itself.
- **Key in config.yaml.** Always `${COMPOSIO_CONSUMER_KEY}`. The doctor flags raw keys.
- **Connecting everything up front.** It widens what can go wrong. Connect per task.
- **Remote workbench as a shortcut.** It runs code with the founder's accounts, so it always needs approval. Prefer specific tool slugs.

## Verification

- `white doctor` shows Composio configured with no raw key.
- Each connected app has one logged safe read with a Composio log id.
- `white/gate-log.jsonl` shows approvals (not silent passes) for the first send or post through Composio.
