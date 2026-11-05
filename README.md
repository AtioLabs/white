# White

**An open-source AI founder's office. Not a tool you prompt, but a colleague that owns part of your job.**

White decides what matters most each day, does most of it, and brings you only the decisions, approvals and proof: in your WhatsApp, in your voice, within the authority you grant. It runs on [Hermes Agent](https://github.com/NousResearch/hermes-agent) with any model you bring.

> Most agents wait for you to say what to do. But founders often don't know what to ask. That's the job. White brings the founder's-office expertise itself: it proposes, pushes back with evidence, and follows through.
> — from ["What humans can do"](https://www.asynarch.com/writing/what-humans-can-do)

## A colleague, not a tool

| A tool | White |
|---|---|
| Waits for a prompt | Runs its own loop every 2 hours and checks in every morning on WhatsApp |
| Does the task asked | Owns outcomes with targets ("5 paying design partners by Jan 31") |
| Executes | Says what matters and challenges you when your time and the data disagree |
| Forgets | Keeps a world model of your people, deals, promises and runway, every fact sourced |
| You check its work | A separate supervisor checks every draft before you see it |
| Can do anything it's told | Can't send anything in your name without approval. Enforced in code, not a prompt |
| Same forever | Learns from your edits and choices, and practices on a bench to get better |

## What it takes off your plate

| Skill | What White does |
|---|---|
| `founder-onboarding` | Learns your voice from your real writing, your company, and your authority rules. Audits your week and proposes what to take over. |
| `outcome-engine` / `white-cycle` | Turns a goal into tracked work and drives it every 2 hours without being prompted |
| `morning-checkin` / `weekly-review` | One short message a day that leads with what matters; a Monday 1:1 with misses reported honestly |
| `design-partner-hunt` | Finds companies showing the pain right now, warm paths first, through to a paid design-partner deal |
| `investor-outreach` / `seed-model` / `investor-update` | Investors with a real reason to care, a seed model that guides you with sourced benchmarks, monthly updates |
| `accelerator-apply` / `distribution` / `sf-intel` | Deadlines and applications, posts in your voice, a weekly "what SF shipped and what it means for you" |
| `inbox-calendar-meetings` | Triage, scheduling, meeting briefs and follow-ups |
| `white-identity` / `white-connect` / `white-network` | Its own inbox and number, your apps through Composio, and intros with other founders' Whites over A2A |

## How it's built

```
Hermes (the body): any model · tools · browser · own computer · WhatsApp/email · cron · kanban · A2A
White core (plugins, tested code):
  white-gate   authority gate on every tool call: block leaks, approval for anything outward
  white-core   world model · judgment engine · supervisor · learning · scorecard · specialists ·
               receipts · doctor · Composio/phone setup
White skills (the training): 16 founder's-office skills, plus vendored Composio
Bench: 10 scenarios. Core layer runs without a model; agent layer scores White vs plain Hermes
```

| Piece | What it does |
|---|---|
| **Authority gate** | A Hermes `pre_tool_call` hook. Messages, email, posts, form submits, payments, calls, SMS, A2A, and Composio actions (e.g. `GMAIL_SEND_EMAIL` inside a router call) need your approval unless you granted a standing permission. Never-share items are blocked outright. Fails closed. |
| **World model** | SQLite holding people, orgs, pipeline, commitments, signals, decisions, actions, lessons and runway. No source, no fact. "Done" needs proof. Readable as a nightly wiki. |
| **Judgment engine** | Scores open work in code (gap to target × deadline × pace × runway × neglect, plus people waiting on you and promises overdue) and raises challenges. The model reasons over the ranking instead of guessing. |
| **Supervisor** | Code checks (leaks, words you never use, AI tells, length, sources, proof, placeholders), then a separate model review. |
| **Learning** | Your edits become voice lessons. Accepted or rejected recommendations shift priorities within bounds. Weekly scorecard. |
| **Specialists** | Outreach, research, content, finance and ops workers via kanban, each with role rules. White orchestrates. |
| **Practice runs** | White proposes changes to its own skills and keeps one only if the bench score rises with no safety check lost (after Google Research's Harness²). |
| **Receipts** | `white receipts` writes a public, redacted log of what White did, with SHA-256 proof fingerprints anyone can verify once you reveal a proof. |

## Install (Windows)

Needs Git and Windows PowerShell. Clone both repos side by side:

```powershell
git clone https://github.com/NousResearch/hermes-agent
git clone https://github.com/<you>/white
powershell -ExecutionPolicy Bypass -File .\white\setup-white.ps1
```

The script installs the Hermes runtime if needed, installs or updates the White profile, enables its plugins, asks for a model if none is set, and runs `white doctor`. Then:

```powershell
.\hermes-agent\.hermes\bin\hermes.exe -p white chat
```

Say **"run founder-onboarding"**. White reads your public writing, drafts your voice and company profile for you to correct, proposes its charter and authority, audits your week, and sets up its own schedule.

macOS and Linux: Hermes supports both. Install Hermes with its own instructions, then run `hermes profile install ./white` and `hermes -p white plugins enable white-gate white-core`.

### Bring your own keys

All keys go in the White profile's `.env` (`%LOCALAPPDATA%\hermes\profiles\white\.env` on Windows). Never paste them into a chat.

| What | Key | Then |
|---|---|---|
| Model (any Hermes provider) | e.g. `GOOGLE_API_KEY`, `OPENROUTER_API_KEY` | `hermes -p white model` |
| Your apps (Gmail, Calendar, LinkedIn, Slack, …) | `COMPOSIO_API_KEY=ak_…` | `hermes -p white white composio-setup` |
| White's own inbox (optional) | `AGENTMAIL_API_KEY` | say "run white-identity" |
| White's own phone (optional, US/CA) | `AGENTPHONE_API_KEY` | `hermes -p white white phone-setup` |
| WhatsApp check-ins | none | `hermes -p white whatsapp`, then `hermes gateway install` |

Check everything with `hermes -p white white doctor`. Other commands: `white judge` (what matters today), `white wiki`, `white receipts`.

## Your data

Everything lives in your Hermes profile, never in this repo:

- `founder/voice.md`, `company.md`: who you are and how you write
- `founder/charter.yaml`: what White owns, with targets
- `founder/authority.yaml`: never-share list and standing permissions, enforced by the gate
- `founder/wiki/`: readable pages generated from the world model
- `white/world.db`, `white/gate-log.jsonl`, `white/weights.yaml`: state, the approval log, learned priorities

## Develop

```bash
python -m pip install pytest pyyaml
python -m pytest plugins bench -q            # unit tests
python bench/core_bench.py                   # core bench, no model needed
python bench/agent_bench.py --profile-dir <profile> --hermes <hermes>     # needs a model
python bench/practice.py --profile-dir <profile> --hermes <hermes> --skill morning-checkin
```

Design: [DESIGN.md](DESIGN.md) · Security: [SECURITY.md](SECURITY.md) · Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)

## Status

Early and honest. The core is built and tested (94 unit tests, core bench at 100%), and it runs end to end on the author's machine with WhatsApp check-ins. It hasn't yet proven itself across a real founder's weeks. Numbers will be published from the bench and from real use: receipts, not counters.

## License

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
