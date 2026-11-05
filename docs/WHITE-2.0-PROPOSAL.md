# White 2.0: proposal (draft for the founder, 2026-11-05)

Nothing built yet. React to the tables; I'll change before coding.

## The idea in one line
White stops waiting for you. You drop things in a folder, it watches what you do, and it uses your tools better than you do, getting better every week.

## Your 8 points → design

| # | Your point | Design | Built from |
|---|---|---|---|
| 1 | Context grows with you | **`White Inbox/` folder** (desktop + phone share). Every file: read → extract facts with sources into the world model → file it in `founder/wiki/` → create the work it implies ("pitch deck v3 → update seed model, tell 2 investors"). Memory gets **time-aware facts** (true from/to) so old facts expire, not pile up. Nightly "dream" pass merges and prunes. | Zep/Graphiti temporal graph; Letta tiered memory; OpenClaw's stale-memory warning |
| 2 | Little or no prompting | **Intent engine**: inbox + email + calendar + WhatsApp signals → "what is the founder trying to do this week?" → ranked guesses, each with evidence. Acts on high-confidence low-risk ones, asks one question on the rest. Must also learn to **do nothing** when there's noise. | PIRA-Bench, ProAgentBench, PASK (IntentFlow) |
| 3 | Expertise beyond the owner | **Capability scan**: on setup and weekly, list what you own (Composio apps, installed CLIs, Hermes skills, subscriptions) → match to your goals → "you pay for X and never use Y; I'll run it." **Expertise packs**: per tool, an expert playbook (skill) loaded only when needed. | Agent Skills progressive disclosure; Skills-over-MCP (SEP-2640); tool-search meta-tool pattern |
| 3a | **Tool mastery: 100% output from any tool** (Ploy is one example of thousands) | For any tool the founder has or White finds, White builds a **mastery pack** by itself: (1) **learn**: official docs, API/CLI, changelog, expert tutorials and community playbooks; (2) **map**: every feature → which founder goal it serves; (3) **drive**: API first, then CLI, then agent-desktop on the UI; (4) **score**: how much of the tool's value White uses (features used ÷ features that fit the goals) and the outcome it produced; (5) **improve**: after each run, write what worked back into the pack. Weekly: "you use 20% of Ploy; here are 3 features I'll run for you." Packs are shareable between Whites. | Agent Skills; Voyager-style skill library; self-improvement loop |
| 3b | Finds and installs skills itself | **Skill scout**: when a task needs a skill White lacks, it searches the skill registries and GitHub → keeps only repos with **≥1k stars** → **inspects** the code (white-gate scan: network calls, secrets, shell, install scripts) → tests it in a sandbox → installs → triggers it by task. It logs a receipt; no founder prompt needed. Anything that fails inspection is blocked. | Skills over MCP; skills.sh registry; white-gate |
| 4 | Efficient computer use | **[agent-desktop](https://github.com/vercel-labs/agent-desktop)** (Vercel Labs, Rust CLI, v1.0.2, Apache-2.0): reads and drives any desktop app through the OS accessibility tree (Windows UI Automation, macOS, Linux), with refs like `@s…:e8` and JSON output. Fewer tokens than screenshots and more reliable. Screenshots only for apps that expose a poor accessibility tree. | Vercel agent-desktop |
| 5 | State of the art | Each module above cites a 2026 paper/system; bench grows with each (inbox, intent, "do nothing"). | Sources below |
| 6 | Positioning | "Agents 2.0: the agent that doesn't need prompts." Table below says why. | — |
| 7 | Growth partner | **Gap report** (weekly): what you and the company lack vs. your charter, with the fix. **Model advisor**: knows current open-weight models, what runs on your hardware, cost; switches White's own routing. **Self-improvement**: White reads its own failed runs, proposes harness/skill edits, keeps them only if the bench passes. | Meta-Harness, Self-Harness, Darwin Gödel Machine; BenchLM / Artificial Analysis boards |
| 8 | No drift | These 8 stay the spec header in `DESIGN.md`; every PR says which point it serves. | — |

## What's new vs. others

| | Hermes | OpenClaw | Town | **White 2.0** |
|---|---|---|---|---|
| Needs prompts | Yes | Heartbeat helps | Briefing, then chat | **No: inbox + intent engine** |
| Memory | Files/skills | MEMORY.md + logs (goes stale) | Wiki, nightly | **Sourced, time-aware world model + wiki** |
| Knows your unused tools | No | No | No | **Capability scan + expert packs** |
| Judgment / pushback | No | No | Light | **Yes (existing judgment engine)** |
| Improves itself safely | Skills | Community skills | — | **Bench-gated harness edits** |
| Model advice | Routing | — | — | **Open-weight advisor for you and itself** |

## Build order (after you approve)
1. Inbox folder + filing (smallest, most visible)
2. Intent engine + "do nothing" bench
3. agent-desktop as default computer use
4. Capability scan + skill scout (≥1k stars, inspect, sandbox test, self-install)
5. Gap report + model advisor
6. Bench-gated self-improvement

## Questions for you
All answered:
1. Ploy is an example; the goal is 100% output from any tool (row 3a).
2. Inbox: **both**, a local folder and Google Drive (phone drops), synced into one queue.
3. Autonomy: **no risk → full speed, no asking. Risky → stop and ask for a decision.** White-gate classifies the risk on every action (outward, money, irreversible, reputation, never-share = risky).

## Also planned (beyond the brief)
- Mastery packs are shared between Whites.
- White suggests better tools for a goal, not just ones you own.
- White watches tool changelogs and adopts new features.

## Sources (live, 2026-11-05; mostly secondary, primary papers to verify before build)
- Memory: [Atlan comparison](https://atlan.com/know/best-ai-agent-memory-frameworks-2026/), [mcp.directory Mem0/Letta/Zep/Cognee](https://mcp.directory/blog/mem0-vs-letta-vs-zep-vs-cognee-2026), [Vectorize on Zep](https://vectorize.io/articles/zep-alternatives)
- Proactive/intent: [PIRA-Bench](https://arxiv.org/html/2603.08013v1), [ProAgentBench](https://arxiv.org/html/2602.04482v1), [PASK](https://www.emergentmind.com/papers/2604.08000), [Google: Proactive AI](https://research.google/pubs/proactive-ai-for-superintelligent-agents/)
- Skills/tool discovery: [AAIF: Skills over MCP](https://aaif.io/blog/skills-over-mcp), [MCP skills extension](https://azukiazusa.dev/en/blog/mcp-skills-extension), [meta-tool pattern](https://dev.to/amitrix/the-meta-tool-pattern-teaching-your-agent-to-discover-its-own-tools-2a54)
- Computer use: [agent-desktop wiki](https://github.com/vercel-labs/agent-desktop/wiki), [Flavio Copes deep dive](https://flaviocopes.com/agent-desktop), [aicybr setup & security](https://aicybr.com/blog/vercel-agent-desktop-accessibility-tree-ai-agent-cli-setup-security)
- Self-improvement: [Recursive Harness Self-Improvement](https://arxiv.org/pdf/2607.15524), [Hierarchical Self-Improvement](https://arxiv.org/pdf/2608.08466), [SIA](https://arxiv.org/pdf/2605.27276), [Lilian Weng summary](https://www.beri.net/learning/lilian-weng-harness-engineering-self-improvement), [Awesome Self-Improving Agents](https://github.com/FrontisAI/Awesome-Self-Improving-Agents)
- Open-weight models: [BenchLM open-source](https://benchlm.ai/best/open-source), [Artificial Analysis gap](https://pasqualepillitteri.it/en/news/14684/open-source-closes-gap-artificial-analysis)
- OpenClaw: [production guide](https://blog.canadianwebhosting.com/openclaw-production-guide-ops-team)
- Ploy: [briefglance](https://briefglance.com/articles/ploy-debuts-with-27m-to-turn-your-website-into-an-ai-employee)
