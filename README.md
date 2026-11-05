<div align="center">

# White

### The founder's office you can't afford to hire yet.

<img src="docs/faces.png" alt="Eight 1-bit pixel portraits: every founder's White gets its own face" width="100%">


**White is an open-source AI colleague that owns part of a founder's job.** It decides what matters today, does most of it, and brings you only the decisions, the approvals and the proof, on WhatsApp, in your voice, inside limits you set.

[![License: MIT](https://img.shields.io/badge/license-MIT-black)](LICENSE)
[![Built on Hermes Agent](https://img.shields.io/badge/built%20on-Hermes%20Agent-gold)](https://github.com/NousResearch/hermes-agent)
[![Any model](https://img.shields.io/badge/model-bring%20your%20own-blue)](#bring-your-own-keys)

[Quickstart](#quickstart) · [Why](#why-white) · [A day with White](#a-day-with-white) · [Faces](#every-white-has-its-own-face) · [What it does](#what-white-does) · [White to White](#white-to-white) · [How it works](#how-it-works) · [Safety](#safe-by-construction) · [Install](#install) · [Status](#status)

</div>

---

## Quickstart

**Windows:** open PowerShell and paste:

```powershell
irm https://raw.githubusercontent.com/AtioLabs/white/main/install.ps1 | iex
```

**macOS / Linux:** open Terminal and paste:

```bash
curl -fsSL https://raw.githubusercontent.com/AtioLabs/white/main/install.sh | bash
```

The Hermes app opens. Pick **white** in the sidebar and say **hi**. White sets up the rest with you, in plain words.

---

## Why White

Well-funded founders have a founder's office: someone who chases the follow-ups, builds the model, finds the design partners, preps the meetings and tells them what they're neglecting. Early-stage founders, the ones who need it most, can't afford one yet. They have a chat box and a to-do list.

Today's agents made that worse in a new way: **you have to know what to ask.** You end up as the prompter, the project manager and the reviewer of your own assistant.

White flips it. You hand it **outcomes**, not prompts ("5 paying design partners by January"), and it does the job the way a sharp chief of staff would:

- **It leads.** It opens every day with the one thing that matters and why, from the numbers.
- **It guides, it doesn't interrogate.** It proposes answers with sourced benchmarks and pushes back when your plan and the data disagree.
- **It follows through.** It runs its own loop every two hours and only interrupts you when you're needed.
- **It shows receipts.** Nothing counts as done without proof.
- **It takes context, not prompts.** Drop anything in the `White Inbox` folder on your Desktop (or a Drive folder, from your phone). White works out what it means and what you're trying to do. Safe work it just does; risky work it prepares and asks you once.
- **It brings the expertise.** It learns your tools from their live docs, finds and vets skills on GitHub (1,000+ stars, code inspected), drives desktop apps through [agent-desktop](https://github.com/vercel-labs/agent-desktop), and tells you weekly what you and the company are missing.

> *"You know what you want to achieve. That doesn't mean you know what to ask for."*
> — [What humans can do](https://www.asynarch.com/writing/what-humans-can-do), the essay White is built on

## A day with White

An illustration of the shape of a check-in, not a recorded transcript:

```text
White — 08:30

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

## Every White has its own face

Your White isn't a logo. It gets a face: a 1-bit pixel portrait in the spirit of classic Mac bitmaps, shown as its avatar in the Hermes app.

- **Pick one:** White shows you 12 faces; choose the one that feels like your colleague.
- **Tweak it:** "add round glasses", "make it a hoodie". One trait changes and the rest stays.
- **Or use yourself:** turn your own photo into a pixel portrait. It's processed **on your machine**, never uploaded, and the photo isn't copied.

Nine traits (face shape, hair, eyes, brows, glasses, nose, mouth, beard, clothes) and endless seeds, so no two Whites need to look alike. Ask White in chat, or run `hermes -p white white face --choices`.

## What White does

| You hand White | What it does without being asked |
|---|---|
| **"Find design partners"** | Defines your ideal partner, finds companies showing the pain *right now* (hiring posts, complaints, tool switches), warm paths first, writes signal-specific outreach in your voice, preps your calls, drives each one to a paid decision |
| **"Get me ready for the seed"** | Builds a driver-based model with every assumption sourced, stress-tests it like an investor would, matches investors who have a real reason to care, writes personal emails, tracks the pipeline |
| **"Keep me on top of everything"** | Triages your inbox, books and protects your calendar, briefs you before meetings, sends follow-ups after, and never lets a promise go overdue |
| **"Help us get seen"** | Picks the 1–2 channels your buyers use and turns real progress and customer stories into posts that sound like you |
| **"Don't let SF leave us behind"** | A weekly brief: what shipped and what changed, with *so what for us* and one action |

19 founder's-office skills ship with White: setup, onboarding, the work loop, daily check-ins, weekly reviews, outcomes, design partners, investors, seed model, investor updates, accelerators, distribution, SF intel, inbox and calendar, identity, app connections, the White network, computer use, and capabilities.

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
| **Practice runs** | Real failures become tests; White rewrites a skill and keeps it only if the bench score rises with no safety check lost (with undo) | Improves the harness, not the model (after Google Research's Harness²) |
| **Receipts** | `white receipts`: a public, redacted log with SHA-256 proof fingerprints | Build in public with proof anyone can verify |

## Safe by construction

White acts in your name, so its limits are **code, not prompts**:

- **The authority gate** sits in front of every tool call. Messages, email, posts, form submits, payments, calls, SMS, agent-to-agent messages, and Composio actions hidden inside router arguments (e.g. `GMAIL_SEND_EMAIL`) all need your approval, unless you granted a narrow standing permission. Anything on your never-share list is blocked outright. If the gate fails, it fails closed.
- **Unattended runs can't approve anything.** Scheduled cycles prepare drafts; you approve. If Hermes is in auto-approve mode (one-shot runs, `/yolo`, approvals off), the gate turns every "ask the founder" into a block.
- **White can't rewrite itself.** Changes to its own code, `authority.yaml`, `config.yaml`, `SOUL.md` or `.env` need your OK, and skill edits only happen through the bench-tested practice loop.
- **Spend limits.** Each run stops at 60 model calls or 15 minutes, so a stuck loop can't drain your credit.
- **Keys never leave `.env`.** Never paste them into a chat. Config references them as `${NAME}`, and the setup commands refuse to write raw keys.
- **It always says it's an AI** when it emails or calls as itself.

Read [SECURITY.md](SECURITY.md) for the known limits.

## Install

### The easy way (about 10 minutes, no coding)

1. **Paste one line.** Windows: open **PowerShell** and paste the Windows line from [Quickstart](#quickstart). Mac/Linux: open **Terminal** and paste the other one.
2. **Wait while it installs.** It installs Hermes and its desktop app (first time only), then White, then switches on White's safety gate.
3. **Pick a model.** Log in with a plan you already pay for, or paste an API key into that window (see [Use the AI you already pay for](#use-the-ai-you-already-pay-for)).
4. **Say hi** (see [Quickstart](#quickstart)).

From there **White sets itself up with you**, one step at a time:

| White asks you to… | Why | How hard |
|---|---|---|
| Tell it about you and your company | So it writes like you and knows what matters | A short chat; it reads your website first |
| Agree on what it owns ("5 design partners by Jan") | So it can prioritize without you | Say yes or adjust |
| Connect Gmail and Calendar | So it sees your real week | Click a link and approve |
| Turn on WhatsApp | So check-ins reach your phone | Scan a QR in the app, tap approve |

Run the same line again anytime to update White. Your data, keys and WhatsApp stay as they are.

### Use the AI you already pay for

White runs on any model Hermes supports, including **the subscription you already have**. Pick it in the model step, or later in the Hermes app's settings.

| You have | How White uses it |
|---|---|
| **ChatGPT / Codex** plan | Log in with ChatGPT, no API key |
| **SuperGrok / X Premium+** | Log in with xAI, no API key (some tiers are blocked by xAI) |
| **GitHub Copilot, Qwen, MiniMax, Nous Portal** | Log in, no API key |
| **Claude Max** | Log in. Uses your purchased *extra usage* credits, not the base plan |
| Claude Pro, Gemini, or anything else | An API key: Anthropic, Google, OpenRouter, Sarvam or any OpenAI-compatible provider, or a local model via Ollama |

Add a backup provider (`hermes -p white fallback add`) so White switches automatically when one hits its limit.

### Bring your own keys

All optional. Add them in the Hermes app's settings for the **white** profile (or its `.env` file).

| For | Key | Get it at |
|---|---|---|
| Your apps (Gmail, Calendar, LinkedIn, Slack, …) | `COMPOSIO_API_KEY` (`ak_…`) | [composio.dev](https://composio.dev) |
| White's own inbox (optional) | `AGENTMAIL_API_KEY` | [agentmail.to](https://agentmail.to) |
| White's own phone (optional, US/CA) | `AGENTPHONE_API_KEY` | [agentphone.ai](https://agentphone.ai) |

### Troubleshooting

| Problem | Fix |
|---|---|
| The app didn't open | Run `hermes desktop` in a new PowerShell/Terminal window |
| `hermes` isn't recognized right after installing | Close and reopen PowerShell/Terminal, then paste the line again |
| WhatsApp says "couldn't link, check your connection" | Turn off phone VPN or data saver, scan the newest QR (it changes every ~20 s), wait 2–3 minutes between tries |
| White doesn't reply on WhatsApp | Approve the pairing request in the app's **Messaging** page |
| Rate-limit errors | Free tiers are too small for a worker that runs all day. Use a paid or credit-backed key, or add a backup provider |
| Anything else | Ask White "what's not set up?", or run `hermes -p white white doctor` |

<details>
<summary><b>For developers: manual install, scripts and CLI</b></summary>

```powershell
git clone https://github.com/NousResearch/hermes-agent
git clone https://github.com/AtioLabs/white
powershell -ExecutionPolicy Bypass -File .\white\setup-white.ps1   # Windows
```

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash   # macOS/Linux
git clone https://github.com/AtioLabs/white && hermes profile install ./white --yes
hermes -p white plugins enable white-gate && hermes -p white plugins enable white-core
```

Useful commands: `hermes -p white chat` · `hermes -p white model` · `hermes -p white white doctor | judge | wiki | receipts | face` · `hermes -p white white composio-setup` · `hermes -p white white phone-setup` · `hermes -p white whatsapp` · `hermes gateway install` (one gateway serves every profile; run it without `-p`).

Updating from a clone: `git pull && hermes profile update white --yes`.

</details>

## Your data stays yours

Nothing about you lives in this repo. Your voice, company, charter, authority rules, world model, approval log and learned priorities stay in your local Hermes profile. White calls only the model and the services you connect.

## Status

**Early, and honest about it.** The core is built and tested, and White runs end to end on the author's machine with WhatsApp check-ins and Composio. It hasn't yet proven itself across many founders' real weeks. That's the next milestone, and the numbers will be published as receipts, not counters.

**Next up:** agent-bench results against plain Hermes · the public White network directory · an official WhatsApp Business API path.

## Contributing

One bar for every change: **does it make White more of a colleague, or more of a tool?** Read [CONTRIBUTING.md](CONTRIBUTING.md) and [DESIGN.md](DESIGN.md).

```bash
python -m pip install pytest pyyaml pillow
python -m pytest plugins bench -q && python bench/core_bench.py
```

## License

[MIT](LICENSE). Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research. Third-party notices in [NOTICE](NOTICE).

<div align="center"><sub>Built by <a href="https://www.asynarch.com">Asrul Ishath</a>, an early-stage founder, for early-stage founders.</sub></div>
