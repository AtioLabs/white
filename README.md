<div align="center">

# ◇ White

### The founder's office you can't afford to hire yet.

**White is an open-source AI colleague that owns part of a founder's job.** It decides what matters today, does most of it, and brings you only the decisions, the approvals and the proof, on WhatsApp, in your voice, inside limits you set.

[![License: MIT](https://img.shields.io/badge/license-MIT-black)](LICENSE)
[![Built on Hermes Agent](https://img.shields.io/badge/built%20on-Hermes%20Agent-gold)](https://github.com/NousResearch/hermes-agent)
[![Any model](https://img.shields.io/badge/model-bring%20your%20own-blue)](#bring-your-own-keys)
[Why](#why-white) · [A day with White](#a-day-with-white) · [What it does](#what-white-does) · [How it works](#how-it-works) · [Safety](#safe-by-construction) · [Install](#install) · [Status](#status)

</div>

---

## Why White

Founders in SF have a founder's office: someone who chases the follow-ups, builds the model, finds the design partners, preps the meetings and tells them what they're neglecting. Most founders everywhere else have a chat box and a to-do list.

Today's agents made that worse in a new way: **you have to know what to ask.** You end up as the prompter, the project manager and the reviewer of your own assistant.

White flips it. You hand it **outcomes**, not prompts ("5 paying design partners by January"), and it does the job the way a sharp chief of staff would:

- **It leads.** It opens every day with the one thing that matters and why, from the numbers.
- **It guides, it doesn't interrogate.** It proposes answers with sourced benchmarks and pushes back when your plan and the data disagree.
- **It follows through.** It runs its own loop every two hours and only interrupts you when you're needed.
- **It shows receipts.** Nothing counts as done without proof.

> *"You know what you want to achieve. That doesn't mean you know what to ask for."*
> — [What humans can do](https://www.asynarch.com/writing/what-humans-can-do), the essay White is built on

## A day with White

An illustration of the shape of a check-in, not a recorded transcript:

```text
◇ White — 08:30

Today's one thing: Ravi (Arka VC) asked for the model before Friday's partner
meeting. That's 2 days, and it's your warmest lead.
I've drafted the reply and updated the model's churn assumption (3%/mo, seed
B2B benchmark, source linked). Approve and I'll send it.

Challenge: design partners are 1/5 with 40 days left, and nothing moved this
week. I recommend 3 hours on Thursday for the 6 warm intros I've queued, or we
move the date. Which?

Approve: 1) reply to Ravi + model   2) intro request to Meera (Lumen)
Done:    LogiCo pilot signed (contract linked) · 14 prospects researched
Score:   design partners 1/5 (behind) · seed 0/1 (on track) · promises 0 overdue
```

You answer in one word. White does the rest, and logs every action with proof.

## What White does

| You hand White | What it does without being asked |
|---|---|
| **"Find design partners"** | Defines your ideal partner, finds companies showing the pain *right now* (hiring posts, complaints, tool switches), warm paths first, writes signal-specific outreach in your voice, preps your calls, drives each one to a paid decision |
| **"Get me ready for the seed"** | Builds a driver-based model with every assumption sourced, stress-tests it like an investor would, matches investors who have a real reason to care, writes personal emails, tracks the pipeline |
| **"Keep me on top of everything"** | Triages your inbox, books and protects your calendar, briefs you before meetings, sends follow-ups after, and never lets a promise go overdue |
| **"Help us get seen"** | Picks the 1–2 channels your buyers use and turns real progress and customer stories into posts that sound like you |
| **"Don't let SF leave us behind"** | A weekly brief: what shipped and what changed, with *so what for us* and one action |
| **Nothing at all** | Audits your week, shows what it can take off your plate ranked by hours saved, and asks which to start with |

16 founder's-office skills ship with White: onboarding, the work loop, daily check-ins, weekly reviews, design partners, investors, seed model, investor updates, accelerators, distribution, SF intel, inbox and calendar, identity, app connections, and the White network.

## How it works

White is a **worker runtime**, not a prompt pack. Skills are its training; the job is done by code with state, judgment and enforced authority.

```text
                         ┌─────────────── you (WhatsApp) ───────────────┐
                         │   decisions · approvals · daily check-in     │
                         └───────────────────────▲──────────────────────┘
┌─────────────────────────── WHITE CORE ─────────┴─────────────────────────────┐
│  Charter ──► World model ──► Event loop ──► Judgment ──► Specialists         │
│  (what it    (people, deals,  (every 2h +   (what matters  (outreach, research,│
│   owns)       promises, runway) on events)   most, and why)  content, finance, ops)│
│                                     ▲                         │              │
│        Learning ◄── Scorecard ◄── Supervisor ◄── Authority gate ◄─┘          │
│      (your edits      (misses,      (checks every    (nothing leaves without  │
│       teach it)       reported)      draft)           your OK, in code)       │
└──────────────────────────────────────▲───────────────────────────────────────┘
┌──────────────────────────── HERMES AGENT ┴───────────────────────────────────┐
│  any model · tools · browser · its own computer · WhatsApp · email · cron ·  │
│  kanban · A2A · Composio (Gmail, Calendar, LinkedIn, Slack, Notion, …)       │
└──────────────────────────────────────────────────────────────────────────────┘
```

| Layer | What it is | Why it matters |
|---|---|---|
| **World model** | SQLite: people, orgs, pipeline, commitments, signals, decisions, actions, lessons, runway. Every fact needs a source; "done" needs proof. | State lives outside the model, so White doesn't forget or invent |
| **Judgment engine** | Code scores open work: gap to target × deadline × pace × runway × neglect, plus people waiting on you and overdue promises. The model reasons over the ranking. | Consistent priorities you can audit, not vibes |
| **Supervisor** | Code checks (leaks, words you never use, AI tells, length, sources, proof), then a separate model review | You see work that's already been checked |
| **Learning** | Your edits become voice lessons, your accept/reject choices tune its priorities within bounds, and a weekly scorecard reports misses | It gets better at *your* job, the way a hire does |
| **Specialists** | Outreach, research, content, finance and ops workers on Hermes kanban, each with role rules | White orchestrates; work runs in parallel |
| **Practice runs** | White proposes edits to its own skills and keeps one only if the bench score rises with no safety check lost | Improves the harness, not the model (after Google Research's Harness²) |
| **Receipts** | `white receipts`: a public, redacted log with SHA-256 proof fingerprints | Build in public with proof anyone can verify |

## Safe by construction

White acts in your name, so its limits are **code, not prompts**:

- **The authority gate** sits in front of every tool call. Messages, email, posts, form submits, payments, calls, SMS, agent-to-agent messages, and Composio actions hidden inside router arguments (e.g. `GMAIL_SEND_EMAIL`) all need your approval, unless you granted a narrow standing permission. Anything on your never-share list is blocked outright. If the gate fails, it fails closed.
- **Unattended runs can't approve anything.** Scheduled cycles prepare drafts; you approve.
- **Keys never leave `.env`.** Config references them as `${NAME}`, and the setup commands refuse to write raw keys.
- **It always says it's an AI** when it emails or calls as itself.

Read [SECURITY.md](SECURITY.md) for the known limits.

## Install

**Windows** (macOS and Linux below). Clone White next to Hermes and run the setup:

```powershell
git clone https://github.com/NousResearch/hermes-agent
git clone https://github.com/<you>/white
powershell -ExecutionPolicy Bypass -File .\white\setup-white.ps1
```

It installs the Hermes runtime if needed, installs White as a Hermes profile, enables its plugins, asks for a model, and runs `white doctor`, which tells you exactly what's left to fix. Then:

```powershell
.\hermes-agent\.hermes\bin\hermes.exe -p white chat
```

Say **"run founder-onboarding"**. White reads your public writing, drafts your voice and company profile for you to correct, proposes its charter and authority, audits your week, and schedules itself.

**macOS / Linux:** install Hermes from its repo, then `hermes profile install ./white` and `hermes -p white plugins enable white-gate white-core`.

### Bring your own keys

Everything is optional except a model. Keys go in the White profile's `.env` (on Windows, `%LOCALAPPDATA%\hermes\profiles\white\.env`), never in a chat.

| For | Add to `.env` | Then run |
|---|---|---|
| **A model** (any Hermes provider) | e.g. `GOOGLE_API_KEY`, `OPENROUTER_API_KEY` | `hermes -p white model` |
| **Your apps** via Composio | `COMPOSIO_API_KEY=ak_…` | `hermes -p white white composio-setup` |
| **WhatsApp check-ins** | none | `hermes -p white whatsapp` → `hermes gateway install` |
| White's **own inbox** | `AGENTMAIL_API_KEY` | say "run white-identity" |
| White's **own phone** (US/CA) | `AGENTPHONE_API_KEY` | `hermes -p white white phone-setup` |

Useful anytime: `white doctor` (health), `white judge` (what matters today), `white wiki` (readable world model), `white receipts`.

## Your data stays yours

Nothing about you lives in this repo. Your voice, company, charter, authority rules, world model, approval log and learned priorities stay in your local Hermes profile. White calls only the model and the services you connect.

## Status

**Early, and honest about it.** The core is built and tested, and White runs end to end on the author's machine with WhatsApp check-ins and Composio. It hasn't yet proven itself across many founders' real weeks. That's the next milestone, and the numbers will be published as receipts, not counters.

**Next up:** agent-bench results against plain Hermes · the public White network directory · an official WhatsApp Business API path · macOS/Linux one-command setup.

## Contributing

One bar for every change: **does it make White more of a colleague, or more of a tool?** Read [CONTRIBUTING.md](CONTRIBUTING.md) and [DESIGN.md](DESIGN.md).

```bash
python -m pip install pytest pyyaml
python -m pytest plugins bench -q && python bench/core_bench.py
```

## License

[MIT](LICENSE). Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research. Third-party notices in [NOTICE](NOTICE).

<div align="center"><sub>Built by <a href="https://www.asynarch.com">Asrul Ishath</a>, a founder outside SF, for founders outside SF.</sub></div>
