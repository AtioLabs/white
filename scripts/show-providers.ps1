# Print White's provider config with secrets masked (debug helper).
$cfg = Join-Path $env:LOCALAPPDATA "hermes\profiles\white\config.yaml"
Get-Content $cfg | ForEach-Object {
  if ($_ -match "(?i)(api_key|key|token|secret)\s*:\s*\S") { ($_ -replace ":\s*(\S{0,4})\S*", ': $1****') } else { $_ }
} | Select-String -Pattern "fallback|custom|provider|base_url|api_key|key_env|model:|name:|sarvam" -Context 0,0
$envf = Join-Path $env:LOCALAPPDATA "hermes\profiles\white\.env"
Get-Content $envf | ForEach-Object { if ($_ -match "^([A-Z0-9_]+)=(.{0,4})") { "$($Matches[1])=$($Matches[2])****" } }
