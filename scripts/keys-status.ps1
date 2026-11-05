# Shows which keys are set in White's .env. Never prints values.
param([string]$Profile = "white")
$ProfileEnv = Join-Path $env:LOCALAPPDATA "hermes\profiles\$Profile\.env"
if (-not (Test-Path $ProfileEnv)) { Write-Host "No .env at $ProfileEnv"; exit 1 }
$text = Get-Content $ProfileEnv -Raw
$names = "GOOGLE_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "AGENTMAIL_API_KEY", "AGENTPHONE_API_KEY", "COMPOSIO_API_KEY", "COMPOSIO_CONSUMER_KEY"
foreach ($name in $names) {
    $state = if ($text -match "(?m)^$name=\S{6,}") { "set" } elseif ($text -match "(?m)^$name=") { "present but looks too short" } else { "-" }
    Write-Host ("{0,-24} {1}" -f $name, $state)
}
