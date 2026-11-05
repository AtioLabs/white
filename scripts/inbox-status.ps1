# Show what's in the Desktop White Inbox and what White has filed.
$Inbox = Join-Path ([Environment]::GetFolderPath("Desktop")) "White Inbox"
Get-ChildItem $Inbox -Recurse -File | ForEach-Object { $_.FullName.Substring($Inbox.Length) }
