# White one-line installer for Windows. Run in PowerShell:
#
#   irm https://raw.githubusercontent.com/AtioLabs/white/main/install.ps1 | iex
#
# What it does, in plain words:
#   1. Installs Hermes Agent and its desktop app, if you don't have them yet (official Nous installer).
#   2. Installs White into Hermes as its own profile, straight from GitHub.
#   3. Switches on White's safety gate and core.
#   4. Helps you pick an AI model (you paste your key here, never in a chat).
#   5. Opens the Hermes desktop app. Choose "white" in the sidebar and say hi.
#
# Safe to run again: it updates White and never touches your keys, files or WhatsApp pairing.
# This file is ASCII-only on purpose (Windows PowerShell 5.1 misreads other characters).

$ErrorActionPreference = "Continue"
$WhiteRepo = "github.com/AtioLabs/white"
$Profile = "white"

function Say($msg) { Write-Host "`n  $msg" -ForegroundColor Cyan }
function Ok($msg) { Write-Host "  [ok] $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow }

function Find-Hermes {
    if ($env:WHITE_HERMES -and (Test-Path $env:WHITE_HERMES)) { return $env:WHITE_HERMES }
    $cmd = Get-Command hermes -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $default = Join-Path $env:LOCALAPPDATA "hermes\hermes-agent\.hermes\bin\hermes.exe"
    if (Test-Path $default) { return $default }
    return $null
}

Write-Host ""
Write-Host "  White - your AI founder's office" -ForegroundColor White
Write-Host "  ---------------------------------"

# 1. Hermes
$Hermes = Find-Hermes
if (-not $Hermes) {
    Say "Step 1 of 5: installing Hermes Agent and its desktop app (one time, about 5-10 minutes)..."
    $tmp = Join-Path $env:TEMP "hermes-install.ps1"
    Invoke-RestMethod "https://hermes-agent.nousresearch.com/install.ps1" -OutFile $tmp
    & powershell -NoProfile -ExecutionPolicy Bypass -File $tmp -IncludeDesktop -NonInteractive
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
    $Hermes = Find-Hermes
    if (-not $Hermes) {
        Warn "Hermes didn't install. Open a new PowerShell window and run this line again, or see https://github.com/NousResearch/hermes-agent"
        return
    }
    Ok "Hermes installed"
} else {
    Ok "Step 1 of 5: Hermes found"
}

# 2. White profile
Say "Step 2 of 5: installing White..."
$profiles = & $Hermes profile list 2>&1 | Out-String
if ($profiles -match "\b$Profile\b") { & $Hermes profile update $Profile --yes | Out-Null; Ok "White updated" }
else { & $Hermes profile install $WhiteRepo --yes | Out-Null; Ok "White installed" }

# 3. Plugins
Say "Step 3 of 5: switching on White's safety gate and core..."
& $Hermes -p $Profile plugins enable white-gate 2>&1 | Out-Null
& $Hermes -p $Profile plugins enable white-core 2>&1 | Out-Null
$ProfileHome = Join-Path $env:LOCALAPPDATA "hermes\profiles\$Profile"
$envPath = Join-Path $ProfileHome ".env"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$envText = ""
if (Test-Path $envPath) { $envText = [System.IO.File]::ReadAllText($envPath, $utf8NoBom).TrimStart([char]0xFEFF) }
if ($envText -notmatch "(?m)^WHATSAPP_REPLY_PREFIX=") {
    $line = 'WHATSAPP_REPLY_PREFIX="*White*\n' + (([string][char]0x2500) * 12) + '\n"'
    $sep = if ($envText -and -not $envText.EndsWith("`n")) { "`n" } else { "" }
    [System.IO.File]::WriteAllText($envPath, $envText + $sep + $line + "`n", $utf8NoBom)
}
Ok "Safety gate and core are on"
# Spend limits per run: a stuck loop can't burn through a founder's model credit.
& $Hermes -p $Profile config set agent.max_turns 60 2>&1 | Out-Null
& $Hermes -p $Profile config set agent.budget_warning_ratio 0.75 2>&1 | Out-Null
& $Hermes -p $Profile config set agent.run_budget_seconds 900 2>&1 | Out-Null
# White Inbox on the Desktop: drop anything there, White files it and does the work.
$WhiteInbox = Join-Path ([Environment]::GetFolderPath("Desktop")) "White Inbox"
New-Item -ItemType Directory -Force $WhiteInbox | Out-Null
$inboxCfg = Join-Path $ProfileHome "founder\inbox.yaml"
New-Item -ItemType Directory -Force (Split-Path $inboxCfg) | Out-Null
if (-not (Test-Path $inboxCfg) -or -not (Select-String -Path $inboxCfg -SimpleMatch $WhiteInbox -Quiet)) {
    if (-not (Test-Path $inboxCfg)) { [System.IO.File]::WriteAllText($inboxCfg, "folders:`n", $utf8NoBom) }
    [System.IO.File]::AppendAllText($inboxCfg, "  - $WhiteInbox`n", $utf8NoBom)
}
Ok "White Inbox is on your Desktop"

# 4. Model
$cfg = Join-Path $ProfileHome "config.yaml"
$hasModel = (Test-Path $cfg) -and (Select-String -Path $cfg -Pattern "^\s*default:\s*\S" -Quiet)
if (-not $hasModel) {
    Say "Step 4 of 5: pick White's AI model."
    Write-Host "  Already pay for ChatGPT, Codex or SuperGrok? Pick it and log in - no API key needed."
    Write-Host "  Otherwise any API key works (OpenRouter, Anthropic, Google, Sarvam, ...)."
    Write-Host "  Paste your key ONLY in this window."
    & $Hermes -p $Profile model
} else {
    Ok "Step 4 of 5: model already set"
}

# 5. Desktop
Say "Step 5 of 5: opening the Hermes desktop app..."
Write-Host "  A second window opens for the app. The very first time it may need to build itself,"
Write-Host "  which can take 5-10 minutes. Leave that window open; the app appears when it's ready."
Start-Process -FilePath $Hermes -ArgumentList "desktop"
Write-Host ""
Write-Host "  Done. When the app opens: pick 'white' in the sidebar and say: hi" -ForegroundColor Green
Write-Host "  White will walk you through the rest (your profile, WhatsApp, your apps)."
Write-Host "  If no app appears, run:  hermes desktop"
Write-Host ""
