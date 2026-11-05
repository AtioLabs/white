# Which White files in the profile differ from the repo (did White edit its own code?).
$p = Join-Path $env:LOCALAPPDATA "hermes\profiles\white"
$repo = "E:\agent\white"
foreach ($sub in "plugins\white-core", "plugins\white-gate", "skills\founder") {
  Get-ChildItem (Join-Path $repo $sub) -Recurse -File | Where-Object { $_.FullName -notmatch "__pycache__" } | ForEach-Object {
    $rel = $_.FullName.Substring($repo.Length + 1)
    $other = Join-Path $p $rel
    if (-not (Test-Path $other)) { "MISSING  $rel" }
    elseif ((Get-FileHash $_.FullName).Hash -ne (Get-FileHash $other).Hash) { "CHANGED  $rel" }
  }
}
Select-String -Path (Join-Path $p "plugins\white-core\*.py") -Pattern "_ensure_thread" | ForEach-Object { "HAS _ensure_thread: $($_.Filename):$($_.LineNumber)" }
