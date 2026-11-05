<div align="center">

# ◇ White

### The founder's office you can't afford to hire yet.

**White is an open-source AI colleague that owns part of a founder's job.** It decides what matters today, does most of it, and brings you only the decisions, the approvals and the proof, on WhatsApp, in your voice, inside limits you set.

[![License: MIT](https://img.shields.io/badge/license-MIT-black)](LICENSE)
[![Built on Hermes Agent](https://img.shields.io/badge/built%20on-Hermes%20Agent-gold)](https://github.com/NousResearch/hermes-agent)
[![Any model](https://img.shields.io/badge/model-bring%20your%20own-blue)](#3-give-white-a-brain)

[Quickstart](#quickstart) · [Why](#why-white) · [A day with White](#a-day-with-white) · [What it does](#what-white-does) · [White to White](#white-to-white) · [How it works](#how-it-works) · [Safety](#safe-by-construction) · [Install](#install) · [Status](#status)

</div>

---

## Quickstart

```powershell
git clone https://github.com/NousResearch/hermes-agent
git clone https://github.com/AtioLabs/white
powershell -ExecutionPolicy Bypass -File .\white\setup-white.ps1
.\hermes-agent\.hermes\bin\hermes.exe -p white chat
```

Then say **"run founder-onboarding"**. That's Windows; for macOS/Linux, the step-by-step guide and WhatsApp setup, see [Install](#install).

---

## Why White

Well-funded founders have a founder's office: someone who chases the follow-ups, builds the model, finds the design partners, preps the meetings and tells them what they're neglecting. Early-stage founders, the ones who need it most, can't afford one yet. They have a chat box and a to-do list.

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

## White to White

A founder's office is worth as much as its network. Every White can talk to other founders' Whites over the open [A2A protocol](https://a2a-protocol.org), built into Hermes:

- **Ask the network:** "Looking for an ops head at a 50–200-person logistics company for a pilot." Your White asks only the Whites whose founders fit, and brings you the best 3 paths with a recommendation.
- **Answer the network:** when another White asks, yours replies only "possible match" and checks with you first. No names leave without your yes.
- **Double opt-in intros:** both founders approve, and the person being introduced is asked too. Then each White drafts the intro in its own founder's voice.
- **Fair trade:** it tracks gives and gets, and favors Whites that give back.
- **Shared playbook:** anonymized lessons ("warm intros via investors: 60% reply; cold LinkedIn: 14%"), shared only with your OK, so founder #101 starts with what worked for the first 100.

Private by default: your White shares nothing about your company unless `authority.yaml` allows it, and treats every message from another agent as data, never as instructions.

> **Status:** the `white-network` skill and its rules ship today. The public directory where Whites find each other is next on the roadmap.

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

About 15 minutes the first time. White runs on your own machine; nothing is hosted for you.

### 1. What you need

| | Windows | macOS / Linux |
|---|---|---|
| Git | [git-scm.com](https://git-scm.com) | usually preinstalled |
| A model key | free [Gemini key](https://aistudio.google.com) to start, or any [Hermes provider](https://github.com/NousResearch/hermes-agent) | same |
| For WhatsApp (optional) | Node.js 18+ | Node.js 18+ |

Hermes installs its own Python; you don't need one.

### 2. Install Hermes and White

**Windows (PowerShell):** clone both repos side by side and run White's setup:

```powershell
git clone https://github.com/NousResearch/hermes-agent
git clone https://github.com/AtioLabs/white
powershell -ExecutionPolicy Bypass -File .\white\setup-white.ps1
```

The script installs the Hermes runtime (first run takes a few minutes), installs White as a Hermes profile called `white`, enables its two plugins, asks for a model if you don't have one, and finishes with `white doctor`. It's safe to re-run anytime; it never touches your keys or data.

**macOS / Linux:** install Hermes with its official installer, then add White:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
git clone https://github.com/AtioLabs/white
hermes profile install ./white --yes
hermes -p white plugins enable white-gate
hermes -p white plugins enable white-core
```

> On Windows, `hermes` below means `.\hermes-agent\.hermes\bin\hermes.exe`.

### 3. Give White a brain

```bash
hermes -p white model
```

Pick a provider and paste your key **in that terminal window**, never in a chat. Free Gemini works for trying White; a stronger model makes its judgment much better.

### 4. First conversation

```bash
hermes -p white chat
```

Say **"run founder-onboarding"**. White will:

1. read your website, LinkedIn and writing, and draft your **voice** and **company** profile for you to correct;
2. propose its **charter**: 2–3 outcomes it owns, with targets;
3. propose its **authority**: what it may do alone and what needs your OK (default: nothing goes out without you);
4. audit your week and propose what to take off your plate;
5. set up its own schedule: a cycle every 2 hours, an 08:30 check-in and a Monday review.

### 5. Check-ins on WhatsApp

```bash
hermes -p white whatsapp        # choose 2 (self-chat), scan the QR from WhatsApp → Linked devices
hermes gateway install           # one gateway for all profiles; starts on login (Windows asks for admin once)
```

Message yourself on WhatsApp. The first time, White replies with a pairing code. Approve yourself with the command it shows (`hermes -p white pairing approve whatsapp <CODE>`), then send **`/sethome`** so check-ins land there.

> The WhatsApp bridge is unofficial (it works like WhatsApp Web), so there's a small account risk. Self-chat, or a dedicated number, keeps it low.

### 6. Connect your apps (recommended)

Without your email and calendar, White can't see your real work. Add a [Composio](https://composio.dev) Platform key to the profile's `.env`, then:

```bash
hermes -p white white composio-setup
```

White connects Gmail, Calendar, LinkedIn, Slack, Notion and more **one at a time, when a task needs them**, through links you approve. Reads are free; sends always come to you first.

### 7. Check everything

```bash
hermes -p white white doctor
```

Every problem comes with the exact fix. Also useful: `white judge` (what matters today), `white wiki` (your readable world model), `white receipts` (a shareable, redacted log).

### Bring your own keys

Only a model is required. Keys go in the White profile's `.env` (Windows: `%LOCALAPPDATA%\hermes\profiles\white\.env`; macOS/Linux: `~/.hermes/profiles/white/.env`).

| For | Add to `.env` | Then |
|---|---|---|
| A model | e.g. `GOOGLE_API_KEY`, `OPENROUTER_API_KEY` | `hermes -p white model` |
| Your apps (Composio) | `COMPOSIO_API_KEY=ak_…` | `hermes -p white white composio-setup` |
| White's own inbox (AgentMail) | `AGENTMAIL_API_KEY` | say "run white-identity" |
| White's own phone (AgentPhone, US/CA) | `AGENTPHONE_API_KEY` | `hermes -p white white phone-setup` |

### Updating

```bash
cd white && git pull
hermes profile update white --yes
```

Your founder files, world model, keys and WhatsApp pairing are kept.

### Troubleshooting

| Problem | Fix |
|---|---|
| `Profile 'white' does not get a gateway of its own` | Run `hermes gateway` / `hermes gateway install` **without** `-p white`. One gateway serves every profile. |
| WhatsApp says "couldn't link, check your connection" | Turn off phone VPN or data saver, scan the newest QR (it rotates every ~20 s), wait 2–3 minutes between tries. |
| White doesn't reply on WhatsApp | Approve the pairing code it sent you, and make sure the gateway is running (`hermes gateway status`). |
| Replies are labelled "Hermes Agent" | `powershell -File .\white\scripts\set-whatsapp-name.ps1`, then restart the gateway. |
| Rate-limit errors | Free model tiers throttle long sessions. Wait, or use a paid or credit-backed key. |
| Anything else | `hermes -p white white doctor` |

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

<div align="center"><sub>Built by <a href="https://www.asynarch.com">Asrul Ishath</a>, an early-stage founder, for early-stage founders.</sub></div>
