# List the most recently changed files in White's profile (to see what a run was doing).
$p = Join-Path $env:LOCALAPPDATA "hermes\profiles\white"
Get-ChildItem $p -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch "\\node_modules\\|\\.git\\" } |
  Sort-Object LastWriteTime -Descending | Select-Object -First 15 |
  ForEach-Object { "{0:HH:mm:ss}  {1,10}  {2}" -f $_.LastWriteTime, $_.Length, $_.FullName.Substring($p.Length) }
