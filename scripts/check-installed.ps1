$ws = Join-Path $env:LOCALAPPDATA "hermes\installs\7dc5c6d9a2c8dc48\environments\53129761675842f5bc925971076f0fd1\workspace"
Select-String -Path (Join-Path $ws "agent\message_sanitization.py") -Pattern "sarvam|_LOCAL_CARRIERS, frozenset|api_msg.pop\(R," | ForEach-Object { "ms $($_.LineNumber): $($_.Line.Trim())" }
Get-ChildItem $ws -Recurse -Filter "*.py" -ErrorAction SilentlyContinue | Select-String -Pattern 'api_msg\["reasoning"\]|\["reasoning"\] = .*reasoning' | ForEach-Object { "$($_.Path.Substring($ws.Length)):$($_.LineNumber): $($_.Line.Trim())" } | Select-Object -First 15
