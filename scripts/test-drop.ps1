# Drop a fake test note into the Desktop White Inbox (for live testing).
$Inbox = Join-Path ([Environment]::GetFolderPath("Desktop")) "White Inbox"
$note = @"
TEST NOTE (White 2.0 live test, fake data)
Call with Meera Iyer, Head of Ops at Lumen Logistics, 5 Nov 2026.
- They lose ~6 hrs/week reconciling delivery exceptions by hand.
- Meera wants a 2-week pilot. She asked for a one-page proposal by Monday 9 Nov.
- I promised to send pricing options too.
- She can intro us to their CFO, Arjun, if the pilot goes well.
"@
Set-Content -Path (Join-Path $Inbox "test-call-notes-lumen.txt") -Value $note -Encoding utf8
Get-ChildItem $Inbox -File | ForEach-Object { $_.Name }
