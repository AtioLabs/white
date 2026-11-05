# Install the inbox watcher and the `white-inbox` cron job (wakes White only when a file is dropped).
param([string]$Hermes = "hermes", [string]$Profile = "white", [string]$Source = "")
$ProfileHome = Join-Path $env:LOCALAPPDATA "hermes\profiles\$Profile"
$scripts = Join-Path $ProfileHome "scripts"
New-Item -ItemType Directory -Force $scripts | Out-Null
if (-not $Source) { $Source = Join-Path $ProfileHome "plugins\white-core\scripts\white_inbox_watch.py" }
Copy-Item $Source (Join-Path $scripts "white_inbox_watch.py") -Force
$jobs = & $Hermes -p $Profile cron list 2>&1 | Out-String
if ($jobs -match "white-inbox") { Write-Host "white-inbox job already exists"; exit 0 }
$prompt = "New file(s) in the White Inbox. Run white_inbox action=scan and handle each item as white-cycle step 1 says (record facts with the item's source, do the work it implies; risky work: prepare it and ask once), then file it. Then white_intent action=context and propose only if a real pattern formed. Reply in at most 3 lines: what you filed and the one decision you need, if any."
& $Hermes -p $Profile cron create "every 5m" $prompt --name white-inbox --monitor-script white_inbox_watch.py --skill white-cycle
