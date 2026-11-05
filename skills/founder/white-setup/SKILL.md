---
name: white-setup
description: Walk a non-technical founder through finishing setup.
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Setup, Onboarding, White]
    category: founder
    related_skills: [founder-onboarding, white-connect, white-cycle, white-identity]
---

# White Setup Skill

Most founders aren't developers. After the one-line install, White finishes its own setup *in the chat*, one plain-language step at a time, the way a new hire sets up their own laptop and asks for the few things only the boss can give. The founder should never need to open a config file or learn a command.

## When to Use

- The first conversation, or whenever `white_status` reports something missing.
- "Set me up", "what else do you need?", "connect my WhatsApp/Gmail".

## Procedure

1. **Check, don't ask.** Call `white_status`. Say in one line what's already working, then only what's missing, as a short numbered list ordered by impact: **founder profile and charter → apps (Gmail/Calendar) → WhatsApp → White's schedule**. Skip anything optional the founder didn't ask for (White's own inbox and phone).
2. **One step at a time.** Do the next step, confirm it worked (call `white_status` again), then offer the next. Never dump all the steps at once.
3. **Plain words, no jargon.** Say "your Hermes app settings", not "the profile's .env". Say "a key from Composio's website", not "API credential". Keep commands out of the chat; if one is truly unavoidable, give exactly one line and say where to paste it.
4. **The steps:**
   - **Founder profile and charter:** run `founder-onboarding`. This is the most important step, because White can't prioritize without it.
   - **Apps (Gmail, Calendar, LinkedIn):** explain why in one sentence ("so I can see your real week"). Ask the founder to create a free Composio account, copy the key starting with `ak_`, and add it in the Hermes app under **Settings → Keys/Environment** as `COMPOSIO_API_KEY`, never pasted into the chat. Then the founder runs one line, `hermes -p white white composio-setup`, and you connect apps one at a time with `white-connect` when a task needs them.
   - **WhatsApp:** explain that White's check-ins arrive there. In the Hermes app go to **Messaging → WhatsApp**, follow its QR step, choose *self-chat*, then approve the pairing request in the same Messaging page. After the first message, the founder sends `/sethome`.
   - **Schedule:** run `white-cycle` step 0 so White schedules its own check-ins.
5. **Keys, the one hard rule:** never ask for, accept, or repeat a key in chat. If the founder pastes one, tell them to delete that message and rotate the key, and don't use it.
6. **Finish** with one line: "You're set. Here's today's one thing: …", from `white_judge`.

## Pitfalls

- **Overwhelming the founder.** One step per message.
- **Jargon.** If a non-technical founder wouldn't understand a word, replace it.
- **Pretending something worked.** Recheck with `white_status` after each step.
- **Accepting keys in chat.** Never.

## Verification

- `white_status` reports `ready: true`, or the founder chose to skip the remaining optional steps.
- The founder never had to edit a file by hand.
