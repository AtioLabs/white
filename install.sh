#!/usr/bin/env bash
# White one-line installer for macOS and Linux:
#
#   curl -fsSL https://raw.githubusercontent.com/AtioLabs/white/main/install.sh | bash
#
# 1. Installs Hermes Agent if missing (official Nous installer).
# 2. Installs White into Hermes as its own profile, straight from GitHub.
# 3. Switches on White's safety gate and core.
# 4. Helps you pick an AI model (paste your key in the terminal, never in a chat).
# 5. Opens the Hermes desktop app. Choose "white" and say hi.
# Safe to re-run: it updates White and never touches your keys, files or pairing.
set -u

REPO="github.com/AtioLabs/white"
PROFILE="white"
say() { printf '\n  \033[36m%s\033[0m\n' "$1"; }
ok() { printf '  [ok] %s\n' "$1"; }

printf '\n  White - your AI founder'"'"'s office\n  ---------------------------------\n'

if ! command -v hermes >/dev/null 2>&1; then
  say "Step 1 of 5: installing Hermes Agent (one time, a few minutes)..."
  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
  export PATH="$HOME/.local/bin:$PATH"
  command -v hermes >/dev/null 2>&1 || { echo "  Hermes didn't install. Open a new terminal and run this again."; exit 1; }
  ok "Hermes installed"
else
  ok "Step 1 of 5: Hermes found"
fi

say "Step 2 of 5: installing White..."
if hermes profile list 2>/dev/null | grep -qw "$PROFILE"; then
  hermes profile update "$PROFILE" --yes >/dev/null && ok "White updated"
else
  hermes profile install "$REPO" --yes >/dev/null && ok "White installed"
fi

say "Step 3 of 5: switching on White's safety gate and core..."
hermes -p "$PROFILE" plugins enable white-gate >/dev/null 2>&1
hermes -p "$PROFILE" plugins enable white-core >/dev/null 2>&1
ok "Safety gate and core are on"

CFG="${HERMES_HOME:-$HOME/.hermes}/profiles/$PROFILE/config.yaml"
if [ ! -f "$CFG" ] || ! grep -Eq '^\s*default:\s*\S' "$CFG"; then
  say "Step 4 of 5: pick White's AI model."
  echo "  Already pay for ChatGPT, Codex or SuperGrok? Pick it and log in - no API key needed."
  echo "  Otherwise any API key works (OpenRouter, Anthropic, Google, Sarvam, ...)."
  hermes -p "$PROFILE" model </dev/tty
else
  ok "Step 4 of 5: model already set"
fi

say "Step 5 of 5: opening the Hermes desktop app..."
echo "  The very first launch may build the app (5-10 minutes). Progress shows below; the app opens when ready."
printf '\n  When the app opens: pick "white" and say: hi. White walks you through the rest.\n\n'
hermes desktop </dev/tty
