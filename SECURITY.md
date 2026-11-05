# Security

White acts in a founder's name, so safety is part of the product, not an add-on.

## What protects you

- **Authority gate** (`plugins/white-gate`): a Hermes `pre_tool_call` hook on every tool call. Outward actions need your approval unless `founder/authority.yaml` grants a standing permission, and anything on your never-share list is blocked. Outward actions include messages, email (CLI, MCP, AgentMail), posts, form submits and clicks on Send/Submit/Pay, calls, SMS, number purchases, A2A messages, and Composio actions named inside tool arguments (e.g. `GMAIL_SEND_EMAIL`). Remote-code tools always ask. If the gate errors, it fails closed.
- **Unattended runs can't approve.** With no human present, Hermes blocks anything the gate flags for approval. Keep `approvals.cron_mode: deny` (`white doctor` checks it).
- **Keys stay in `.env`.** Config references keys as `${NAME}`. `white composio-setup` and `white phone-setup` refuse to write raw keys, and `white doctor` flags any raw key it finds.
- **Supervisor:** drafts are checked for never-share leaks before you see them.
- **Receipts are redacted:** names are pseudonymized, never-share items, emails and phone numbers are removed, and proofs are published only as SHA-256 fingerprints.

## Known limits

- The gate's shell and screen checks use patterns. A cleverly disguised command could slip past, which is why the supervisor and your approvals are separate layers. Prefer specific tools over raw shell.
- Read-only routing is decided by tool-name and slug words. Unknown tools default to asking.
- Community skills: read every `SKILL.md`, and scan with [NVIDIA SkillSpector](https://github.com/NVIDIA/SkillSpector), before installing.
- WhatsApp through the Baileys bridge is unofficial and carries account risk. Use self-chat or a dedicated number. The official Cloud API is the production path.

## Reporting a vulnerability

Please open a private security advisory on this repository (GitHub → Security → Report a vulnerability) rather than a public issue.
