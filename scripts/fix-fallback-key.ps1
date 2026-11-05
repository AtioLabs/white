# Hermes `fallback add` drops key_env for custom endpoints; add it back for the Sarvam fallback.
$cfg = Join-Path $env:LOCALAPPDATA "hermes\profiles\white\config.yaml"
Copy-Item $cfg "$cfg.bak" -Force
$lines = [System.Collections.Generic.List[string]](Get-Content $cfg -Encoding utf8)
$inFb = $false
for ($i = 0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match "^fallback_providers:") { $inFb = $true; continue }
  if ($inFb -and $lines[$i] -match "^\S") { break }
  if ($inFb -and $lines[$i] -match "^\s+base_url:\s*https://api\.sarvam\.ai") {
    $indent = ($lines[$i] -replace "base_url.*", "")
    if (-not ($lines[$i + 1] -match "key_env")) {
      $lines.Insert($i + 1, "${indent}key_env: HERMES_CUSTOM_API_SARVAM_AI_API_KEY")
      Write-Host "Added key_env to Sarvam fallback"
    } else { Write-Host "key_env already present" }
  }
}
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllLines($cfg, $lines, $utf8NoBom)
