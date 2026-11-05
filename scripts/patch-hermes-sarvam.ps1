# Patch the installed Hermes so Sarvam gets reasoning_content only (fixes HTTP 400 duplicate field).
$f = Join-Path $env:LOCALAPPDATA "hermes\installs\7dc5c6d9a2c8dc48\environments\53129761675842f5bc925971076f0fd1\workspace\agent\message_sanitization.py"
$text = [System.IO.File]::ReadAllText($f)
if ($text.Contains('"sarvam.ai"')) { Write-Host "already patched"; exit 0 }
Copy-Item $f "$f.bak" -Force
$anchor = '    (_LOCAL_CARRIERS, frozenset({"ollama-cloud", "custom", "lmstudio", "upstage"})'
$nl = "`n"; if ($text.Contains("`r`n")) { $nl = "`r`n" }
$add = '    # Sarvam aliases reasoning/reasoning_content: both keys -> HTTP 400 duplicate field.' + $nl + '    (frozenset({RC}), frozenset(), ("sarvam.ai",)),' + $nl
$text = $text.Replace($anchor, $add + $anchor)
[System.IO.File]::WriteAllText($f, $text, (New-Object System.Text.UTF8Encoding($false)))
Get-ChildItem (Join-Path (Split-Path $f) "__pycache__") -Filter "message_sanitization*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force
Write-Host "patched"
