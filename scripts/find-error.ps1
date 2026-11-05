# Find recent SQLite/thread errors in White's logs and sessions (prints only matching lines).
$p = Join-Path $env:LOCALAPPDATA "hermes\profiles\white"
Get-ChildItem $p -Recurse -File -Include *.log, *.jsonl, *.json -ErrorAction SilentlyContinue |
  Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-3) -and $_.Length -lt 50MB } |
  Select-String -Pattern "thread|ProgrammingError|Recursive use|database is locked" |
  Select-Object -Last 8 | ForEach-Object {
    $l = $_.Line; if ($l.Length -gt 400) { $i = [Math]::Max(0, $l.IndexOf("thread") - 200); $l = $l.Substring($i, [Math]::Min(400, $l.Length - $i)) }
    "$($_.Filename): $l"
  }
