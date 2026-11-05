$root = Join-Path $env:LOCALAPPDATA "hermes"
Get-ChildItem $root -Recurse -Filter message_sanitization.py -ErrorAction SilentlyContinue | ForEach-Object {
  $_.FullName
  Select-String -Path $_.FullName -Pattern '"custom", "lmstudio"' | ForEach-Object { "  line $($_.LineNumber): $($_.Line.Trim())" }
}
