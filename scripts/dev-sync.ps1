# Copy local White plugin/skill changes into the installed 'white' Hermes profile (dev use, no push needed).
$Repo = Split-Path -Parent $PSScriptRoot
$ProfileHome = Join-Path $env:LOCALAPPDATA "hermes\profiles\white"
if (-not (Test-Path $ProfileHome)) { Write-Host "No white profile at $ProfileHome"; exit 1 }
$core = Get-ChildItem $ProfileHome -Recurse -Filter white_judgment.py -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $core) { Write-Host "white-core not found in profile"; exit 1 }
Copy-Item (Join-Path $Repo "plugins\white-core\*") $core.DirectoryName -Recurse -Force
Write-Host "white-core -> $($core.DirectoryName)"
$cycle = Get-ChildItem $ProfileHome -Recurse -Filter SKILL.md -ErrorAction SilentlyContinue | Where-Object { $_.Directory.Name -eq "white-cycle" } | Select-Object -First 1
if ($cycle) { Copy-Item (Join-Path $Repo "skills\founder\white-cycle\SKILL.md") $cycle.FullName -Force; Write-Host "white-cycle -> $($cycle.FullName)" }
New-Item -ItemType Directory -Force (Join-Path $ProfileHome "founder\inbox") | Out-Null
Write-Host "Inbox ready: $(Join-Path $ProfileHome 'founder\inbox')"
Write-Host "Restart White's gateway to load it: hermes -p white gateway stop; hermes -p white gateway start"
