# Pin reasoning to "none" for White's Sarvam fallback model (avoids Hermes duplicate-reasoning 400).
$cfg = Join-Path $env:LOCALAPPDATA "hermes\profiles\white\config.yaml"
$model = "deepseekv4.1-flash-1017"
$lines = [System.Collections.Generic.List[string]](Get-Content $cfg -Encoding utf8)
if (($lines -join "`n") -match [regex]::Escape("${model}: none")) { Write-Host "already set"; exit 0 }
Copy-Item $cfg "$cfg.bak2" -Force
$agent = $lines.IndexOf("agent:")
if ($agent -lt 0) { $lines.Add("agent:"); $agent = $lines.Count - 1 }
$ro = -1
for ($i = $agent + 1; $i -lt $lines.Count -and ($lines[$i] -match "^\s" -or $lines[$i] -eq ""); $i++) {
  if ($lines[$i] -match "^  reasoning_overrides:") { $ro = $i; break }
}
if ($ro -ge 0) {
  $lines[$ro] = "  reasoning_overrides:"
  $lines.Insert($ro + 1, "    ${model}: none")
} else {
  $lines.Insert($agent + 1, "  reasoning_overrides:")
  $lines.Insert($agent + 2, "    ${model}: none")
}
[System.IO.File]::WriteAllLines($cfg, $lines, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Sarvam reasoning set to none"
