# Compare the profile's white-cycle skill with the repo copy; show curator ledger tail and agent.log tail.
$p = Join-Path $env:LOCALAPPDATA "hermes\profiles\white"
$a = Get-Content "E:\agent\white\skills\founder\white-cycle\SKILL.md"
$b = Get-Content (Join-Path $p "skills\founder\white-cycle\SKILL.md")
Write-Host "=== diff repo (<=) vs profile (=>) ==="
Compare-Object $a $b | Select-Object -First 30 | ForEach-Object { "$($_.SideIndicator) $($_.InputObject)" }
Write-Host "=== curator ledger (last 4) ==="
Get-Content (Join-Path $p "skills\.curator_ledger.jsonl") -Tail 4
Write-Host "=== agent.log (last 25) ==="
Get-Content (Join-Path $p "logs\agent.log") -Tail 25 | ForEach-Object { if ($_.Length -gt 300) { $_.Substring(0, 300) } else { $_ } }
