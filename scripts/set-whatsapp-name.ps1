# Sets White's WhatsApp reply header (replaces Hermes's default) in the profile's .env.
# ASCII-only on purpose: Windows PowerShell 5.1 misreads non-ASCII in BOM-less scripts.
# Writes UTF-8 WITHOUT a BOM: a BOM would corrupt the first key name in .env.
param([string]$Profile = "white", [string]$Name = "White")
$ProfileEnv = Join-Path $env:LOCALAPPDATA "hermes\profiles\$Profile\.env"
$rule = ([string][char]0x2500) * 12
$prefix = 'WHATSAPP_REPLY_PREFIX="*' + $Name + '*\n' + $rule + '\n"'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$text = ""
if (Test-Path $ProfileEnv) { $text = [System.IO.File]::ReadAllText($ProfileEnv, $utf8NoBom).TrimStart([char]0xFEFF) }
$kept = @($text -split "`r?`n" | Where-Object { $_ -ne "" -and $_ -notmatch "^WHATSAPP_REPLY_PREFIX=" })
$kept += $prefix
[System.IO.File]::WriteAllText($ProfileEnv, (($kept -join "`n") + "`n"), $utf8NoBom)
Write-Host "WhatsApp replies will show: $Name (restart the gateway to apply)"
