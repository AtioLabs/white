# Checks White's WhatsApp pairing. Prints setting names and modes only; no numbers or secrets.
param([string]$Profile = "white")
$ProfileHome = Join-Path $env:LOCALAPPDATA "hermes\profiles\$Profile"
$creds = Get-ChildItem -Path $ProfileHome -Recurse -Filter creds.json -ErrorAction SilentlyContinue | Select-Object -First 1
if ($creds) { Write-Host "paired session: yes ($($creds.LastWriteTime))" } else { Write-Host "paired session: no (run: hermes -p $Profile whatsapp)" }
$envText = Get-Content (Join-Path $ProfileHome ".env") -Raw
foreach ($n in "WHATSAPP_ENABLED", "WHATSAPP_MODE", "WHATSAPP_ALLOWED_USERS", "WHATSAPP_REPLY_PREFIX") {
    $m = [regex]::Match($envText, "(?m)^$n=(.*)$")
    if (-not $m.Success) { Write-Host ("{0,-24} -" -f $n); continue }
    $v = $m.Groups[1].Value.Trim()
    if ($n -in "WHATSAPP_ENABLED", "WHATSAPP_MODE") { Write-Host ("{0,-24} {1}" -f $n, $v) } else { Write-Host ("{0,-24} set" -f $n) }
}
