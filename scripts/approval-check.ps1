# White's approval settings and recent approval decisions in the log.
$p = Join-Path $env:LOCALAPPDATA "hermes\profiles\white"
Select-String -Path (Join-Path $p "config.yaml") -Pattern "^approvals:" -Context 0,10
Select-String -Path (Join-Path $p "logs\agent.log") -Pattern "guardian|smart.approv|plugin_rule|AUTO-APPROVED|approval" |
  Select-Object -Last 8 | ForEach-Object { $l = $_.Line; if ($l.Length -gt 260) { $l.Substring(0, 260) } else { $l } }
