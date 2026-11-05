---
name: white-computer
description: "Use any app on the founder's computer through its accessibility tree (agent-desktop), not screenshots."
version: 0.1.0
author: Asrul Ishath (asynarch), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Founder, Computer Use, Desktop, White]
    category: founder
    related_skills: [white-cycle, white-connect]
---

# White Computer Skill

When work needs an app that has no API or Composio connection (a desktop app, a web app with no integration, a file dialog), use `white_desktop`. It reads the app's accessibility tree, so it costs far fewer tokens than screenshots and clicks the exact element.

## When to Use

- The founder points you at a tool ("use Ploy", "do it in Excel") and there's no API, CLI or connection for it.
- A task needs a desktop app: spreadsheets, design tools, installers, settings pages inside an app.
- Order of preference: **API / Composio → CLI → `white_desktop` → screenshots** (last resort, for apps with no tree).

## Procedure

1. `white_desktop` command=`launch` args=[`<App>`] (or `focus-window`), if it isn't open.
2. `white_desktop` command=`snapshot` args=[`--app`, `<App>`, `-i`, `--compact`]. `-i` = interactive elements only. For big apps add `--skeleton` first, then snapshot the part you need.
3. Pick the element by its **role and name**. Act with its ref and give its real name as `label`:
   - click: command=`click` ref=`@s…:eN` label=`<name>`
   - fill a field: command=`set-value` ref=… label=… args=[`<text>`]
   - keys: command=`press` args=[`ctrl+s`] label=`save`
4. **Snapshot again** and check the change happened. Never report success you didn't see.
5. Refs expire with each snapshot: always act on refs from the latest one.

## Safety

- Anything that sends, pays, posts, signs, deletes or submits goes to the founder for approval automatically (white-gate). Prepare everything up to that click, then ask one question.
- Never put a fake `label` on an element: the tool checks the real name and refuses.
- Don't run raw `agent-desktop` actions in the terminal; the gate stops them. Read-only commands (snapshot, list-apps) are fine there.

## Pitfalls

- `NOT_INSTALLED`: tell the founder `npm install -g agent-desktop` is needed (one time), don't try workarounds.
- Empty or tiny tree (some games, canvas apps): fall back to screenshots and say so.
- `PERM_DENIED` on Windows: the app runs as admin and White doesn't. Ask the founder to open it normally.
- On Windows, `type` needs `--headed`; prefer `set-value`.
