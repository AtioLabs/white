# Last entries of White's gate log.
$f = Join-Path $env:LOCALAPPDATA "hermes\profiles\white\white\gate-log.jsonl"
if (Test-Path $f) { Get-Content $f -Tail 6 } else { "no gate log at $f" }
