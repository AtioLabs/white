# Show where reasoning fields appear in the latest Hermes request dump (no message text printed).
$logs = Join-Path $env:LOCALAPPDATA "hermes\profiles\white\logs"
$f = Get-ChildItem (Join-Path $env:LOCALAPPDATA "hermes") -Recurse -Filter "request_dump_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host "dump: $($f.Name)"
$j = Get-Content $f.FullName -Raw | ConvertFrom-Json
$b = $j.request.body
Write-Host "top-level body keys: $(($b.PSObject.Properties.Name) -join ', ')"
$i = 0
foreach ($m in $b.messages) {
  $keys = $m.PSObject.Properties.Name
  if ($keys -match "reason") { Write-Host "msg $i role=$($m.role) keys: $($keys -join ', ')" }
  $i++
}
Write-Host "messages: $i"
