# One-command setup for White on Windows. Safe to re-run: installs or updates, never touches
# your founder files, world model or keys.
#
#   powershell -ExecutionPolicy Bypass -File .\setup-white.ps1 [-HermesDir <path to hermes-agent>]
#
# By default it expects hermes-agent cloned next to this repo (..\hermes-agent).

param(
    [string]$HermesDir = (Join-Path (Split-Path $PSScriptRoot -Parent) "hermes-agent"),
    [string]$Profile = "white"
)

$ErrorActionPreference = "Continue"
$WhiteDir = $PSScriptRoot
$Hermes = Join-Path $HermesDir ".hermes\bin\hermes.exe"
function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

if (-not (Test-Path (Join-Path $HermesDir "setup-hermes.ps1"))) {
    Write-Host "Hermes not found at $HermesDir" -ForegroundColor Red
    Write-Host "Clone it first:  git clone https://github.com/NousResearch/hermes-agent `"$HermesDir`""
    exit 1
}

# 1. Hermes runtime
if (-not (Test-Path $Hermes)) {
    Step "Installing the Hermes runtime (first time only, a few minutes)"
    & powershell -ExecutionPolicy Bypass -File (Join-Path $HermesDir "setup-hermes.ps1") -RuntimeOnly
    if (-not (Test-Path $Hermes)) { Write-Host "Hermes setup failed; see above." -ForegroundColor Red; exit 1 }
}

# 2. White profile: install the first time, update after
Step "Installing White's profile"
$profiles = & $Hermes profile list 2>&1 | Out-String
if ($profiles -match "\b$Profile\b") { & $Hermes profile update $Profile --yes }
else { & $Hermes profile install $WhiteDir --yes }

# 3. Plugins
Step "Enabling White's plugins (authority gate + core)"
& $Hermes -p $Profile plugins enable white-gate
& $Hermes -p $Profile plugins enable white-core

# 4. Model (only asks if none is configured yet)
$cfg = Join-Path $env:LOCALAPPDATA "hermes\profiles\$Profile\config.yaml"
if (-not (Test-Path $cfg) -or -not (Select-String -Path $cfg -Pattern "^\s*default:\s*\S" -Quiet)) {
    Step "Pick White's model (paste keys in this window, never in a chat)"
    & $Hermes -p $Profile model
}

# 5. Doctor
Step "White doctor"
& $Hermes -p $Profile white doctor

Write-Host "`nNext:" -ForegroundColor Green
Write-Host "  Chat:          $Hermes -p $Profile chat     (say: run founder-onboarding)"
Write-Host "  Composio:      $Hermes -p $Profile white composio-setup   (COMPOSIO_API_KEY=ak_... in .env)"
Write-Host "  Phone:         $Hermes -p $Profile white phone-setup      (AGENTPHONE_API_KEY in .env, optional)"
Write-Host "  WhatsApp:      $Hermes -p $Profile whatsapp, then: $Hermes gateway install"
