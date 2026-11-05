# Copy local White plugins and founder skills into the installed 'white' Hermes profile (dev use, no push needed).
$Repo = Split-Path -Parent $PSScriptRoot
$ProfileHome = Join-Path $env:LOCALAPPDATA "hermes\profiles\white"
if (-not (Test-Path $ProfileHome)) { Write-Host "No white profile at $ProfileHome"; exit 1 }
foreach ($p in "white-core", "white-gate") {
  $dst = Join-Path $ProfileHome "plugins\$p"
  New-Item -ItemType Directory -Force $dst | Out-Null
  Copy-Item (Join-Path $Repo "plugins\$p\*") $dst -Recurse -Force
  Write-Host "$p -> $dst"
}
$skills = Join-Path $ProfileHome "skills\founder"
New-Item -ItemType Directory -Force $skills | Out-Null
Copy-Item (Join-Path $Repo "skills\founder\*") $skills -Recurse -Force
Write-Host "founder skills -> $skills"
$bench = Join-Path $ProfileHome "bench"
New-Item -ItemType Directory -Force $bench | Out-Null
Get-ChildItem (Join-Path $Repo "bench") -File | Copy-Item -Destination $bench -Force
Write-Host "bench -> $bench"
New-Item -ItemType Directory -Force (Join-Path $ProfileHome "founder\inbox") | Out-Null
Write-Host "Restart White's gateway to load it: hermes -p white gateway stop; hermes -p white gateway start"
